import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "tracker.db")

# Database URL: default to local persistent SQLite file in project directory
# Can be overridden by setting the DATABASE_URL environment variable (e.g. on Render or with Supabase/Neon)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# SQLAlchemy 1.4+ fix for Postgres URIs starting with postgres:// instead of postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    campaign_id = Column(String(120), default="default", index=True)
    recipient = Column(String(255), default="unknown", index=True)
    subject = Column(String(255), nullable=True)
    ip_address = Column(String(64), default="unknown")
    user_agent = Column(Text, default="")
    device_type = Column(String(64), default="Unknown")
    os_name = Column(String(64), default="Unknown")
    browser_name = Column(String(64), default="Unknown")
    client_type = Column(String(64), default="Unknown")
    referer = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_campaign_recipient", "campaign_id", "recipient"),
    )

    def to_dict(self):
        ts = self.timestamp
        ts_str = None
        if ts:
            # If timestamp is naive (from SQLite), attach UTC timezone so frontend parses it accurately
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            ts_str = ts.isoformat()

        return {
            "id": self.id,
            "timestamp": ts_str,
            "campaign_id": self.campaign_id,
            "recipient": self.recipient,
            "subject": self.subject or "",
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_type": self.device_type,
            "os_name": self.os_name,
            "browser_name": self.browser_name,
            "client_type": self.client_type,
            "referer": self.referer or "",
        }


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
