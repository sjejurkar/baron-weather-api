# coding: utf-8

import base64
import datetime
import hmac
from io import StringIO
import time
import urllib.request
import requests
from dotenv import load_dotenv
import os
from hashlib import sha1 as sha
import json


load_dotenv("local.env")


host = "http://api.velocityweather.com/v1"
access_key = os.getenv("BARON_KEY")
if access_key is None:
    raise ValueError("Missing BARON_KEY in local.env file")
access_key_secret = os.getenv("BARON_SECRET")
if access_key_secret is None:
    raise ValueError("Missing BARON_SECRET in local.env file")


def sign_old(string_to_sign, secret):
    """ Returns the signature for string_to_sign
    """
    signature_bytes = base64.urlsafe_b64encode(
        hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), sha).digest())
    signature = signature_bytes.decode('utf-8')

    return signature.replace('/', '_').replace('+', '-').rstrip('=')


def sign(string_to_sign, secret):
    hmac_sha1 = hmac.new(
        # Convert secret to bytes using UTF-8
        secret.encode('utf-8'),
        # Convert input string to bytes using UTF-8
        string_to_sign.encode('utf-8'),
        sha                        # Use SHA1 hash algorithm
    )

    # Get the binary digest
    hmac_digest = hmac_sha1.digest()

    # Encode to base64
    base64_encoded = base64.b64encode(hmac_digest).decode('utf-8')

    # Replace characters to make URL safe
    signature = base64_encoded.replace('/', '_').replace('+', '-')

    return signature


def sign_request(url, key, secret):
    """ Returns signed url
    """

    ts = str(int(time.time()))
    sig = sign(key + ":" + ts, secret)
    q = '?' if url.find("?") == -1 else '&'
    url += "%ssig=%s&ts=%s" % (q, sig, ts)
    return url


def request_marine_zone_forecast_all():

    uri = "/reports/forecast/marine/us/all.json"
    url = "%s/%s%s" % (host, access_key, uri)
    return sign_request(url, access_key, access_key_secret)


def request_pointquery_nws_watches_warning_all():

    uri = "/reports/alert/all-poly/point.json?lat=29.70&lon=-80.41"
    url = "%s/%s%s" % (host, access_key, uri)
    return sign_request(url, access_key, access_key_secret)


def request_lightning_count():

    uri = "/reports/lightning/count/region.json?w_lon=-160&e_lon=0&n_lat=-2&s_lat=-70"
    url = "%s/%s%s" % (host, access_key, uri)
    return sign_request(url, access_key, access_key_secret)


def request_storm_vector(sitecode):

    uri = "/reports/stormvector/station/%s.json" % (sitecode)
    url = "%s/%s%s" % (host, access_key, uri)
    return sign_request(url, access_key, access_key_secret)


def request_geocodeip():
    uri = "/reports/geocode/ipaddress.json"
    url = "%s/%s%s" % (host, access_key, uri)
    url = sign_request(url, access_key, access_key_secret)
    return sign_request(url, access_key, access_key_secret)


def request_geocodecity(cityname):
    uri = "/reports/geocode/city.json?name=%s" % (cityname)
    url = "%s/%s%s" % (host, access_key, uri)
    url = sign_request(url, access_key, access_key_secret)
    return sign_request(url, access_key, access_key_secret)


def request_metar_nearest(lat, lon):

    uri = "/reports/metar/nearest.json?lat=%s&lon=%s&within_radius=500&max_age=75" % (
        lat, lon)
    url = "%s/%s%s" % (host, access_key, uri)
    url = sign_request(url, access_key, access_key_secret)
    return sign_request(url, access_key, access_key_secret)


def request_metar(station_id):

    uri = "/reports/metar/station/%s.json" % station_id
    url = "%s/%s%s" % (host, access_key, uri)
    return sign_request(url, access_key, access_key_secret)


def request_ndfd_hourly(lat, lon, utc_datetime):

    datetime_str = utc_datetime.replace(microsecond=0).isoformat() + 'Z'
    uri = "/reports/ndfd/hourly.json?lat=%s&lon=%s&utc=%s" % (
        lat, lon, datetime_str)
    url = "%s/%s%s" % (host, access_key, uri)
    return sign_request(url, access_key, access_key_secret)


def request_tile(product, product_config, z, x, y):
    url = "%s/%s/meta/tiles/product-instances/%s/%s" % (
        host, access_key, product, product_config)
    meta_url = sign_request(url, access_key, access_key_secret)

    response = urllib.request.urlopen(meta_url).read()
    data = json.loads(response)
    if not data:
        return

    meta_date = data[0]['time']
    url = "%s/%s/tms/1.0.0/%s+%s+%s/%d/%d/%d.png" % (
        host, access_key, product, product_config, meta_date, z, x, y)
    return sign_request(url, access_key, access_key_secret)


def point_query(product, product_config, lon, lat):
    """
    For the given product and product_config, queries the most recent 'time'
    (and most recent 'valid_time' if it's a forecast product).
    """

    # Get the list of product instances.
    url = '{host}/{key}/meta/tiles/product-instances/{product}/{product_config}'.format(
        host=host,
        key=access_key,
        product=product,
        product_config=product_config
    )
    # request = urllib.Request(sign_request(url, access_key, access_key_secret))
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print('HTTP status code:', e.code)
        print('content:')
        print(e.read())
        return
    assert response.code == 200
    data = json.loads(response.read())

    # Select the most recent product instance for this example.
    product_instance = data[0]

    # Query our lon, lat point.
    url = '{host}/{key}/point/{product}/{product_config}/{product_instance}.{file_type}?lon={lon}&lat={lat}'.format(
        host=host,
        key=access_key,
        product=product,
        product_config=product_config,
        product_instance=product_instance['time'],
        file_type='json',
        lon=lon,
        lat=lat
    )

    try:
        # If it's a forecast product, it will have valid_times. The latest one is used for this example.
        url += '&valid_time={}'.format(product_instance['valid_times'][0])
    except KeyError:
        pass

    # request = urllib.Request(sign_request(url, access_key, access_key_secret))
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print('HTTP status code:', e.code)
        print('content:')
        print(e.read())
        return
    assert response.code == 200

    content = response.read()
    charset = response.headers.getparam('charset')
    if charset:
        content = content.decode(charset)
    content = json.loads(content)

    print('headers:')
    print(json.dumps(response.headers.dict, indent=4, sort_keys=True))
    print('content:')
    print(json.dumps(content, indent=4, sort_keys=True, ensure_ascii=False))


def request_wms(product, product_config, image_size_in_pixels, image_bounds):
    """
    Requests a WMS image and saves it to disk in the current directory.
    @param product: The product code, such as 'C39-0x0302-0'
    @param product_config: The product configuration, such as 'Standard-Mercator' or 'Standard-Geodetic'.
    @param image_size_in_pixels: The image width and height in pixels, such as [1024, 1024].
    @param image_bounds: The bounds of the image. This value has several caveats, depending
        on the projection being requested.
        A. If requesting a Mercator (EPSG:3857) image:
            1. The coordinates must be in meters.
            2. The WMS 1.3.0 spec requires the coordinates be in this order [xmin, ymin, xmax, ymax]
            3. As an example, to request the whole world, you would use [-20037508.342789244, -20037508.342789244, 20037508.342789244, 20037508.342789244].
               Because this projection stretches to infinity as you approach the poles, the ymin and ymax values
               are clipped to the equivalent of -85.05112877980659 and 85.05112877980659 latitude, not -90 and 90 latitude,
               resulting in a perfect square of projected meters.
        B. If requesting a Geodetic (EPSG:4326) image:
            1. The coordinates must be in decimal degrees.
            2. The WMS 1.3.0 spec requires the coordinates be in this order [lat_min, lon_min, lat_max, lon_max].
            3. As an example, to request the whole world, you would use [-90, -180, 90, 180].

    Theoretically it is possible to request any arbitrary combination of image_size_in_pixels and image_bounds,
    but this is not advisable and is actually discouraged. It is expected that the proportion you use for
    image_width_in_pixels/image_height_in_pixels is equal to image_width_bounds/image_height_bounds. If this is
    not the case, you have most likely done some incorrect calculations. It will result in a distorted (stretched
    or squished) image that is incorrect for the requested projection. One fairly obvious sign that your
    proportions don't match up correctly is that the image you receive from your WMS request will have no
    smoothing (interpolation), resulting in jaggy or pixelated data.
    """

    # We're using the TMS-style product instances API here for simplicity. If you
    # are using a standards-compliant WMS client, do note that we also provide a
    # WMS-style API to retrieve product instances which may be more suitable to your
    # needs. See our documentation for details.

    # For this example, we use the optional parameter "page_size" to limit the
    # list of product instances to the most recent instance.
    meta_url = '{}/{}/meta/tiles/product-instances/{}/{}?page_size=1'.format(
        host, access_key, product, product_config)
    meta_url = sign_request(meta_url, access_key, access_key_secret)

    # request = urllib.Request(meta_url)
    try:
        response = urllib.request.urlopen(meta_url)
    except urllib.error.HTTPError as e:
        print('HTTP status code:', e.code)
        print('content:')
        print(e.read())
        return
    assert response.code == 200

    # Decode the product instance response and get the most recent product instance time,
    # to be used in the WMS image request.
    content = json.loads(response.read())
    product_instance_time = content[0]['time']

    # WMS uses EPSG codes, while our product configuration code uses 'Geodetic' or
    # 'Mercator'. We map between the two here to prepare for the WMS CRS query parameter.
    epsg_code = 'EPSG:4326' if product_config.endswith(
        '-Geodetic') else 'EPSG:3857'

    # Convert the image bounds to a comma-separated string.
    image_bounds = ','.join(str(x) for x in image_bounds)

    wms_url = '{}/{}/wms/{}/{}?VERSION=1.3.0&SERVICE=WMS&REQUEST=GetMap&CRS={}&LAYERS={}&BBOX={}&WIDTH={}&HEIGHT={}'.format(
        host,
        access_key,
        product,
        product_config,
        epsg_code,
        product_instance_time,
        image_bounds,
        image_size_in_pixels[0],
        image_size_in_pixels[1]
    )
    wms_url = sign_request(wms_url, access_key, access_key_secret)
    print(wms_url)

    # request = urllib.Request(wms_url)
    try:
        response = urllib.request.urlopen(wms_url)
    except urllib.error.HTTPError as e:
        print('HTTP status code:', e.code)
        print('content:')
        print(e.read())
        return
    assert response.code == 200

    content = response.read()
    filename = './wms_img_{}_{}.png'.format(product, product_config)
    print('Read {} bytes, saving as {}'.format(len(content), filename))
    with open(filename, 'wb') as f:
        f.write(content)


def point_query_region(product, product_config, region_bounds):
    """
    Queries a specific region for weather data using a given product and configuration.

    This function retrieves weather data for a specified region by making two API requests:
    1. Fetches metadata to determine the most recent product instance time.
    2. Uses the product instance time to query the weather data for the specified region.

    Args:
        product (str): The product identifier for the weather data.
        product_config (str): The configuration identifier for the product.
        region_bounds (list or tuple): A list or tuple containing the bounding coordinates of the region
            in the format [west_longitude, north_latitude, east_longitude, south_latitude].

    Returns:
        None: The function prints the response headers and content in JSON format.

    Raises:
        AssertionError: If the response status code is not 200.
        requests.exceptions.RequestException: If there is an issue with the HTTP request.

    Notes:
        - The function assumes the existence of `host`, `access_key`, and `access_key_secret` variables
          for API authentication.
        - The `sign_request` function is used to sign the API requests.
        - The response content is printed in a formatted JSON structure for readability.
    """
    meta_url = f'{host}/{access_key}/meta/tiles/product-instances/{product}/{product_config}?page_size=1'
    meta_url = sign_request(meta_url, access_key, access_key_secret)

    try:
        response = requests.get(meta_url)
    except requests.exceptions.RequestException as e:
        print('Request failed:', e)
        return
    assert response.status_code == 200

    # Decode the product instance response and get the most recent product instance time,
    # to be used in the WMS image request.
    content = json.loads(response.text)
    product_instance_time = content[0]['time']

    w_lon = region_bounds[0]
    n_lat = region_bounds[1]
    e_lon = region_bounds[2]
    s_lat = region_bounds[3]
    query_region = f'w_lon={w_lon}&n_lat={n_lat}&e_lon={e_lon}&s_lat={s_lat}'

    url = f'{host}/{access_key}/point/region/{product}/{product_config}/{product_instance_time}.json?{query_region}'
    url = sign_request(url, access_key, access_key_secret)

    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip'
    }

    try:
        response = requests.get(url, headers=headers)
        print(f'Response status code: {response.status_code}')
        print(f'Response headers: {response.headers}')
        print(f'Response content: {response.content}')
    except requests.exceptions.RequestException as e:
        print('Request failed:', e)
        return
    assert response.status_code == 200

    content = json.loads(response.text)

    print('headers:')
    print(json.dumps(str(response.headers), indent=4, sort_keys=True))
    print('content:')
    print(json.dumps(content, indent=4, sort_keys=True, ensure_ascii=False))


def main():
    texas_bound_box = [-106.645646, 36.500704, -93.508292, 25.837164]
    arkansas_bound_box = [-94.724121, 32.512896, -89.428711, 36.576877]
    usa_bound_box = [-125.859375, 25.618963, -63.193359, 49.378416]
    temp_bound_box = [-106.645646, 36.500704, -105.808292, 35.837164]
    whole_world_bound_box = [-90, -180, 90, 180]
    tx_panhandle_bound_box = [-103.05, 34.65, -99.99, 36.53]

    print("WMS...2: Fire Tracker US")
    request_wms('fire-tracker-us', 'Standard-Geodetic',
                [2048, 1024], tx_panhandle_bound_box)

    # print("Point Query Region...1: Flash Flood Risk")
    # point_query_region('fire-hotspot-us', 'Standard-Geodetic', temp_bound_box)

    exit(0)

    # print("WMS...0: Debug Tiles")
    # request_wms('debug-tiles', 'Standard-Geodetic',
    #             [2048, 1024], texas_bound_box)

    # print("*** request point query ***")
    # point_query('C09-0x0331-0', 'Standard-Mercator', -86, 34)
    # print
    # exit(0)

    print("WMS...1: Standard Radar")
    # Request the whole world in the EPSG:4326 projection. Note that the proportions for
    # the image size in pixels and the image bounds are identical (2:1).

    # Standard Radar (https://developer.baronweather.com/products/radar-imagery/#standard-radar-2-5-mins)
    request_wms('C39-0x0302-0', 'Standard-Geodetic',
                [2048, 1024], texas_bound_box)

    print("Point Query Region...1: Standard Radar")
    point_query_region('C39-0x0302-0', 'Standard-Geodetic', temp_bound_box)

    print("WMS...1-1: Standard Radar")
    # Request the whole world in the EPSG:3857 projection. Note that the proportions for
    # the image size in pixels and the image bounds are identical (1:1).
    request_wms('C39-0x0302-0', 'Standard-Mercator',
                [2048, 2048], [-20037508.342789244, -20037508.342789244, 20037508.342789244, 20037508.342789244])

    print("WMS...2: Fire Tracker US")
    request_wms('fire-tracker-us', 'Standard-Geodetic',
                [2048, 1024], texas_bound_box)

    # request_wms('C39-0x0355-0', 'Standard-Geodetic',
    #             [2048, 1024], [-90, -180, 90, 180])

    url = request_metar_nearest("38", "-96")
    print("*** request METAR nearest ***")
    print(url)
    print(urllib.request.urlopen(url).read())
    print

    url = request_metar("egll")
    print("*** request METAR ***")
    print(url)
    print(urllib.request.urlopen(url).read())
    print()

    exit(0)

    url = request_lightning_count()
    print("*** lightning count ***")
    print(url)
    print(urllib.request.urlopen(url).read())
    print()

    forecast_time = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    url = request_ndfd_hourly(34.730301, -86.586098, forecast_time)
    print("*** request NDFD hourly ***")
    print(url)
    print(urllib.request.urlopen(url).read())
    print()

    url = request_tile("C39-0x0302-0", "Standard-Mercator", 1, 0, 1)
    print("*** request tile ***")
    print(url)
    print('Tile is %d bytes' % len(urllib.request.urlopen(url).read()))
    print

    url = request_storm_vector("mhx")
    print("*** request storm vectors ***")
    print(url)
    print('JSON for storm vectors is %d bytes' %
          len(urllib.request.urlopen(url).read()))
    print()

    url = request_geocodeip()
    print("*** geocode IP address ***")
    print(url)
    print(urllib.request.urlopen(url).read())
    print()

    url = request_geocodecity("Hunt")
    print("*** geocode city name ***")
    print(url)
    print(urllib.request.urlopen(url).read())
    print()

    url = request_marine_zone_forecast_all()
    print("*** Marine zone forecast -- all ***")
    print(url)
    print(urllib.request.urlopen(url).read())
    print


if __name__ == '__main__':
    main()
