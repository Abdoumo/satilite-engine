import requests
import json
import os
from datetime import datetime, timedelta

# ============================================================
# SETTINGS
# ============================================================
LATITUDE = 36.9000
LONGITUDE = 7.7667

TOKEN_FILE = "accessstokenofdataspace"

def search_and_download_copernicus():
    print("=" * 70)
    print("COPERNICUS DATA SPACE ECOSYSTEM (SENTINEL-2)")
    print("=" * 70)

    # 1. Load Token
    if not os.path.exists(TOKEN_FILE):
        print(f"Error: Token file '{TOKEN_FILE}' not found.")
        return

    with open(TOKEN_FILE, "r") as f:
        try:
            data = json.load(f)
            token = data.get("access_token")
        except json.JSONDecodeError:
            print("Error: Token file is not valid JSON.")
            return

    if not token:
        print("Error: 'access_token' not found in token file.")
        return

    # 2. Setup bounding box
    delta = 0.05
    lon1, lat1 = LONGITUDE - delta, LATITUDE - delta
    lon2, lat2 = LONGITUDE + delta, LATITUDE + delta
    polygon = f"POLYGON(({lon1} {lat1},{lon2} {lat1},{lon2} {lat2},{lon1} {lat2},{lon1} {lat1}))"

    # 3. Date range (last 10 days to ensure we catch recent images)
    today = datetime.utcnow()
    start_date = (today - timedelta(days=10)).strftime('%Y-%m-%dT00:00:00.000Z')

    # 4. Search OData API
    url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    params = {
        "$filter": f"Collection/Name eq 'SENTINEL-2' and OData.CSC.Intersects(area=geography'SRID=4326;{polygon}') and ContentDate/Start gt {start_date}",
        "$top": 5,
        "$orderby": "ContentDate/Start desc"
    }

    print("Searching for recent Sentinel-2 images...")
    try:
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
    except requests.RequestException as e:
        print("Error querying CDSE:", e)
        return

    products = res.json().get("value", [])

    if not products:
        print("No Sentinel-2 images found in the last 10 days.")
        return

    print(f"\nFound {len(products)} recent scenes:")
    print("-" * 70)
    for p in products:
        cloud = p.get('CloudCover')
        cloud_str = f"{cloud:.2f}%" if cloud is not None else "N/A"
        print(f"Date: {p['ContentDate']['Start'][:10]}   Cloud: {cloud_str:6s}   ID: {p['Id']}")
    print("-" * 70)

    # 5. Select the most recent product
    selected = products[0]
    product_id = selected["Id"]
    product_name = selected["Name"]

    print("\nSELECTED SCENE:")
    print(f"Name: {product_name}")
    print(f"Date: {selected['ContentDate']['Start']}")
    
    # 6. Download the product
    # Note: Sentinel-2 L2A full products are typically ~1GB in size.
    # The CDSE zipper endpoint streams the product zip archive.
    download_url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }

    output_zip = f"{product_name}.zip"
    
    print(f"\nStarting download of {output_zip} ...")
    print(f"URL: {download_url}")
    print("(This may take a while depending on your internet speed, typical size is ~1GB)")

    try:
        with requests.get(download_url, headers=headers, stream=True, timeout=60) as r:
            if r.status_code == 200:
                with open(output_zip, 'wb') as f:
                    downloaded = 0
                    # Read in chunks of 8MB
                    for chunk in r.iter_content(chunk_size=8192 * 1024): 
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            print(f"\rDownloaded: {downloaded / (1024*1024):.2f} MB", end="")
                print(f"\n\nDownload completed: {output_zip}")
            else:
                print(f"\nDownload failed with status {r.status_code}")
                print(r.text[:500])
    except requests.RequestException as e:
        print(f"\nError during download: {e}")

if __name__ == "__main__":
    search_and_download_copernicus()
