import operator
from datetime import date as dt_date
from datetime import datetime, timedelta
from typing import Annotated

from pydantic import BaseModel, Field, PrivateAttr, field_validator

from app.core.enums import ScrapingSourceEnum
from app.schemas.topic import TopicBase


class TopicWorkflow(BaseModel):
    """Topic model for use in workflow state - contains only fields needed for scraping"""

    id: int
    name: str
    description: str
    country: str | None = None
    language: str | None = None

    class Config:
        from_attributes = True


class ScrapingSourceWorkflow(BaseModel):
    """Scraping source model for use in workflow state - contains only fields needed for scraping"""

    id: int
    topic_id: int
    base_url: str  # TODO: rename to url
    source_type: ScrapingSourceEnum
    language: str | None = None
    country_code: str | None = None
    last_scraped_at: datetime | None = None
    degrees_of_separation: int = Field(default=0, ge=0)
    topic: TopicWorkflow
    _visited: bool = PrivateAttr(default=False)  # Whether the source has been visited for source extraction

    class Config:
        from_attributes = True


class WebSourceBase(BaseModel):
    """A web source (article, press release, etc.)"""

    url: str = Field(description="The full URL of the web source")
    date: datetime | None = Field(
        default=None, description="The date when the source was published or last updated. Only set if you are certain."
    )
    title: str | None = Field(default=None, description="The headline or title of the source, if available")


class WebSourceWithMetadata(WebSourceBase):
    """A web source (article, press release, etc.) containing metadata."""

    date: datetime = Field(description="The date when the source was published or last updated")
    _visited: bool = PrivateAttr(default=False)  # Whether the source has been visited for source extraction
    degrees_of_separation: int = Field(
        description="The number of degrees of separation from the original source", default=0
    )

    @classmethod
    def from_web_source_with_markdown(cls, web_source_with_markdown: "WebSourceWithMarkdown"):
        return cls(
            url=web_source_with_markdown.url,
            date=web_source_with_markdown.date,
            title=web_source_with_markdown.title,
            _visited=web_source_with_markdown._visited,
            degrees_of_separation=web_source_with_markdown.degrees_of_separation,
        )


class WebSourceWithMarkdown(WebSourceWithMetadata):
    """A web source (article, press release, etc.) containing content and metadata."""

    markdown: str = Field(description="The full source's content, converted to markdown format for processing")


class ExtractedWebSources(BaseModel):
    """Web sources extracted from content by LLM."""

    sources: list[WebSourceBase] = Field(description="A list of web sources extracted from the web source")


class ExtractedEventBase(BaseModel):
    """An event extracted from a web source that is relevant to a specific topic of interest."""

    title: str = Field(
        description="A clear, concise title or name for the event",
        examples=["City Council Meeting", "Tech Conference 2024", "Climate Action Workshop"],
    )
    description: str = Field(
        description="A concise description of what the event is about, including key details and context, anywhere from 20 to 200 words",
        examples=[
            "Monthly city council meeting to discuss urban planning and budget allocation",
            "Annual technology conference featuring speakers from major tech companies",
        ],
    )
    # date: datetime | DateTimeframe = Field(
    #     description="Event timing: use datetime for exact timing (e.g., '2024-03-15T14:00:00'), or DateTimeframe for approximate timing with earliest/latest bounds. Exact timing is preferred, though only if you are certain that you can determine an exact date. If you are not certain, use DateTimeframe."
    # )
    date: datetime | dt_date = Field(
        description="The date (and, if available, time) when the event takes place. If only a date is mentioned (e.g., 'July 29th'), represent it as a date object (e.g., 2025-07-29). If a date and time are mentioned, represent them as a datetime object (e.g. 2025-07-29T14:30:00).",
        examples=[
            "2024-03-15",  # Specific time with timezone
            "2024-03-15T14:30:00",  # Specific time without timezone
        ],
    )
    snippet: str = Field(
        description="A short snippet of text from the source, EXACTLY as it appears in the source, specifying when the event will take place.",
        examples=["The parliamentary vote on the new law is scheduled for the 20th of August 2030."],
    )
    country_code: str | None = Field(
        default=None,
        description="The ISO 3166-1 alpha-2 code of the country where the event will take place",
        examples=["DE", "US", "FR", "ES", "IT", "PT", "GR", "TR"],
    )
    location: str | None = Field(
        default=None,
        description="The geographic location where the event takes place",
        examples=["Berlin, Germany", "Online", "Town Hall, 123 Main St", "Central Park"],
    )
    significance: float = Field(
        description="A numerical weight (0.0 to 1.0) indicating how important this event is. 0.0 means not important at all, 1.0 means extremely important. This is a subjective measure, and should be based on: 1. The importance of the event to the topic, 2. The nature of the event (is it a mere deadline that is likely to be extended? An intermediate step in a long process? Or the culmination of a long process, where specific results will be presented / decisions will be made?), 3. The likelihood of the event actually happening.",
    )
    duration: timedelta | None = Field(
        default=None,
        description="How long the event lasts, in ISO 8601 duration format. Leave blank if no duration is mentioned.",
        examples=["P3DT12H30M5S", "PT1H30M", "P1D", "PT1H", "PT30M"],
    )
    additional_infos: dict[str, str] | None = Field(
        default=None,
        description="Optional supplementary information about the event, to be stored as key-value pairs. DO NOT include information here that fits more accurately into any of the other fields, or that relates to the source where the event was found.",
        examples=[
            {"Registration link": "https://www.example.com/registration"},
            {"Reference number": "1234567890"},
            {"Accreditation deadline": "2025-08-01"},
        ],
    )


class ExtractedEvent(ExtractedEventBase):
    """An event extracted from a web source that is relevant to a specific topic of interest, with the source from which it was extracted."""

    source: WebSourceWithMetadata = Field(description="The web source from which the event was extracted")


class ExtractedBaseEvents(BaseModel):
    events: list[ExtractedEventBase] = Field(description="A list of events extracted from the web source")


class EventMergeResponse(BaseModel):
    is_same_event: bool = Field(
        description="Whether the two events refer to the same real-world event. True if they do, False if they do not."
    )
    merged_title: str | None = Field(
        description="The merged title of the two events, if they refer to the same real-world event. When merging, try to preserve the most important information from both events. However, if there is contradictory information, you should prioritize the information from the second event.",
        default=None,
    )
    merged_description: str | None = Field(
        description="The merged description of the two events, if they refer to the same real-world event. When merging, try to preserve the most important information from both events. However, if there is contradictory information, you should prioritize the information from the second event.",
        default=None,
    )


class ScrapingState(BaseModel):
    scraping_source: ScrapingSourceWorkflow = Field(description="The scraping source that is being processed")
    sources: Annotated[list[WebSourceWithMarkdown], operator.add]
    events: Annotated[list[ExtractedEvent], operator.add]
