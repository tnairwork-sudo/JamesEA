from __future__ import annotations

from typing import Optional

import requests
from bs4 import BeautifulSoup


def _search_google_html(query: str) -> str:
    response = requests.get(
        "https://www.google.com/search",
        params={"q": query, "hl": "en"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=12,
    )
    response.raise_for_status()
    return response.text


def get_contact_info(name: str, email: Optional[str] = None) -> str:
    identity = f"{name} {email or ''}".strip()
    queries = [f'"{name}" site:linkedin.com', f'"{name}" professional profile']
    for q in queries:
        try:
            html = _search_google_html(q)
            soup = BeautifulSoup(html, "html.parser")
            first = soup.select_one("h3")
            snippet = soup.select_one("div.VwiC3b") or soup.select_one("span.aCOpRe")
            if first:
                title = first.get_text(" ", strip=True)
                desc = snippet.get_text(" ", strip=True) if snippet else "Profile details available online."
                return f"{identity}: {title}. {desc[:160]}"
        except Exception:
            continue
    return f"{identity}: No reliable public profile summary found quickly."
