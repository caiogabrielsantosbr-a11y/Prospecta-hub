"""
SQLAlchemy models for all modules.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON
from database.db import Base


# ── GMap Leads ──────────────────────────────────────────────
class GMapLead(Base):
    __tablename__ = "gmap_leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, default="")
    website = Column(String, default="")
    endereco = Column(String, default="")
    cidade = Column(String, default="")
    url = Column(String, default="")
    task_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Facebook ADS Leads ──────────────────────────────────────
class FacebookAdsLead(Base):
    __tablename__ = "facebook_ads_leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    page_url = Column(String, default="")
    ad_url = Column(String, default="")
    page_id = Column(String, default="")
    emails = Column(Text, default="")
    phones = Column(Text, default="")
    instagram = Column(String, default="")
    stage = Column(String, default="feed")  # feed | contacts
    task_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Email Extraction Results ────────────────────────────────
class EmailResult(Base):
    __tablename__ = "email_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String, nullable=False)
    email = Column(String, default="")
    source = Column(String, default="")  # RDAP | Reciclagem
    task_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Background Tasks ────────────────────────────────────────
class TaskRecord(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    module = Column(String, nullable=False)  # gmap | facebook | emails | email_dispatch
    status = Column(String, default="running")  # running | paused | completed | failed | stopped
    config = Column(JSON, default=dict)
    stats = Column(JSON, default=dict)
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Email Dispatch ───────────────────────────────────────────
class EmailDispatch(Base):
    __tablename__ = "email_dispatches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient = Column(String, nullable=False)
    subject = Column(String, default="")
    status = Column(String, default="pending")  # pending | sent | failed
    error_detail = Column(Text, default="")
    task_id = Column(String, index=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── DM Templates ────────────────────────────────────────────
class DMTemplate(Base):
    __tablename__ = "dm_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    messages = Column(JSON, default=list)
    audios = Column(JSON, default=list)
    send_mode = Column(String, default="sequential")
    delay_dm_min = Column(Integer, default=10)
    delay_dm_max = Column(Integer, default=20)
    delay_lead_min = Column(Integer, default=30)
    delay_lead_max = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Approach Scripts ────────────────────────────────
class ApproachScript(Base):
    __tablename__ = "approach_scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
