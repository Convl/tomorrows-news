import asyncio
import html
from datetime import datetime, timezone
from time import sleep

import feedparser
import newspaper
from langchain_core.messages import HumanMessage
from markdownify import markdownify
from newspaper import Article, Config

from app.core.enums import ScrapingSourceEnum
from app.models.scraping_source import ScrapingSourceDB

from .llm_service import LlmService
from .scraping_models import ExtractedWebSources, ScrapingSourceWorkflow, WebSourceBase, WebSourceWithMarkdown

MIN_ENTRIES_TO_CONSIDER_VALID_LISTING = 8

# Module-level LLM service instance that can be used by functions
_llm_service = None


async def get_llm_service() -> LlmService:
    """Get or create the module-level LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LlmService()
    return _llm_service


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


async def web_sources_from_scraping_source(scraping_source: ScrapingSourceWorkflow) -> list[WebSourceWithMarkdown]:
    scraping_source._visited = True
    match scraping_source.source_type:
        case ScrapingSourceEnum.WEBPAGE:
            if scraping_source.degrees_of_separation == 0:
                return [await download_and_parse_article(scraping_source.base_url)]
            else:
                return await extract_sources_from_web(scraping_source)
        case ScrapingSourceEnum.RSS:
            return await extract_sources_from_rss(
                scraping_source.base_url,
                scraping_source.last_scraped_at,
                degrees_of_separation=1,
            )
        case _:
            raise ValueError(f"Unsupported source type: {scraping_source.source_type}")


async def extract_sources_from_web(scraping_source: ScrapingSourceWorkflow) -> list[WebSourceWithMarkdown]:
    """Extract sources from a website, using newspaper if possible, LLM-assisted if not."""

    # Some example URLs for testing:
    lto = "https://www.lto.de/recht/presseschau"
    bgh = "https://www.bundesgerichtshof.de/DE/Presse/Pressemitteilungen/pressemitteilungen_node.html"
    einspruch = "https://www.faz.net/einspruch/"
    welt = "https://www.welt.de/politik/deutschland/"
    urls = [lto, bgh, einspruch, welt]

    sources = []

    config = Config()
    config.memorize_articles = False
    config.disable_category_cache = True
    website = newspaper.build(scraping_source.base_url, only_in_path=True, config=config)

    # If newspaper failed to propperly retrieve the articles listed on the page...
    if len(website.articles) < MIN_ENTRIES_TO_CONSIDER_VALID_LISTING:
        # Parse the page AS an Article instead
        website = Article(scraping_source.base_url, memoize_articles=False, disable_category_cache=True)
        website.download()
        website.parse()

        markdown = markdownify(choose_input_for_markdownify(website.article_html, website.html))

        llm_service = await get_llm_service()

        # Let LLM extract sources from the page
        messages = [
            await llm_service.get_source_extraction_system_message(scraping_source.topic),
            HumanMessage(f"Extract sources from the following webpage: {markdown}"),
        ]
        response = await llm_service.source_extracting_llm.ainvoke(messages)
        extracted_sources: list[WebSourceBase] = response["parsed"].sources

        # TODO: remove :3, only filter by last_scraped_at
        for extracted_source in extracted_sources[:3]:
            # Below check avoids parsing unnecessary articles. Commented out for now because LLM-determined date from listings page might not be reliable enough
            # if extracted_source.date and extracted_source.date < scraping_source.last_scraped_at:
            #     continue

            source = await download_and_parse_article(
                extracted_source.url,
                date_according_to_calling_func=extracted_source.date,
                prefer_own_publish_date=True,  # LLM-determined publish-date probably less reliable than newspaper-determined publish date of the actual article
                degrees_of_separation=1,
            )
            sleep(0.1)

            # At this point, the source must have a recent date, either from the llm, or from newspaper
            if source and source.date >= scraping_source.last_scraped_at:
                sources.append(source)

    else:
        # If newspaper was able to retrieve the articles listed on the page, parse them one by one, no need for LLM to get involved.
        for article in website.articles:
            source = await download_and_parse_article(article.url, degrees_of_separation=1)
            if source and source.date >= scraping_source.last_scraped_at:
                sources.append(source)
            sleep(0.1)

    return sources


def choose_input_for_markdownify(article_html: str, full_html: str) -> str:
    """Choose the input for markdownify based on the quality of the article HTML."""
    if _is_article_html_good_quality(article_html, full_html):
        return article_html
    else:
        return sanitize_html(full_html)


def sanitize_html(raw_html: str) -> str:
    """Sanitize raw HTML by removing problematic elements and fixing entities."""
    if not raw_html or not raw_html.strip():
        return raw_html

    # Unescape HTML entities like &shy;, &nbsp;, etc.
    unescaped_html = html.unescape(raw_html)

    # TODO: Check if markdownify has issues with any other HTML entities or just this one
    cleaned_html = unescaped_html.replace("&shy;", " ")

    return cleaned_html


def _is_article_html_good_quality(article_html: str, full_html: str) -> bool:
    """Detect if newspaper's article_html properly extracted main content."""
    if not article_html or not article_html.strip():
        return False

    article_len = len(article_html.strip())
    full_len = len(full_html)

    # Should be substantial content but not the entire page
    min_length = 1000  # At least 1000 chars
    max_ratio = 0.8  # Not more than 80% of full page
    min_ratio = 0.1  # At least 10% of full page

    if article_len < min_length:
        return False

    ratio = article_len / full_len if full_len > 0 else 0
    if ratio > max_ratio or ratio < min_ratio:
        return False

    # Check for text density (avoid pure HTML with little content)
    text_chars = len([c for c in article_html if c.isalnum() or c.isspace()])
    text_ratio = text_chars / article_len if article_len > 0 else 0
    if text_ratio < 0.3:  # At least 30% actual text
        return False

    return True


async def extract_sources_from_rss(scraping_source: ScrapingSourceDB) -> list[WebSourceWithMarkdown]:
    """Extract sources from an RSS feed."""
    feed = await asyncio.to_thread(feedparser.parse, scraping_source.base_url)
    sources = []

    # TODO: Remove [:1], filter by last_scraped_at instead
    for entry in feed.entries[:3]:
        if not entry.link:
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
            continue

        # Use the RSS feed date instead of letting the function parse the article date
        source = await download_and_parse_article(
            entry.link,
            date_according_to_calling_func=date,
            prefer_own_publish_date=False,
            degrees_of_separation=1,
        )

        if source and source.date >= scraping_source.last_scraped_at:
            sources.append(source)
        sleep(0.1)

    return sources


def uniform_publish_date(publish_date: datetime | None) -> datetime | None:
    """Uniform the publish date to UTC."""
    if publish_date is None:
        return None
    if publish_date.tzinfo is None:
        return publish_date.replace(tzinfo=timezone.utc)
    return publish_date.astimezone(timezone.utc)


async def download_and_parse_article(
    url: str, date_according_to_calling_func: datetime = None, prefer_own_publish_date: bool = True, degrees_of_separation: int = 0
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
    try:
        article = Article(url, memoize_articles=False, disable_category_cache=True)
        article.download()
        article.parse()

        date_according_to_article = uniform_publish_date(article.publish_date)
        date_according_to_calling_func = uniform_publish_date(date_according_to_calling_func)
        date_to_use = None

        if not date_according_to_calling_func or (prefer_own_publish_date and date_according_to_article is not None):
            date_to_use = date_according_to_article
        else:
            date_to_use = date_according_to_calling_func

        if not date_to_use:
            return None

        markdown = markdownify(choose_input_for_markdownify(article.article_html, article.html))

        return WebSourceWithMarkdown(
            url=article.url,
            date=date_to_use,
            title=article.title,
            markdown=markdown,
            degrees_of_separation=degrees_of_separation,
        )
    except Exception as e:
        print(f"Error downloading or parsing article {url}: {e}")
        return None
