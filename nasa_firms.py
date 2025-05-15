import pandas as pd
from dotenv import load_dotenv
import os
from io import StringIO

import leafmap.kepler as leafmap

load_dotenv("local.env")

MAP_KEY = os.getenv("NASA_FIRMS_MAP_KEY")
if MAP_KEY is None:
    raise ValueError("NASA FIRMS MAP_KEY not found in environment variables.")


def get_transaction_count():
    txn_url = f"https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={MAP_KEY}"
    count = 0
    try:
        df = pd.read_json(txn_url,  typ='series')
        count = df['current_transactions']
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return count


def get_wildfires():
    tcount = get_transaction_count()
    print('Our current transaction count is %i' % tcount)

    # Sensor type
    # SENSOR = 'VIIRS_SNPP_NRT'
    SENSOR = 'VIIRS_NOAA20_NRT'
    # SENSOR = 'MODIS_NRT'

    # Date of interest
    # DATE = '2025-04-09'  # Replace with your desired date
    DAYS = '1'

    # Bounding box for Texas
    BBOX = '-106.645646,25.837377,-93.508292,36.500704'

    # Construct the API URL
    url = f'https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SENSOR}/{BBOX}/{DAYS}'

    start_count = get_transaction_count()
    df_area = pd.read_csv(url)
    end_count = get_transaction_count()

    print(df_area.head())

    print('We used %i transactions.' % (end_count-start_count))

    return df_area


def main():
    # Get the wildfires data
    wildfires_data = get_wildfires()

    # generate a Pandas GeoDataFrame with point data based on columns latitude and longitude
    # from the wildfires data
    gdf = pd.DataFrame(wildfires_data, columns=['latitude', 'longitude'])
    gdf['geometry'] = gdf.apply(
        lambda row: f"POINT({row['longitude']} {row['latitude']})", axis=1)
    # gdf = gdf.set_index('geometry')

    hc_long = -100
    hc_lat = 31

    m = leafmap.Map(center=[hc_lat, hc_long], zoom=9,
                    epsg="4326")


if __name__ == "__main__":
    main()
