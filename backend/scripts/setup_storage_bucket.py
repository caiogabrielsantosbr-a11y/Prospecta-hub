"""
Script to set up the location-files bucket in Supabase Storage.

This script:
1. Checks if the location-files bucket exists
2. Creates the bucket if it doesn't exist
3. Sets up the correct policies for public read access
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

async def check_bucket_exists():
    """Check if the location-files bucket exists."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/bucket/location-files",
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}'
            }
        )
        
        if response.status_code == 200:
            print("✅ Bucket 'location-files' already exists")
            return True
        elif response.status_code == 404:
            print("❌ Bucket 'location-files' does not exist")
            return False
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            return False

async def create_bucket():
    """Create the location-files bucket with public read access."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{SUPABASE_URL}/storage/v1/bucket",
            json={
                "id": "location-files",
                "name": "location-files",
                "public": True,
                "file_size_limit": 10485760,  # 10MB
                "allowed_mime_types": ["application/json"]
            },
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code in (200, 201):
            print("✅ Successfully created bucket 'location-files'")
            return True
        else:
            print(f"❌ Failed to create bucket: {response.status_code}")
            print(f"Response: {response.text}")
            return False

async def main():
    """Main function to set up the storage bucket."""
    print("=" * 60)
    print("Supabase Storage Bucket Setup")
    print("=" * 60)
    print()
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return
    
    print(f"Supabase URL: {SUPABASE_URL}")
    print()
    
    # Check if bucket exists
    print("Checking if bucket exists...")
    exists = await check_bucket_exists()
    print()
    
    if not exists:
        print("Creating bucket...")
        success = await create_bucket()
        print()
        
        if success:
            print("✅ Setup complete! The location-files bucket is ready.")
        else:
            print("❌ Setup failed. Please check the error messages above.")
            print()
            print("Manual setup instructions:")
            print("1. Go to your Supabase dashboard")
            print("2. Navigate to Storage")
            print("3. Create a new bucket named 'location-files'")
            print("4. Set it as public")
            print("5. Set file size limit to 10MB")
    else:
        print("✅ No action needed. The bucket is already set up.")

if __name__ == "__main__":
    asyncio.run(main())
