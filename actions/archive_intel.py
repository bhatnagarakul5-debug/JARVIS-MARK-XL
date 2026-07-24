"""
actions/archive_intel.py — The Internet Archive & Wayback Machine Intelligence Engine for JARVIS Mark XL
Allows searching Wayback Machine snapshots of any website and searching Archive.org's library of books, docs & media.
"""

import requests
import json
from pathlib import Path

WAYBACK_AVAILABILITY_API = "http://archive.org/wayback/available"
ARCHIVE_SEARCH_API = "https://archive.org/advancedsearch.php"


def archive_intel(parameters: dict, player=None) -> str:
    """
    Action handler for The Internet Archive and Wayback Machine.

    parameters:
        action     : wayback | search_archive | fetch_page
        url        : Website URL for wayback snapshot search (e.g. "google.com", "openai.com")
        timestamp  : Optional target year/date for Wayback Machine (e.g. "2015", "20100101")
        query      : Search query for Internet Archive library (e.g. "quantum physics", "iron man", "cybernetics")
        media_type : Optional filter for library search: texts | movies | audio | software
        limit      : Number of results (default 5)
    """
    params = parameters or {}
    action = (params.get("action") or "wayback").lower().strip()
    url_target = params.get("url", "").strip()
    timestamp = params.get("timestamp", "").strip()
    query = params.get("query", "").strip()
    media_type = params.get("media_type", "").strip()
    limit = int(params.get("limit", 5))

    if player and hasattr(player, "write_log"):
        player.write_log(f"ARCHIVE: Executing archive_intel action='{action}' url='{url_target}' query='{query}'")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 1. Wayback Machine Snapshot Search
    if action in ("wayback", "snapshot", "historical"):
        if not url_target:
            if query:
                url_target = query
            else:
                return "Please provide a website URL to search on the Wayback Machine, sir."

        # Clean URL
        if not url_target.startswith("http"):
            url_target = "http://" + url_target

        req_params = {"url": url_target}
        if timestamp:
            req_params["timestamp"] = timestamp

        try:
            resp = requests.get(WAYBACK_AVAILABILITY_API, params=req_params, headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                snapshots = data.get("archived_snapshots", {})
                closest = snapshots.get("closest", {})
                if closest and closest.get("available"):
                    snap_url = closest.get("url")
                    snap_time = closest.get("timestamp")
                    formatted_time = f"{snap_time[:4]}-{snap_time[4:6]}-{snap_time[6:8]}" if len(snap_time) >= 8 else snap_time
                    return (
                        f"Wayback Machine Snapshot Found!\n"
                        f"• Target URL: {url_target}\n"
                        f"• Snapshot Date: {formatted_time}\n"
                        f"• Archived Link: {snap_url}"
                    )
                else:
                    return f"No archived snapshot found on Wayback Machine for '{url_target}'."
            return "Could not reach Wayback Machine API at this moment."
        except Exception as e:
            return f"Wayback Machine search error: {e}"

    # 2. Internet Archive Library Search (Books, Docs, Media)
    if action in ("search_archive", "library", "books", "docs"):
        search_query = query or url_target
        if not search_query:
            return "Please provide a search term for the Internet Archive library, sir."

        q_str = f"title:({search_query}) OR description:({search_query})"
        if media_type:
            q_str += f" AND mediatype:({media_type})"

        search_params = {
            "q": q_str,
            "fl[]": "identifier,title,mediatype,year,publicdate",
            "rows": limit,
            "page": 1,
            "output": "json"
        }

        try:
            resp = requests.get(ARCHIVE_SEARCH_API, params=search_params, headers=headers, timeout=7)
            if resp.status_code == 200:
                data = resp.json()
                docs = data.get("response", {}).get("docs", [])
                if not docs:
                    return f"No Internet Archive documents or media found for '{search_query}'."

                lines = [f"=== Internet Archive Library Results for '{search_query}' ==="]
                for idx, doc in enumerate(docs, 1):
                    item_id = doc.get("identifier", "")
                    title = doc.get("title", "Untitled")
                    m_type = doc.get("mediatype", "unknown")
                    year = doc.get("year", doc.get("publicdate", "")[:4])
                    item_link = f"https://archive.org/details/{item_id}"
                    lines.append(f"{idx}. [{m_type.upper()}] {title} ({year})\n   Link: {item_link}")

                return "\n".join(lines)
            return "Could not fetch Internet Archive search results."
        except Exception as e:
            return f"Internet Archive search error: {e}"

    # Fallback to Wayback Machine
    return archive_intel({"action": "wayback", "url": url_target or query}, player=player)
