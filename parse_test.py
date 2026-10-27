from bs4 import BeautifulSoup
import pandas as pd

def parse_view(html, category):
    soup = BeautifulSoup(html, "lxml")
    root = soup.select_one("section.small-screen div.another-categories")
    if root is None:
        raise ValueError("results container not found; page may not have rendered")
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
                pct = None
            rows.append({"category": category, "group": group,
                         "answer": answer, "pct": pct, "raw_pct": num})
    return rows

html = open("race_snippet.html", encoding="utf-8").read()
df = pd.DataFrame(parse_view(html, "Race"))
print(df)