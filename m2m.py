import requests
import json
import os
import tarfile
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds, transform
import matplotlib.pyplot as plt
import numpy as np

USERNAME = "bedoushop@gmail.com"
# Put your NEW token here
TOKEN = "!JRSA2ACTC6GXF_!ufGadI1D4YInHkrBZKOIQ2jCVbkCUz64MGfN75x726h!l6nO"
ENDPOINT = "https://m2m.cr.usgs.gov/api/api/json/stable/"

LAT = 36.9
LON = 7.7667
DELTA = 0.15 # Bounding box for crop

def get_temperature_map():
    print("=" * 70)
    print("USGS M2M: LANDSAT SURFACE TEMPERATURE")
    print("=" * 70)

    # 1. Login
    print("Logging into USGS M2M...")
    payload = {"username": USERNAME, "token": TOKEN, "authType": "EROS"}
    r = requests.post(ENDPOINT + "login-token", json=payload)
    if r.status_code != 200 or r.json().get('errorCode'):
        print("Login failed:", r.text)
        return
    api_key = r.json()['data']
    headers = {"X-Auth-Token": api_key}
    
    # 2. Search
    print(f"Searching Landsat Collection 2 Level 2 for Annaba (Lat: {LAT}, Lon: {LON})...")
    search_payload = {
        "datasetName": "landsat_ot_c2_l2",
        "sceneFilter": {
            "spatialFilter": {
                "filterType": "mbr",
                "lowerLeft": {"latitude": LAT - DELTA, "longitude": LON - DELTA},
                "upperRight": {"latitude": LAT + DELTA, "longitude": LON + DELTA}
            }
        },
        "maxResults": 10
    }
    
    r = requests.post(ENDPOINT + "scene-search", json=search_payload, headers=headers)
    res = r.json()
    if res.get('errorCode'):
        print("Search failed:", res.get('errorMessage'))
        return
        
    results = res.get('data', {}).get('results', [])
    if not results:
        print("No scenes found.")
        return
        
    scene = results[0]
    entity_id = scene['entityId']
    print(f"Selected Scene: {entity_id}")
    
    # 3. Get Download Options
    print("Retrieving download options...")
    r = requests.post(ENDPOINT + "download-options", json={"datasetName": "landsat_ot_c2_l2", "entityIds": [entity_id]}, headers=headers)
    try:
        options = r.json().get('data', [])
    except json.JSONDecodeError:
        print(f"\nUSGS API Error {r.status_code}: {r.reason}")
        print("Your USGS account likely does not have 'Machine-to-Machine (M2M)' download privileges approved yet.")
        print("You can apply for M2M access in your EROS Registration profile.")
        return
    
    if not options:
        print("No download options available.")
        return
        
    product_id = None
    for opt in options:
        # We want the standard Level-2 product (which contains ST_B10)
        if opt['available'] and "Product" in opt['productName']:
            product_id = opt['id']
            break
            
    if not product_id:
        print("Standard Level-2 product is not immediately available. It may need to be ordered.")
        return
        
    # 4. Request Download URL
    print("Requesting download URL...")
    r = requests.post(ENDPOINT + "download-request", json={"downloads": [{"entityId": entity_id, "productId": product_id}]}, headers=headers)
    downloads = r.json().get('data', {}).get('availableDownloads', [])
    
    if not downloads:
        print("Could not get immediate download URL. The scene might be in the 'preparing' queue.")
        return
        
    download_url = downloads[0]['url']
    output_tar = f"{entity_id}.tar"
    
    if not os.path.exists(output_tar):
        print(f"Downloading {output_tar} (This is a large ~1GB bundle and may take time)...")
        with requests.get(download_url, stream=True) as d_res:
            d_res.raise_for_status()
            with open(output_tar, 'wb') as f:
                downloaded = 0
                for chunk in d_res.iter_content(chunk_size=8192*1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        print(f"\rDownloaded: {downloaded / (1024*1024):.2f} MB", end="")
        print("\nDownload complete.")
    else:
        print(f"{output_tar} already exists. Skipping download.")
        
    # 5. Extract ST_B10
    extracted_dir = f"{entity_id}_extracted"
    os.makedirs(extracted_dir, exist_ok=True)
    st_b10_file = None
    
    print("Extracting surface temperature band (ST_B10)...")
    with tarfile.open(output_tar) as tar:
        for member in tar.getmembers():
            if member.name.endswith("ST_B10.TIF"):
                st_b10_file = os.path.join(extracted_dir, member.name)
                if not os.path.exists(st_b10_file):
                    tar.extract(member, path=extracted_dir)
                break
                
    if not st_b10_file:
        print("Error: Could not find ST_B10.TIF in the downloaded archive.")
        return
        
    # 6. Process Temperature Map
    print("Reading and calculating surface temperature...")
    with rasterio.open(st_b10_file) as src:
        # Crop bounds
        min_lon, min_lat = LON - DELTA, LAT - DELTA
        max_lon, max_lat = LON + DELTA, LAT + DELTA
        
        bounds_crs = transform_bounds("EPSG:4326", src.crs, min_lon, min_lat, max_lon, max_lat)
        window = from_bounds(*bounds_crs, src.transform)
        
        img_window = rasterio.windows.Window(0, 0, src.width, src.height)
        window = window.intersection(img_window)
        
        dn = src.read(1, window=window)
        cropped_transform = src.window_transform(window)
        
        # Get pixel coordinates for marker
        target_x, target_y = transform("EPSG:4326", src.crs, [LON], [LAT])
        target_col, target_row = ~cropped_transform * (target_x[0], target_y[0])
        
        # Exact temperature at the point
        target_col_int = int(target_col)
        target_row_int = int(target_row)
        point_dn = dn[target_row_int, target_col_int]
        
    # Calculate Landsat C2 L2 Surface Temperature
    # Kelvin = DN * 0.00341802 + 149.0
    # Celsius = Kelvin - 273.15
    temperature_kelvin = dn * 0.00341802 + 149.0
    temperature_celsius = temperature_kelvin - 273.15
    
    point_temp = point_dn * 0.00341802 + 149.0 - 273.15

    # Filter bad data (fill values, clouds)
    valid_mask = (dn > 0) & (temperature_celsius > -50) & (temperature_celsius < 100)
    temperature_celsius = np.where(valid_mask, temperature_celsius, np.nan)

    print(f"\n======================================")
    print(f"SURFACE TEMPERATURE AT MARKED POINT:")
    print(f"Latitude: {LAT}, Longitude: {LON}")
    print(f"Temperature: {point_temp:.2f} °C")
    print(f"======================================\n")

    print("Rendering map...")
    plt.figure(figsize=(12, 10))
    # Use a colormap suitable for temperature
    cmap = plt.cm.jet
    cmap.set_bad('black', 1.)
    
    im = plt.imshow(temperature_celsius, cmap=cmap, interpolation='nearest')
    plt.colorbar(im, label='Surface Temperature (°C)')
    
    # Plot red marker
    plt.plot(target_col, target_row, marker='+', color='red', markersize=20, markeredgewidth=2)
    plt.plot(target_col, target_row, marker='o', color='red', markersize=8, fillstyle='none', markeredgewidth=2)
    
    # Title
    date_str = entity_id[17:25] # e.g. LC08_L2SP_193034_20130607
    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}" if len(date_str) == 8 else entity_id
    title_str = (
        f"Landsat Surface Temperature ({formatted_date})\n"
        f"Latitude : {LAT:.4f}° N\n"
        f"Longitude: {LON:.4f}° E\n"
        f"Point Temperature: {point_temp:.2f} °C"
    )
    plt.title(title_str, fontsize=16)
    plt.axis('off')
    
    output_png = "annaba_landsat_temperature.png"
    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Done! Saved map as: {output_png}")

if __name__ == "__main__":
    get_temperature_map()