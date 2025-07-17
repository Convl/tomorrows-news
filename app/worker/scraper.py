from typing import Union

from sqlalchemy import select

from app.core.enums import ScrapingSourceEnum
from app.database import get_db_session
from app.models import ScrapingSource
from app.worker.scrapers.rssscraper import RssScraper
from app.worker.scrapers.webscraper import WebScraper


class Scraper:
    def __init__(self):
        self.scrapers = {}

    def get_scraper(self, source_type: ScrapingSourceEnum) -> Union[WebScraper, RssScraper]:
        if source_type not in self.scrapers:
            match source_type:
                case ScrapingSourceEnum.WEBPAGE:
                    self.scrapers[source_type] = WebScraper()
                case ScrapingSourceEnum.RSS:
                    self.scrapers[source_type] = RssScraper()
                case _:
                    raise ValueError(f"Unsupported source type: {source_type}")
        return self.scrapers[source_type]

    async def scrape(self, source_id: int, url=None):
        async with get_db_session() as db:
            source: ScrapingSource = (
                (await db.execute(select(ScrapingSource).where(ScrapingSource.id == source_id))).scalars().one_or_none()
            )
            if not source:
                raise ValueError(f"Source with id {source_id} not found.")

        scraper = self.get_scraper(source.source_type)
        return await scraper.scrape(source, url=url)


scraper = Scraper()
