import json
import multiprocessing
import logging

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def get_soup(link):
    """Returns a BeautifulSoup object of the given link"""
    try:
        response = requests.get(link)
        response.raise_for_status()  # Raises stored HTTPError, if one occurred.
    except requests.HTTPError as http_err:
        logging.error(f"HTTP error occurred: %s", http_err)
        return None
    except Exception as err:
        logging.error(f"Other error occurred: %s", err)
        return None
    else:
        return BeautifulSoup(response.text, "html.parser")


def scrape_speech(item_html):
    """Returns a dictionary of speech data from the media post item"""
    item_soup = BeautifulSoup(item_html, "html.parser")
    date = item_soup.find("p", class_="media-post-date").text.strip()
    title_tag = item_soup.find("a", class_="media-post-title")
    title = title_tag.text.strip()
    link = title_tag["href"]

    logging.info(f"Scraping speech '%s'...", title)
    soup = get_soup(link)

    if not soup:
        logging.error(f"Error scraping speech '%s'. Skipping...", title)
        return None

    content = soup.find("div", class_="media-post-page-content").text.strip()

    return {
        "title": title,
        "link": link,
        "date": date,
        "content": content,
    }


if __name__ == "__main__":
    page_link = "https://www.ovp.gov.ph/category/1/vp-sara-speeches"
    speeches = []
    page_count = 1

    while page_link:
        logging.info(f"Scraping page %s...", page_count)
        page_soup = get_soup(page_link)

        if not page_soup:
            logging.error(f"Error scraping page %s. Skipping...", page_count)
            continue  # Skip this page if there's an error.

        items = [str(item) for item in page_soup.find_all("div", class_="media-post-item")]

        with multiprocessing.Pool() as pool:
            results = pool.map(scrape_speech, items)

        speeches.extend(result for result in results if result is not None)

        pagination = page_soup.find_all("a", class_="page-link")
        next_links = [link for link in pagination if link.text == "Next →"]
        page_link = next_links[0]["href"] if next_links else None

        page_count += 1

    with open("speeches.json", "w") as f:
        logging.info(f"Saving speeches to speeches.json...")
        json.dump(speeches, f, indent=4)
