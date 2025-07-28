import asyncio
import calendar
import json
import operator
import time
from datetime import datetime, timezone
from pprint import pprint
from time import sleep
from typing import Annotated, Any, Self, Union

import feedparser
import newspaper
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Send
from markdownify import markdownify
from newspaper import Article, Config, Source, utils
from pydantic import BaseModel, Extra, Field, model_validator
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode, JsonSchemaValue
from sqlalchemy import select

from app.core.config import settings
from app.core.enums import ScrapingSourceEnum
from app.database import get_db_session
from app.models import ScrapingSourceDB, TopicDB
from app.schemas.topic import TopicBase


class WebSource(BaseModel):
    """A web source (article, press release, etc.) containing content and metadata."""

    url: str = Field(description="The full URL of the web source")
    date: datetime = Field(description="The date when the source was published or last updated")
    title: str | None = Field(default=None, description="The headline or title of the source, if available")
    summary: str | None = Field(
        default=None, description="A brief summary or excerpt of the source's content, if available"
    )
    markdown: str = Field(description="The full source's content, converted to markdown format for processing")
    degrees_of_separation: int = Field(
        description="The number of degrees of separation from the original source", default=0
    )


MAX_DEGREES_OF_SEPARATION = 1


class ExtractedUrls(BaseModel):
    urls: list[str] = Field(description="A list of URLs extracted from the web source")


class AdditionalInfo(BaseModel):
    """Supplementary information about an event with an importance weight. This can be used to provide additional context or details about the event."""

    info_name: str = Field(
        description="The name of the additional piece of information (e.g. 'registration_link', 'reference_number', 'accreditation_deadline', etc.)"
    )
    info_value: str = Field(
        description="The value of the additional piece of information (e.g. 'https://www.example.com/registration', '1234567890', '2025-08-01', etc.)"
    )
    weight: float = Field(
        description="A numerical weight (0.0 to 1.0) indicating how helpful this piece of additional information will be in disambiguating the event that it belongs to from other, similar events pertaining to the same topic. 0.0 means not helpful at all, 1.0 means extremely helpful."
    )


class DateTimeframe(BaseModel):
    earliest: datetime = Field(description="Earliest possible date/time for the event")
    latest: datetime = Field(description="Latest possible date/time for the event")


class ExtractedEvent(BaseModel):
    """An event extracted from a web source that is relevant to a specific topic of interest."""

    date: datetime | DateTimeframe = Field(
        description="Event timing: use datetime for exact timing (e.g., '2024-03-15T14:00:00'), or DateTimeframe for approximate timing with earliest/latest bounds. Exact timing is preferred, though only if you are certain that you can determine an exact date. If you are not certain, use DateTimeframe."
    )
    title: str = Field(
        description="A clear, concise title or name for the event",
        examples=["City Council Meeting", "Tech Conference 2024", "Climate Action Workshop"],
    )
    location: str | None = Field(
        default=None,
        description="The geographic location where the event takes place",
        examples=["Berlin, Germany", "Online", "Town Hall, 123 Main St", "Central Park"],
    )
    description: str = Field(
        description="A concise description of what the event is about, including key details and context, anywhere from 20 to 200 words",
        examples=[
            "Monthly city council meeting to discuss urban planning and budget allocation",
            "Annual technology conference featuring speakers from major tech companies",
        ],
    )
    duration: str | None = Field(
        default=None,
        description="How long the event lasts",
        examples=["2 hours", "3 days", "1 week", "30 minutes", "all day"],
    )
    additional_infos: list[AdditionalInfo] | None = Field(
        default=None,
        description="Optional supplementary information about the event with associated importance weights",
    )


class ExtractedEvents(BaseModel):
    events: list[ExtractedEvent] = Field(description="A list of events extracted from the web source")


class ScrapingState(BaseModel):
    sources: Annotated[list[WebSource], operator.add]
    events: Annotated[list[ExtractedEvent], operator.add]
    topic: TopicBase


class Scraper:
    def __init__(self, source_id):
        self.sources = []
        self.source_id = source_id
        utils.cache_disk.enabled = False

    async def extract_sources_from_single_source(self, state: dict) -> dict:
        """Extract additional sources from a single web source."""

        # to skip this part, simply return {}
        source = state["source"]  # Extract the source from the state dict
        try:
            print(f"Processing source: {source.url}")
            messages = [
                self.source_extraction_system_message,
                HumanMessage(f"Extract sources from the following webpage: {source.markdown}"),
            ]
            response = await self.source_extracting_llm.ainvoke(messages)
            urls = response["parsed"].urls
            print(f"Found {len(urls)} URLs to extract from {source.url}")

            sources = []
            for url in urls:
                try:
                    article = Article(url, memoize_articles=False, disable_category_cache=True)
                    article.download()
                    article.parse()
                except Exception as e:
                    print(f"Error downloading or parsing article {url}: {e}")
                    continue

                # Handle timezone-naive datetime from newspaper
                if not isinstance(article.publish_date, datetime):
                    continue

                # Make timezone-aware if naive
                if article.publish_date.tzinfo is None:
                    # Assume naive datetime is in UTC (or use local timezone if preferred)
                    article_date = article.publish_date.replace(tzinfo=timezone.utc)
                else:
                    article_date = article.publish_date

                if article_date < self.scraping_source.last_scraped_at:
                    continue

                markdown = markdownify(article.article_html)
                new_source = WebSource(
                    url=article.url,
                    date=article.publish_date,
                    title=article.title,
                    summary=article.summary,
                    markdown=markdown,
                    degrees_of_separation=source.degrees_of_separation + 1,
                )
                sources.append(new_source)

            print(f"Successfully extracted {len(sources)} sources from {source.url}")
            return {"sources": sources}

        except Exception as e:
            print(f"ERROR in extract_sources_from_single_source for {source.url}: {e}")
            # Return empty sources instead of failing
            return {"sources": []}

    async def start_source_extraction(self, state: ScrapingState):
        """Initial node that starts the source extraction process."""
        print(f"Starting source extraction with {len(state.sources)} initial sources")
        return {}

    async def route_to_source_extraction(self, state: ScrapingState):
        """Route to source extraction for parallel processing."""

        eligible_sources = [
            source for source in state.sources if source.degrees_of_separation < MAX_DEGREES_OF_SEPARATION
        ]
        print(f"Initial state has {len(state.sources)} sources")
        print(f"Routing {len(eligible_sources)} sources for source extraction (degrees < {MAX_DEGREES_OF_SEPARATION})")

        if not eligible_sources:
            print("No eligible sources for extraction - skipping to event extraction")
            return []

        return [Send("extract_sources_from_single_source", {"source": source}) for source in eligible_sources]

    async def route_to_event_extraction(self, state: ScrapingState):
        """Route to event extraction for parallel processing."""
        print(f"Event extraction phase - state has {len(state.sources)} total sources")
        print(f"Sources by degree: {[(s.degrees_of_separation, s.url[:50] + '...') for s in state.sources[:3]]}")

        if not state.sources:
            print("WARNING: No sources available for event extraction!")
            return []

        return [Send("extract_events_from_single_source", {"source": source}) for source in state.sources]

    async def prepare_event_extraction(self, state: ScrapingState):
        """Pass-through node that prepares for event extraction."""
        print(f"=== PREPARE EVENT EXTRACTION ===")
        print(f"Total sources in state: {len(state.sources)}")
        print(f"Events so far: {len(state.events)}")
        print(
            f"Sources by degree: degree 0: {len([s for s in state.sources if s.degrees_of_separation == 0])}, degree 1: {len([s for s in state.sources if s.degrees_of_separation == 1])}"
        )
        return {}  # No state changes needed

    async def extract_events_from_single_source(self, state: dict):
        """Extract events from a single source."""
        source = state["source"]  # Extract the source from the state dict
        print(f"Extracting events from source: {source.url}")
        messages = [
            self.event_extraction_system_message,
            HumanMessage(f"Extract events from the following webpage: {source.markdown}"),
        ]
        response = await self.event_extracting_llm.ainvoke(messages)
        events = response["parsed"].events
        print(f"Extracted {len(events)} events from {source.url}")
        return {"events": events}

    async def print_events(self, state: ScrapingState):
        """Print all collected events to the console."""
        print(f"FINAL RESULTS: Found {len(state.events)} total events")
        for i, event in enumerate(state.events, 1):
            print(f"\nEvent {i}:")
            pprint(event)
        # return state

    async def scrape(self):
        await self._prepare_scraper()
        await self.graph.ainvoke(self.scraping_state)
        # async with get_db_session() as db:
        #     self.scraping_source.last_scraped_at = datetime.now(timezone.utc)
        #     db.add(self.scraping_source)
        #     await db.commit()
        #     await db.refresh(self.scraping_source)
        print("henlo")

    async def _prepare_scraper(self):
        async with get_db_session() as db:
            self.scraping_source: ScrapingSourceDB = (
                (await db.execute(select(ScrapingSourceDB).where(ScrapingSourceDB.id == self.source_id)))
                .scalars()
                .one_or_none()
            )
            if not self.scraping_source:
                raise ValueError(f"Source with id {self.source_id} not found.")

            topic: TopicDB = (
                (await db.execute(select(TopicDB).where(TopicDB.id == self.scraping_source.topic_id)))
                .scalars()
                .one_or_none()
            )
            if not topic:
                raise ValueError(f"Topic with id {self.scraping_source.topic_id} not found.")
            self.topic = TopicBase.model_validate(topic, from_attributes=True)

            self.event_extraction_system_message = SystemMessage(
                f"""
You will be given a markdown-converted webpage by the user.
If the webpage contains information about upcoming events that are relevant to the following topic, you need to extract that information.
Topic name: {self.topic.name}
Topic description: {self.topic.description}
Topic country: {self.topic.country}
Notice that today's date is {datetime.now(timezone.utc).strftime("%Y-%m-%d")}.
You should only extract information about events that will **take place in the future** and are **relevant to the topic**.
Notice that the point of this task is to create a forward planner with a list of upcoming events relating to the given topic, to be used by e.g. journalists or business analysts.
Therefore, you should only extract events which are specific enough to be used as actionable items in a forward planner.
Examples of events that are specific enough:
- The German parliament plans to vote on a new law proposed by the government on climate change on the 20th of August 2025. (date specific, event specific, actionable)
- A fact-finding committee plans to present its findings on the impact of recent measures to combat climate change at some point between the 10th and 15th of May 2026. (date range specific, event specific, can be used to prepare for the event)
- The next hearing in the criminal case against the former president of the United States will take place on either the 10th or the 11th of July 2025, at 10:00 AM. (date range specific, event specific, actionable)
Examples of events that are not specific enough:
- The German government plans to issue a review of its recent changes to the criminal code at some point within the next three years. (date range very broad, event somewhat vague, not actionable)
- Some pundits suspect that the French president will resign before the end of the year. (date range specific, event specific, but mere suspicion that event might happen is not sufficient)
- The new law is expected to cause rents to go up once it takes effect on the 1st of January 2026. (date specific, but this is a broader develpopment, not a specific event)
"""
            )

        self.source_extraction_system_message = SystemMessage(
            f"""
You will be given a markdown-converted webpage by the user.
If the webpage contains links to other webpages that are relevant to the following topic, you need to extract those links. 
Do not change anything about the links that you extracted, like replacing hyphens or dashes with tildes. 
Topic name: {self.topic.name}
Topic description: {self.topic.description}
Topic country: {self.topic.country}
"""
        )

        match self.scraping_source.source_type:
            case ScrapingSourceEnum.WEBPAGE:
                self.sources += await self._sources_from_web(self.scraping_source.base_url)
            case ScrapingSourceEnum.RSS:
                self.sources += await self._sources_from_rss(self.scraping_source.base_url)
            case _:
                raise ValueError(f"Unsupported source type: {self.scraping_source.source_type}")

        self.rate_limiter = InMemoryRateLimiter(
            requests_per_second=1,
            check_every_n_seconds=0.9,
            max_bucket_size=1,
        )

        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            model_name="google/gemini-2.5-pro",
            rate_limiter=self.rate_limiter,
        )
        self.event_extracting_llm = self.llm.with_structured_output(
            schema=ExtractedEvents,
            method="json_schema",
            include_raw=True,
            strict=True,
        )
        self.source_extracting_llm = self.llm.with_structured_output(
            schema=ExtractedUrls,
            method="json_schema",
            include_raw=True,
            strict=True,
        )

        self.scraping_state = ScrapingState(sources=self.sources, events=[], topic=self.topic)

        self.graph_builder = StateGraph(ScrapingState)

        # Add only the actual processing nodes
        self.graph_builder.add_node("start_source_extraction", self.start_source_extraction)
        self.graph_builder.add_node("extract_sources_from_single_source", self.extract_sources_from_single_source)
        self.graph_builder.add_node("extract_events_from_single_source", self.extract_events_from_single_source)
        self.graph_builder.add_node("prepare_event_extraction", self.prepare_event_extraction)
        self.graph_builder.add_node("print_events", self.print_events)

        # Start the graph
        self.graph_builder.add_edge(START, "start_source_extraction")

        # Phase 1: Source extraction with map-reduce
        # The third parameter must match the node names that Send targets
        self.graph_builder.add_conditional_edges(
            "start_source_extraction",
            self.route_to_source_extraction,
            ["extract_sources_from_single_source"],  # This matches Send("extract_sources_from_single_source", ...)
        )

        # After all source extractions complete, go to prepare_event_extraction
        self.graph_builder.add_edge("extract_sources_from_single_source", "prepare_event_extraction")

        # Phase 2: Event extraction with map-reduce
        self.graph_builder.add_conditional_edges(
            "prepare_event_extraction",
            self.route_to_event_extraction,
            ["extract_events_from_single_source"],  # This matches Send("extract_events_from_single_source", ...)
        )

        # After all event extractions complete, go to print_events
        self.graph_builder.add_edge("extract_events_from_single_source", "print_events")
        self.graph_builder.add_edge("print_events", END)

        self.graph = self.graph_builder.compile()

    async def _sources_from_web(self, url: str) -> list[WebSource]:
        config = Config()
        config.memorize_articles = False
        config.disable_category_cache = True
        website = newspaper.build(url, only_in_path=True, config=config)
        sources = []
        for article in website.articles:
            article.download()
            article.parse()

            # Handle timezone-naive datetime from newspaper
            if not isinstance(article.publish_date, datetime):
                continue

            # Make timezone-aware if naive
            if article.publish_date.tzinfo is None:
                # Assume naive datetime is in UTC (or use local timezone if preferred)
                article_date = article.publish_date.replace(tzinfo=timezone.utc)
            else:
                article_date = article.publish_date

            if article_date < self.scraping_source.last_scraped_at:
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
        for entry in feed.entries[:1]:
            if not entry.link:
                continue

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

            if date < self.scraping_source.last_scraped_at:
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

    async def test(self):
        schema = ExtractedEvents.model_json_schema()
        json_schema = json.dumps(schema, indent=2)
        print(json_schema)

    @classmethod
    async def scrape_source(cls, source_id: int):
        scraper = cls(source_id)
        await scraper.scrape(source_id)
