# locator_extractor.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def get_rendered_html(url):
    """Loads a URL headlessly and returns fully rendered HTML."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)  # allow JS to render
    html = driver.page_source
    driver.quit()
    return html


def extract_dom_metadata(html):
    """Extracts relevant field/button info for AI context."""
    soup = BeautifulSoup(html, "html.parser")
    inputs, buttons, links = [], [], []

    for tag in soup.find_all("input"):
        inputs.append({
            "id": tag.get("id"),
            "name": tag.get("name"),
            "placeholder": tag.get("placeholder"),
            "type": tag.get("type")
        })

    for tag in soup.find_all("button"):
        buttons.append({
            "id": tag.get("id"),
            "name": tag.get("name"),
            "text": tag.text.strip(),
            "type": tag.get("type")
        })

    for tag in soup.find_all("a"):
        links.append({
            "href": tag.get("href"),
            "text": tag.text.strip()
        })

    return {
        "inputs": inputs,
        "buttons": buttons,
        "links": links
    }


def extract_locators_for_url(url):
    """Convenience function: directly get DOM metadata from URL."""
    html = get_rendered_html(url)
    return extract_dom_metadata(html)
