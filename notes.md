1. newspaper4k requires lxml_html_clean, which warns of security issues, though those are likely minor: https://pypi.org/project/lxml-html-clean/
2. Three ways to get a db session: get_db (async for fastapi), get_db_session (with asynccontextmanager for async access outside of FastApi) (both database.py) and gdbs in debug.py to get a sync session for debugging purposes
3. CONTEXT_ARGS propperty in settings, used to initialize engine, is set up to avoid collisions of prepared statements when using Supabase with transaction pooler
4. If changes to the connection type or other sqlalchemy changes cause issues with the scheduler, check to make sure the event listeners for the ScrapingSource are compatible with the new setup



TODO:
1. When new ScrapingSources get created, don't just check for identical URLs in the db, but similar ones like http://abc.com vs http://abc.com/
2. When extracting sources, newspaper4k sometimes fails to find article.publish_date, even though it is there. This happens e.g. for beck-aktuell articles. Those articles currently get discarded, because we can't verify that they were published since the last scraping run. In the future, try to add additional logic, e.g. by trying to discover the article in a rss feed, custom html/url/header parsing, etc, to ascertain publication date when newspaper4k can't.
3. Is extracting links via LLM really any better than extracting them via beautifulsoup? Test performance of different models in extracting (only/all) relevant links
4. Further investigate this error: https://github.com/langchain-ai/langgraph/issues/5675

Feature Ideas:
1. Extend possible dates for Events to date ranges (see commented out code using datetime | DateTimeFrame)
