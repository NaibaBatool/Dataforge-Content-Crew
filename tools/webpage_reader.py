"""DataForge Content Crew - Webpage Reader Tool
Phase 3: Research Tools
"""

import re
import requests
from typing import Any, Dict


def read_webpage(url: str, max_chars: int = 2500) -> Dict[str, Any]:
    """Retrieves public web page text safely and treats retrieved content as untrusted evidence."""
    if not url or not url.startswith(("http://", "https://")):
        return {
            "success": False,
            "url": url,
            "error": "Invalid URL scheme. Only http/https URLs are permitted.",
            "text": ""
        }

    headers = {
        "User-Agent": "DataForgeContentCrew/1.0 (+https://dataforge.local)",
        "Accept": "text/html,application/xhtml+xml"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        if not response.ok:
            return {
                "success": False,
                "url": url,
                "status_code": response.status_code,
                "error": f"Failed to retrieve page: HTTP {response.status_code}",
                "text": ""
            }

        html = response.text

        # Strip scripts, styles, comments
        clean_html = re.sub(r"<(script|style|noscript|header|footer|nav)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        clean_html = re.sub(r"<!--.*?-->", " ", clean_html, flags=re.DOTALL)
        # Strip remaining tags
        raw_text = re.sub(r"<[^>]+>", " ", clean_html)
        # Normalize whitespace
        clean_text = " ".join(raw_text.split())

        # Guard against prompt injection instructions in external page
        untrusted_text = clean_text[:max_chars]

        return {
            "success": True,
            "url": url,
            "char_count": len(untrusted_text),
            "text": untrusted_text,
            "is_untrusted_evidence": True
        }

    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": f"Connection error: {str(e)}",
            "text": ""
        }
