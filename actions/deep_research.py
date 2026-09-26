"""
actions/deep_research.py — Deep Academic & Technical Research Engine for JARVIS Mark 58
Expands JARVIS's research capabilities beyond surface-level snippets:
- Multi-source academic query: ArXiv preprint papers, Wikipedia, DuckDuckGo & Web scraping.
- Full web page scraping and content distillation using BeautifulSoup.
- Synthesizes comprehensive research briefs with citations, theoretical frameworks, and trade-off analysis.
- Instant export to Word (.docx) or PDF on Desktop.
"""

import os
import re
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
from google import genai
from core.ai_client import generate_text_with_retry, get_api_key as _get_api_key

BASE_DIR = Path(__file__).resolve().parent.parent


def search_arxiv(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Fetches academic research papers and preprints from ArXiv API."""
    try:
        clean_q = urllib.parse.quote(query.strip())
        url = f"https://export.arxiv.org/api/query?search_query=all:{clean_q}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/atom+xml,application/xml"
        }
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return []

        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []

        for entry in root.findall("atom:entry", ns):
            title = (entry.find("atom:title", ns).text or "").strip().replace("\n", " ")
            summary = (entry.find("atom:summary", ns).text or "").strip().replace("\n", " ")
            link = entry.find("atom:id", ns).text or ""
            published = (entry.find("atom:published", ns).text or "")[:10]
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None]

            papers.append({
                "title": title,
                "summary": summary[:400],
                "url": link,
                "date": published,
                "authors": ", ".join(authors[:3])
            })

        return papers
    except Exception as e:
        print(f"[DeepResearch] ArXiv query notice: {e}")
        return []


def search_web_ddg(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Performs web search via DuckDuckGo."""
    results = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
    except Exception:
        # Fallback to direct HTTP search
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select(".result__body")[:max_results]:
                t = a.select_one(".result__title")
                s = a.select_one(".result__snippet")
                if t and s:
                    results.append({
                        "title": t.get_text(strip=True),
                        "snippet": s.get_text(strip=True),
                        "url": ""
                    })
        except Exception:
            pass
    return results


def scrape_page_content(url: str, max_chars: int = 2500) -> str:
    """Scrapes and distills the core body text of an informative web page."""
    if not url or not url.startswith("http"):
        return ""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove scripts, styles, headers, footers
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
                tag.decompose()
            text = " ".join(soup.get_text().split())
            return text[:max_chars]
    except Exception:
        pass
    return ""


def deep_research(parameters: dict, player=None) -> str:
    """
    Main tool handler for deep multi-source academic and technical research.
    parameters:
      query: Research topic or academic inquiry
      focus: 'academic' | 'technical' | 'market' | 'general'
      export_to: 'none' | 'docx' | 'pdf'
    """
    params = parameters or {}
    query = (params.get("query") or "").strip()
    focus = (params.get("focus") or "academic").lower().strip()
    export_to = (params.get("export_to") or "none").lower().strip()

    if not query:
        return "Please specify a research question or topic, sir."

    if player and hasattr(player, "write_log"):
        player.write_log(f"DEEP RESEARCH: Investigating '{query[:45]}' across academic & web indices...")

    api_key = _get_api_key()
    if not api_key:
        return "Sir, Gemini API Key is required for deep research synthesis."

    # 1. Gather ArXiv academic literature
    arxiv_papers = search_arxiv(query, max_results=3)

    # 2. Gather Web Intelligence
    web_results = search_web_ddg(query, max_results=4)

    # 3. Deep scrape top 2 relevant pages
    scraped_data = []
    for item in web_results[:2]:
        url = item.get("url")
        if url:
            body = scrape_page_content(url, max_chars=1800)
            if body:
                scraped_data.append(f"Source [{item.get('title')}]:\n{body}\n")

    # 4. Assemble synthesis prompt for Gemini
    arxiv_block = ""
    if arxiv_papers:
        arxiv_block = "ACADEMIC PAPERS (ArXiv):\n"
        for p in arxiv_papers:
            arxiv_block += f"• Title: {p['title']} ({p['date']}) by {p['authors']}\n  Abstract: {p['summary']}\n  Link: {p['url']}\n\n"

    web_block = ""
    if web_results:
        web_block = "WEB INTELLIGENCE:\n"
        for w in web_results:
            web_block += f"• {w['title']}: {w['snippet']} ({w['url']})\n"

    deep_block = "\n".join(scraped_data)

    client = genai.Client(api_key=api_key)
    prompt = (
        f"You are J.A.R.V.I.S., Tony Stark's advanced research intelligence.\n"
        f"Conduct a thorough, high-level research briefing on: '{query}'\n"
        f"Focus Area: {focus.upper()}\n\n"
        f"{arxiv_block}\n"
        f"{web_block}\n"
        f"DEEP SOURCE SCRAPES:\n{deep_block}\n\n"
        "Generate a structured, authoritative report:\n"
        "1. Executive Summary & Core Thesis\n"
        "2. Technical / Theoretical Architecture (Mechanisms, formulas, principles)\n"
        "3. Critical Comparison & State of the Art (Trade-offs, strengths, limits)\n"
        "4. Practical Implementation Takeaways\n"
        "5. Key References & Academic Bibliography\n\n"
        "Keep the tone sophisticated, razor-sharp, and highly informative."
    )

    output = generate_text_with_retry(prompt, client=client)

    # 5. Handle optional export to Word / PDF
    if export_to in ("docx", "pdf"):
        from actions.file_generator import universal_file_creator
        clean_q = re.sub(r'[^a-zA-Z0-9_-]', '_', query)[:25]
        f_res = universal_file_creator({
            "file_type": export_to,
            "filename": f"Research_Brief_{clean_q}",
            "title": f"Deep Research: {query.title()}",
            "content": output,
            "open_after": True
        }, player=player)
        output += f"\n\n📁 **Research Brief Exported**: {f_res}"

    return output
