import base64
import re
from typing import Tuple, Dict, Any
from starlette.requests import Request

# 43-byte 1x1 transparent GIF
TRANSPARENT_GIF_BYTES = base64.b64decode(
    b"R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)

CACHE_CONTROL_HEADERS = {
    "Content-Type": "image/gif",
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "Access-Control-Allow-Origin": "*",
}

def extract_client_ip(request: Request) -> str:
    """
    Extract the real client IP address, handling reverse proxies (Render, Cloudflare, Nginx, AWS, etc.).
    """
    # 1. Cloudflare header
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip and cf_ip.strip():
        return cf_ip.strip()

    # 2. X-Forwarded-For header (comma-separated list, first is original client)
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        ips = [ip.strip() for ip in xff.split(",") if ip.strip()]
        if ips:
            return ips[0]

    # 3. X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and real_ip.strip():
        return real_ip.strip()

    # 4. Fallback to direct client host
    if request.client and request.client.host:
        return request.client.host

    return "Unknown"


def parse_user_agent(ua_string: str) -> Dict[str, str]:
    """
    Lightweight, dependency-free User-Agent parser that identifies OS, browser/client,
    device category, and specifically flags email proxies (GoogleImageProxy, Apple Mail Privacy).
    """
    if not ua_string or not ua_string.strip():
        return {
            "device_type": "Unknown",
            "os_name": "Unknown",
            "browser_name": "Unknown",
            "client_type": "Unknown",
        }

    ua = ua_string
    device_type = "Desktop"
    os_name = "Unknown"
    browser_name = "Other"
    client_type = "Standard Browser / Webmail"

    # Detect specialized Email Proxies and Clients
    if "GoogleImageProxy" in ua:
        client_type = "Gmail Image Proxy"
        browser_name = "Gmail Proxy"
        device_type = "Email Proxy"
        os_name = "Google Cloud"
    elif "Thunderbird" in ua:
        client_type = "Mozilla Thunderbird"
        browser_name = "Thunderbird"
    elif "Microsoft Office" in ua or "Outlook" in ua:
        client_type = "Microsoft Outlook"
        browser_name = "Outlook"
    elif "AppleWebKit" in ua and "CFNetwork" in ua:
        client_type = "Apple Mail (iOS/macOS)"
        device_type = "Mobile / Mac"
    elif "YahooMailProxy" in ua:
        client_type = "Yahoo Mail Proxy"
        browser_name = "Yahoo Proxy"
        device_type = "Email Proxy"
    elif "bot" in ua.lower() or "crawler" in ua.lower() or "spider" in ua.lower():
        client_type = "Automated Bot / Scanner"
        device_type = "Bot"

    # Detect OS if not an email proxy
    if os_name == "Unknown":
        if "Windows NT 10.0" in ua:
            os_name = "Windows 10/11"
        elif "Windows NT 6.3" in ua:
            os_name = "Windows 8.1"
        elif "Windows NT 6.1" in ua:
            os_name = "Windows 7"
        elif "Windows" in ua:
            os_name = "Windows"
        elif "iPhone" in ua:
            os_name = "iOS (iPhone)"
            device_type = "Mobile"
        elif "iPad" in ua:
            os_name = "iPadOS"
            device_type = "Tablet"
        elif "Macintosh" in ua or "Mac OS X" in ua:
            os_name = "macOS"
        elif "Android" in ua:
            os_name = "Android"
            device_type = "Mobile" if "Mobile" in ua else "Tablet"
        elif "Linux" in ua:
            os_name = "Linux"
        elif "CrOS" in ua:
            os_name = "ChromeOS"

    # Detect Browser / Application if not set
    if browser_name == "Other":
        if "Edg/" in ua or "Edge/" in ua:
            browser_name = "Microsoft Edge"
        elif "Chrome/" in ua and "Safari/" in ua:
            browser_name = "Google Chrome"
        elif "Firefox/" in ua:
            browser_name = "Mozilla Firefox"
        elif "Version/" in ua and "Safari/" in ua:
            browser_name = "Apple Safari"
        elif "MSIE" in ua or "Trident/" in ua:
            browser_name = "Internet Explorer"
        else:
            browser_name = "HTTP Client / Unknown"

    return {
        "device_type": device_type,
        "os_name": os_name,
        "browser_name": browser_name,
        "client_type": client_type,
    }
