lto = "https://www.lto.de/recht/presseschau"
    bgh = "https://www.bundesgerichtshof.de/DE/Presse/Pressemitteilungen/pressemitteilungen_node.html"
    einspruch = "https://www.faz.net/einspruch/"
    welt = "https://www.welt.de/politik/deutschland/"
    urls = [lto, bgh, einspruch, welt]

    print("\n\n### Testing readability")
    for url in urls:
        print(f"Testing {url}")
        try:
            response = requests.get(url)
            doc = Document(response.text)
            print(doc.summary())
        except Exception as e:
            print(f"Error downloading or parsing article {url}: {e}")
    print("\n\n### Testing trafilatura")

    for url in urls:
        print(f"Testing {url}")
        try:
            downloaded = trafilatura.fetch_url(url)
            main_content_html = trafilatura.extract(downloaded, output_format="html", include_links=True)
            soup = BeautifulSoup(main_content_html, "html.parser")
            links = [link.get("href") for link in soup.find_all("a", href=True)]
            print(links)
        except Exception as e:
            print(f"Error downloading or parsing article {url}: {e}")

    print("\n\n### Testing custom_extract_one")
    for url in urls:
        print(f"Testing {url}")
        try:
            links = await custom_extract_one(url)
            print(links)
        except Exception as e:
            print(f"Error downloading or parsing article {url}: {e}")

    print("\n\n### Testing custom_extract_two")
    for url in urls:
        print(f"Testing {url}")
        try:
            links = await custom_extract_two(url)
            print(links)
        except Exception as e:
            print(f"Error downloading or parsing article {url}: {e}")
    
    print("\n\n### Testing Firecrawl")
    app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY.get_secret_value())
    for url in urls:
        print(f"Testing {url}")
        try:
            response = app.scrape_url(url, formats=["links"], only_main_content=True)
            print(response)
        except Exception as e:
            print(f"Error downloading or parsing article {url}: {e}")