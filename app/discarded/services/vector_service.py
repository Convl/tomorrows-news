import asyncio
from typing import Any, Dict, List, Optional

from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.event import EventDB
from app.models.extracted_event import ExtractedEventDB
from app.worker.scraping_models import ExtractedEvent


class VectorService:
    """Service for managing event embeddings using direct pgvector integration."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []

        # Remove empty texts
        valid_texts = [text for text in texts if text.strip()]
        if not valid_texts:
            return []

        # Generate embeddings using OpenAI
        embeddings = await asyncio.to_thread(self.embeddings.embed_documents, valid_texts)
        return embeddings

    async def update_event_embeddings(self, event: EventDB) -> None:
        """Generate and store embeddings for an event."""
        # Prepare content for embeddings
        semantic_content = f"{event.title}\n{event.description or ''}".strip()
        location_content = event.location or ""

        # Generate embeddings
        contents = []
        if semantic_content:
            contents.append(semantic_content)
        if location_content:
            contents.append(location_content)

        if not contents:
            return

        embeddings = await self._generate_embeddings(contents)

        # Update the event with new embeddings
        if semantic_content and embeddings:
            event.semantic_vector = embeddings[0]
        if location_content and len(embeddings) > 1:
            event.location_vector = embeddings[1] if len(contents) == 2 else embeddings[0]
        elif location_content and semantic_content and embeddings:
            # If we only have location, use the first embedding
            event.location_vector = embeddings[0]

        # Commit the changes
        await self.db_session.commit()

    async def update_extracted_event_embeddings(self, extracted_event: ExtractedEventDB) -> None:
        """Generate and store embeddings for an extracted event."""
        # Prepare content for embeddings
        semantic_content = f"{extracted_event.title}\n{extracted_event.description or ''}".strip()
        location_content = extracted_event.location or ""

        # Generate embeddings
        contents = []
        if semantic_content:
            contents.append(semantic_content)
        if location_content:
            contents.append(location_content)

        if not contents:
            return

        embeddings = await self._generate_embeddings(contents)

        # Update the extracted event with new embeddings
        if semantic_content and embeddings:
            extracted_event.semantic_vector = embeddings[0]
        if location_content and len(embeddings) > 1:
            extracted_event.location_vector = embeddings[1] if len(contents) == 2 else embeddings[0]
        elif location_content and semantic_content and embeddings:
            extracted_event.location_vector = embeddings[0]

        # Commit the changes
        await self.db_session.commit()

    async def find_similar_events(
        self, event: EventDB, limit: int = 10, similarity_threshold: float = 0.8, topic_filter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find events similar to the given event using cosine similarity."""
        if not event.semantic_vector:
            return []

        # Build the query with vector similarity
        query = select(
            EventDB,
            func.abs(1 - func.cosine_distance(EventDB.semantic_vector, event.semantic_vector)).label("similarity"),
        ).where(EventDB.id != event.id, EventDB.semantic_vector.isnot(None))

        # Add topic filter if specified
        if topic_filter:
            query = query.where(EventDB.topic_id == topic_filter)

        # Order by similarity and limit results
        query = query.order_by(text("similarity DESC")).limit(limit)

        result = await self.db_session.execute(query)
        similar_events = []

        for similar_event, similarity in result:
            if similarity >= similarity_threshold:
                similar_events.append(
                    {
                        "event_id": similar_event.id,
                        "title": similar_event.title,
                        "similarity_score": float(similarity),
                        "event": similar_event,
                    }
                )

        return similar_events

    async def find_potential_duplicates(
        self, event: EventDB, similarity_threshold: float = 0.9
    ) -> List[Dict[str, Any]]:
        """Find potential duplicate events with high similarity."""
        return await self.find_similar_events(
            event=event,
            limit=5,
            similarity_threshold=similarity_threshold,
            topic_filter=event.topic_id,  # Only search within same topic
        )

    async def find_similar_extracted_events(
        self, extracted_event: ExtractedEventDB, limit: int = 10, similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Find extracted events similar to the given extracted event."""
        if not extracted_event.semantic_vector:
            return []

        # Build the query with vector similarity
        query = (
            select(
                ExtractedEventDB,
                func.abs(
                    1 - func.cosine_distance(ExtractedEventDB.semantic_vector, extracted_event.semantic_vector)
                ).label("similarity"),
            )
            .where(ExtractedEventDB.id != extracted_event.id, ExtractedEventDB.semantic_vector.isnot(None))
            .order_by(text("similarity DESC"))
            .limit(limit)
        )

        result = await self.db_session.execute(query)
        similar_events = []

        for similar, similarity in result:
            if similarity >= similarity_threshold:
                similar_events.append(
                    {
                        "extracted_event_id": similar.id,
                        "title": similar.title,
                        "similarity_score": float(similarity),
                        "extracted_event": similar,
                    }
                )

        return similar_events

    async def search_events_by_text(
        self, query_text: str, limit: int = 10, similarity_threshold: float = 0.7, topic_filter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search events by text similarity."""
        # Generate embedding for the query
        query_embeddings = await self._generate_embeddings([query_text])
        if not query_embeddings:
            return []

        query_vector = query_embeddings[0]

        # Build the search query
        query = select(
            EventDB, func.abs(1 - func.cosine_distance(EventDB.semantic_vector, query_vector)).label("similarity")
        ).where(EventDB.semantic_vector.isnot(None))

        # Add topic filter if specified
        if topic_filter:
            query = query.where(EventDB.topic_id == topic_filter)

        # Order by similarity and limit results
        query = query.order_by(text("similarity DESC")).limit(limit)

        result = await self.db_session.execute(query)
        search_results = []

        for event, similarity in result:
            if similarity >= similarity_threshold:
                search_results.append(
                    {"event_id": event.id, "title": event.title, "similarity_score": float(similarity), "event": event}
                )

        return search_results


async def get_vector_service(db_session: AsyncSession) -> VectorService:
    """Dependency to get vector service instance."""
    return VectorService(db_session)
