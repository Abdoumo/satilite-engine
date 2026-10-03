import requests, json

url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
params = {
    '$filter': "Collection/Name eq 'SENTINEL-2' and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON((7.7167 36.85, 7.8167 36.85, 7.8167 36.95, 7.7167 36.95, 7.7167 36.85))')",
    '$top': 5,
    '$orderby': 'ContentDate/Start desc'
}

print("Checking recent dates:")
r = requests.get(url, params=params)
try:
    for p in r.json().get('value', []):
        print(f"Date: {p['ContentDate']['Start']}, Name: {p['Name']}")
except Exception as e:
    print(e)
    print(r.text)
