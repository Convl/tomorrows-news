import json
from datetime import datetime, timedelta, timezone
from pprint import pprint

from langchain_core.messages import HumanMessage
from langchain_openai import OpenAIEmbeddings
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
from app.models.event_comparison import EventComparisonDB
from app.models.extracted_event import ExtractedEventDB
from app.schemas.topic import TopicBase

from .llm_service import LlmService
from .scraping_config import EVENT_MERGE_SYSTEM_TEMPLATE
from .scraping_models import (
    EventMergeResponse,
    ExtractedEvent,
    ExtractedEventBase,
    ScrapingSourceWorkflow,
    ScrapingState,
    WebSourceBase,
    WebSourceWithMarkdown,
)
from .scraping_utils import (
    download_and_parse_article,
    web_sources_from_scraping_source,
)

CONSIDER_SAME_EVENT_THRESHOLD = 0.7
CONSIDER_NEW_DATE_TRUE_THRESHOLD = 3
CONSIDER_NEW_DURATION_TRUE_THRESHOLD = 3
CONSIDER_NEW_LOCATION_TRUE_THRESHOLD = 3


class Scraper:
    def __init__(self, source_id):
        self.sources = []
        self.scraping_source_id = source_id

    async def calculate_evidence_score(self, evidence_list: list[ExtractedEventDB]) -> float:
        """Calculate weighted score for a list of evidence based on recency."""
        if not evidence_list:
            return 0.0

        now = datetime.now(timezone.utc)
        score = 0.0

        for evidence in evidence_list:
            # Calculate fractional age in days
            age = (now - evidence.source_published_date).total_seconds() / (24 * 3600)
            # Exponential decay: newer sources get higher weight. Half-life of 30 days (score becomes 0.5 after 30 days)
            value = 0.5 ** (age / 30.0)
            score += value

        return score

    async def resolve_evidence_based_conflict(
        self,
        event_db: EventDB,
        extracted_event_db: ExtractedEventDB,
        db: AsyncSession,
        field_name: str,
        from_field_name: str,
        threshold: int = 3,
    ):
        """Generic evidence-based conflict resolution for any field."""
        old_value = getattr(event_db, field_name)
        new_value = getattr(extracted_event_db, field_name)

        # Query evidence for old value
        evidence_for_old_value = (
            (
                await db.execute(
                    select(ExtractedEventDB)
                    .where(ExtractedEventDB.event_id == event_db.id)
                    .where(getattr(ExtractedEventDB, field_name) == old_value)
                )
            )
            .scalars()
            .all()
        )

        # Query evidence for new value
        evidence_for_new_value = (
            (
                await db.execute(
                    select(ExtractedEventDB)
                    .where(ExtractedEventDB.event_id == event_db.id)
                    .where(getattr(ExtractedEventDB, field_name) == new_value)
                )
            )
            .scalars()
            .all()
        )

        # Check if recent evidence for new value meets threshold
        recent_evidence_for_new_value = [
            new_evidence
            for new_evidence in evidence_for_new_value
            if all(
                new_evidence.source_published_date > old_evidence.source_published_date
                for old_evidence in evidence_for_old_value
            )
        ]
        if len(recent_evidence_for_new_value) >= threshold:
            setattr(event_db, field_name, new_value)
            setattr(event_db, from_field_name, extracted_event_db.id)
            db.add(event_db)
            await db.flush()
            return

        # Calculate evidence scores and update if new evidence is stronger
        evidence_for_old_value_score = await self.calculate_evidence_score(evidence_for_old_value)
        evidence_for_new_value_score = await self.calculate_evidence_score(evidence_for_new_value)
        if evidence_for_new_value_score > evidence_for_old_value_score:
            setattr(event_db, field_name, new_value)
            setattr(event_db, from_field_name, extracted_event_db.id)
            db.add(event_db)
            await db.flush()

    async def resolve_date_conflict(self, event_db: EventDB, extracted_event_db: ExtractedEventDB, db: AsyncSession):
        """Resolve date conflicts between an EventDB and an ExtractedEventDB."""
        # If the dates are the same, do nothing
        if event_db.date == extracted_event_db.date:
            return

        # If the event does not specify a time (midnight effectively means 'no time', as pure dates get set to midnight in ExtractedEventDB.from_extracted_event), and the extracted event does, use the extracted event date
        if event_db.date.date() == extracted_event_db.date.date():
            if event_db.date.time() == datetime.time(0, 0, 0):
                event_db.date = extracted_event_db.date
                event_db.date_from_id = extracted_event_db.id
                db.add(event_db)
                await db.flush()
                return

        # Use generic evidence-based conflict resolution
        await self.resolve_evidence_based_conflict(
            event_db, extracted_event_db, db, "date", "date_from_id", CONSIDER_NEW_DATE_TRUE_THRESHOLD
        )

    async def resolve_duration_conflict(
        self, event_db: EventDB, extracted_event_db: ExtractedEventDB, db: AsyncSession
    ):
        """Resolve duration conflicts between an EventDB and an ExtractedEventDB."""
        # If both durations are identical or new event lacks duration info, do nothing
        if event_db.duration == extracted_event_db.duration or extracted_event_db.duration is None:
            return

        # If new event has duration info, but old event does not, update old event
        if event_db.duration is None:
            event_db.duration = extracted_event_db.duration
            event_db.duration_from_id = extracted_event_db.id
            db.add(event_db)
            await db.flush()
            return

        # Use generic evidence-based conflict resolution
        await self.resolve_evidence_based_conflict(
            event_db, extracted_event_db, db, "duration", "duration_from_id", CONSIDER_NEW_DURATION_TRUE_THRESHOLD
        )

    async def resolve_location_conflict(
        self, event_db: EventDB, extracted_event_db: ExtractedEventDB, db: AsyncSession
    ):
        """Resolve location conflicts between an EventDB and an ExtractedEventDB."""
        # If the locations are the same or the new event lacks location info, do nothing
        if event_db.location == extracted_event_db.location or extracted_event_db.location is None:
            return

        # Update the event if it currently has no location, or the new location merely adds information
        if event_db.location is None or event_db.location in extracted_event_db.location:
            event_db.location = extracted_event_db.location
            event_db.location_from_id = extracted_event_db.id
            db.add(event_db)
            await db.flush()
            return

        # Use generic evidence-based conflict resolution
        await self.resolve_evidence_based_conflict(
            event_db, extracted_event_db, db, "location", "location_from_id", CONSIDER_NEW_LOCATION_TRUE_THRESHOLD
        )

    async def merge_with_llm_if_same_event(
        self, extracted_event_db: ExtractedEventDB, event_db: EventDB, db: AsyncSession
    ) -> EventMergeResponse:
        """
        Check if two events represent the same real-world event and merge their titles and descriptions if they do.
        """
        merge_message = await EVENT_MERGE_SYSTEM_TEMPLATE.aformat(
            title_1=event_db.title,
            description_1=event_db.description,
            title_2=extracted_event_db.title,
            description_2=extracted_event_db.description,
        )
        response = await self.llm_service.event_merging_llm.ainvoke([merge_message])
        parsed_response: EventMergeResponse = response["parsed"]

        return parsed_response

    async def store_event_comparison(
        self,
        extracted_event_db: ExtractedEventDB,
        event_db: EventDB,
        vector_similarity: float,
        vector_threshold_met: bool,
        llm_considers_same_event: bool,
        db: AsyncSession,
    ):
        """Stores data from an ExtractedEventDB and EventDB comparison for analysis purposes."""
        comparison = EventComparisonDB(
            extracted_event_id=extracted_event_db.id,
            event_id=event_db.id,
            extracted_event_title=extracted_event_db.title,
            extracted_event_description=extracted_event_db.description,
            event_title=event_db.title,
            event_description=event_db.description,
            vector_similarity=vector_similarity,
            vector_threshold_met=vector_threshold_met,
            llm_considers_same_event=llm_considers_same_event,
        )
        db.add(comparison)
        await db.flush()

    async def update_event_db(
        self,
        event_db: EventDB,
        extracted_event_db: ExtractedEventDB,
        merge_response: EventMergeResponse,
        db: AsyncSession,
    ):
        """Update the date, duration, location, and additional infos of an EventDB with an ExtractedEventDB."""
        # Set title and description; these were determined by merge_with_llm_if_same_event
        event_db.title = merge_response.merged_title
        event_db.description = merge_response.merged_description

        # Resolve conflicts / merge data for date, duration and location
        await self.resolve_date_conflict(event_db, extracted_event_db, db)
        await self.resolve_duration_conflict(event_db, extracted_event_db, db)
        await self.resolve_location_conflict(event_db, extracted_event_db, db)

        # Merge additional infos
        if extracted_event_db.additional_infos:
            if not event_db.additional_infos:
                event_db.additional_infos = {}

            for k, v in extracted_event_db.additional_infos.items():
                if k in event_db.additional_infos:
                    event_db.additional_infos[k] += f"\n{v}"
                else:
                    event_db.additional_infos[k] = v

        db.add(event_db)
        await db.flush()

    async def commit_extracted_events_to_db(self, state: ScrapingState):
        """Commit ExtractedEvents to the database, then call consolidate_extracted_events."""
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
            await self.consolidate_extracted_events(extracted_events_db, db)

    async def consolidate_extracted_events(self, extracted_events_db: list[ExtractedEventDB], db: AsyncSession):
        """After ExtractedEvents have been added to the database, either merge them into existing EventDBs or create new EventDBs from them."""
        for extracted_event_db in extracted_events_db:
            event_with_similarity = (
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
            ).first()
            event_db, similarity = event_with_similarity if event_with_similarity else (None, 0)

            # TODO: change to if event_db and similarity > CONSIDER_SAME_EVENT_THRESHOLD, remove the latter condition in the next if clause, once confident about the threshold value
            if event_db:
                merge_response = await self.merge_with_llm_if_same_event(extracted_event_db, event_db, db)
                await self.store_event_comparison(
                    extracted_event_db,
                    event_db,
                    similarity,
                    similarity > CONSIDER_SAME_EVENT_THRESHOLD,
                    merge_response.is_same_event,
                    db,
                )

                # if extracted_event_db and event_db both refer to the same real-world event according to their vector scores and merge_with_llm_if_same_event, merge them
                if merge_response.is_same_event and similarity > CONSIDER_SAME_EVENT_THRESHOLD:
                    extracted_event_db.event_id = event_db.id

                    db.add(extracted_event_db)
                    await db.flush()
                    await self.update_event_db(event_db, extracted_event_db, merge_response, db)
                    continue

            # if we get here, no similar event was found, so we create a new one
            print("### No similar event found, creating new event")
            new_event = EventDB.from_extracted_event_db(extracted_event_db)
            db.add(new_event)
            await db.flush()
            extracted_event_db.event_id = new_event.id
            db.add(extracted_event_db)
            await db.flush()
        await db.commit()

    async def extract_sources_from_single_source(
        self, state: dict[str, WebSourceWithMarkdown]
    ) -> dict[str, list[WebSourceWithMarkdown] | list]:
        """Extract additional sources from a single web source."""

        # to skip this part, simply return {}
        source: WebSourceWithMarkdown = state["source"]
        try:
            source._visited = True
            print(f"Processing source: {source.url}")
            messages = [
                self.source_extraction_system_message,
                HumanMessage(f"Extract sources from the following webpage: {source.markdown}"),
            ]
            response = await self.llm_service.source_extracting_llm.ainvoke(messages)
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
        if not state.sources and not state.scraping_source._visited:
            return {"sources": await web_sources_from_scraping_source(state.scraping_source)}
        else:
            return {}

    async def route_to_source_extraction(self, state: ScrapingState):
        """Route to source extraction for parallel processing."""

        eligible_sources = [
            source
            for source in state.sources
            if source.degrees_of_separation < state.scraping_source.degrees_of_separation and not source._visited
        ]
        print(f"State has {len(state.sources)} sources")

        if eligible_sources:
            print(f"Routing {len(eligible_sources)} eligible sources to source extraction")
            return [Send("extract_sources_from_single_source", {"source": source}) for source in eligible_sources]
        else:
            print("No eligible sources for extraction, proceeding to event extraction")
            return "prepare_event_extraction"

    async def extract_events_from_single_source(self, state: dict[str, WebSourceWithMarkdown]):
        """Extract events from a single source."""
        source = state["source"]
        print(f"Extracting events from source: {source.url}")
        messages = [
            self.event_extraction_system_message,
            HumanMessage(f"Extract events from the following webpage: {source.markdown}"),
        ]
        try:
            response = await self.llm_service.event_extracting_llm.ainvoke(messages)
            events: list[ExtractedEventBase] = response["parsed"].events
            print(f"Extracted {len(events)} events from {source.url}")
        except Exception as e:
            print(f"ERROR in extract_events_from_single_source for {source.url}: {e}")
            return {"events": []}

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
                (await db.execute(select(ScrapingSourceDB).where(ScrapingSourceDB.id == self.scraping_source_id)))
                .scalars()
                .one_or_none()
            )
            if not self.scraping_source:
                raise ValueError(f"Source with id {self.scraping_source_id} not found.")

            topic: TopicDB = (
                (await db.execute(select(TopicDB).where(TopicDB.id == self.scraping_source.topic_id)))
                .scalars()
                .one_or_none()
            )
            if not topic:
                raise ValueError(f"Topic with id {self.scraping_source.topic_id} not found.")
            self.topic = TopicBase.model_validate(topic, from_attributes=True)

            # Initialize LLM service
            self.llm_service = LlmService()

            # Create system messages using the LLM service
            self.event_extraction_system_message = await self.llm_service.get_event_extraction_system_message(
                self.topic, self.scraping_source.language
            )
            self.source_extraction_system_message = await self.llm_service.get_source_extraction_system_message(
                self.topic
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
            # ["extract_sources_from_single_source"],
            {
                "prepare_event_extraction": "prepare_event_extraction",
                "extract_sources_from_single_source": "extract_sources_from_single_source",
            },
        )

        # After all source extractions complete, go to prepare_event_extraction
        # self.graph_builder.add_edge("extract_sources_from_single_source", "prepare_event_extraction")
        self.graph_builder.add_edge("extract_sources_from_single_source", "start_source_extraction")

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
        print(json.dumps(ExtractedEventBase.model_json_schema(), indent=2))

    @classmethod
    async def scrape_source(cls, source_id: int):
        scraper = cls(source_id)
        await scraper.scrape()
