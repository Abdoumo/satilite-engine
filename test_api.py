import requests
import json

print("=== TESTING COPERNICUS CDSE ODATA API ===")
url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=OData.CSC.Intersects(footprint, geography'SRID=4326;POINT(7.7667 36.9)') and ContentDate/Start ge 2026-09-24T00:00:00.000Z and ContentDate/Start le 2026-09-25T00:00:00.000Z&$top=10"
r = requests.get(url)
print(f"CDSE Status: {r.status_code}")
data = r.json()
print("Found products:")
for p in data.get('value', []):
    print(f"- {p['Name']} (Collection: {p.get('Collection', {}).get('Name', 'Unknown')})")

print("\n=== TESTING NASA CMR STAC ===")
stac_url = "https://cmr.earthdata.nasa.gov/stac/LPCLOUD/search"
payload = {
    "bbox": [7.7567, 36.89, 7.7767, 36.91],
    "datetime": "2026-09-24T00:00:00Z/2026-09-25T00:00:00Z",
    "limit": 10
}
r2 = requests.post(stac_url, json=payload)
print(f"NASA CMR Status: {r2.status_code}")
data2 = r2.json()
print("Found features (Collections):")
for f in data2.get('features', []):
    print(f"- {f['collection']} | {f['id']}")
