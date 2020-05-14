# from this area https://www.padmapper.com/apartments/lakewood-ca?box=-119.0400575,33.2569095,-117.1593151,34.4010754117.1593151,34.4010754117.1593151,34.4010754

import requests
import json
import numpy as np
from bs4 import BeautifulSoup as bs
import re


def pin_request(min_lat, min_lng, xz_token=''):

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
              '"minLng":%s,"minPrice":0,"shortTerm": false,"sort":["newest"],"transits":{},"limit":1000}' % (str(min_lat+delta), str(min_lng+delta), str(min_lat), str(min_lng))
    res = requests.request("POST", pin_url, data=payload, headers=headers)
    if res.status_code != 200:
        xz_token = json.loads(res.text)['xz_token']
        return pin_request(min_lat=min_lat, min_lng=min_lng, xz_token=xz_token)
    return res


def apart_request(url):
    apart = requests.get(url=url)
    soup = bs(apart.content, 'html5lib')
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
        description = description_soup.text.strip()
    else:
        description = ''
    agent_soup = soup.find('div', {'class': 'AgentInfo_agent__2qvKf'})
    agent_soup.find('div', {'class': 'row p-no-gutter AgentInfo_header__2mr09'}).decompose()
    agent_gutter = agent_soup.find_all(class_='row p-no-gutter')
    agent_name = agent_gutter[0].text.replace('\xa0', ' ').replace('\n', ' ').strip()
    agent_phone = agent_gutter[1].text.replace('\xa0', ' ').replace('\n', ' ').strip()
    preloaded_state = soup.find('script', text=re.compile("window.__PRELOADED_STATE__"))\
        .text.replace('window.__PRELOADED_STATE__', '').replace('=', '').replace('\xa0', ' ').replace('\n', ' ').strip()[:-1]
    preloaded = "{" + re.search('"entity":{(.*)"favoritesView":', preloaded_state).group(1)[:-1]
    one_line = [price, street, city_state, address, agent_name, agent_phone, description, apartment_amenities, building_amenities]
    floor_plans = json.loads(preloaded)['floorplan_listings']
    bedrooms = soup.find_all(class_='Floorplan_floorplansContainer__2Rtwg')
    for bedroom in bedrooms:
        count_bedroom = bedroom.find(class_='Floorplan_title__179XB').text.strip()
        available_count = bedroom.find(class_='Floorplan_availabilityCount__RvEqU').text.strip()
        bedroom_price_soup = bedroom.find(class_='Floorplan_priceRange__x-BQo')
        if bedroom_price_soup:
            bedroom_price = bedroom.find(class_='Floorplan_priceRange__x-BQo').text.replace('\xa0', ' ').replace('\n', ' ').strip()
        else:
            bedroom_price = ''
        bedroom_box = [count_bedroom, available_count, bedroom_price]
        for floor_plan in floor_plans:
            if 'bedrooms' in floor_plan and str(floor_plan['bedrooms']) in count_bedroom:
                title =floor_plan['title'].replace('\xa0', ' ').replace('\n', ' ').strip()
                if 'square_feet' in floor_plan and floor_plan['square_feet'] is not None:
                    square_feet = str(floor_plan['square_feet']).replace('\xa0', ' ').replace('\n', ' ').strip()
                else:
                    square_feet = ''
                bathroom_count = str(floor_plan['bathrooms']).replace('\xa0', ' ').replace('\n', ' ').strip()
                amenity_tags = floor_plan['amenity_tags']
                amenity_tags_list = []
                if amenity_tags:
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
                print(bedroom_box)
        one_line.append(bedroom_box)
    print(one_line)


def loop_apartments(data):
    base_url = 'https://www.padmapper.com/apartments/long-beach-ca/'
    for leaf in data:
        if 'image_ids' in leaf and 'building_name' in leaf:
            image_name = leaf['building_name']
            image_id = leaf['image_ids'][0]
            image_dict.append({image_name: image_id})
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


if __name__ == '__main__':
    delta = 0.1
    lat_bottom = 33.75
    lat_ceil = 33.83789
    lng_bottom = -118.125
    lng_ceil = -117.94921
    image_dict = []
    count = 0
    pin_url = 'https://www.padmapper.com/api/t/1/pins'

    for lat in np.arange(lat_bottom, lat_ceil, delta):
        for lng in np.arange(lng_bottom, lng_ceil, delta):
            pin_response = pin_request(min_lat=lat, min_lng=lng).text
            lng_lat_json = json.loads(pin_response)
            count += len(lng_lat_json)
            loop_apartments(lng_lat_json)
    print(count)
