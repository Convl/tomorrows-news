@app.get("/debug/reschedule/{job_id}/{minutes}")
async def reschedule_job(job_id: str, minutes: int):
    """Manually reschedule a job to run in X minutes from now"""
    from datetime import datetime, timedelta

    from app.worker.scheduler import scheduler

    try:
        # Calculate the target time
        next_run_time = datetime.now() + timedelta(minutes=minutes)

        # Get the job
        job = scheduler.get_job(job_id, jobstore="scraping")

        if not job:
            return {"error": f"Job '{job_id}' not found!", "success": False}

        old_next_run = job.next_run_time

        # Modify the job's next run time
        scheduler.modify_job(job_id=job_id, jobstore="scraping", next_run_time=next_run_time)

        # Verify the change
        updated_job = scheduler.get_job(job_id, jobstore="scraping")

        return {
            "success": True,
            "job_id": job_id,
            "old_next_run_time": old_next_run.isoformat() if old_next_run else None,
            "new_next_run_time": updated_job.next_run_time.isoformat() if updated_job.next_run_time else None,
            "minutes_from_now": minutes,
            "message": f"Job '{job_id}' will run in {minutes} minutes",
        }

    except Exception as e:
        return {"error": str(e), "success": False}
