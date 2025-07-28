import json
from datetime import datetime, timedelta, timezone
from pprint import pprint

from langchain_core.messages import HumanMessage
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pgvector.sqlalchemy import Vector
from psycopg.errors import QueryCanceled
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from sqlalchemy import cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import QueryableAttribute

from app.core.config import settings
from app.core.enums import ScrapingSourceEnum
from app.database import get_db_session
from app.models import ScrapingSourceDB, TopicDB
from app.models.event import EventDB
from app.models.extracted_event import ExtractedEventDB
from app.schemas.topic import TopicBase

from .scraping_config import (
    EVENT_EXTRACTION_SYSTEM_TEMPLATE,
    MAX_DEGREES_OF_SEPARATION,
    SOURCE_EXTRACTION_SYSTEM_TEMPLATE,
)
from .scraping_models import (
    ExtractedBaseEvents,
    ExtractedEvent,
    ExtractedEventBase,
    ExtractedUrls,
    ScrapingSourceWorkflow,
    ScrapingState,
    WebSourceBase,
    WebSourceWithMarkdown,
)
from .scraping_utils import (
    download_and_parse_article,
    extract_sources_from_rss,
    extract_sources_from_web,
    web_sources_from_scraping_source,
)

CONSIDER_SAME_EVENT_THRESHOLD = 0.8
CONSIDER_NEW_DATE_TRUE_THRESHOLD = 3


class Scraper:
    def __init__(self, source_id):
        self.sources = []
        self.source_id = source_id

    async def resolve_date_conflict(self, event_db: EventDB, extracted_event_db: ExtractedEventDB, db: AsyncSession):
        """Resolve date conflicts between an EventDB and an ExtractedEventDB."""
        if event_db.date == extracted_event_db.date:
            return

        evidence_for_old_date = (
            (
                await db.execute(
                    select(ExtractedEventDB)
                    .where(ExtractedEventDB.event_id == event_db.id)
                    .where(ExtractedEventDB.date == event_db.date)
                )
            )
            .scalars()
            .all()
        )

        evidence_for_new_date = (
            (
                await db.execute(
                    select(ExtractedEventDB)
                    .where(ExtractedEventDB.event_id == event_db.id)
                    .where(ExtractedEventDB.date == extracted_event_db.date)
                )
            )
            .scalars()
            .all()
        )

        # If at least CONSIDER_NEW_DATE_TRUE_THRESHOLD of the most recent events agree on the new date, accept it as true
        recent_evidence_for_new_date = [
            new_evidence
            for new_evidence in evidence_for_new_date
            if all(
                new_evidence.source_published_date > old_evidence.source_published_date
                for old_evidence in evidence_for_old_date
            )
        ]
        if len(recent_evidence_for_new_date) >= CONSIDER_NEW_DATE_TRUE_THRESHOLD:
            event_db.date = extracted_event_db.date
            event_db.date_from_id = extracted_event_db.id
            db.add(event_db)
            await db.flush()

        # Otherwise, calculate scores that takes into account number of ExtractedEventDBs suggesting the old and the new date and the age of their respective .source_published_date (older = worse)
        evidence_for_old_date_score = ...
        evidence_for_new_date_score = ...

        # if len(evidence_for_new_date) >= CONSIDER_NEW_DATE_TRUE_THRESHOLD:
        #     event_db.date = extracted_event_db.date
        #     db.add(event_db)
        #     await db.flush()

    async def update_event_db(self, event_db: EventDB, extracted_event_db: ExtractedEventDB, db: AsyncSession):
        """Update an EventDB with an ExtractedEventDB."""
        self.resolve_date_conflict(event_db, extracted_event_db, db)

    async def commit_extracted_events_to_db(self, state: ScrapingState):
        extracted_events_db = []
        async with get_db_session() as db:
            for extracted_event in state.events:
                extracted_event_db = ExtractedEventDB.from_extracted_event(extracted_event, self.scraping_source)
                db.add(extracted_event_db)
                await db.flush()

                semantic_content = f"{extracted_event.title}\n{extracted_event.description or ''}".strip()
                semantic_vector = await self.embeddings.aembed_query(semantic_content)

                extracted_event_db.semantic_vector = semantic_vector

                db.add(extracted_event_db)
                extracted_events_db.append(extracted_event_db)
                await db.flush()
            await db.commit()

            for extracted_event_db in extracted_events_db:
                most_similar_extracted_events = (
                    await db.execute(
                        select(
                            ExtractedEventDB,
                            (
                                1 - ExtractedEventDB.semantic_vector.cosine_distance(extracted_event_db.semantic_vector)
                            ).label("similarity"),
                        )
                        .where(ExtractedEventDB.semantic_vector.isnot(None))
                        .order_by(text("similarity DESC"))
                    )
                ).all()
                print(f"### Most similar events: for {extracted_event_db.title}")
                for i, (event, similarity) in enumerate(most_similar_extracted_events):
                    print(f"Similar event {i}: Cosine distance: {similarity}")
                    print(f"Similar event {i}: {event.title}")
                    print(f"Similar event {i}: {event.description}")
                    print(f"Similar event {i}: {event.location}")
                    print(f"Similar event {i}: {event.date}")

                most_similar_event, similarity = (
                    await db.execute(
                        select(
                            EventDB,
                            (1 - EventDB.semantic_vector.cosine_distance(extracted_event_db.semantic_vector)).label(
                                "similarity"
                            ),
                        )
                        .where(EventDB.semantic_vector.isnot(None))
                        .order_by(text("similarity DESC"))
                        .limit(1)
                    )
                ).all()
                if most_similar_event and similarity > CONSIDER_SAME_EVENT_THRESHOLD:
                    print("### Similar event found:")
                    print(f"Similar event: {most_similar_event.title}")
                    print(f"Similar event: {most_similar_event.description}")
                    extracted_event_db.event_id = most_similar_event.id
                    db.add(extracted_event_db)
                    await db.flush()

                    break
                else:
                    print("### No similar event found, creating new event")
                    new_event = EventDB.from_extracted_event_db(extracted_event_db)
                    db.add(new_event)
                    await db.flush()
                    extracted_event_db.event_id = new_event.id
                    db.add(extracted_event_db)
                    await db.flush()
                    break
            await db.commit()

    async def extract_sources_from_single_source(
        self, state: dict[str, WebSourceWithMarkdown]
    ) -> dict[str, list[WebSourceWithMarkdown] | list]:
        """Extract additional sources from a single web source."""

        # to skip this part, simply return {}
        source: WebSourceWithMarkdown = state["source"]
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
                new_source = await download_and_parse_article(
                    url, degrees_of_separation=source.degrees_of_separation + 1
                )
                if new_source and new_source.date >= self.scraping_source.last_scraped_at:
                    sources.append(new_source)

            print(f"Successfully extracted {len(sources)} sources from {source.url}")
            return {"sources": sources}

        except Exception as e:
            print(f"ERROR in extract_sources_from_single_source for {source.url}: {e}")
            return {"sources": []}

    async def start_source_extraction(self, state: ScrapingState):
        """Initial node that populates state.sources from the scraping source."""
        return {"sources": await web_sources_from_scraping_source(state.scraping_source)}

    async def route_to_source_extraction(self, state: ScrapingState):
        """Route to source extraction for parallel processing."""

        eligible_sources = [
            source
            for source in state.sources
            if source.degrees_of_separation < state.scraping_source.degrees_of_separation
            and source.degrees_of_separation < MAX_DEGREES_OF_SEPARATION
        ]
        print(f"Initial state has {len(state.sources)} sources")
        print(f"Routing {len(eligible_sources)} sources for source extraction (degrees < {state.scraping_source.degrees_of_separation})")

        if not eligible_sources:
            print("No eligible sources for extraction - skipping to event extraction")
            return []

        return [Send("extract_sources_from_single_source", {"source": source}) for source in eligible_sources]

    async def extract_events_from_single_source(self, state: dict[str, WebSourceWithMarkdown]):
        """Extract events from a single source."""
        source = state["source"]  # Extract the source from the state dict
        print(f"Extracting events from source: {source.url}")
        messages = [
            self.event_extraction_system_message,
            HumanMessage(f"Extract events from the following webpage: {source.markdown}"),
        ]
        response = await self.event_extracting_llm.ainvoke(messages)
        events: list[ExtractedEventBase] = response["parsed"].events
        print(f"Extracted {len(events)} events from {source.url}")

        source_without_markdown = WebSourceBase.from_web_source_with_markdown(source)
        events_with_source = [ExtractedEvent(**event.model_dump(), source=source_without_markdown) for event in events]
        return {"events": events_with_source}

    async def prepare_event_extraction(self, state: ScrapingState):
        """Pass-through node that prepares for event extraction."""
        print(f"=== PREPARE EVENT EXTRACTION ===")
        print(f"Total sources in state: {len(state.sources)}")
        print(f"Events so far: {len(state.events)}")
        return {}

    async def route_to_event_extraction(self, state: ScrapingState):
        """Route to event extraction for parallel processing."""
        print(f"Event extraction phase - state has {len(state.sources)} total sources")

        if not state.sources:
            print("WARNING: No sources available for event extraction!")
            return []

        return [Send("extract_events_from_single_source", {"source": source}) for source in state.sources]

    async def print_events(self, state: ScrapingState):
        """Print all collected events to the console."""
        print(f"FINAL RESULTS: Found {len(state.events)} total events")
        for i, event in enumerate(state.events, 1):
            print(f"\nEvent {i}:")
            pprint(event)
        return state

    async def scrape_with_checkpointer(self):
        async with get_db_session() as db:
            thread_id = (
                (
                    await db.execute(
                        text("""
                SELECT COALESCE(MAX(CAST(thread_id AS INTEGER)), 0) + 1 
                FROM checkpoints 
                WHERE thread_id ~ '^[0-9]+$'
            """)
                    )
                )
                .scalars()
                .one_or_none()
            )

        async with AsyncPostgresSaver.from_conn_string(settings.PSYCOPG3_DATABASE_URL, pipeline=False) as checkpointer:
            checkpointer.conn.prepare_threshold = None
            await self._prepare_scraper(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": thread_id}}

            snapshot_config = {"configurable": {"thread_id": thread_id - 1}}
            async for snapshot in self.graph.aget_state_history(snapshot_config):
                print(f"Checkpoint {snapshot.config['configurable']['checkpoint_id']}")
                print(f"Next: {snapshot.next}")
            print(snapshot)

            try:
                await self.graph.ainvoke(self.scraping_state, config=config)
            except Exception as e:  # TODO: Seems fine to ignore the error, figure out why it happens though
                print(f"Error: {e}")

    async def scrape(self):
        await self._prepare_scraper()
        await self.graph.ainvoke(self.scraping_state)

        # async with get_db_session() as db:
        #     self.scraping_source.last_scraped_at = datetime.now(timezone.utc)
        #     db.add(self.scraping_source)
        #     await db.commit()
        #     await db.refresh(self.scraping_source)

    async def _prepare_scraper(self, checkpointer: AsyncPostgresSaver | None = None):
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

            # Create system messages using the templates
            self.event_extraction_system_message = await EVENT_EXTRACTION_SYSTEM_TEMPLATE.aformat(
                topic_name=self.topic.name,
                topic_description=self.topic.description,
                topic_country=self.topic.country,
                current_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                language=self.scraping_source.language,
            )

            self.source_extraction_system_message = await SOURCE_EXTRACTION_SYSTEM_TEMPLATE.aformat(
                topic_name=self.topic.name,
                topic_description=self.topic.description,
                topic_country=self.topic.country,
            )

        # # Load initial sources based on source type
        # match self.scraping_source.source_type:
        #     case ScrapingSourceEnum.WEBPAGE:
        #         self.sources += await extract_sources_from_web(
        #             self.scraping_source.base_url, self.scraping_source.last_scraped_at
        #         )
        #     case ScrapingSourceEnum.RSS:
        #         self.sources += await extract_sources_from_rss(
        #             self.scraping_source.base_url, self.scraping_source.last_scraped_at
        #         )
        #     case _:
        #         raise ValueError(f"Unsupported source type: {self.scraping_source.source_type}")

        # Setup LLM and rate limiter
        self.rate_limiter = InMemoryRateLimiter(
            requests_per_second=1,
            check_every_n_seconds=0.9,
            max_bucket_size=1,
        )

        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            model_name="google/gemini-2.5-pro",
            # model_name="openai/gpt-4.1-mini",
            rate_limiter=self.rate_limiter,
        )
        self.event_extracting_llm = self.llm.with_structured_output(
            schema=ExtractedBaseEvents,
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
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY.get_secret_value()
        )

        # Setup initial state and graph
        scraping_source_workflow = ScrapingSourceWorkflow.model_validate(self.scraping_source, from_attributes=True)
        self.scraping_state = ScrapingState(
            scraping_source=scraping_source_workflow,
            sources=[],
            events=[],
            topic=self.topic,
        )

        self.graph_builder = StateGraph(ScrapingState)

        # Add nodes
        self.graph_builder.add_node("start_source_extraction", self.start_source_extraction)
        self.graph_builder.add_node("extract_sources_from_single_source", self.extract_sources_from_single_source)
        self.graph_builder.add_node("extract_events_from_single_source", self.extract_events_from_single_source)
        self.graph_builder.add_node("prepare_event_extraction", self.prepare_event_extraction)
        self.graph_builder.add_node("commit_extracted_events_to_db", self.commit_extracted_events_to_db)
        self.graph_builder.add_node("print_events", self.print_events)

        # Build the graph
        self.graph_builder.add_edge(START, "start_source_extraction")

        # Phase 1: Source extraction with map-reduce
        self.graph_builder.add_conditional_edges(
            "start_source_extraction",
            self.route_to_source_extraction,
            ["extract_sources_from_single_source"],
        )

        # After all source extractions complete, go to prepare_event_extraction
        self.graph_builder.add_edge("extract_sources_from_single_source", "prepare_event_extraction")

        # Phase 2: Event extraction with map-reduce
        self.graph_builder.add_conditional_edges(
            "prepare_event_extraction",
            self.route_to_event_extraction,
            ["extract_events_from_single_source"],
        )

        # After all event extractions complete, go to commit_events_to_db
        self.graph_builder.add_edge("extract_events_from_single_source", "commit_extracted_events_to_db")

        # After commiting events to db, go to print_events
        self.graph_builder.add_edge("commit_extracted_events_to_db", "print_events")
        self.graph_builder.add_edge("print_events", END)

        self.graph = self.graph_builder.compile(checkpointer=checkpointer)

    async def test(self, semantic_content: str):
        # await self._prepare_scraper()
        # print(f"Running test for {semantic_content}")

        # semantic_vector = await self.embeddings.aembed_query(semantic_content)

        # async with get_db_session() as db:
        #     query = (
        #         select(
        #             ExtractedEventDB,
        #             (1 - ExtractedEventDB.semantic_vector.cosine_distance(semantic_vector)).label("similarity"),
        #         )
        #         .where(ExtractedEventDB.semantic_vector.isnot(None))
        #         .order_by(text("similarity DESC"))
        #     )
        #     result = (await db.execute(query)).all()

        #     for i, (event, similarity) in enumerate(result):
        #         print(f"Similar event {i}: Cosine distance: {similarity}")
        #         print(f"Similar event {i}: Title: {event.title}")
        #         print(f"Similar event {i}: Description: {event.description}")
        #         print(f"Similar event {i}: Location: {event.location}")
        #         print(f"Similar event {i}: Date: {event.date}")
        print(json.dumps(ExtractedEventBase.model_json_schema(), indent=2))

    @classmethod
    async def scrape_source(cls, source_id: int):
        scraper = cls(source_id)
        await scraper.scrape()
