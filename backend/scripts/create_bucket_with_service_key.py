"""
Create Supabase Storage bucket using Service Role Key.

This script requires the SUPABASE_SERVICE_ROLE_KEY environment variable.
The service role key has admin privileges and can create buckets.

To get your service role key:
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Settings > API
4. Copy the "service_role" key (NOT the anon key)
5. Add to .env: SUPABASE_SERVICE_ROLE_KEY=your_key_here
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

async def create_bucket_with_policies():
    """Create the location-files bucket with proper policies."""
    print("=" * 60)
    print("Supabase Storage Bucket Creation (Service Role)")
    print("=" * 60)
    print()
    
    if not SUPABASE_URL:
        print("❌ Error: SUPABASE_URL must be set in .env")
        return False
    
    if not SERVICE_ROLE_KEY:
        print("❌ Error: SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        print()
        print("To get your service role key:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to Settings > API")
        print("4. Copy the 'service_role' key (NOT the anon key)")
        print("5. Add to .env: SUPABASE_SERVICE_ROLE_KEY=your_key_here")
        print()
        print("⚠️  WARNING: Never expose the service role key in frontend code!")
        return False
    
    print(f"Supabase URL: {SUPABASE_URL}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Create bucket
        print("Step 1: Creating bucket 'location-files'...")
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
                'apikey': SERVICE_ROLE_KEY,
                'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code in (200, 201):
            print("✅ Bucket created successfully!")
        elif response.status_code == 409 or "already exists" in response.text.lower():
            print("ℹ️  Bucket already exists, continuing...")
        else:
            print(f"❌ Failed to create bucket: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print()
        
        # Step 2: Set up policies using SQL
        print("Step 2: Setting up storage policies...")
        print("Note: Policies must be created via SQL or Dashboard")
        print()
        print("Run these SQL commands in your Supabase SQL Editor:")
        print()
        print("-- Policy 1: Public read access")
        print("CREATE POLICY \"Public read access\"")
        print("ON storage.objects FOR SELECT")
        print("TO public")
        print("USING (bucket_id = 'location-files');")
        print()
        print("-- Policy 2: Authenticated write access")
        print("CREATE POLICY \"Authenticated write access\"")
        print("ON storage.objects FOR INSERT")
        print("TO authenticated")
        print("WITH CHECK (bucket_id = 'location-files');")
        print()
        print("-- Policy 3: Authenticated delete access")
        print("CREATE POLICY \"Authenticated delete access\"")
        print("ON storage.objects FOR DELETE")
        print("TO authenticated")
        print("USING (bucket_id = 'location-files');")
        print()
        
        print("=" * 60)
        print("✅ Bucket created! Now add the policies via SQL Editor.")
        print("=" * 60)
        return True

if __name__ == "__main__":
    asyncio.run(create_bucket_with_policies())
