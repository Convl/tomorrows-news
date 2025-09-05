from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rich.traceback import install

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.custom_logging import create_logger
from app.worker.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Initialize loguru logging once for entire project
create_logger()


# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve static files (frontend)
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "openapi_json": f"{settings.API_V1_STR}/openapi.json",
    }


@app.get("/debug")
async def dbg():
    source_id = 15

    # Clear test data before running scraper
    # from sqlalchemy import delete, select
    # from app.database import get_db_session
    # from app.models import EventComparisonDB, EventDB, ExtractedEventDB, ScrapingSourceDB
    # import datetime
    # async with get_db_session() as db:
    #     await db.execute(delete(EventComparisonDB))
    #     await db.execute(delete(EventDB))
    #     await db.execute(delete(ExtractedEventDB))
    # sources = (await db.execute(select(ScrapingSourceDB))).scalars().all()
    # for source in sources:
    #     source.last_scraped_at = datetime.now(timezone.utc) - timedelta(days=1)
    # db.add(source)
    #     await db.commit()
    #     print("Cleared all EventDB, ExtractedEventDB, and EventComparisonDB records, and set last_scraped_at 1 days back")

    # Run scraper
    # from app.worker.scraper import Scraper
    # scraper = Scraper(source_id)
    # await scraper.scrape()

    # Reschedule jobs
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from app.database import get_db_session
    from app.models import ScrapingSourceDB
    from app.worker.scheduler import scheduler

    # async with get_db_session() as db:
    #     sources = (await db.execute(select(ScrapingSourceDB))).scalars().all()
    #     for source in sources:
    #         source.last_scraped_at = datetime.now(timezone.utc) - timedelta(days=3)
    #         db.add(source)
    #         print(f"Set last_scraped_at for source {source.id} to {source.last_scraped_at}")
    #     await db.commit()

    # from app.worker.scraper import Scraper
    # scraper = Scraper(source_id)
    # await scraper.scrape()

    # async with get_db_session() as db:
    #     sources = (await db.execute(select(ScrapingSourceDB))).scalars().all()
    #     for source in sources:
    #         source.currently_scraping = False
    #         db.add(source)
    #     await db.commit()

    # for i, job in enumerate(scheduler.get_jobs()):
    #     print(f"Job with id {job.id} will run at {job.next_run_time}")
        # scheduler.modify_job(job.id, next_run_time=datetime.now(timezone.utc) + timedelta(seconds=20 * i))
        # print(f"Rescheduled job {i}: {job.id} to {datetime.now(timezone.utc) + timedelta(seconds=20 * i)}")

    from newspaper import Article
    urls = [
    # "https://www.faz.net/aktuell/wissen/computer-mathematik/supercomputer-jupiter-eingeweiht-europa-an-der-weltspitze-accg-110672169.html",
    # "https://www.faz.net/einspruch/exklusiv/cannabis-reform-weckt-erinnerung-an-gescheiterte-pkw-maut-accg-110670566.html",
    # "https://www.sueddeutsche.de/politik/steuerentlastungen-gastwirte-pendler-soeders-vorschlaege-li.3308055",
    # "https://www.sueddeutsche.de/politik/von-der-leyen-putin-gps-jamming-bulgarien-li.3307713?reduced=true",
    # "https://www.welt.de/politik/deutschland/article68ba8bc66775f2119f5a0a7e/gegenrede-die-infame-botschaft-an-israelis-sie-muessten-dankbar-sein-wenn-man-sie-normal-behandelt.html",
    "https://www.welt.de/politik/deutschland/plus68ba86f046b61b4dcb0ba90e/kommunalwahl-in-nrw-wie-sich-ein-bruch-der-gruenen-welle-anbahnt.html",
    # "https://rsw.beck.de/aktuell/daily/meldung/detail/eugh-leistungen-asylbewerber-bett-brot-seife-mindestniveau",
    # "https://www.bundesgerichtshof.de/DE/Presse/Pressemitteilungen/pressemitteilungen_node.html",
    # "https://www.bundesgerichtshof.de/SharedDocs/Pressemitteilungen/DE/2025/2025164.html?nn=10690868",
    ] # TODO: why do script tags and others remain in welt paywall article?
    from app.worker.scraping_utils import _is_article_html_good_quality, sanitize_html
    for url in urls:
        article = Article(url, memoize_articles=False, disable_category_cache=True)
        article.download()
        article.parse()
        print("############################################################\n"*10)
        print(f"url: {url}")
        print(f"is article html good quality: {_is_article_html_good_quality(article.article_html)}")
        print(f"sanitized html: {sanitize_html(article.html)}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        reload=False,
        log_level=None,
        log_config=None,
        port=8000,
    )
