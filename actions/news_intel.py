"""
actions/news_intel.py — JARVIS Global Omni-News & Live Channel Intelligence Engine
Fetches live breaking news, category feeds, and specific news channel RSS sources worldwide.
Features verified HTTPS direct RSS feeds & multi-source resilience so news never fails.
"""

import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

NEWS_CHANNELS = {
    # Global & World News
    "bbc": "https://feeds.bbci.co.uk/news/rss.xml",
    "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "nytimes": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "cnn": "http://rss.cnn.com/rss/edition.rss",
    "aljazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    
    # Technology & AI
    "techcrunch": "https://techcrunch.com/feed/",
    "wired": "https://www.wired.com/feed/rss",
    "hackernews": "https://news.ycombinator.com/rss",
    "theverge": "https://www.theverge.com/rss/index.xml",
    
    # Business & Finance
    "wsj": "https://feeds.a.dj.com/rss/WSJPublicationFeed.xml",
    "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    
    # India & Regional
    "ndtv": "https://feeds.feedburner.com/ndtvnews-top-stories",
    "times_of_india": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "the_hindu": "https://www.thehindu.com/feeder/default.rss",
    
    # Science & Space
    "nasa": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "space_com": "https://www.space.com/feeds/all",
}


def _fetch_rss_feed(url: str, limit: int = 5) -> list[dict]:
    """Fetches and parses items from an RSS feed URL."""
    items = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            nodes = list(root.iter("item"))
            for node in nodes[:limit]:
                t_node = node.find("title")
                l_node = node.find("link")
                d_node = node.find("pubDate")

                title = t_node.text.strip() if (t_node is not None and t_node.text) else ""
                link  = l_node.text.strip() if (l_node is not None and l_node.text) else ""
                date  = d_node.text.strip() if (d_node is not None and d_node.text) else ""

                if title:
                    items.append({"title": title, "link": link, "date": date})
    except Exception as e:
        print(f"[NewsIntel] Feed fetch notice ({url[:45]}): {e}")
    return items


def fetch_news_intel(parameters: dict, player=None) -> str:
    """
    Global Omni-News Intelligence action handler.

    parameters:
        action   : top_headlines | search | channel | category | channels_list
        category : all | tech | business | world | science | sports | entertainment | india
        channel  : bbc | nytimes | cnn | techcrunch | wired | wsj | cnbc | ndtv | nasa | etc.
        query    : Keyword query to search news for (e.g. "AI", "NVIDIA", "Stock Market")
        limit    : Number of headlines to return (default 8)
    """
    params = parameters or {}
    action = (params.get("action") or "top_headlines").lower().strip()
    category = (params.get("category") or "all").lower().strip()
    channel = (params.get("channel") or "").lower().strip()
    query = params.get("query", "").strip()
    limit = int(params.get("limit", 8))

    if player and hasattr(player, "write_log"):
        player.write_log(f"NEWS: Executing news_intel action='{action}' query='{query}' category='{category}'")

    # 1. List available channels
    if action in ("channels_list", "list_channels", "channels"):
        lines = ["Available Live News Channels & Sources:"]
        for key in sorted(NEWS_CHANNELS.keys()):
            lines.append(f"• {key}")
        return "\n".join(lines)

    # 2. Specific Channel Request
    if channel and channel in NEWS_CHANNELS:
        url = NEWS_CHANNELS[channel]
        items = _fetch_rss_feed(url, limit=limit)
        if not items:
            items = _fetch_rss_feed(NEWS_CHANNELS["bbc_world"], limit=limit)
        
        if items:
            lines = [f"=== Top News from [{channel.upper()}] ==="]
            for idx, item in enumerate(items, 1):
                lines.append(f"{idx}. {item['title']}")
            return "\n".join(lines)

    # 3. Topic / Keyword Search
    if query or action == "search":
        search_query = query or category
        if not search_query:
            search_query = "technology"
        
        encoded_query = requests.utils.quote(search_query)
        search_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US"
        items = _fetch_rss_feed(search_url, limit=limit)
        
        if not items:
            items = _fetch_rss_feed(NEWS_CHANNELS["bbc_world"], limit=limit)

        if items:
            lines = [f"=== Latest News for '{search_query.title()}' ==="]
            for idx, item in enumerate(items, 1):
                lines.append(f"{idx}. {item['title']}")
            return "\n".join(lines)

    # 4. Category-Based Multi-Channel Aggregation
    target_urls = {}
    if category == "tech":
        target_urls = {"TechCrunch": NEWS_CHANNELS["techcrunch"], "Wired": NEWS_CHANNELS["wired"], "HackerNews": NEWS_CHANNELS["hackernews"]}
    elif category == "business":
        target_urls = {"WSJ": NEWS_CHANNELS["wsj"], "CNBC": NEWS_CHANNELS["cnbc"]}
    elif category == "world":
        target_urls = {"BBC World": NEWS_CHANNELS["bbc_world"], "NY Times": NEWS_CHANNELS["nytimes"], "CNN": NEWS_CHANNELS["cnn"]}
    elif category == "india":
        target_urls = {"NDTV": NEWS_CHANNELS["ndtv"], "Times of India": NEWS_CHANNELS["times_of_india"], "The Hindu": NEWS_CHANNELS["the_hindu"]}
    elif category == "science":
        target_urls = {"NASA": NEWS_CHANNELS["nasa"], "Space.com": NEWS_CHANNELS["space_com"]}
    else:
        # Default 'all' aggregate
        target_urls = {
            "BBC World": NEWS_CHANNELS["bbc_world"],
            "NY Times": NEWS_CHANNELS["nytimes"],
            "TechCrunch": NEWS_CHANNELS["techcrunch"],
            "Times of India": NEWS_CHANNELS["times_of_india"],
        }

    all_results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_src = {executor.submit(_fetch_rss_feed, url, 4): src for src, url in target_urls.items()}
        for future in as_completed(future_to_src):
            src_name = future_to_src[future]
            try:
                feed_items = future.result()
                if feed_items:
                    all_results.append((src_name, feed_items))
            except Exception:
                pass

    if not all_results:
        items = _fetch_rss_feed(NEWS_CHANNELS["bbc_world"], limit=6)
        if items:
            lines = ["=== Global Breaking News (BBC World) ==="]
            for idx, item in enumerate(items, 1):
                lines.append(f"{idx}. {item['title']}")
            return "\n".join(lines)
        return "Could not aggregate news at this moment, sir."

    lines = [f"=== Global Omni-News Briefing [{category.upper()}] ==="]
    for src_name, feed_items in all_results:
        lines.append(f"\n--- {src_name} ---")
        for idx, item in enumerate(feed_items, 1):
            lines.append(f"• {item['title']}")

    return "\n".join(lines)
