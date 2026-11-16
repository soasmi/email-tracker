import os
import csv
import io
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import FastAPI, Request, Response, Depends, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import init_db, get_db, TrackingEvent
from utils import (
    TRANSPARENT_GIF_BYTES,
    CACHE_CONTROL_HEADERS,
    extract_client_ip,
    parse_user_agent,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Initialize FastAPI app
app = FastAPI(
    title="OpenPixel Email Tracker",
    description="24/7 Server-Hosted Free Email Tracking Web Service",
    version="1.0.0",
)

# Enable CORS so webmail clients (Gmail, Outlook 365, etc.) don't block image retrieval
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.on_event("startup")
def on_startup():
    init_db()


def record_tracking_event(
    campaign_id: str,
    recipient: str,
    subject: Optional[str],
    ip_address: str,
    user_agent: str,
    referer: Optional[str],
):
    """
    Background worker function that writes the tracking event into the persistent database.
    Running this in BackgroundTasks guarantees the 1x1 GIF is delivered instantaneously to the email client.
    """
    from database import SessionLocal
    db = SessionLocal()
    try:
        ua_info = parse_user_agent(user_agent)
        event = TrackingEvent(
            timestamp=datetime.now(timezone.utc),
            campaign_id=campaign_id or "default",
            recipient=recipient or "anonymous",
            subject=subject,
            ip_address=ip_address,
            user_agent=user_agent or "",
            device_type=ua_info["device_type"],
            os_name=ua_info["os_name"],
            browser_name=ua_info["browser_name"],
            client_type=ua_info["client_type"],
            referer=referer,
        )
        db.add(event)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error logging tracking event: {e}")
    finally:
        db.close()


@app.get("/", include_in_schema=False)
def root():
    """Redirect root path to interactive dashboard"""
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request):
    """Render the responsive monitoring dashboard"""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={}
    )


@app.get("/tracker.gif")
def track_email(
    request: Request,
    background_tasks: BackgroundTasks,
    cid: Optional[str] = Query(None, description="Campaign ID or Tag"),
    campaign: Optional[str] = Query(None, description="Alternative alias for campaign"),
    recipient: Optional[str] = Query(None, description="Recipient identifier or email"),
    email: Optional[str] = Query(None, description="Alternative alias for recipient email"),
    to: Optional[str] = Query(None, description="Alternative alias for to email"),
    subject: Optional[str] = Query(None, description="Optional subject or note"),
    title: Optional[str] = Query(None, description="Alternative alias for subject"),
):
    """
    Public 1x1 transparent GIF tracking endpoint.
    Parses request headers (IP, User-Agent, Referer, Timestamp) and logs open event.
    Returns 43-byte GIF with strict no-cache headers.
    """
    # Normalize query parameters with fallbacks
    resolved_campaign = cid or campaign or "default"
    resolved_recipient = recipient or email or to or "anonymous"
    resolved_subject = subject or title or None

    # Parse headers
    client_ip = extract_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    referer = request.headers.get("referer", None)

    # Dispatch database write to background task so GIF returns under ~5ms
    background_tasks.add_task(
        record_tracking_event,
        campaign_id=resolved_campaign,
        recipient=resolved_recipient,
        subject=resolved_subject,
        ip_address=client_ip,
        user_agent=user_agent,
        referer=referer,
    )

    return Response(
        content=TRANSPARENT_GIF_BYTES,
        media_type="image/gif",
        headers=CACHE_CONTROL_HEADERS,
    )


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Aggregate statistics for the dashboard KPI cards"""
    total_opens = db.query(func.count(TrackingEvent.id)).scalar() or 0
    unique_recipients = (
        db.query(func.count(func.distinct(TrackingEvent.recipient))).scalar() or 0
    )
    unique_campaigns = (
        db.query(func.count(func.distinct(TrackingEvent.campaign_id))).scalar() or 0
    )

    twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    opens_last_24h = (
        db.query(func.count(TrackingEvent.id))
        .filter(TrackingEvent.timestamp >= twenty_four_hours_ago)
        .scalar()
        or 0
    )

    # Distinct campaign names
    campaigns = [
        row[0]
        for row in db.query(func.distinct(TrackingEvent.campaign_id))
        .order_by(TrackingEvent.campaign_id)
        .all()
        if row[0]
    ]

    return {
        "total_opens": total_opens,
        "unique_recipients": unique_recipients,
        "unique_campaigns": unique_campaigns,
        "opens_last_24h": opens_last_24h,
        "campaign_list": campaigns,
    }


@app.get("/api/events")
def get_events(
    limit: int = 150,
    db: Session = Depends(get_db)
):
    """Retrieve the latest tracking events in reverse chronological order"""
    events = (
        db.query(TrackingEvent)
        .order_by(TrackingEvent.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [e.to_dict() for e in events]


@app.get("/api/export")
def export_csv(db: Session = Depends(get_db)):
    """Download full tracking audit history in CSV format"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Event ID",
        "Timestamp (UTC)",
        "Campaign ID",
        "Recipient",
        "Subject / Note",
        "Client IP Address",
        "Device Type",
        "Operating System",
        "Browser",
        "Email Client Type",
        "Referer",
        "Full User-Agent String",
    ])

    events = db.query(TrackingEvent).order_by(TrackingEvent.timestamp.desc()).all()
    for e in events:
        writer.writerow([
            e.id,
            e.timestamp.isoformat() if e.timestamp else "",
            e.campaign_id,
            e.recipient,
            e.subject or "",
            e.ip_address,
            e.device_type,
            e.os_name,
            e.browser_name,
            e.client_type,
            e.referer or "",
            e.user_agent,
        ])

    output.seek(0)
    filename = f"email_tracking_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/clear")
def clear_events(db: Session = Depends(get_db)):
    """Purge all recorded tracking events (useful for resetting or cleaning test data)"""
    try:
        db.query(TrackingEvent).delete()
        db.commit()
        return {"status": "success", "message": "All tracking records cleared."}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}


@app.get("/health")
@app.get("/ping")
def health_check():
    """
    Lightweight health endpoint for uptime ping services (cron-job.org / UptimeRobot)
    Keeps Render free tier alive 24/7 without entering hibernation mode.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "OpenPixel Email Tracker",
    }
