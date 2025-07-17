import newspaper
from newspaper import utils, Source

from app.models.scraping_source import ScrapingSource


class WebScraper:
    async def scrape(self, source: ScrapingSource, url : str | None = None):
        print(f"WebScraper running on {source}")
        utils.cache_disk.enabled = False

        url = url or source.base_url
        website = newspaper.build(
            url, only_in_path=True, memoize_articles=False, disable_category_cache=True
        )
        print(f"Printing articles for {url}")
        for article in website.articles:
            print(article.url)
        print(f"Printing categories for {url}")
        for category in website.category_urls():
            print(category)

        # lto = newspaper.build("https://www.lto.de/")
        # print(f"Printing articles for LTO")
        # for article in lto.articles:
        #     print(article.url)
        # print(f"Printing categories for LTO")
        # for category in lto.category_urls():
        #     print(category)
