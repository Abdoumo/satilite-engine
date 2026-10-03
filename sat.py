import os
import sys
import requests
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from rasterio.warp import transform


# ============================================================
# SETTINGS
# ============================================================

LATITUDE = 36.9000
LONGITUDE = 7.7667

OUTPUT_DIR = "annaba_landsat"

ST_B10_FILE = os.path.join(
    OUTPUT_DIR,
    "ST_B10.tif"
)

TEMP_FILE = os.path.join(
    OUTPUT_DIR,
    "land_surface_temperature_C.tif"
)

MAP_FILE = os.path.join(
    OUTPUT_DIR,
    "land_surface_temperature.png"
)

MAX_SCENES = 50


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# LANDSATLOOK SEARCH API
# ============================================================

SEARCH_URL = (
    "https://cmr.earthdata.nasa.gov/stac/LPCLOUD/search"
)


# ============================================================
# SEARCH LANDSAT
# ============================================================

def search_landsat():

    delta = 0.05

    bbox = [
        LONGITUDE - delta,
        LATITUDE - delta,
        LONGITUDE + delta,
        LATITUDE + delta
    ]

    from datetime import datetime, timedelta
    
    # Get the date range for the last 30 days to get recent images
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    date_range = f"{start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"

    payload = {
        "collections": ["HLSL30.v2.0"],
        "bbox": bbox,
        "datetime": date_range,
        "limit": MAX_SCENES
    }

    print()
    print("Searching Landsat scenes...")

    try:

        response = requests.post(
            SEARCH_URL,
            json=payload,
            timeout=60
        )

    except requests.RequestException as e:

        print()
        print("ERROR connecting to LandsatLook:")
        print(e)

        sys.exit(1)

    print("HTTP:", response.status_code)

    if response.status_code != 200:

        print()
        print("Server response:")
        print(response.text[:2000])

        sys.exit(1)

    try:

        data = response.json()

    except Exception:

        print()
        print("ERROR: Response is not JSON.")
        print(response.text[:2000])

        sys.exit(1)

    features = data.get(
        "features",
        []
    )

    print(
        "Scenes found:",
        len(features)
    )

    if not features:

        print()
        print("No Landsat scenes found.")

        sys.exit(1)

    return features


# ============================================================
# GET CLOUD COVER
# ============================================================

def get_cloud(scene):

    properties = scene.get(
        "properties",
        {}
    )

    cloud = properties.get(
        "eo:cloud_cover"
    )

    if cloud is None:

        cloud = properties.get(
            "landsat:cloud_cover"
        )

    if cloud is None:

        return 999.0

    try:

        return float(cloud)

    except Exception:

        return 999.0


# ============================================================
# GET DATE
# ============================================================

def get_date(scene):

    properties = scene.get(
        "properties",
        {}
    )

    return properties.get(
        "datetime",
        "Unknown"
    )


# ============================================================
# BUILD LANDSATLOOK ST_B10 URL
# ============================================================

def build_st_b10_url(scene_id):

    """
    Example scene:

    LC08_L2SP_193035_20260729_20260801_02_T1_ST

    Becomes:

    https://landsatlook.usgs.gov/data/collection02/
    level-2/standard/oli-tirs/2026/193/035/
    LC08_L2SP_193035_20260729_20260801_02_T1/
    LC08_L2SP_193035_20260729_20260801_02_T1_ST_B10.TIF
    """

    parts = scene_id.split("_")

    if len(parts) < 7:

        return None

    spacecraft = parts[0]

    # Example:
    # L2SP
    processing = parts[1]

    path_row = parts[2]

    date = parts[3]

    processing_date = parts[4]

    collection = parts[5]

    tier_st = parts[6]

    # --------------------------------------------------------
    # Example path/row:
    #
    # 193035
    #
    # path = 193
    # row  = 035
    # --------------------------------------------------------

    path = path_row[:3]
    row = path_row[3:]

    year = date[:4]

    # Remove "_ST" from the scene directory name
    base_scene = (
        f"{spacecraft}_"
        f"{processing}_"
        f"{path_row}_"
        f"{date}_"
        f"{processing_date}_"
        f"{collection}_"
        f"{tier_st}"
    )

    filename = (
        base_scene +
        "_ST_B10.TIF"
    )

    url = (
        "https://landsatlook.usgs.gov/data/"
        "collection02/level-2/standard/oli-tirs/"
        f"{year}/{path}/{row}/"
        f"{base_scene}/"
        f"{filename}"
    )

    return url


# ============================================================
# SELECT SCENE
# ============================================================

def select_scene(features):

    scenes = []

    for scene in features:

        scene_id = scene.get(
            "id"
        )

        if not scene_id:

            continue

        cloud = get_cloud(scene)

        date = get_date(scene)

        # Get B10 asset for surface temperature (ST_B10 equivalent in HLS)
        assets = scene.get("assets", {})
        lwir_asset = assets.get("B10")

        if lwir_asset is None:
            continue
            
        st_url = lwir_asset.get("href")
        
        if st_url is None:
            continue

        scenes.append(
            {
                "id": scene_id,
                "date": date,
                "cloud": cloud,
                "st_url": st_url
            }
        )

    if not scenes:

        print()
        print(
            "No Level-2 Landsat scenes found."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Sort by cloud cover
    # --------------------------------------------------------

    scenes.sort(
        key=lambda x: x["cloud"]
    )

    print()
    print("Available scenes:")
    print("-" * 70)

    for item in scenes[:10]:

        print(
            f"{item['date']}   "
            f"Cloud: {item['cloud']:.2f}%   "
            f"{item['id']}"
        )

    selected = scenes[0]

    print()
    print("=" * 70)
    print("SELECTED SCENE")
    print("=" * 70)

    print(
        "ID:",
        selected["id"]
    )

    print(
        "Date:",
        selected["date"]
    )

    print(
        "Cloud cover:",
        selected["cloud"],
        "%"
    )

    print()
    print("ST_B10:")
    print(selected["st_url"])

    return selected


# ============================================================
# DOWNLOAD ST_B10
# ============================================================

def download_st_b10(url):

    print()
    print("=" * 70)
    print("DOWNLOADING ST_B10")
    print("=" * 70)

    headers = {
        "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/140 Safari/537.36"
    }

    # Load NASA Earthdata token
    credential_file = r"f:\satilites\nasaCredential"
    if os.path.exists(credential_file):
        with open(credential_file, "r") as f:
            cred_text = f.read().strip()
            if cred_text.startswith("token="):
                token = cred_text.split("=", 1)[1]
                headers["Authorization"] = f"Bearer {token}"
            else:
                headers["Authorization"] = f"Bearer {cred_text}"

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=180,
            allow_redirects=True
        )

    except requests.RequestException as e:

        print()
        print("DOWNLOAD ERROR:")
        print(e)

        sys.exit(1)

    print(
        "HTTP status:",
        response.status_code
    )

    print(
        "Content-Type:",
        response.headers.get(
            "Content-Type"
        )
    )

    print(
        "Size:",
        len(response.content),
        "bytes"
    )

    print(
        "Final URL:",
        response.url
    )

    # --------------------------------------------------------
    # HTTP ERROR
    # --------------------------------------------------------

    if response.status_code != 200:

        print()
        print("USGS returned an HTTP error.")

        print()
        print(
            response.text[:2000]
        )

        sys.exit(1)

    # --------------------------------------------------------
    # CHECK TIFF HEADER
    # --------------------------------------------------------

    first_four = response.content[:4]

    print()
    print(
        "First 4 bytes:",
        first_four
    )

    valid_tiff = first_four in (
        b"II*\x00",
        b"MM\x00*"
    )

    if not valid_tiff:

        print()
        print("=" * 70)
        print("THE DOWNLOAD IS NOT A TIFF")
        print("=" * 70)

        debug_file = os.path.join(
            OUTPUT_DIR,
            "USGS_response.bin"
        )

        with open(
            debug_file,
            "wb"
        ) as f:

            f.write(
                response.content
            )

        print()
        print(
            "USGS response saved to:"
        )

        print(
            os.path.abspath(
                debug_file
            )
        )

        # Try to display server response
        try:

            text = response.text

            print()
            print(
                "Server response:"
            )

            print(
                text[:3000]
            )

        except Exception:

            pass

        sys.exit(1)

    # --------------------------------------------------------
    # SAVE TIFF
    # --------------------------------------------------------

    with open(
        ST_B10_FILE,
        "wb"
    ) as f:

        f.write(
            response.content
        )

    print()
    print(
        "Saved:",
        ST_B10_FILE
    )

    print(
        "File size:",
        os.path.getsize(
            ST_B10_FILE
        ),
        "bytes"
    )

    # --------------------------------------------------------
    # VERIFY WITH RASTERIO
    # --------------------------------------------------------

    try:

        with rasterio.open(
            ST_B10_FILE
        ) as src:

            print()
            print(
                "Raster verification successful."
            )

            print(
                "Width :",
                src.width
            )

            print(
                "Height:",
                src.height
            )

            print(
                "CRS   :",
                src.crs
            )

            print(
                "Bands :",
                src.count
            )

    except Exception as e:

        print()
        print(
            "Rasterio cannot open the file:"
        )

        print(e)

        sys.exit(1)


# ============================================================
# COORDINATE -> PIXEL
# ============================================================

def coordinate_to_pixel(
    src,
    latitude,
    longitude
):

    xs, ys = transform(
        "EPSG:4326",
        src.crs,
        [longitude],
        [latitude]
    )

    x = xs[0]
    y = ys[0]

    row, col = src.index(
        x,
        y
    )

    return row, col


# ============================================================
# READ + CONVERT TEMPERATURE
# ============================================================

def process_temperature():

    print()
    print("=" * 70)
    print("PROCESSING LAND SURFACE TEMPERATURE")
    print("=" * 70)

    with rasterio.open(
        ST_B10_FILE
    ) as src:

        print(
            "CRS:",
            src.crs
        )

        print(
            "Resolution:",
            src.res
        )

        dn = src.read(
            1
        ).astype(
            np.float32
        )

        # ----------------------------------------------------
        # HLS Collection 2 B10 scaling
        #
        # Celsius =
        # DN * 0.01
        # ----------------------------------------------------

        temperature_celsius = dn * 0.01

        # Fill pixels
        temperature_celsius[
            dn == 0
        ] = np.nan

        # Remove physically unreasonable values
        temperature_celsius[
            (temperature_celsius < -50) |
            (temperature_celsius > 100)
        ] = np.nan

        # ----------------------------------------------------
        # Requested point
        # ----------------------------------------------------

        row, col = coordinate_to_pixel(
            src,
            LATITUDE,
            LONGITUDE
        )

        print()
        print(
            "Requested coordinate:"
        )

        print(
            "Latitude :",
            LATITUDE
        )

        print(
            "Longitude:",
            LONGITUDE
        )

        print()
        print(
            "Raster pixel:"
        )

        print(
            "Row:",
            row
        )

        print(
            "Column:",
            col
        )

        if (
            row < 0 or
            row >= src.height or
            col < 0 or
            col >= src.width
        ):

            print()
            print(
                "ERROR: Point is outside raster."
            )

            sys.exit(1)

        point_temperature = (
            temperature_celsius[
                row,
                col
            ]
        )

        print()

        if np.isnan(
            point_temperature
        ):

            print(
                "Temperature at point:"
            )

            print(
                "NO VALID DATA"
            )

        else:

            print(
                "================================"
            )

            print(
                f"LAND SURFACE TEMPERATURE: "
                f"{point_temperature:.2f} °C"
            )

            print(
                "================================"
            )

        # ----------------------------------------------------
        # Save temperature GeoTIFF
        # ----------------------------------------------------

        profile = src.profile.copy()

        profile.update(
            dtype="float32",
            count=1,
            compress="deflate",
            nodata=-9999.0
        )

        output = (
            temperature_celsius.copy()
        )

        output[
            np.isnan(output)
        ] = -9999.0

        with rasterio.open(
            TEMP_FILE,
            "w",
            **profile
        ) as dst:

            dst.write(
                output.astype(
                    np.float32
                ),
                1
            )

        print()
        print(
            "Temperature GeoTIFF:"
        )

        print(
            os.path.abspath(
                TEMP_FILE
            )
        )

        return (
            temperature_celsius,
            row,
            col
        )


# ============================================================
# CREATE PNG MAP
# ============================================================

def create_map(
    temperature,
    row,
    col
):

    print()
    print(
        "Creating temperature map..."
    )

    with rasterio.open(
        ST_B10_FILE
    ) as src:

        data = np.ma.masked_invalid(
            temperature
        )

        plt.figure(
            figsize=(12, 9)
        )

        image = plt.imshow(
            data,
            cmap="inferno",
            vmin=10,
            vmax=50,
            interpolation="nearest"
        )

        plt.scatter(
            col,
            row,
            s=150,
            c="cyan",
            edgecolors="white",
            linewidths=2,
            label="Target coordinate"
        )

        colorbar = plt.colorbar(
            image
        )

        colorbar.set_label(
            "Land Surface Temperature (°C)"
        )

        plt.title(
            "Landsat Land Surface Temperature\n"
            f"{LATITUDE:.6f}, "
            f"{LONGITUDE:.6f}"
        )

        plt.xlabel(
            "Pixel column"
        )

        plt.ylabel(
            "Pixel row"
        )

        plt.legend()
        
        # ZOOM IN closely around the target coordinate
        zoom_radius = 60 # 60 pixels = ~1.8km radius
        plt.xlim(col - zoom_radius, col + zoom_radius)
        # Note: image coordinates have 0 at the top, so max is at bottom
        plt.ylim(row + zoom_radius, row - zoom_radius)

        plt.tight_layout()

        plt.savefig(
            MAP_FILE,
            dpi=200,
            bbox_inches="tight"
        )

        plt.close()

    print()
    print(
        "Map saved:"
    )

    print(
        os.path.abspath(
            MAP_FILE
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("LANDSAT SURFACE TEMPERATURE")
    print("=" * 70)

    print()
    print(
        "Latitude :",
        LATITUDE
    )

    print(
        "Longitude:",
        LONGITUDE
    )

    # --------------------------------------------------------
    # 1. Search
    # --------------------------------------------------------

    scenes = search_landsat()

    # --------------------------------------------------------
    # 2. Select scene
    # --------------------------------------------------------

    selected = select_scene(
        scenes
    )

    # --------------------------------------------------------
    # 3. Download ST_B10
    # --------------------------------------------------------

    download_st_b10(
        selected["st_url"]
    )

    # --------------------------------------------------------
    # 4. Convert to temperature
    # --------------------------------------------------------

    temperature, row, col = (
        process_temperature()
    )

    # --------------------------------------------------------
    # 5. Create map
    # --------------------------------------------------------

    create_map(
        temperature,
        row,
        col
    )

    # --------------------------------------------------------
    # 6. Create Normal True Color Map (RGB)
    # --------------------------------------------------------
    download_and_process_rgb(selected["st_url"], row, col)

    # --------------------------------------------------------
    # DONE
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("PROCESS COMPLETE")
    print("=" * 70)

    print()
    print(
        "Output folder:"
    )

    print(
        os.path.abspath(
            OUTPUT_DIR
        )
    )

    print()
    print(
        "Generated files:"
    )

    print(
        "  ST_B10.tif"
    )

    print(
        "  land_surface_temperature_C.tif"
    )

    print(
        "  land_surface_temperature.png"
    )

    print(
        "  land_surface_rgb.png"
    )

def download_and_process_rgb(st_url, row, col):
    print("\n" + "=" * 70)
    print("DOWNLOADING AND PROCESSING NORMAL RGB IMAGE")
    print("=" * 70)
    
    headers = {}
    credential_file = r"f:\satilites\nasaCredential"
    if os.path.exists(credential_file):
        with open(credential_file, "r") as f:
            cred_text = f.read().strip()
            if cred_text.startswith("token="):
                headers["Authorization"] = f"Bearer {cred_text.split('=', 1)[1]}"
            else:
                headers["Authorization"] = f"Bearer {cred_text}"

    bands = {"B04": "Red", "B03": "Green", "B02": "Blue"}
    rgb_data = []
    
    zoom_radius = 60 # 1.8km radius
    
    for band_id in ["B04", "B03", "B02"]:
        band_url = st_url.replace("B10.tif", f"{band_id}.tif")
        band_file = os.path.join(OUTPUT_DIR, f"{band_id}.tif")
        
        if not os.path.exists(band_file):
            print(f"Downloading {bands[band_id]} band ({band_id})...")
            try:
                r = requests.get(band_url, headers=headers, timeout=180, allow_redirects=True)
                r.raise_for_status()
                with open(band_file, "wb") as f:
                    f.write(r.content)
            except Exception as e:
                print(f"Error downloading {band_id}: {e}")
                return
                
        # Read the cropped window
        print(f"Processing {band_id}...")
        with rasterio.open(band_file) as src:
            window = rasterio.windows.Window(col - zoom_radius, row - zoom_radius, zoom_radius * 2, zoom_radius * 2)
            # Clip window to image bounds
            img_window = rasterio.windows.Window(0, 0, src.width, src.height)
            window = window.intersection(img_window)
            
            data = src.read(1, window=window).astype(float)
            rgb_data.append(data)
            
    # Stack and enhance RGB
    print("Rendering True Color Map...")
    rgb_img = np.dstack(rgb_data)
    
    # Apply a 2-98% contrast stretch
    for i in range(3):
        band = rgb_img[:,:,i]
        valid_pixels = band[band > 0]
        if len(valid_pixels) > 0:
            p2, p98 = np.percentile(valid_pixels, (2, 98))
            if p98 > p2:
                band = np.clip(band, p2, p98)
                band = (band - p2) / (p98 - p2) * 255.0
                rgb_img[:,:,i] = band
                
    rgb_img = rgb_img.astype(np.uint8)
    
    plt.figure(figsize=(12, 10))
    plt.imshow(rgb_img, interpolation='nearest')
    plt.plot(zoom_radius, zoom_radius, marker='+', color='red', markersize=20, markeredgewidth=2, label="Target coordinate")
    plt.plot(zoom_radius, zoom_radius, marker='o', color='red', markersize=8, fillstyle='none', markeredgewidth=2)
    plt.title(f"Landsat True Color (RGB)\n{LATITUDE:.6f}, {LONGITUDE:.6f}", fontsize=16)
    plt.axis('off')
    plt.legend()
    plt.tight_layout()
    
    out_map = os.path.join(OUTPUT_DIR, "land_surface_rgb.png")
    plt.savefig(out_map, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"Map saved: {os.path.abspath(out_map)}")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
