import datetime

from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.topic import TopicBase

from .scraping_config import EVENT_EXTRACTION_SYSTEM_TEMPLATE, SOURCE_EXTRACTION_SYSTEM_TEMPLATE
from .scraping_models import EventMergeResponse, ExtractedBaseEvents, ExtractedUrls, ExtractedWebSources


class LlmService:
    """Handles LLM initialization and prompt formatting for scraping operations."""

    def __init__(self):
        # Setup rate limiter and LLM
        self.rate_limiter = InMemoryRateLimiter(
            requests_per_second=1,
            check_every_n_seconds=0.9,
            max_bucket_size=1,
        )

        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            # model_name="moonshotai/kimi-k2",
            # model_name="google/gemini-2.5-pro",
            model_name="openai/gpt-5-mini",
            temperature=0.2,
            rate_limiter=self.rate_limiter,
        )

        self.source_extracting_llm = self.llm.with_structured_output(
            # schema=ExtractedUrls,
            schema=ExtractedWebSources,
            method="json_schema",
            include_raw=True,
            strict=True,
        )

        self.event_extracting_llm = self.llm.with_structured_output(
            schema=ExtractedBaseEvents,
            method="json_schema",
            include_raw=True,
            strict=True,
        )

        self.event_merging_llm = self.llm.with_structured_output(
            schema=EventMergeResponse,
            method="json_schema",
            include_raw=True,
            strict=True,
        )

    async def get_event_extraction_system_message(self, topic: TopicBase, language: str) -> str:
        """Format the event extraction system message."""
        return await EVENT_EXTRACTION_SYSTEM_TEMPLATE.aformat(
            topic_name=topic.name,
            topic_description=topic.description,
            topic_country=topic.country,
            current_date=datetime.datetime.now(datetime.timezone.utc).strftime("%A, %d. of %B %Y"),
            language=language,
        )

    async def get_source_extraction_system_message(self, topic: TopicBase) -> str:
        """Format the source extraction system message."""
        return await SOURCE_EXTRACTION_SYSTEM_TEMPLATE.aformat(
            topic_name=topic.name,
            topic_description=topic.description,
            topic_country=topic.country,
        )
