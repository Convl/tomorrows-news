import asyncio
from datetime import datetime
from time import sleep
from typing import Annotated, Any, Union

import feedparser
import newspaper
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import PydanticState
from markdownify import markdownify
from newspaper import Article, Config, Source, utils
from pydantic import BaseModel, Extra
from sqlalchemy import select

from app.core.config import settings
from app.core.enums import ScrapingSourceEnum
from app.database import get_db_session
from app.models import ScrapingSource, Topic


class WebSource(BaseModel):
    url: str
    date: datetime
    title: str | None = None
    summary: str | None = None
    markdown: str


class AdditionalInfo(BaseModel):
    info: dict[str, Any]
    weight: float


class ExtractedEvent(BaseModel):
    source: WebSource
    date: datetime
    title: str
    location: str
    description: str
    additional_infos: list[AdditionalInfo] | None


class ScrapingState(BaseModel):
    sources: list[WebSource]
    events: list[ExtractedEvent]
    topic: Topic


class Scraper:
    def __init__(self, source_id):
        self.sources = []
        utils.cache_disk.enabled = False

    async def extract_events(self, state: ScrapingState):
        """
        Extract events pertaining to the topic of interest from the given source.
        """
        for source in state.sources:
            messages = [
                SystemMessage(
                    f"""
You will be given a markdown-converted webpage by the user. 
Your task is to extract events from this webpage that are relevant to the following topic:
name: {state.topic.name}
description: {state.topic.description}
country: {state.topic.country}


You need to extract events relevant to this topic from the webpage and return them in a list of events.
Each event should be a dictionary with the following keys:
{ExtractedEvent.model_json_schema()['properties']}
"""
                ),
                HumanMessage(
                    f"Extract events from the following webpage: {source.markdown}"
                ),
            ]
            response = await self.llm.ainvoke(messages)

    async def scrape(self, source_id: int):
        await self._prepare_sources(source_id)

    async def _prepare_sources(self, source_id: int):
        async with get_db_session() as db:
            self.scraping_source: ScrapingSource = (
                (await db.execute(select(ScrapingSource).where(ScrapingSource.id == source_id))).scalars().one_or_none()
            )
            if not self.scraping_source:
                raise ValueError(f"Source with id {source_id} not found.")
            self.topic: Topic = (
                (await db.execute(select(Topic).where(Topic.id == self.scraping_source.topic_id)))
                .scalars()
                .one_or_none()
            )
            if not self.topic:
                raise ValueError(f"Topic with id {self.scraping_source.topic_id} not found.")

        match self.scraping_source.source_type:
            case ScrapingSourceEnum.WEBPAGE:
                self.sources += await self._sources_from_web(self.scraping_source.base_url)
            case ScrapingSourceEnum.RSS:
                self.sources += await self._sources_from_rss(self.scraping_source.base_url)
            case _:
                raise ValueError(f"Unsupported source type: {self.scraping_source.source_type}")

        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            model_name="openai/gpt-4.1-mini",
        )

        self.graph = StateGraph(ScrapingState)

        self.graph.add_node("extract_events", self.extract_events)

        self.graph.add_edge(START, "extract_events")
        self.graph.add_edge("extract_events", END)

        self.graph.compile()

    async def _sources_from_web(self, url: str) -> list[WebSource]:
        config = Config()
        config.memorize_articles = False
        config.disable_category_cache = True
        website = newspaper.build(url, only_in_path=True, config=config)
        sources = []
        for article in website.articles:
            article.download()
            article.parse()

            if not isinstance(article.publish_date, datetime):
                continue

            markdown = markdownify(article.article_html)

            source = WebSource(
                url=article.url,
                date=article.publish_date,
                title=article.title,
                summary=article.summary,
                markdown=markdown,
            )
            sources.append(source)
            sleep(0.1)

        return sources

    async def _sources_from_rss(self, url: str) -> list[WebSource]:
        feed = await asyncio.to_thread(feedparser.parse, url)
        sources = []
        for entry in feed.entries:
            if not entry.link:
                continue

            published = (
                entry.published_parsed
                if hasattr(entry, "published_parsed") and isinstance(entry.published_parsed, datetime)
                else datetime(1900, 1, 1)
            )
            updated = (
                entry.updated
                if hasattr(entry, "update_parsed") and isinstance(entry.updated_parsed, datetime)
                else datetime(1900, 1, 1)
            )
            if (date := max(published, updated)) == datetime(1900, 1, 1):
                continue

            article = Article(entry.link, memoize_articles=False, disable_category_cache=True)
            article.download()
            article.parse()

            markdown = markdownify(article.article_html)

            source = WebSource(
                url=entry.link,
                date=date,
                title=article.title,
                summary=article.summary,
                markdown=markdown,
            )
            sources.append(source)
            sleep(0.1)

        return sources

    async def test(self, source_id: int, url=None):
        async with get_db_session() as db:
            source: ScrapingSource = (
                (await db.execute(select(ScrapingSource).where(ScrapingSource.id == source_id))).scalars().one_or_none()
            )
            if not source:
                raise ValueError(f"Source with id {source_id} not found.")

        scraper = self.get_scraper(source.source_type)
        return await scraper.test()


scraper = Scraper()
