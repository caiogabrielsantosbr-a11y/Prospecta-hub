"""
Script de migração: busca JSON do Supabase Storage e popula coluna locations
"""
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gyenypsxpidmsxabjhqg.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

RECORDS = [
    {"id": "ff66a712-0a8b-45a6-9b2d-5db374acd84b", "name": "Brasil",     "file_path": "a5086c88-c7b1-42a9-946d-ab3b6fae59d2.json"},
    {"id": "77341c2f-9661-4142-bda3-eb8698dbc33a", "name": "teste",      "file_path": "d2d20b43-7686-488d-b9d0-2a955b4eec30.json"},
    {"id": "69603c2a-467f-49d9-b77a-d7e27d98662b", "name": "Teste 100",  "file_path": "4e895a40-dc5b-4aa4-9c10-cc1262c2721b.json"},
]

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
}

def main():
    with httpx.Client(timeout=60.0) as client:
        for record in RECORDS:
            storage_url = f"{SUPABASE_URL}/storage/v1/object/public/location-files/{record['file_path']}"
            print(f"\n[{record['name']}] Baixando {storage_url}...")

            r = client.get(storage_url)
            if r.status_code != 200:
                print(f"  ERRO ao baixar: HTTP {r.status_code} - {r.text[:200]}")
                continue

            try:
                data = r.json()
            except Exception as e:
                print(f"  ERRO ao parsear JSON: {e}")
                continue

            # O JSON tem campo "locais" com a lista de cidades
            locais = data.get("locais") or data.get("locations") or []
            if not locais:
                print(f"  AVISO: JSON sem campo 'locais' ou 'locations'. Campos: {list(data.keys())}")
                continue

            print(f"  Encontradas {len(locais)} cidades. Atualizando banco...")

            patch = client.patch(
                f"{SUPABASE_URL}/rest/v1/location_sets?id=eq.{record['id']}",
                headers=headers,
                json={"locations": locais, "location_count": len(locais)},
            )
            if patch.status_code in (200, 204):
                print(f"  ✅ {record['name']}: {len(locais)} cidades salvas no banco!")
            else:
                print(f"  ❌ Erro no UPDATE: HTTP {patch.status_code} - {patch.text}")

if __name__ == "__main__":
    main()
