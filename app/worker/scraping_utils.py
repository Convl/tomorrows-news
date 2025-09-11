import asyncio
import concurrent.futures
import html
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import feedparser
import newspaper
from bs4 import BeautifulSoup, Comment
from langchain_core.messages import HumanMessage
from markdownify import markdownify
from newspaper import Article, Config

from app.core.enums import ScrapingSourceEnum
from app.models.scraping_source import ScrapingSourceDB

from .llm_service import LlmService
from .scraping_models import ExtractedWebSources, ScrapingSourceWorkflow, WebSourceBase, WebSourceWithMarkdown

if TYPE_CHECKING:
    from loguru import Logger


MIN_ENTRIES_TO_CONSIDER_VALID_LISTING = 8
MIN_ARTICLE_LENGTH = 1000
MAX_ARTICLE_LENGTH = 30000


def struct_time_to_datetime(struct_time_obj) -> datetime | None:
    """Convert feedparser's struct_time to datetime with UTC timezone."""
    if struct_time_obj is None:
        return None
    try:
        # Feedparser converts dates to UTC before converting them into tz-naive struct_time objects, so we can safely set UTC for the datetime object
        utc_dt = datetime(*struct_time_obj[:6], tzinfo=timezone.utc)
        return utc_dt
    except (ValueError, TypeError):
        return None


async def web_sources_from_scraping_source(
    scraping_source: ScrapingSourceWorkflow, logger: "Logger", llm_service: LlmService
) -> list[WebSourceWithMarkdown]:
    scraping_source._visited = True
    match scraping_source.source_type:
        case ScrapingSourceEnum.WEBPAGE:
            if scraping_source.degrees_of_separation == 0:
                return [await download_and_parse_article(scraping_source.base_url, logger=logger)]
            else:
                return await extract_sources_from_web(scraping_source, logger, llm_service)
        case ScrapingSourceEnum.RSS:
            return await extract_sources_from_rss(scraping_source, logger)
        case _:
            raise ValueError(f"Unsupported source type: {scraping_source.source_type}")


async def extract_sources_from_web(
    scraping_source: ScrapingSourceWorkflow, logger: "Logger", llm_service: LlmService
) -> list[WebSourceWithMarkdown]:
    """Extract sources from a website, using newspaper if possible, LLM-assisted if not."""
    sources = []

    config = Config()
    config.memorize_articles = False
    config.disable_category_cache = True
    config.thread_timeout_seconds = 120

    logger.info("🔄 About to call newspaper.build for {url}...", url=scraping_source.base_url)

    # Create a task that we can monitor
    import time

    start_time = time.time()

    async def newspaper_build_with_progress():
        """Wrapper that logs progress during newspaper.build"""
        try:
            logger.info("📰 Starting newspaper.build thread...")
            result = await asyncio.to_thread(
                newspaper.build, scraping_source.base_url, only_in_path=True, config=config
            )
            logger.info("📰 newspaper.build thread completed successfully")
            return result
        except Exception as e:
            logger.error("📰 newspaper.build thread failed: <red>{e}</red>", e=e)
            raise

    # Monitor progress every 30 seconds
    async def progress_monitor():
        """Monitor and log progress every 30 seconds"""
        while True:
            await asyncio.sleep(30)
            elapsed = time.time() - start_time
            logger.info("⏱️  newspaper.build still running... {elapsed:.1f}s elapsed", elapsed=elapsed)

    try:
        # Start both the newspaper task and progress monitor
        newspaper_task = asyncio.create_task(newspaper_build_with_progress())
        monitor_task = asyncio.create_task(progress_monitor())

        # Wait for newspaper task with timeout, cancel monitor when done
        try:
            website = await asyncio.wait_for(newspaper_task, timeout=120)  # 2 minute timeout
            monitor_task.cancel()
            logger.info(
                "✅ newspaper.build completed for {url}, found {count} articles",
                url=scraping_source.base_url,
                count=len(website.articles),
            )
        except asyncio.TimeoutError:
            # Cancel both tasks
            newspaper_task.cancel()
            monitor_task.cancel()
            logger.error(
                "❌ TIMEOUT: newspaper.build took longer than 2 minutes for {url}", url=scraping_source.base_url
            )
            raise Exception(f"newspaper.build timed out for {scraping_source.base_url}")

    except Exception as e:
        logger.error("❌ ERROR in newspaper.build for {url}: <red>{e}</red>", url=scraping_source.base_url, e=e)
        raise

    # If newspaper failed to propperly retrieve the articles listed on the page...
    if len(website.articles) < MIN_ENTRIES_TO_CONSIDER_VALID_LISTING:
        # Parse the page AS an Article instead
        log = f"❌ Newspaper failed to retrieve scraping source <cyan>{scraping_source.id}</cyan> ({scraping_source.base_url}) as Website, falling back to LLM-assisted parsing."
        website = Article(scraping_source.base_url, memoize_articles=False, disable_category_cache=True)

        logger.info("🔄 About to download article for LLM parsing...")
        try:
            await asyncio.wait_for(asyncio.to_thread(website.download), timeout=60)  # 1 minute timeout
            await asyncio.wait_for(asyncio.to_thread(website.parse), timeout=30)  # 30 second timeout
            logger.info("✅ Article download and parse completed for LLM processing")
        except asyncio.TimeoutError:
            logger.error("❌ TIMEOUT: Article download/parse took too long for {url}", url=scraping_source.base_url)
            raise Exception(f"Article processing timed out for {scraping_source.base_url}")
        except Exception as e:
            logger.error("❌ ERROR in article download/parse: <red>{e}</red>", e=e)
            raise

        # Choose Website as parsed by newspaper or raw html for source extraction
        input = choose_input_for_listing_page(website.article_html, website.html, scraping_source.base_url, logger)
        if input is None:
            log += "❌ Could not determine input for markdownify. Skipping."
            logger.warning(log)
            return []
        markdown = markdownify(input)

        # Let LLM extract sources from the page
        messages = [
            await llm_service.get_source_extraction_system_message(scraping_source.topic, scraping_source.base_url),
            HumanMessage(f"Extract sources from the following webpage: {markdown}"),
        ]
        response = await asyncio.wait_for(
            llm_service.source_extracting_llm.ainvoke(messages),
            timeout=180,  # 3 minute timeout
        )
        extracted_sources: list[WebSourceBase] = response["parsed"].sources
        log += f" LLM extracted <cyan>{len(extracted_sources)}</cyan> sources from scraping source with id:<cyan>{scraping_source.id}</cyan> ({scraping_source.base_url})."
        logger.info(log)

        for extracted_source in extracted_sources:
            # Below check avoids parsing unnecessary articles. Commented out for now because LLM-determined date from listings page might not be reliable enough
            # if extracted_source.date and extracted_source.date < scraping_source.last_scraped_at:
            #     continue

            source = await download_and_parse_article(
                extracted_source.url,
                date_according_to_calling_func=extracted_source.date,
                prefer_own_publish_date=True,  # LLM-determined publish-date probably less reliable than newspaper-determined publish date of the actual article
                degrees_of_separation=1,
                logger=logger,
            )
            await asyncio.sleep(0.1)

            # At this point, the source must have a recent date, either from the llm, or from newspaper
            if source and source.date >= scraping_source.last_scraped_at:
                sources.append(source)

    else:
        # If newspaper was able to retrieve the articles listed on the page, parse them one by one, no need for LLM to get involved.
        logger.info(
            "✅ Newspaper successfully parsed scraping source <cyan>{id}</cyan> ({base_url}) as Website, now processing <yellow>{count}</yellow> articles",
            id=scraping_source.id,
            base_url=scraping_source.base_url,
            count=len(website.articles),
        )
        for article in website.articles:
            source = await download_and_parse_article(article.url, degrees_of_separation=1, logger=logger)
            if source and source.date >= scraping_source.last_scraped_at:
                sources.append(source)
            await asyncio.sleep(0.1)

    return sources


def choose_input_for_listing_page(article_html: str, full_html: str, base_url: str, logger: "Logger") -> str | None:
    """Choose the best HTML input for a listing page that should contain article links."""
    from urllib.parse import urlparse

    domain = urlparse(base_url).netloc

    # Check if article_html contains meaningful article links
    if _has_sufficient_article_links(article_html, domain):
        logger.info("✅ Article HTML contains sufficient article links, using it")
        return article_html
    elif _has_sufficient_article_links(full_html, domain):
        logger.info("❌ Article HTML does not contain sufficient article links, but full HTML does, using it")
        # no return sanitize(full_html) here, as it is only suited for articles, not listing pages
        return full_html
    else:
        logger.info("❌ Neither HTML version contains sufficient article links")
        return None


def _has_sufficient_article_links(html_content: str, domain: str, min_links: int = 5) -> bool:
    """Check if HTML contains at least min_links that look like article links."""
    if not html_content or not html_content.strip():
        return False

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        article_links = set()

        # Find all links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "").strip()
            if not href:
                continue

            # Skip obvious non-article links
            if _is_likely_article_link(href, domain):
                article_links.add(href)

            if len(article_links) >= min_links:
                return True

        return False

    except Exception:
        return False


def _is_likely_article_link(href: str, domain: str) -> bool:
    """Determine if a link is likely to be an article link."""
    # TODO: This function is not very useful right now, as too many non-article-links will make it through

    href_lower = href.lower()

    skip_patterns = ["#", "mailto:", "tel:", "javascript:"]

    for pattern in skip_patterns:
        if href_lower.startswith(pattern):
            return False

    # Must be internal link or full URL to same domain
    if href.startswith("/"):
        return True
    elif domain in href:
        return True

    return False


def choose_input_for_markdownify(article_html: str, full_html: str, logger: "Logger") -> str | None:
    """Choose the input for markdownify based on the quality of the article HTML."""
    if _is_article_html_good_quality(article_html):
        logger.info("✅ Article HTML as parsed by newspaper is good quality, using it")
        return article_html
    else:
        sanitized_html = sanitize_html(full_html)
        if sanitized_html is None:
            logger.info(
                "❌ Could not sanitize HTML manually. Notice that this might be due to the article being behind a paywall, so MIN_ARTICLE_LENGTH might never be reached."
            )
            return None
        else:
            logger.info("✅ Successfully sanitized HTML manually")
            return sanitized_html


def extract_main_content_by_ratio(raw_html: str) -> str | None:
    """Extract main article content using recursive text-to-HTML ratio analysis."""

    try:
        soup = BeautifulSoup(raw_html, "html.parser")

        # Pre-filter HTML to remove guaranteed non-content elements
        filtered_soup = prefilter_html(soup)

        # Find leaf text elements (elements with text but no text-containing children)
        leaf_text_elements = find_leaf_text_elements(filtered_soup)

        if not leaf_text_elements:
            return raw_html

        # Find optimal container using bottom-up recursive analysis
        memo = {}
        best_element = None
        best_score = 0

        for leaf_element in leaf_text_elements:
            optimal_element, score = find_optimal_higher_node(leaf_element, memo)
            text_length = len(optimal_element.get_text(strip=True))

            if text_length >= MIN_ARTICLE_LENGTH and score > best_score:
                best_score = score
                best_element = optimal_element

        if best_element is not None:
            # Clean empty elements from the result before returning
            cleaned_element = remove_empty_elements(best_element)
            return str(cleaned_element)
        else:
            return None

    except Exception:
        return None


def remove_empty_elements(element):
    """Remove empty child elements from the given element."""
    # Find all descendants that have no text content
    empty_elements = []
    for child in element.find_all():
        # Skip if this element has text content
        if child.get_text(strip=True):
            continue

        # Skip important structural elements even if empty
        if child.name in ["br", "hr", "wbr"]:
            continue

        empty_elements.append(child)

    # Remove empty elements
    for empty_elem in empty_elements:
        empty_elem.decompose()

    return element


def find_leaf_text_elements(soup: BeautifulSoup) -> list:
    """Find leaf text elements - elements that contain text but have no text-containing children."""
    leaf_elements = []

    # Get all elements that contain text
    text_containing_elements = []
    for element in soup.find_all():
        if element.get_text(strip=True):
            text_containing_elements.append(element)

    # Filter to only leaf elements (no text-containing descendants)
    for element in text_containing_elements:
        has_text_containing_children = False

        # Check if any descendants contain text
        for descendant in element.find_all():
            if descendant != element and descendant.get_text(strip=True):
                has_text_containing_children = True
                break

        if not has_text_containing_children:
            leaf_elements.append(element)

    return leaf_elements


def prefilter_html(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove elements guaranteed not to contain article content."""
    # Elements to remove completely
    unwanted_tags = [
        "script",
        "style",
        "noscript",
        "img",
        "svg",
        "video",
        "nav",
        "footer",
        "header",
        "aside",
        "iframe",
        "canvas",
        "audio",
        "track",
        "source",
        "object",
        "embed",
        "map",
        "area",
        "form",
        "button",
        "input",
        "select",
        "textarea",
        "progress",
        "meter",
        "menu",
        "menuitem",
        "dialog",
        "template",
    ]

    for tag_name in unwanted_tags:
        for element in soup.find_all(tag_name):
            element.decompose()

    # Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    return soup


def calculate_container_score(element) -> float:
    """Calculate score as text_length * text_to_html_ratio."""
    if not element:
        return 0.0

    # Get text content of current + all children
    text_content = element.get_text(strip=True)
    text_length = len(text_content)

    if text_length == 0:
        return 0.0

    # Get HTML markup length of current, including all children
    html_content = str(element)
    markup_length = len(html_content) - text_length

    if markup_length < 0:
        markup_length = 0

    # Calculate text-to-HTML ratio
    total_length = text_length + markup_length
    if total_length == 0:
        return 0.0

    text_to_html_ratio = text_length / total_length

    # Final score: text_length * ratio
    return text_length * text_to_html_ratio


def find_optimal_higher_node(element, memo: dict) -> tuple:
    """Find the optimal higher node by evaluating all higher nodes up the tree."""
    # Check memo to avoid recalculation
    if element in memo:
        return memo[element]

    best_element = element
    best_score = calculate_container_score(element)
    traversed_elements = [element]  # Track all elements we evaluate

    # Traverse all ancestors and find the one with the highest score
    current = element
    while current.parent and current.parent.name:  # Skip NavigableString parents
        current = current.parent

        # Check if parent is already memoized
        if current in memo:
            parent_best_element, parent_best_score = memo[current]
            if parent_best_score > best_score:
                best_element = parent_best_element
                best_score = parent_best_score
            break

        # Track this element for memoization
        traversed_elements.append(current)

        # Calculate score for this ancestor
        current_score = calculate_container_score(current)
        if current_score > best_score:
            best_element = current
            best_score = current_score

    # Memoize ALL elements in the traversal path with the optimal result
    result = (best_element, best_score)
    for traversed_element in traversed_elements:
        memo[traversed_element] = result

    return result


def sanitize_html(raw_html: str) -> str | None:
    """Sanitize raw HTML by extracting main content and fixing entities."""
    if not raw_html or not raw_html.strip():
        return raw_html

    # Try to extract main content using ratio analysis
    main_content = extract_main_content_by_ratio(raw_html)

    if main_content is None:
        return None

    # Unescape HTML entities like &shy;, &nbsp;, etc.
    unescaped_html = html.unescape(main_content)

    # TODO: Check if markdownify has issues with any other HTML entities or just this one
    cleaned_html = unescaped_html.replace("&shy;", " ")

    return cleaned_html


def _is_article_html_good_quality(article_html: str) -> bool:
    """Detect if newspaper's article_html properly extracted main content."""
    if not article_html or not article_html.strip():
        return False

    try:
        soup = BeautifulSoup(article_html, "html.parser")
        text_content = soup.get_text(strip=True)

        # Basic length checks
        if len(text_content) < MIN_ARTICLE_LENGTH or len(text_content) > MAX_ARTICLE_LENGTH:
            return False

        # Check text-to-markup ratio
        markup_length = len(article_html) - len(text_content)
        if markup_length > 0:
            text_ratio = len(text_content) / (len(text_content) + markup_length)
            if text_ratio < 0.4:  # At least 40% actual text
                return False

        return True

    except Exception:
        # If BeautifulSoup parsing fails, fall back to basic checks
        article_len = len(article_html.strip())
        return MIN_ARTICLE_LENGTH <= article_len <= MAX_ARTICLE_LENGTH


async def extract_sources_from_rss(scraping_source: ScrapingSourceDB, logger: "Logger") -> list[WebSourceWithMarkdown]:
    """Extract sources from an RSS feed."""
    feed = await asyncio.to_thread(feedparser.parse, scraping_source.base_url)
    sources = []

    logger.info(
        "RSS feed <cyan>{id}</cyan> ({base_url}) fetched. Found <yellow>{entries}</yellow> entries.",
        id=scraping_source.id,
        base_url=scraping_source.base_url,
        entries=len(feed.entries),
    )

    for entry in feed.entries:
        if not entry.link:
            logger.info("❌ Entry <cyan>{entry_id}</cyan> has no link, skipping.", entry_id=entry.id)
            continue

        # Get parsed dates and convert to datetime
        published_dt = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_dt = struct_time_to_datetime(entry.published_parsed)

        updated_dt = None
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            updated_dt = struct_time_to_datetime(entry.updated_parsed)

        # Use the more recent date
        if published_dt and updated_dt:
            date = max(published_dt, updated_dt)
        else:
            date = updated_dt or published_dt

        # Skip entries without valid dates or that have already been scraped
        if date is None or date < scraping_source.last_scraped_at:
            logger.info(
                "❌ Entry <cyan>{entry_id}</cyan> has date <yellow>{date}</yellow>. That is invalid or older than last scrape date. Skipping.",
                entry_id=entry.id,
                date=date,
            )
            continue

        # Use the RSS feed date instead of letting the function parse the article date
        source = await download_and_parse_article(
            entry.link,
            date_according_to_calling_func=date,
            prefer_own_publish_date=False,
            degrees_of_separation=1,
            logger=logger,
        )

        if source and source.date >= scraping_source.last_scraped_at:
            sources.append(source)
            logger.info(
                "✅ Entry <cyan>{entry_id}</cyan> successfully downloaded, parsed and added to sources.",
                entry_id=entry.id,
            )
        else:
            logger.info(
                "❌ Entry <cyan>{entry_id}</cyan> could not be downloaded and parsed. Skipping.", entry_id=entry.id
            )

        await asyncio.sleep(0.1)

    return sources


def uniform_publish_date(publish_date: datetime | None) -> datetime | None:
    """Uniform the publish date to UTC."""
    if publish_date is None:
        return None
    if publish_date.tzinfo is None:
        return publish_date.replace(tzinfo=timezone.utc)
    return publish_date.astimezone(timezone.utc)


async def download_and_parse_article(
    url: str,
    date_according_to_calling_func: datetime = None,
    prefer_own_publish_date: bool = True,
    degrees_of_separation: int = 0,
    logger: "Logger" = None,
) -> WebSourceWithMarkdown | None:
    """Download and parse an article from a URL, returning a WebSource object.

    Args:
        url: The URL to download
        publish_date: The publish date if known, otherwise will use article's date
        prefer_own_publish_date: Whether to prefer the article's publish date over the provided date
        degrees_of_separation: How many degrees away from original source

    Returns:
        WebSource object or None if parsing failed
    """
    await asyncio.sleep(1)
    try:
        article = Article(url, memoize_articles=False, disable_category_cache=True)
        await asyncio.to_thread(article.download)
        await asyncio.to_thread(article.parse)

        date_according_to_article = uniform_publish_date(article.publish_date)
        date_according_to_calling_func = uniform_publish_date(date_according_to_calling_func)
        date_to_use = None

        if date_according_to_article and (prefer_own_publish_date or not date_according_to_calling_func):
            date_to_use = date_according_to_article
            log = f"✅ Successfully downloaded and parsed article {url}. Using date as determined by newspaper <yellow>{date_according_to_article}</yellow>."
        elif date_according_to_calling_func:
            date_to_use = date_according_to_calling_func
            log = f"✅ Successfully downloaded and parsed article {url}. Using date as determined by calling function <yellow>{date_according_to_calling_func}</yellow>."
        else:
            logger.info("❌ Could not determine date for article {url}. Skipping.", url=url)
            return None

        input = choose_input_for_markdownify(article.article_html, article.html, logger)
        if input is None:
            logger.info("❌ Could not determine input for markdownify. Skipping.", url=url)
            return None

        markdown = markdownify(input)
        logger.info(log)

        return WebSourceWithMarkdown(
            url=article.url,
            date=date_to_use,
            title=article.title,
            markdown=markdown,
            degrees_of_separation=degrees_of_separation,
        )
    except Exception as e:
        logger.error("Error downloading or parsing article {url}: <red>{e}</red>", url=url, e=e)
        return None
