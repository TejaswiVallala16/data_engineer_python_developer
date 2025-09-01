import requests
from lxml import html
from urllib.parse import urljoin
import logging
import coloredlogs
import json
from datetime import datetime

BASE_URL = "https://books.toscrape.com/"
BOOK_LIST = []
# Create logger
logger = logging.getLogger("book_scraper")

# Install colored logs (level, format)
coloredlogs.install(
    level="DEBUG",
    logger=logger,
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def get_category_list():
    logger.info("Retriving Categories")
    try:
        r = requests.get(BASE_URL)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return
    tree = html.fromstring(r.content)
    categories = tree.xpath("//div[@class='side_categories']//ul//li/a[contains(@href, 'books/')]/@href")
    logger.info(f"Got {len(categories)} categories")
    for cat in categories:
        get_books(urljoin(BASE_URL,cat))

def get_books(category_url):
    try:
        cat_res = requests.get(category_url)
        cat_res.raise_for_status()
    except Exception as e:
        logger.error(f"Request Failed: {e}")
        return
    cat_tree = html.fromstring(cat_res.content)
    books = cat_tree.xpath("//section//li//article[@class='product_pod']")
    category = "".join(cat_tree.xpath("//li[@class='active']/text()"))
    logger.info(f"Retriving books from {category}")
    rating_map = {"One":1,"Two":2,"Three":3,"Four":4,"Five":5}
    for book in books:
        rating_str = "".join(book.xpath("./p/@class")).replace("star-rating","").strip()
        rating = rating_map.get(rating_str, None)
        BOOK_LIST.append(
                {
                    "title": "".join(book.xpath("./h3//text()")),
                    "image_url": urljoin(BASE_URL, "".join(book.xpath(".//img/@src"))),
                    "rating": rating,
                    "price": "".join(book.xpath("./div/p[@class='price_color']/text()")),
                    "availability": "".join(book.xpath("./div/p[contains(@class, 'availability')]/text()")).replace("\n","").strip(),
                    "book_url": urljoin(BASE_URL, "".join(book.xpath("./h3/a/@href"))),
                    "category": category,
                    "scrape_date": datetime.now().isoformat()
                }
        )
    next_page = cat_tree.xpath("//li[@class='next']/a/@href")
    if next_page != []:
        get_books(urljoin(category_url,"".join(next_page)))
    

if __name__ == "__main__":
    get_category_list()
    with open("books_scrapper/books.json", "w", encoding="utf-8") as f:
        json.dump(BOOK_LIST, f, ensure_ascii=False, indent=4)
    logger.info("Saved books into json file...")