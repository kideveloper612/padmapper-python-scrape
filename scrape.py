import requests
import json
import numpy as np
from bs4 import BeautifulSoup
import re
import urllib.request
import csv
import os

csv_header = [['PRICE', 'STREET', 'CITY_STATE', 'ADDRESS', 'AGENT_NAME', 'AGENT_PHONE', 'DESCRIPTION', 'APARTMENT_AMENITIES', 'BUILDING_AMENITIES', 'BEDROOMS']]


def write_direct_csv(lines, filename):
    """
    Write real data on csv file
    :param lines: records for writing
    :param filename: file name for saving
    :return:
    """
    with open('output/%s' % filename, 'a', encoding="utf-8", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerows(lines)
    csv_file.close()


def write_csv(lines, filename):
    """
    Call write_direct_csv function
    :param lines: records for writing
    :param filename: file name for saving
    :return:
    """
    if not os.path.isdir('output'):
        os.mkdir('output')
    if not os.path.isfile('output/%s' % filename):
        write_direct_csv(lines=csv_header, filename=filename)
    write_direct_csv(lines=lines, filename=filename)


def pin_request(min_lat, min_lng, xz_token=''):
    """
    GET initial data for apartments in area
    :param min_lat: Start latitude
    :param min_lng: Start longitude
    :param xz_token: Interval for latitude and longitude
    :return: api data from pin endpoint
    """
    headers = {
        'Content-Type': "application/json",
        'X-Zumper-XZ-Token': xz_token,
        'User-Agent': "PostmanRuntime/7.15.0",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Postman-Token': "83847dcd-d401-454a-b663-282ef18e1e72,05087467-cba5-4082-b386-8feb43a655fa",
        'Host': "www.padmapper.com",
        'accept-encoding': "gzip, deflate",
        'content-length': "165",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
    }
    payload = '{"external": true,"longTerm": true,"maxLat":%s,"maxLng":%s,"minLat":%s,' \
              '"minLng":%s,"minPrice":0,"shortTerm": false,"sort":["newest"],"transits":{},"limit":10000}' % (str(min_lat+delta), str(min_lng+delta), str(min_lat), str(min_lng))
    res = requests.request("POST", pin_url, data=payload, headers=headers)
    if res.status_code != 200:
        xz_token = json.loads(res.text)['xz_token']
        return pin_request(min_lat=min_lat, min_lng=min_lng, xz_token=xz_token)
    return res


def apart_request(url):
    """
    Get all data for a url
    :param url: URL for scrapping one page
    :return:
    """
    apart = requests.get(url=url)
    soup = BeautifulSoup(apart.content, 'html5lib')
    price_soup = soup.find(class_='FullDetail_price___O0l5')
    if price_soup:
        price = soup.find(class_='FullDetail_price___O0l5').text.strip()
    else:
        price = ''
    street_soup = soup.find(class_='FullDetail_street__zq-XK')
    if street_soup:
        street_soup_parent = street_soup.parent
        street = street_soup.text.replace('\xa0', ' ').replace('\n', ' ').strip()
        street_soup.decompose()
        city_state = street_soup_parent.text.replace('\xa0', ' ').replace('\n', ' ').strip()
    else:
        street, city_state = '', ''
    address_soup = soup.find(class_='SummaryTable_header__2gj_9')
    if address_soup:
        address = soup.find(class_='SummaryTable_header__2gj_9').next_sibling.text.replace('\xa0', ' ').replace('\n', ' ').strip()
    else:
        address = ''
    apartment_amenities, building_amenities = [], []
    gutters = soup.findAll(attrs={'class': 'row p-no-gutter undefined'})
    for gutter in gutters:
        key = gutter.find(attrs={'class': 'Amenities_header__D_u2k'})
        if key:
            if 'Apartment' in key.text:
                apartment_amenities_soup = gutter.findAll(attrs={'class': 'Amenities_amenityContainer__3G3vu'})
                for apart in apartment_amenities_soup:
                    apartment_amenities.append(apart.text.replace('\xa0', ' ').replace('\n', ' ').strip())
            elif 'Building' in key.text:
                building_amenities_soup = gutter.findAll('div', {'class': 'Amenities_amenityContainer__3G3vu'})
                for build in building_amenities_soup:
                    building_amenities.append(build.text.replace('\xa0', ' ').replace('\n', ' ').strip())
    description_soup = soup.find('div', {'class': 'Description_text__13mnt'})
    if description_soup:
        description = description_soup.text.replace('\xa0', ' ').replace('\n', ' ').strip()
    else:
        description = ''
    agent_soup = soup.find('div', {'class': 'AgentInfo_agent__2qvKf'})
    if agent_soup:
        if agent_soup.find('div', {'class': 'row p-no-gutter AgentInfo_header__2mr09'}):
            agent_soup.find('div', {'class': 'row p-no-gutter AgentInfo_header__2mr09'}).decompose()
        agent_gutter = agent_soup.find_all(class_='row p-no-gutter')
        if len(agent_gutter) == 2:
            agent_name = agent_gutter[0].text.replace('\xa0', ' ').replace('\n', ' ').strip()
            agent_phone = agent_gutter[1].text.replace('\xa0', ' ').replace('\n', ' ').strip()
    preloaded_state = soup.find('script', text=re.compile("window.__PRELOADED_STATE__"))\
        .text.replace('window.__PRELOADED_STATE__', '').replace('=', '').replace('\xa0', ' ').replace('\n', ' ').strip()[:-1]
    preloaded = "{" + re.search('"entity":{(.*)"favoritesView":', preloaded_state).group(1)[:-1]
    one_line = [price, street, city_state, address, agent_name, agent_phone, description, apartment_amenities, building_amenities]
    bedrooms = soup.find_all(class_='Floorplan_floorplansContainer__2Rtwg')
    for bedroom in bedrooms:
        count_bedroom = bedroom.find(class_='Floorplan_title__179XB').text.replace('\xa0', ' ').replace('\n', ' ').strip()
        available_count = bedroom.find(class_='Floorplan_availabilityCount__RvEqU').text.replace('\xa0', ' ').replace('\n', ' ').strip()
        bedroom_price_soup = bedroom.find(class_='Floorplan_priceRange__x-BQo')
        if bedroom_price_soup:
            bedroom_price = bedroom.find(class_='Floorplan_priceRange__x-BQo').text.replace('\xa0', ' ').replace('\n', ' ').strip()
        else:
            bedroom_price = ''
        bedroom_box = [count_bedroom, available_count, bedroom_price]
        if 'floorplan_listings' in json.loads(preloaded):
            floor_plans = json.loads(preloaded)['floorplan_listings']
            for floor_plan in floor_plans:
                if 'bedrooms' in floor_plan and str(floor_plan['bedrooms']) in count_bedroom:
                    if 'title' in floor_plan and floor_plan['title'] is not None:
                        title =floor_plan['title'].replace('\xa0', ' ').replace('\n', ' ').strip()
                    else:
                        title = ''
                    if 'square_feet' in floor_plan and floor_plan['square_feet'] is not None:
                        square_feet = str(floor_plan['square_feet']).replace('\xa0', ' ').replace('\n', ' ').strip()
                    else:
                        square_feet = ''
                    if 'bathrooms' in floor_plan and floor_plan['bathrooms'] is not None:
                        bathroom_count = str(floor_plan['bathrooms']).replace('\xa0', ' ').replace('\n', ' ').strip()
                    else:
                        bathroom_count = ''
                    amenity_tags_list = []
                    if 'amenity_tags' in floor_plan and floor_plan['amenity_tags'] is not None:
                        amenity_tags = floor_plan['amenity_tags']
                        for ament in amenity_tags:
                            amenity_tags_list.append(ament.replace('\xa0', ' ').replace('\n', ' '))
                    min_price = str(floor_plan['min_price']).strip()
                    max_price = str(floor_plan['max_price']).strip()
                    if min_price == '0':
                        avaiable_price = max_price
                    elif max_price == '0':
                        avaiable_price = min_price
                    else:
                        avaiable_price = min_price + '~' + max_price
                    bedroom_box.append([title, square_feet, bathroom_count, amenity_tags_list, avaiable_price])
        one_line.append(bedroom_box)
    print(one_line)
    write_csv(lines=[one_line], filename=file_name)


def loop_apartments(data):
    """
    Loop function with response data of pin request
    :param data: Json data from pin request
    :return:
    """
    base_url = 'https://www.padmapper.com/apartments/long-beach-ca/'
    for leaf in data:
        if 'image_ids' in leaf and 'building_name' in leaf:
            image_name = leaf['building_name']
            if leaf['image_ids'] is not None:
                image_id = leaf['image_ids'][0]
                if image_name is not None:
                    image_dict.append({
                        'image_name': image_name + '.jpg',
                        'image_id': image_id
                    })
                else:
                    continue
        if 'pb_id' in leaf and leaf['pb_id'] is not None:
            url = '{}b-p{}'.format(base_url, leaf['pb_id'])
        elif 'pl_id' in leaf and leaf['pl_id'] is not None:
            url = '{}l-{}p'.format(base_url, leaf['pl_id'])
        elif 'listing_id' in leaf and leaf['listing_id'] is not None:
            url = '{}l-{}'.format(base_url, leaf['listing_id'])
        else:
            continue
        print(url)
        apart_request(url=url)


def download_image(url, name):
    """
    Download image from url using urllib
    :param url: image link
    :param name: name of image for downloading
    :return:
    """
    print(url)
    if not os.path.isdir(image_directory):
        os.mkdir(image_directory)
    urllib.request.urlretrieve(url, '{}/{}'.format(image_directory, name))


if __name__ == '__main__':
    """
        Main Thread for scrapping apartments"""
    print('------------ Start ------------')
    delta = 0.1  # Interval degree for latitude and longitude
    lat_bottom = 33.75  # Latitude for start point of area you want
    lat_ceil = 33.83789  # Latitude for end point of area you want
    lng_bottom = -118.125  # Longitude for start point of area you want
    lng_ceil = -117.94921  # Longitude for end point of area you want
    image_dict = []
    image_directory = 'Image'
    file_name = 'result.csv'
    pin_url = 'https://www.padmapper.com/api/t/1/pins'

    for lat in np.arange(lat_bottom, lat_ceil, delta):
        for lng in np.arange(lng_bottom, lng_ceil, delta):
            pin_response = pin_request(min_lat=lat, min_lng=lng).text
            lng_lat_json = json.loads(pin_response)
            loop_apartments(lng_lat_json)
    print('======================= Start Downloading =======================')
    for record in image_dict:
        image_url = 'https://img.zumpercdn.com/%s/1280x960' % record['image_id']
        image_name = record['image_name']
        download_image(url=image_url, name=image_name)
    print('------------ The End ------------')
