"""
Scrape a YouGov "Daily Question" poll across all six breakdown tabs
(All adults, Region, Gender, Politics, Age, Race) into one long-format CSV.

Setup (once):
    pip install beautifulsoup4 lxml pandas playwright
    playwright install chromium

Run:
    python scrape_yougov_poll.py
    python scrape_yougov_poll.py https://yougov.com/en-us/daily-results/XXXX  (any other poll URL)

Output columns:
    poll_url, question, published, conducted, n_adults,
    category, group, answer, pct, raw_pct

NOTE: the page is an Angular app. The results are only in the HTML after
JavaScript runs, so Playwright loads the page and Beautiful Soup parses it.
Please check YouGov's Public data licence and robots.txt before scraping
many polls, and keep the delay between page loads.
"""

import re
import sys
import time

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

DEFAULT_URL = "https://yougov.com/en-us/daily-results/20221018-4280f-3"

# <option value=...> in the site's <select>, in the site's own order
TABS = {0: "All adults", 1: "Region", 2: "Gender", 3: "Politics", 4: "Age", 5: "Race"}

CONTAINER = "section.small-screen div.another-categories"       # Region/Gender/Politics/Age/Race
FLAT = "section.small-screen div.small-screens-results div.daily-section"  # All adults (flat layout)
LABELS = "section.small-screen div.small-screens-results label.bar-label"  # works for every tab
SELECT = "section.small-screen select"


# ---------------------------------------------------------------- parsing
def parse_view(html, category):
    """Parse one rendered tab into a list of row dicts."""
    soup = BeautifulSoup(html, "lxml")
    root = soup.select_one(CONTAINER)
    if root is None:
        raise ValueError("results container not found")

    rows = []
    for block in root.find_all("div", recursive=False):
        label_el = block.select_one("p.category-label")
        if label_el is None:
            continue
        answer = label_el.get_text(strip=True)
        for sec in block.select("div.daily-section"):
            group = sec.select_one("label.bar-label").get_text(strip=True)
            num = sec.select_one("span.number").get_text(strip=True)
            try:
                pct = int(num)
            except ValueError:
                pct = None  # e.g. "<1"; raw_pct keeps the original text
            rows.append(
                {"category": category, "group": group, "answer": answer,
                 "pct": pct, "raw_pct": num}
            )
    return rows


def parse_flat(html, category):
    """
    Parse the 'All adults' tab. Its layout is flatter than the other tabs:
    there is no per-answer wrapper and no group level. Each div.daily-section
    holds one answer (label.bar-label) and its percentage (span.number).
    """
    soup = BeautifulSoup(html, "lxml")
    secs = soup.select(FLAT)
    if not secs:
        raise ValueError("flat results not found")

    rows = []
    for sec in secs:
        label_el = sec.select_one("label.bar-label")
        num_el = sec.select_one("span.number")
        if label_el is None or num_el is None:
            continue
        num = num_el.get_text(strip=True)
        try:
            pct = int(num)
        except ValueError:
            pct = None
        rows.append(
            {"category": category, "group": "All",
             "answer": label_el.get_text(strip=True),
             "pct": pct, "raw_pct": num}
        )
    return rows


def parse_any(html, category):
    """Use the grouped parser if that layout is present, otherwise the flat one."""
    soup = BeautifulSoup(html, "lxml")
    if soup.select_one(CONTAINER) is not None:
        return parse_view(html, category)
    return parse_flat(html, category)


def signature(html):
    """Fingerprint of the labels currently shown, used to detect a re-render."""
    soup = BeautifulSoup(html, "lxml")
    return tuple(l.get_text(strip=True) for l in soup.select(LABELS))


def get_meta(page):
    """Question text, publish date, survey date, and sample size from the page text."""
    text = page.inner_text("body")
    m = re.search(
        r"(.+?)\s*Published on (.+?)\s*→\s*Survey conducted on (.+?) on ([\d,]+) U\.S\. adults",
        text, re.S,
    )
    question = page.title().split("|")[0].strip()
    if m:
        return question, m.group(2).strip(), m.group(3).strip(), m.group(4).replace(",", "")
    return question, None, None, None


# ---------------------------------------------------------------- scraping
def scrape_poll(page, url):
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector(SELECT, state="attached", timeout=15000)
    question, published, conducted, n_adults = get_meta(page)

    all_rows = []
    prev_sig = None

    for idx, name in TABS.items():
        page.select_option(SELECT, index=idx)

        # wait until the group labels change (i.e. the tab actually re-rendered)
        if prev_sig is not None:
            try:
                page.wait_for_function(
                    """([sel, prev]) => {
                        const cur = [...document.querySelectorAll(sel)].map(e => e.textContent.trim());
                        return JSON.stringify(cur) !== JSON.stringify(prev);
                    }""",
                    arg=[LABELS, list(prev_sig)],
                    timeout=5000,
                )
            except Exception:
                print(f"  [warn] '{name}' labels did not change after selecting; "
                      f"data may be stale")
        page.wait_for_timeout(500)

        html = page.content()
        try:
            rows = parse_any(html, name)
        except ValueError:
            print(f"  [warn] could not parse '{name}'")
            rows = []
        prev_sig = signature(html)

        groups = list(dict.fromkeys(r["group"] for r in rows))
        print(f"  {name:<10} {len(rows):>3} rows | groups: {groups}")
        all_rows += rows

    df = pd.DataFrame(all_rows)

    # If the "All adults" tab uses a layout the parser could not read,
    # rebuild it from the "All" rows that every other tab contains.
    if df.empty or "All adults" not in set(df["category"]):
        fallback = df[df["group"] == "All"].drop_duplicates(["answer"]).copy()
        if not fallback.empty:
            fallback["category"] = "All adults"
            df = pd.concat([fallback, df], ignore_index=True)
            print("  [info] 'All adults' tab rebuilt from the 'All' rows of other tabs")

    df.insert(0, "poll_url", url)
    df.insert(1, "question", question)
    df.insert(2, "published", published)
    df.insert(3, "conducted", conducted)
    df.insert(4, "n_adults", n_adults)
    return df


# ---------------------------------------------------------------- checks
def validate(df):
    print("\nValidation")
    ok = True

    # 1. every tab should be present
    missing = set(TABS.values()) - set(df["category"])
    if missing:
        ok = False
        print(f"  [FAIL] missing tabs: {sorted(missing)}")

    # 2. the 'All' row must be identical in every tab
    all_rows = df[df["group"] == "All"]
    if not all_rows.empty:
        spread = all_rows.groupby("answer")["pct"].nunique()
        bad = spread[spread > 1]
        if len(bad):
            ok = False
            print(f"  [FAIL] 'All' values differ across tabs for: {list(bad.index)}")

    # 3. answer percentages within a group should sum to roughly 100
    sums = df.groupby(["category", "group"])["pct"].sum()
    off = sums[(sums < 97) | (sums > 103)]
    if len(off):
        ok = False
        print("  [WARN] group totals far from 100 (rounding is normally within +/-2):")
        print(off.to_string())

    # 4. non-numeric percentages
    odd = df[df["pct"].isna()]
    if len(odd):
        print(f"  [WARN] {len(odd)} non-numeric values, see raw_pct column")

    if ok:
        print("  All checks passed.")


# ---------------------------------------------------------------- main
def main():
    urls = sys.argv[1:] or [DEFAULT_URL]
    frames = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # phone-width viewport -> the site shows the <select> layout our parser expects
        page = browser.new_page(viewport={"width": 390, "height": 900})
        for i, url in enumerate(urls):
            print(f"\n[{i + 1}/{len(urls)}] {url}")
            frames.append(scrape_poll(page, url))
            time.sleep(3)  # be polite between polls
        browser.close()

    df = pd.concat(frames, ignore_index=True)
    validate(df)

    out = "yougov_poll_data.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved {len(df)} rows to {out}")
    print(df[["category", "group", "answer", "pct"]].head(12).to_string(index=False))


if __name__ == "__main__":
    main()