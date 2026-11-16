import os
import sys

# Ensure email-tracker is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from database import init_db, SessionLocal, TrackingEvent
from utils import TRANSPARENT_GIF_BYTES, parse_user_agent

def run_tests():
    print("=== 1. Testing Database & App Startup ===")
    init_db()
    client = TestClient(app)

    print("=== 2. Testing User-Agent & Device Parsing ===")
    # Test Gmail proxy
    ua_gmail = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 (via GoogleImageProxy)"
    parsed_gmail = parse_user_agent(ua_gmail)
    assert parsed_gmail["client_type"] == "Gmail Image Proxy", f"Expected Gmail Image Proxy, got {parsed_gmail['client_type']}"
    assert parsed_gmail["device_type"] == "Email Proxy"
    print("  [OK] Gmail Image Proxy parsed correctly")

    # Test iPhone
    ua_iphone = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    parsed_iphone = parse_user_agent(ua_iphone)
    assert parsed_iphone["device_type"] == "Mobile"
    assert parsed_iphone["os_name"] == "iOS (iPhone)"
    print("  [OK] iPhone User-Agent parsed correctly")

    # Test Outlook
    ua_outlook = "Microsoft Office/16.0 (Windows NT 10.0; Microsoft Outlook 16.0.14326; Pro)"
    parsed_outlook = parse_user_agent(ua_outlook)
    assert parsed_outlook["client_type"] == "Microsoft Outlook"
    print("  [OK] Microsoft Outlook parsed correctly")

    print("=== 3. Testing /tracker.gif Endpoint ===")
    response = client.get(
        "/tracker.gif?cid=spring_sale&recipient=sarah%40acme.com&subject=Special+Offer",
        headers={
            "User-Agent": ua_iphone,
            "X-Forwarded-For": "203.0.113.195, 10.0.0.1",
            "Referer": "https://mail.google.com/"
        }
    )
    assert response.status_code == 200, f"Status code: {response.status_code}"
    assert response.headers["content-type"] == "image/gif"
    assert "no-cache" in response.headers["cache-control"]
    assert response.content == TRANSPARENT_GIF_BYTES
    assert len(response.content) == len(TRANSPARENT_GIF_BYTES)
    print("  [OK] /tracker.gif returns transparent GIF with anti-cache headers")

    print("=== 4. Testing Database Record Persistence ===")
    db = SessionLocal()
    event = db.query(TrackingEvent).filter_by(recipient="sarah@acme.com").first()
    assert event is not None, "Event was not saved in DB"
    assert event.campaign_id == "spring_sale"
    assert event.ip_address == "203.0.113.195"
    assert event.device_type == "Mobile"
    assert event.os_name == "iOS (iPhone)"
    assert event.subject == "Special Offer"
    db.close()
    print("  [OK] Event record verified in SQLite database with exact IP & device metadata")

    print("=== 5. Testing /api/stats & /api/events ===")
    stats_resp = client.get("/api/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_opens"] >= 1
    assert "spring_sale" in stats["campaign_list"]
    print(f"  [OK] /api/stats verified: {stats}")

    events_resp = client.get("/api/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) >= 1
    assert events[0]["recipient"] == "sarah@acme.com"
    print(f"  [OK] /api/events verified: latest record captured for {events[0]['recipient']}")

    print("=== 6. Testing /dashboard HTML & /health ===")
    dash_resp = client.get("/dashboard")
    assert dash_resp.status_code == 200
    assert "OpenPixel" in dash_resp.text
    print("  [OK] Dashboard loads successfully")

    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"
    print("  [OK] Health check endpoint operational")

    print("=== 7. Testing CSV Export ===")
    csv_resp = client.get("/api/export")
    assert csv_resp.status_code == 200
    assert "sarah@acme.com" in csv_resp.text
    assert "203.0.113.195" in csv_resp.text
    print("  [OK] CSV export functional and contains tracked headers")

    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
