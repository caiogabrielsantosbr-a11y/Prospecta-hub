"""
Test script to verify Supabase Storage upload functionality.

This script attempts to upload a test file to verify the bucket is configured correctly.
"""
import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

async def test_upload():
    """Test uploading a file to the location-files bucket."""
    print("=" * 60)
    print("Supabase Storage Upload Test")
    print("=" * 60)
    print()
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return
    
    print(f"Supabase URL: {SUPABASE_URL}")
    print()
    
    # Create test data
    test_data = {
        "nome": "Test Location Set",
        "descricao": "This is a test location set",
        "locais": [
            "São Paulo, SP",
            "Rio de Janeiro, RJ",
            "Belo Horizonte, MG"
        ]
    }
    
    test_file_path = "test-upload.json"
    json_bytes = json.dumps(test_data, ensure_ascii=False, indent=2).encode('utf-8')
    
    print(f"Test file: {test_file_path}")
    print(f"File size: {len(json_bytes)} bytes")
    print()
    
    # Attempt upload
    print("Attempting upload...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{SUPABASE_URL}/storage/v1/object/location-files/{test_file_path}",
            content=json_bytes,
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json'
            }
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        print()
        
        if response.status_code in (200, 201):
            print("✅ Upload successful!")
            print()
            print(f"File URL: {SUPABASE_URL}/storage/v1/object/public/location-files/{test_file_path}")
            print()
            
            # Test download
            print("Testing download...")
            download_response = await client.get(
                f"{SUPABASE_URL}/storage/v1/object/public/location-files/{test_file_path}"
            )
            
            if download_response.status_code == 200:
                print("✅ Download successful!")
                downloaded_data = download_response.json()
                print(f"Downloaded data: {json.dumps(downloaded_data, indent=2, ensure_ascii=False)}")
                print()
                
                # Clean up test file
                print("Cleaning up test file...")
                delete_response = await client.delete(
                    f"{SUPABASE_URL}/storage/v1/object/location-files/{test_file_path}",
                    headers={
                        'apikey': SUPABASE_KEY,
                        'Authorization': f'Bearer {SUPABASE_KEY}'
                    }
                )
                
                if delete_response.status_code in (200, 204):
                    print("✅ Test file deleted successfully")
                else:
                    print(f"⚠️  Failed to delete test file: {delete_response.status_code}")
                
                print()
                print("=" * 60)
                print("✅ All tests passed! Storage is configured correctly.")
                print("=" * 60)
            else:
                print(f"❌ Download failed: {download_response.status_code}")
                print(f"Response: {download_response.text}")
        
        elif response.status_code == 404:
            print("❌ Bucket 'location-files' not found!")
            print()
            print("Please create the bucket manually:")
            print("1. Go to https://supabase.com/dashboard")
            print("2. Navigate to Storage")
            print("3. Create a new bucket named 'location-files'")
            print("4. Set it as public")
            print()
            print("See SUPABASE_STORAGE_SETUP.md for detailed instructions.")
        
        elif response.status_code in (401, 403):
            print("❌ Authentication error!")
            print()
            print("Possible causes:")
            print("1. Invalid SUPABASE_KEY in .env")
            print("2. Bucket policies not configured correctly")
            print("3. Bucket is not public")
            print()
            print("See SUPABASE_STORAGE_SETUP.md for setup instructions.")
        
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print()
            print("See SUPABASE_STORAGE_SETUP.md for troubleshooting.")

if __name__ == "__main__":
    asyncio.run(test_upload())
