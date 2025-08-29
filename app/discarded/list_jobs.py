    # List scheduler jobs
    from datetime import timezone

    from app.worker.scheduler import scheduler

    job_infos = []
    for job in scheduler.get_jobs():
        job_info = {
            "id": job.id,
            "name": job.name,
            "func": f"{job.func.__module__}.{job.func.__name__}",
            "args": job.args,
            "trigger": str(job.trigger),
            "next_run_time": job.next_run_time.astimezone(timezone.utc).isoformat() if job.next_run_time else None,
            "misfire_grace_time": job.misfire_grace_time,
            "coalesce": job.coalesce,
            "max_instances": job.max_instances,
            "executor": job.executor,
        }
        job_infos.append(job_info)
        print(job_info)

    return {"jobs": job_infos}