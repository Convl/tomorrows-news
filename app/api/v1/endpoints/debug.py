from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import current_active_user
from app.database import get_db
from app.models.user import UserDB
from app.worker.scheduler import scheduler

router = APIRouter()


@router.post("/debug/trigger-job/{source_id}")
async def debug_trigger_job(source_id: int, current_user: UserDB = Depends(current_active_user)):
    """Trigger a job for a scraping source"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    job_id = f"scraping_source_{source_id}"
    scheduler.modify_job(job_id, next_run_time=datetime.now(timezone.utc) + timedelta(seconds=30))
    return {"message": f"Job {job_id} scheduled to run in 30 seconds"}


@router.get("/debug/get-jobs")
async def get_jobs(current_user: UserDB = Depends(current_active_user)):
    """Get all jobs"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    jobs = scheduler.get_jobs()
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        }
        for job in jobs
    ]


@router.get("/debug")
async def dbg(current_user: UserDB = Depends(current_active_user)):
    """Debug endpoint, used for testing various things"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

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
