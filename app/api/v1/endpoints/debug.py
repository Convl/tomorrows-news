import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.database import get_db, get_db_session
from app.models import ExtractedEventDB
from app.models.user import UserDB
from app.worker.scheduler import scheduler

router = APIRouter()


@router.get("/frontend")
async def debug_frontend():
    await asyncio.sleep(3)
    return {"message": "Connection to backend established"}


@router.post("/trigger-job/{source_id}")
async def debug_trigger_job(source_id: int):
    """Trigger a job for a scraping source"""
    job_id = f"scraping_source_{source_id}"
    scheduler.modify_job(job_id, next_run_time=datetime.now(timezone.utc) + timedelta(seconds=30))
    return {"message": f"Job {job_id} scheduled to run in 30 seconds"}


@router.get("/get-jobs")
async def get_jobs():
    """Get all jobs"""
    jobs = scheduler.get_jobs()
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "max_instances": job.max_instances,
        }
        for job in jobs
    ]


@router.delete("/delete-scraping-job/{source_id}")
async def delete_scraping_job(source_id: int):
    """Delete a scraping job for a scraping source"""
    scheduler.remove_job(job_id=f"scraping_source_{source_id}", jobstore="scraping")
    return {"message": f"Job {f'scraping_source_{source_id}'} deleted"}


@router.get("/get-magic-link")
async def get_magic_link(
    user_email: str,
    lifetime_seconds: int = 0,
    url: str = "https://tomorrows-news.vercel.app/login",
    db: AsyncSession = Depends(get_db),
):
    if not (target_user := (await db.execute(select(UserDB).where(UserDB.email == user_email))).scalar_one_or_none()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_email} not found")

    from fastapi_users.authentication import JWTStrategy

    from app.core.config import settings

    jwt_strategy = JWTStrategy(secret=settings.JWT_SECRET.get_secret_value(), lifetime_seconds=lifetime_seconds)
    token = await jwt_strategy.write_token(target_user)

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}token={token}"


@router.get("/")
async def dbg(current_user: UserDB = Depends(current_active_user), db: AsyncSession = Depends(get_db)):
    """Debug endpoint, used for testing various things"""
    logger.info("This <red>is</red> a <yellow>test</yellow> message")
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # import json

    # from sqlalchemy.orm import selectinload

    # from app.api.v1.sse import sse_broadcaster
    # from app.models.event import EventDB
    # from app.models.extracted_event import ExtractedEventDB
    # from app.schemas.event import EventResponse

    # query = select(EventDB).options(selectinload(EventDB.extracted_events)).where(EventDB.id == 928)
    # event = (await db.execute(query)).scalars().first()
    # old_title = event.title
    # event.title = "Test Event"
    # db.add(event)
    # await db.flush()
    # await db.commit()
    # # Re-fetch event with extracted_events loaded for response
    # query = select(EventDB).options(selectinload(EventDB.extracted_events)).where(EventDB.id == event.id)
    # event = (await db.execute(query)).scalars().one()
    # await sse_broadcaster.publish(
    #     user_id=current_user.id,
    #     message=json.dumps(
    #         {
    #             "type": "event_update",
    #             "topic_id": event.topic_id,
    #             "payload": EventResponse.model_validate(event).model_dump(mode="json"),
    #         }
    #     ),
    # )
    # await asyncio.sleep(10)
    # event.title = old_title
    # db.add(event)
    # await db.flush()
    # await db.commit()
    # # Re-fetch event with extracted_events loaded for response
    # query = select(EventDB).options(selectinload(EventDB.extracted_events)).where(EventDB.id == event.id)
    # event = (await db.execute(query)).scalars().one()
    # await sse_broadcaster.publish(
    #     user_id=current_user.id,
    #     message=json.dumps(
    #         {
    #             "type": "event_update",
    #             "topic_id": event.topic_id,
    #             "payload": EventResponse.model_validate(event).model_dump(mode="json"),
    #         }
    #     ),
    # )

    # source_id = 15
    # from datetime import datetime, timedelta, timezone

    # from sqlalchemy import select

    # from app.database import get_db_session
    # from app.models import ScrapingSourceDB
    # from app.worker.scheduler import scheduler

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
    #     if job.id == "scraping_source_31":
    #         scheduler.modify_job(job.id, next_run_time=datetime.now(timezone.utc) + timedelta(seconds=60))
    #         print(f"Job with id {job.id} will run at {job.next_run_time}")
    # scheduler.modify_job(job.id, next_run_time=datetime.now(timezone.utc) + timedelta(seconds=20 * i))
    # print(f"Rescheduled job {i}: {job.id} to {datetime.now(timezone.utc) + timedelta(seconds=20 * i)}")

    # from newspaper import Article
    # urls = [
    # # "https://www.faz.net/aktuell/wissen/computer-mathematik/supercomputer-jupiter-eingeweiht-europa-an-der-weltspitze-accg-110672169.html",
    # # "https://www.faz.net/einspruch/exklusiv/cannabis-reform-weckt-erinnerung-an-gescheiterte-pkw-maut-accg-110670566.html",
    # # "https://www.sueddeutsche.de/politik/steuerentlastungen-gastwirte-pendler-soeders-vorschlaege-li.3308055",
    # # "https://www.sueddeutsche.de/politik/von-der-leyen-putin-gps-jamming-bulgarien-li.3307713?reduced=true",
    # # "https://www.welt.de/politik/deutschland/article68ba8bc66775f2119f5a0a7e/gegenrede-die-infame-botschaft-an-israelis-sie-muessten-dankbar-sein-wenn-man-sie-normal-behandelt.html",
    # "https://www.welt.de/politik/deutschland/plus68ba86f046b61b4dcb0ba90e/kommunalwahl-in-nrw-wie-sich-ein-bruch-der-gruenen-welle-anbahnt.html",
    # # "https://rsw.beck.de/aktuell/daily/meldung/detail/eugh-leistungen-asylbewerber-bett-brot-seife-mindestniveau",
    # # "https://www.bundesgerichtshof.de/DE/Presse/Pressemitteilungen/pressemitteilungen_node.html",
    # # "https://www.bundesgerichtshof.de/SharedDocs/Pressemitteilungen/DE/2025/2025164.html?nn=10690868",
    # ] # TODO: why do script tags and others remain in welt paywall article?
    # from app.worker.scraping_utils import _is_article_html_good_quality, sanitize_html
    # for url in urls:
    #     article = Article(url, memoize_articles=False, disable_category_cache=True)
    #     article.download()
    #     article.parse()
    #     print("############################################################\n"*10)
    #     print(f"url: {url}")
    #     print(f"is article html good quality: {_is_article_html_good_quality(article.article_html)}")
    #     print(f"sanitized html: {sanitize_html(article.html)}")
