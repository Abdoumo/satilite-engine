import os
import glob
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds, transform
import matplotlib.pyplot as plt
import numpy as np

SAFE_DIR = r"f:\satilites\S2A_MSIL2A_20260929T101741_N0513_R065_T32SLF_20260929T165907.SAFE"

# Center on Annaba (same as sat.py)
LAT = 36.9
LON = 7.7667
# Bounding box delta (degrees) - smaller delta = closer zoom (0.02 = ~2.2km radius)
DELTA = 0.02

def process_tci():
    print("="*60)
    print("PROCESSING SENTINEL-2 TRUE COLOR IMAGE")
    print("="*60)
    
    print("Finding True Color Image (TCI) in 10m resolution...")
    search_pattern = os.path.join(SAFE_DIR, "**", "*TCI_10m.jp2")
    tci_files = glob.glob(search_pattern, recursive=True)
    
    if not tci_files:
        print("TCI_10m.jp2 not found! Trying without 10m suffix...")
        search_pattern = os.path.join(SAFE_DIR, "**", "*TCI*.jp2")
        tci_files = glob.glob(search_pattern, recursive=True)
        if not tci_files:
            print("No TCI found in the SAFE folder.")
            return
            
    tci_path = tci_files[0]
    print(f"Found TCI: {os.path.basename(tci_path)}")
    
    with rasterio.open(tci_path) as src:
        # Convert Lat/Lon bounding box to the image's coordinate reference system (CRS)
        min_lon, min_lat = LON - DELTA, LAT - DELTA
        max_lon, max_lat = LON + DELTA, LAT + DELTA
        
        bounds_crs = transform_bounds(
            "EPSG:4326", src.crs, 
            min_lon, min_lat, max_lon, max_lat
        )
        window = from_bounds(*bounds_crs, src.transform)
        
        # Intersect with actual image bounds to avoid reading outside the image
        img_window = rasterio.windows.Window(0, 0, src.width, src.height)
        window = window.intersection(img_window)
        
        print("Reading cropped image data (Annaba region)...")
        img = src.read(window=window)
        cropped_transform = src.window_transform(window)
        
        # Get pixel coordinates for the exact requested LAT/LON point
        target_x, target_y = transform("EPSG:4326", src.crs, [LON], [LAT])
        target_col, target_row = ~cropped_transform * (target_x[0], target_y[0])
    # Transpose from (Bands, Rows, Cols) to (Rows, Cols, Bands) for Matplotlib
    img = np.transpose(img, (1, 2, 0)).astype(float)
    
    # Apply a 2-98% Contrast Stretch to fix dark/washed-out satellite images
    for i in range(3): # For R, G, B bands
        band = img[:,:,i]
        # Calculate percentiles, ignoring pure black edges
        valid_pixels = band[band > 0]
        if len(valid_pixels) > 0:
            p2, p98 = np.percentile(valid_pixels, (2, 98))
            if p98 > p2:
                band = np.clip(band, p2, p98)
                band = (band - p2) / (p98 - p2) * 255.0
                img[:,:,i] = band
                
    img = img.astype(np.uint8)
        
    print("Rendering map...")
    plt.figure(figsize=(10, 10)) # Adjusted size for sharper display
    # Use nearest interpolation to prevent the image from looking smudged/blurry
    plt.imshow(img, interpolation='nearest')
    plt.axis('off')
    
    # Plot a bright red marker (crosshair or dot) at the exact requested location
    plt.plot(target_col, target_row, marker='+', color='red', markersize=20, markeredgewidth=2)
    plt.plot(target_col, target_row, marker='o', color='red', markersize=8, fillstyle='none', markeredgewidth=2)

    # Extract date from SAFE folder name
    date_str = os.path.basename(SAFE_DIR).split('_')[2][:8]
    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    
    # Format the title with the exact coordinates requested
    title_str = (
        f"Sentinel-2 True Color Image ({formatted_date})\n"
        f"Latitude : 36.9000° N (36° 54' N)\n"
        f"Longitude: 7.7667° E (7° 46' E)"
    )
    plt.title(title_str, fontsize=16)
    
    output_png = "annaba_sentinel2_tci.png"
    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Done! Saved map as: {output_png}")

if __name__ == "__main__":
    process_tci()
