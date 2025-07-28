import asyncio
from datetime import datetime, timezone
from time import sleep

import feedparser
import newspaper
from markdownify import markdownify
from newspaper import Article, Config

from app.core.enums import ScrapingSourceEnum

from .scraping_models import ScrapingSourceWorkflow, WebSourceWithMarkdown


def struct_time_to_datetime(struct_time_obj) -> datetime | None:
    """Convert feedparser's struct_time to datetime with UTC timezone."""
    if struct_time_obj is None:
        return None
    try:
        # Direct conversion since feedparser's struct_time is UTC
        utc_dt = datetime(*struct_time_obj[:6], tzinfo=timezone.utc)
        return utc_dt.astimezone()
    except (ValueError, TypeError):
        return None


async def web_sources_from_scraping_source(scraping_source: ScrapingSourceWorkflow) -> list[WebSourceWithMarkdown]:
    match scraping_source.source_type:
        case ScrapingSourceEnum.WEBPAGE:
            if scraping_source.degrees_of_separation == 0:
                return [await download_and_parse_article(scraping_source.base_url)]
            else:
                return await extract_sources_from_web(
                    scraping_source.base_url,
                    last_scraped_at=scraping_source.last_scraped_at,
                    degrees_of_separation=scraping_source.degrees_of_separation + 1,
                )
        case ScrapingSourceEnum.RSS:
            return await extract_sources_from_rss(
                scraping_source.base_url,
                scraping_source.last_scraped_at,
                degrees_of_separation=scraping_source.degrees_of_separation + 1,
            )
        case _:
            raise ValueError(f"Unsupported source type: {scraping_source.source_type}")


async def extract_sources_from_web(
    url: str, last_scraped_at: datetime, degrees_of_separation: int = 0
) -> list[WebSourceWithMarkdown]:
    """Extract sources from a website using newspaper."""
    config = Config()
    config.memorize_articles = False
    config.disable_category_cache = True
    website = newspaper.build(url, only_in_path=True, config=config)
    sources = []

    for article in website.articles:
        source = await download_and_parse_article(article.url, degrees_of_separation=degrees_of_separation)
        if source and source.date >= last_scraped_at:
            sources.append(source)
        sleep(0.1)

    return sources


async def extract_sources_from_rss(url: str, last_scraped_at: datetime, degrees_of_separation: int = 0) -> list[WebSourceWithMarkdown]:
    """Extract sources from an RSS feed."""
    feed = await asyncio.to_thread(feedparser.parse, url)
    sources = []

    # TODO: Remove [:1], filter by last_scraped_at instead
    for entry in feed.entries[:1]:
        if not entry.link:
            continue

        # Get parsed dates and convert to datetime
        published_dt = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_dt = struct_time_to_datetime(entry.published_parsed)

        updated_dt = None
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            updated_dt = struct_time_to_datetime(entry.updated_parsed)

        # Use the more recent date, fallback to a default if neither exists
        if published_dt and updated_dt:
            date = max(published_dt, updated_dt)
        elif published_dt:
            date = published_dt
        elif updated_dt:
            date = updated_dt
        else:
            # Skip entries without valid dates
            continue

        if date < last_scraped_at:
            continue

        # Use the RSS feed date instead of letting the function parse the article date
        source = await download_and_parse_article(entry.link, publish_date=date, degrees_of_separation=degrees_of_separation)
        if source:
            sources.append(source)
        sleep(0.1)

    return sources


async def download_and_parse_article(
    url: str, publish_date: datetime = None, degrees_of_separation: int = 0
) -> WebSourceWithMarkdown | None:
    """Download and parse an article from a URL, returning a WebSource object.

    Args:
        url: The URL to download
        publish_date: The publish date if known, otherwise will use article's date
        degrees_of_separation: How many degrees away from original source

    Returns:
        WebSource object or None if parsing failed
    """
    try:
        article = Article(url, memoize_articles=False, disable_category_cache=True)
        article.download()
        article.parse()

        # Use provided date or article's publish date
        if publish_date:
            date = publish_date
        elif isinstance(article.publish_date, datetime):
            # Make timezone-aware if naive
            if article.publish_date.tzinfo is None:
                date = article.publish_date.replace(tzinfo=timezone.utc)
            else:
                date = article.publish_date
        else:
            # Skip articles without valid dates
            return None

        markdown = markdownify(article.article_html)

        return WebSourceWithMarkdown(
            url=article.url,
            date=date,
            title=article.title,
            markdown=markdown,
            degrees_of_separation=degrees_of_separation,
        )
    except Exception as e:
        print(f"Error downloading or parsing article {url}: {e}")
        return None
