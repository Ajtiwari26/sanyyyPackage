#!/usr/bin/env python3
"""
Sanyyy Real-Time Web Search Engine
====================================
Provides ultra-fast (~150ms) live web search capabilities for Gemini Live.
Uses DuckDuckGo Lite API + Instant Answer API for real-time web results.
"""

import json
import urllib.request
import urllib.parse
import re
from html import unescape


def search_web_live(query: str, max_results: int = 5) -> str:
    """
    Perform real-time web search for any query and return clean summary text for LLM consumption.
    Fast ~150-300ms execution.
    """
    query = query.strip()
    if not query:
        return "Empty search query."

    # 1. Try DDG Lite (150ms, super reliable)
    try:
        url = "https://lite.duckduckgo.com/lite/"
        post_data = urllib.parse.urlencode({"q": query}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=post_data,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            snippets = re.findall(
                r'<td class=[\'\"]result-snippet[\'\"][^>]*>(.*?)</td>',
                body,
                re.DOTALL,
            )
            clean_snippets = []
            for s in snippets[:max_results]:
                clean = re.sub(r"<[^>]+>", "", s).strip()
                clean = unescape(clean)
                if clean:
                    clean_snippets.append(f"• {clean}")

            if clean_snippets:
                return (
                    f"🌐 Real-Time Web Search Results for '{query}':\n"
                    + "\n".join(clean_snippets)
                )
    except Exception as err:
        print(f"⚠️ DDG Lite search error: {err}")

    # 2. Fallback to DDG Instant Answer API
    try:
        url = (
            "https://api.duckduckgo.com/?q="
            + urllib.parse.quote(query)
            + "&format=json&no_html=1"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            abstract = data.get("AbstractText", "")
            heading = data.get("Heading", "")
            related = data.get("RelatedTopics", [])

            results = []
            if abstract:
                results.append(f"📌 {heading}: {abstract}")

            for topic in related[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(f"• {topic['Text']}")

            if results:
                return (
                    f"🌐 Real-Time Web Search Results for '{query}':\n"
                    + "\n".join(results)
                )
    except Exception as err:
        print(f"⚠️ DDG Instant Answer error: {err}")

    return f"⚠️ Web search for '{query}' could not fetch results. Please check your internet connection."


if __name__ == "__main__":
    print("🧪 Testing Sanyyy Real-Time Web Search...")
    print(search_web_live("macOS Sequoia release date"))
