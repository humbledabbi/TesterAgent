# locator_extractor.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import time
from lxml import etree


def get_rendered_html(url):
    """Loads a URL headlessly and returns fully rendered HTML."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(2)

    # Scroll to force full DOM render
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

    html = driver.page_source
    driver.quit()
    return html


# ---------------------------------------------------------
# BETTER XPATH GENERATOR
# ---------------------------------------------------------

def generate_xpath_safely(tag):
    try:
        soup_str = str(tag)
        parser = etree.HTMLParser()
        full_dom = etree.HTML(str(tag.parent))
        element = etree.HTML(soup_str)
        return element.getroottree().getpath(element)
    except Exception:
        return None


# ---------------------------------------------------------
# BETTER CSS SELECTOR BUILDER
# ---------------------------------------------------------

def build_css_selector(tag):
    """Generate a reliable CSS selector for any tag."""
    if tag.get("id"):
        return f'#{tag.get("id")}'

    if tag.get("class"):
        classes = ".".join(tag.get("class"))
        return f"{tag.name}.{classes}"

    return tag.name


# ---------------------------------------------------------
# FULL ATTRIBUTE EXTRACTION
# ---------------------------------------------------------

def extract_common_attrs(tag):
    """Extract all meaningful attributes."""
    attributes = dict(tag.attrs)

    return {
        "tag": tag.name,
        "attributes": attributes,
        "text": tag.get_text(strip=True),

        # key attributes
        "id": attributes.get("id"),
        "class": attributes.get("class"),
        "name": attributes.get("name"),
        "placeholder": attributes.get("placeholder"),
        "value": attributes.get("value"),
        "type": attributes.get("type"),
        "role": attributes.get("role"),
        "href": attributes.get("href"),
        "src": attributes.get("src"),
        "title": attributes.get("title"),
        "alt": attributes.get("alt"),
        "aria_label": attributes.get("aria-label"),
        "aria_labelledby": attributes.get("aria-labelledby"),
        "data_test": (
            attributes.get("data-test")
            or attributes.get("data-testid")
            or attributes.get("data-qa")
        ),

        # selectors
        "css_selector": build_css_selector(tag),
        "xpath": None,  # filled later
    }


# ---------------------------------------------------------
# MAIN DOM SCANNER
# ---------------------------------------------------------

def extract_dom_metadata(html):
    """Extracts full DOM metadata including inputs, buttons, images, clickables, etc."""
    soup = BeautifulSoup(html, "html.parser")

    inputs, buttons, links, images, labels, selects, products = [], [], [], [], [], [], []
    clickables = []

    all_tags = soup.find_all(True)

    for tag in all_tags:
        info = extract_common_attrs(tag)

        # accurate xpath
        info["xpath"] = generate_xpath_safely(tag)

        # basic categorization
        if tag.name == "input":
            inputs.append(info)

        elif tag.name == "button":
            buttons.append(info)

        elif tag.name == "a":
            links.append(info)

        elif tag.name == "img":
            images.append(info)

        elif tag.name in ("label", "span"):
            labels.append(info)

        elif tag.name == "select":
            info["options"] = [opt.get_text(strip=True) for opt in tag.find_all("option")]
            selects.append(info)

        # unified CLICKABLE detection
        is_clickable = (
            tag.name in ("button", "a") or
            tag.get("onclick") or
            tag.get("role") == "button" or
            tag.get("tabindex") == "0" or
            "click" in str(tag.get("class", "")).lower() or
            tag.get("data-test") or
            tag.get("data-testid")
        )

        if is_clickable:
            clickables.append(info)

    # -----------------------------------------------------
    # Product-like card grouping
    # -----------------------------------------------------
    card_selectors = [
        "[class*=product]",
        "[class*=inventory]",
        ".card",
        ".item",
        "[data-test*=item]"
    ]

    for sel in card_selectors:
        for item in soup.select(sel):
            title = item.find(["h1", "h2", "h3", "span", "div"], string=True)
            price = item.find(["span", "div"], string=lambda t: t and "$" in t)
            btn = item.find("button")

            products.append({
                "title": title.get_text(strip=True) if title else None,
                "price": price.get_text(strip=True) if price else None,
                "button": extract_common_attrs(btn) if btn else None
            })

    # final data payload
    return {
        "inputs": inputs,
        "buttons": buttons,
        "links": links,
        "images": images,
        "labels": labels,
        "selects": selects,
        "products": products,
        "clickables": clickables
    }


# ---------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------

def extract_locators_for_url(url):
    html = get_rendered_html(url)
    return extract_dom_metadata(html)
