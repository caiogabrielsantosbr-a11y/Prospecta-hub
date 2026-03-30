"""
Initialize SQLite database with all tables.
Run this script to create the database schema.
"""
import asyncio
from database.db import engine, Base
from database.models import (
    GMapLead,
    FacebookAdsLead,
    EmailResult,
    TaskRecord,
    EmailDispatch,
    DMTemplate,
    ApproachScript
)


async def init_db():
    """Create all tables in the database."""
    print("Initializing database...")
    print(f"Database URL: {engine.url}")
    
    async with engine.begin() as conn:
        # Drop all tables (optional - comment out if you want to keep existing data)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database initialized successfully!")
    print("\nTables created:")
    print("  - gmap_leads")
    print("  - facebook_ads_leads")
    print("  - email_results")
    print("  - tasks")
    print("  - email_dispatches")
    print("  - dm_templates")
    print("  - approach_scripts")


if __name__ == "__main__":
    asyncio.run(init_db())
