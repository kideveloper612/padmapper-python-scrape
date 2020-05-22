import requests
import json
import numpy as np
from bs4 import BeautifulSoup
import re
import urllib.request
import csv
import os
import random
import string
from datetime import datetime
csv_header = [['ADDRESS', 'CITY', 'STATE', 'LOW RANGE RENT', 'HIGH RANGE RENT', 'BEDS COUNT', 'BATHS COUNT', 'SQUARE FOOTAGE', 'PROPERTY NAME', 'UNIT DESCRIPTION', 'APARTMENT AMENITIES', 'BUILDING AMENITIES', 'AGENT NAME', 'AGENT PHONE', 'IMAGE NAME', 'DATE', 'REFERRAL LINK']]


def write_direct_csv(lines, filename):
    """
    Write real data on csv file
    :param lines: records for writing
    :param filename: file name for saving
    :return:
    """
    with open(filename, 'a', encoding="utf-8", newline='') as csv_file:
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
    if not os.path.isfile(filename):
        write_direct_csv(lines=csv_header, filename=filename)
    write_direct_csv(lines=lines, filename=filename)


def read_progress():
    global file_name
    if not os.path.isfile(file_name):
        return []
    file = open(file_name, 'r', encoding='utf-8')
    rows = list(csv.reader(file))
    file.close()
    result = []
    for r in rows:
        if len(r) > 16 and 'https' in r[16]:
            result.append(r[16])
    return result


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


def apart_request(url, image_name):
    """
    Get all data for a url
    :param url: URL for scrapping one page
    :return: Boolean variable if image
    """
    global date
    apart = requests.get(url=url)
    soup = BeautifulSoup(apart.content, 'html5lib')
    price_soup = soup.find(class_='FullDetail_price___O0l5')
    city, state, min_price, max_price = '', '', '', ''
    dup_check = []
    if price_soup:
        price = soup.find(class_='FullDetail_price___O0l5').text
        price_split = price.split('-')
        if len(price_split) == 2:
            min_price = price_split[0].strip()
            max_price = price_split[1].strip()
        elif len(price_split) == 1:
            max_price, min_price = price_split[0].strip(), price_split[0].strip()
    else:
        min_price, max_price = 'Unknown', 'Unknown'
    street_soup = soup.find(class_='FullDetail_street__zq-XK')
    if street_soup:
        street_soup_parent = street_soup.parent
        street = street_soup.text.replace('\xa0', ' ').replace('\n', ' ').strip()
        street_soup.decompose()
        property_name = street_soup_parent.text.replace('\xa0', ' ').replace('\n', ' ').strip()
    else:
        street, property_name = '', ''
    address_soup = soup.find(class_='SummaryTable_header__2gj_9', text=re.compile('Address'))
    if address_soup:
        address_c_s = address_soup.next_sibling.text.replace('\xa0', ' ').replace('\n', ' ').split(',')
        if len(address_c_s) == 3:
            address = address_c_s[0].strip()
            city = address_c_s[1].strip()
            state = address_c_s[2].strip()
        elif len(address_c_s) == 2:
            address = address_c_s[0].strip()
            state = address_c_s[1].strip()
        elif len(address_c_s) == 1:
            address = address_c_s[0].strip()
        else:
            address, city, state = '', '', ''
    else:
        address, city, state = '', '', ''
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
        else:
            agent_name, agent_phone = '', ''
    else:
        agent_name, agent_phone = '', ''
    preloaded_state = soup.find('script', text=re.compile("window.__PRELOADED_STATE__"))\
        .text.replace('window.__PRELOADED_STATE__', '').replace('=', '').replace('\xa0', ' ').replace('\n', ' ').strip()[:-1]
    preloaded = "{" + re.search('"entity":{(.*)"favoritesView":', preloaded_state).group(1)[:-1]
    bedrooms = soup.find_all(class_='Floorplan_floorplansContainer__2Rtwg')
    if bedrooms:
        for bedroom in bedrooms:
            if bedroom.find(class_='Floorplan_title__179XB'):
                count_bedroom = bedroom.find(class_='Floorplan_title__179XB').text.replace('\xa0', ' ').replace('\n', ' ').strip()
            else:
                count_bedroom = ''
            if bedroom.find(class_='Floorplan_availabilityCount__RvEqU'):
                available_count = bedroom.find(class_='Floorplan_availabilityCount__RvEqU').text.replace('\xa0', ' ').replace('\n', ' ').strip()
            else:
                available_count = ''
            bedroom_price_soup = bedroom.find(class_='Floorplan_priceRange__x-BQo')
            if bedroom_price_soup:
                bedroom_price = bedroom.find(class_='Floorplan_priceRange__x-BQo').text.replace('\xa0', ' ').replace('\n', ' ').strip()
            else:
                bedroom_price = ''
            if 'floorplan_listings' in json.loads(preloaded):
                floor_plans = json.loads(preloaded)['floorplan_listings']
                for floor_plan in floor_plans:
                    if 'is_messageable' in floor_plan and floor_plan['is_messageable'] is False:
                        continue
                    if 'bedrooms' in floor_plan:
                        if 'title' in floor_plan and floor_plan['title'] is not None:
                            title =floor_plan['title'].replace('\xa0', ' ').replace('\n', ' ').strip()
                        else:
                            title = ''
                        if 'square_feet' in floor_plan and floor_plan['square_feet'] is not None:
                            square_feet = str(floor_plan['square_feet']).replace('\xa0', ' ').replace('\n', ' ').strip()
                            if square_feet == '0':
                                square_feet = ''
                        else:
                            square_feet = ''
                        if 'bathrooms' in floor_plan and floor_plan['bathrooms'] is not None:
                            bathroom_count = str(floor_plan['bathrooms']).replace('\xa0', ' ').replace('\n', ' ').strip() + ' Bathrooms'
                        else:
                            bathroom_count = ''
                        if 'half_bathrooms' in floor_plan and str(floor_plan['half_bathrooms']).strip() != '0':
                            half_bathrooms = ', {} Half Bathrooms'.format(str(floor_plan['half_bathrooms']).strip())
                            bathroom_count += half_bathrooms
                        amenity_tags_list = []
                        if 'amenity_tags' in floor_plan and floor_plan['amenity_tags'] is not None:
                            amenity_tags = floor_plan['amenity_tags']
                            for ament in amenity_tags:
                                amenity_tags_list.append(ament.replace('\xa0', ' ').replace('\n', ' '))
                        min_price = str(floor_plan['min_price']).strip()
                        max_price = str(floor_plan['max_price']).strip()
                        if min_price == '0':
                            min_price = max_price
                        elif max_price == '0':
                            max_price = min_price
                        if min_price == '0' and max_price == '0':
                            continue
                        min_price = '$' + min_price
                        max_price = '$' + max_price
                        one_line = [address, city, state, min_price, max_price, count_bedroom, bathroom_count, square_feet, property_name, description, apartment_amenities, building_amenities, agent_name, agent_phone, image_name, date, url]
                        if one_line not in dup_check:
                            dup_check.append(one_line)
                            print(one_line)
                            write_csv(lines=[one_line], filename=file_name)
    elif soup.find(attrs={'class': 'Description_feature__39cQ0 Description_standalone__1VmC2'}):
        bedroom_card_soup = soup.find(class_='SummaryTable_header__2gj_9', text=re.compile('Bedrooms'))
        if bedroom_card_soup:
            bedroom_card_count = bedroom_card_soup.next_sibling.text.replace('\xa0', ' ').replace('\n', ' ')
        else:
            bedroom_card_count = ''
        bathroom_card_soup = soup.find(class_='SummaryTable_header__2gj_9', text=re.compile('Bathrooms'))
        if bathroom_card_soup:
            bathroom_card_count = bathroom_card_soup.next_sibling.text.replace('\xa0', ' ').replace('\n', ' ')
        else:
            bathroom_card_count = ''
        square_card_soup = soup.find(class_='SummaryTable_header__2gj_9', text=re.compile('Square'))
        if square_card_soup:
            square_card_count = square_card_soup.next_sibling.text.replace('\xa0', ' ').replace('\n', ' ').replace('—', '')
        else:
            square_card_count = ''
        one_line = [address, city, state, min_price, max_price, bedroom_card_count, bathroom_card_count, square_card_count, property_name, description, apartment_amenities, building_amenities, agent_name, agent_phone, image_name, date, url]
        if one_line not in dup_check:
            dup_check.append(one_line)
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
        image_name = 'None'
        if 'image_ids' in leaf and 'address' in leaf:
            image_name = leaf['address']
            if leaf['image_ids'] is not None and len(leaf['image_ids']) > 0:
                image_id = leaf['image_ids'][0]
                if image_name is not None:
                    if '.jpg' in image_name:
                        image_name = image_name.replace('/', '_')
                    else:
                        image_name = image_name.replace('/', '_').replace('.', '') + '.jpg'
                else:
                    image_name = '%s.jpg' % ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        if 'pb_id' in leaf and leaf['pb_id'] is not None:
            url = '{}b-p{}'.format(base_url, leaf['pb_id'])
        elif 'pl_id' in leaf and leaf['pl_id'] is not None:
            url = '{}l-{}p'.format(base_url, leaf['pl_id'])
        elif 'listing_id' in leaf and leaf['listing_id'] is not None:
            url = '{}l-{}'.format(base_url, leaf['listing_id'])
        else:
            continue
        print(url)
        if url in progress_urls:
            print('Done already!')
            continue
        apart_request(url=url, image_name=image_name)
        download_image(image_id=image_id, name=image_name)


def download_image(image_id, name):
    """
    Download image from url using urllib
    :param url: image link
    :param name: name of image for downloading
    :return:
    """
    image_url = 'https://img.zumpercdn.com/%s/1280x960' % image_id
    print(image_url)
    if not os.path.isdir(image_directory):
        os.mkdir(image_directory)
    try:
        if '.jpg' not in name:
            name += '.jpg'
        urllib.request.urlretrieve(image_url, '{}/{}'.format(image_directory, name))
    except Exception as e:
        print(e)


if __name__ == '__main__':
    """
        Main Thread for scrapping apartments"""
    print('------------ Start ------------')
    delta = 0.1  # Interval degree for latitude and longitude
    lat_bottom = 33.75  # Latitude for start point of area you want
    lat_ceil = 33.83789  # Latitude for end point of area you want
    lng_bottom = -118.125  # Longitude for start point of area you want
    lng_ceil = -117.94921  # Longitude for end point of area you want
    image_directory = 'Image'
    file_name = 'result.csv'
    pin_url = 'https://www.padmapper.com/api/t/1/pins'
    progress_urls = read_progress()
    date = datetime.today().strftime('%d/%m/%Y')

    for lat in np.arange(lat_bottom, lat_ceil, delta):
        for lng in np.arange(lng_bottom, lng_ceil, delta):
            pin_response = pin_request(min_lat=lat, min_lng=lng).text
            lng_lat_json = json.loads(pin_response)
            loop_apartments(lng_lat_json)
    print('------------ The End ------------')
