import sys
import os
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime

HTML_FILE = "opinion.html"
XML_FILE = "articles.xml"
MAX_ITEMS = 500

# Load HTML
if not os.path.exists(HTML_FILE):
    print("HTML not found")
    sys.exit(1)

with open(HTML_FILE, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

articles = []

# =========================================================
# FETCH ALL EDITORIAL ARTICLES FROM categoryArea STRUCTURE
# =========================================================
# Definition:
# editorial article = any <a> tag whose href contains "/editorial/"
# Data sources:
# - main card (h1, p, img)
# - secondary cards (h5, img)
# =========================================================

for a in soup.select("a.stretched-link[href*='/editorial/']"):
    url = a.get("href", "").strip()
    if not url:
        continue

    container = a.find_parent("div", class_="position-relative")
    if not container:
        continue

    # Title extraction
    title = None
    h1 = container.select_one("h1")
    if h1:
        title = h1.get_text(strip=True)
    else:
        h5 = container.select_one("h5")
        if h5:
            title = h5.get_text(strip=True)

    if not title:
        continue

    # Description (only main card has it)
    desc_tag = container.select_one("p")
    desc = desc_tag.get_text(strip=True) if desc_tag else ""

    # Image
    img_tag = container.select_one("img")
    img = img_tag.get("src", "") if img_tag else ""

    articles.append({
        "url": url,
        "title": title,
        "desc": desc,
        "pub": "",
        "img": img
    })

# ======================
# LOAD OR CREATE XML
# ======================
if os.path.exists(XML_FILE):
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    except ET.ParseError:
        root = ET.Element("rss", version="2.0")
else:
    root = ET.Element("rss", version="2.0")

channel = root.find("channel")
if channel is None:
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Editorial"
    ET.SubElement(channel, "link").text = "https://www.bd-pratidin.com/editorial"
    ET.SubElement(channel, "description").text = "Latest editorial articles"

# ======================
# DEDUPLICATION
# ======================
existing = set()
for item in channel.findall("item"):
    link = item.find("link")
    if link is not None and link.text:
        existing.add(link.text.strip())

# ======================
# APPEND NEW ITEMS
# ======================
for art in articles:
    if art["url"] in existing:
        continue

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = art["title"]
    ET.SubElement(item, "link").text = art["url"]
    ET.SubElement(item, "description").text = art["desc"]
    ET.SubElement(item, "pubDate").text = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    if art["img"]:
        ET.SubElement(
            item,
            "enclosure",
            url=art["img"],
            type="image/jpeg"
        )

# ======================
# TRIM TO MAX_ITEMS
# ======================
items = channel.findall("item")
if len(items) > MAX_ITEMS:
    for old in items[:-MAX_ITEMS]:
        channel.remove(old)

# ======================
# SAVE XML
# ======================
tree = ET.ElementTree(root)
tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
