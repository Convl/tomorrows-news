1. newspaper4k requires lxml_html_clean, which warns of security issues, though those are likely minor: https://pypi.org/project/lxml-html-clean/
2. Three ways to get a db session: get_db (async for fastapi), get_db_session (with asynccontextmanager for async access outside of FastApi) (both database.py) and gdbs in debug.py to get a sync session for debugging purposes
3. CONTEXT_ARGS propperty in settings, used to initialize engine, is set up to avoid collisions of prepared statements when using Supabase with transaction pooler
4. If changes to the connection type or other sqlalchemy changes cause issues with the scheduler, check to make sure the event listeners for the ScrapingSource are compatible with the new setup



TODO:
1. When new ScrapingSources get created, don't just check for identical URLs in the db, but similar ones like http://abc.com vs http://abc.com/