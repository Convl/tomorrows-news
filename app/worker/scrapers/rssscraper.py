import asyncio
from time import sleep

import feedparser
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify
from newspaper import Article, utils

from app.models.scraping_source import ScrapingSource


class RssScraper:
    def __init__(self) -> None:
        utils.cache_disk.enabled = False

    async def scrape(self, source: ScrapingSource, url: str | None = None):
        print(f"RssScraper running on {source}")
        url = url or source.base_url
        feed = await asyncio.to_thread(feedparser.parse, url)

        for f in feed.entries:
            print(f"{f.updated if hasattr(f, 'updated') and f.updated else f.published}: {f.link}")

        links = [entry.link for entry in feed.entries]
        newspaper_articles = [Article(link, memoize_articles=False, disable_category_cache=True) for link in links]
        markdown_articles = []
        for article in newspaper_articles:
            article.download()
            article.parse()
            markdown = markdownify(article.article_html)
            markdown_articles.append(markdown)
            print(f"{article.publish_date}: {article.title} - {article.url}")
            sleep(0.1)

    async def test(self):
        from app.worker.scrapers.lg_stuff import HumanMessage, llm

        messages = [HumanMessage(content=f"Tell me a joke please.", name="Lance")]
        result = llm.invoke(messages)
        print(result)
