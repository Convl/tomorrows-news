import asyncio

import feedparser
from newspaper import Article, utils
from time import sleep
from app.models.scraping_source import ScrapingSource


class RssScraper:
    async def scrape(self, source: ScrapingSource, url: str | None = None):
        print(f"RssScraper running on {source}")
        url = url or source.base_url
        feed = await asyncio.to_thread(feedparser.parse, url)
        for f in feed.entries:
            print(f"{f.updated if hasattr(f, "updated") and f.updated else f.published}: {f.link}")
        links = [entry.link for entry in feed.entries]
        utils.cache_disk.enabled = False
        articles = [Article(link, memoize_articles=False, disable_category_cache=True) for link in links]
        for article in articles:
            article.download()
            article.parse()
            print(f"{article.publish_date}: {article.title} - {article.url}")
            sleep(0.1)
