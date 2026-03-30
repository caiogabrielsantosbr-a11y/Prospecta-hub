"""
Test script to create a location set and see detailed error messages.
"""
import asyncio
import httpx
import json

async def test_create():
    """Test creating a location set."""
    print("=" * 60)
    print("Testing Location Set Creation")
    print("=" * 60)
    print()
    
    # Test data
    data = {
        "name": "Teste Cidades SP",
        "description": "Teste de criação de conjunto",
        "locations": [
            "Taubaté - SP",
            "Suzano - SP",
            "Limeira - SP",
            "Guarujá - SP",
            "Sumaré - SP",
            "Cotia - SP"
        ]
    }
    
    print(f"Creating location set: {data['name']}")
    print(f"Locations: {len(data['locations'])}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/locations",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print()
            
            try:
                response_data = response.json()
                print(f"Response body:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
            except:
                print(f"Response text: {response.text}")
            
            print()
            
            if response.status_code in (200, 201):
                print("✅ Location set created successfully!")
            else:
                print(f"❌ Failed to create location set")
                
    except httpx.ConnectError as e:
        print(f"❌ Connection error: {e}")
        print()
        print("Make sure the backend is running:")
        print("  cd backend")
        print("  python main.py")
        
    except httpx.TimeoutException as e:
        print(f"❌ Timeout error: {e}")
        print()
        print("The request took too long. This might indicate:")
        print("  - Slow network connection to Supabase")
        print("  - Backend is processing but taking too long")
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_create())
