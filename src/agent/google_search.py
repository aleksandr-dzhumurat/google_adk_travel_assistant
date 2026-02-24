import hashlib
import json
import logging
import os
from typing import Optional
from urllib.parse import quote

import requests

logger = logging.getLogger('my_logger')
logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)


class RecsCache:
    def __init__(self):
        self.db_file = '/srv/data/links_db.json'
    
    def save_recs(self, recs, location = None):
        links_db = {}
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                links_db = json.load(f)
        # page_link should be generated
        seed_phrase = ','.join([i['event'] for i in recs])
        page_link = str(hashlib.md5(seed_phrase.encode('utf-8')).hexdigest())[:6]
        # saving recs
        links_db[page_link] = {}
        links_db[page_link]['activities'] = recs
        links_db[page_link]['location'] = location
        with open(self.db_file, 'w') as f:
            json.dump(links_db, f)

        return page_link
    
    def save_places(self, page_link, places):
        links_db = {}
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                links_db = json.load(f)
        links_db[page_link]['places'] = places
        with open(self.db_file, 'w') as f:
            json.dump(links_db, f)

        return page_link

    def load_recs(self, page_link: str):
        links_db = {}
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                links_db = json.load(f)
        recs = links_db.get(page_link, {})
        return recs


class GooglePlaceApi:
    def __init__(self):
        self.API_TYPE = 'textsearch' # findplacefromtext
        self.url = f"https://maps.googleapis.com/maps/api/place/{self.API_TYPE}/json"
        self.google_api_key = os.getenv('GOOGLE_API_KEY')

    def shareble_link(self, lat, lng):
        # maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        location_param = quote(f'{lat},{lng}')
        maps_url =  f"https://www.google.com/maps?q={location_param}"
        return maps_url

    def shareble_link_pretty(self, item):
        """ATTENTION: do NOT use to avoid additional payments, x2"""
        from urllib.parse import quote

        place_id =  item['place_id']
        fields = quote('name,url')

        params = {
            "place_id": place_id,
            "fields": fields,
            "key": self.google_api_key
        }
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        headers = {}
        response = requests.get(url, params=params, headers=headers).json()['result']

        return response

    def api_request(self, q: str, lat_lng: Optional[str]):

        if lat_lng is None:
            lat, lng = 34.707130,33.022617  # Lemesos city centre
        else:
            lat, lng = lat_lng.split(',')
        radius = 5000
        
        params = {
            "inputtype": "textquery",
            "fields": "formatted_address,name,place_id",
            "key": self.google_api_key
        }
        if self.API_TYPE == 'findplacefromtext':
            location = f'circle:{radius}@{lat},{lng}'
            params.update({"locationbias": location, "input": q})
        else:
            location_param = f'{lat},{lng}'
            params.update({"location": location_param, 'radius': radius, "query": q})

        headers = {}
        response = requests.get(self.url, params=params, headers=headers).json()
        if self.API_TYPE == 'findplacefromtext':
            response = response['candidates']
        else:
            response = response['results']
        return response

    def get_recs_for_activity(self, q: str, share_id, cache):
        import numpy as np

        cached_page = cache.load_recs(share_id)

        cached_places = cached_page.get('places', {})
        location = cached_page.get('location')
        activity_rec = cached_places.get(q)
        if activity_rec is None:
            response = self.api_request(q, lat_lng=location)
            candidates = []
            for item in response:
                share_link = self.shareble_link(**item['geometry']['location']) # or shareble_link_pretty(item)
                place = {'name': item['name'], 'link': share_link}
                candidates.append(place)
            res_link = None
            if len(candidates) > 0:
                res_link = np.random.choice(candidates)
                cached_places[q] = res_link
                cache.save_places(page_link=share_id, places=cached_places)
            else:
                logger.info('ERROR: failed to recomend %s', q)
        else:
            res_link = activity_rec
        return res_link

    def find_place(self, place_name: str):
        print('place_name %s' % place_name)
        params = {
            "address": place_name,
            "key": self.google_api_key
        }
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        response = requests.get(url, params=params)
        data = response.json()
        
        print(data)

        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            latitude = location['lat']
            longitude = location['lng']
            print(f'Latitude: {latitude}, Longitude: {longitude}')
        else:
            print('Geocoding failed')
        return f'{latitude},{longitude}'

place_recommender = GooglePlaceApi()


class ContentDB:
    def __init__(self):
        self.db_df = None
        self.db_settings = ['daystart_option', 'kids_option', 'evening_option']
        self.mapping = {
            'Which town are you based in?': 'location_option',
            'Want to start the day in the morning 🌞?': 'daystart_option',
            'Looking for kids activities 👨‍👩‍👧‍👦?': 'kids_option',
            'How about adding an evening to the plan 🌃?': 'evening_option',
        }
        self.cache = None
    
    def generate_key(self, user_params: dict):
        res = ''
        for setting in self.db_settings:
            if setting != 'location_option':  # location not used when plan was generated 
                res += f'{setting}_{user_params[setting]}_'
        return res
    
    def init_db(self, input_file: str, cache_db):
        import pandas as pd

        with open(input_file, 'r') as f:
            self.db_df = pd.json_normalize(json.loads(f.read()), max_level=0)
        self.db_df['rec_key'] = self.db_df['user_answers'].apply(lambda x: self.generate_key(x))

        self.cache = cache_db

        return self

    def recommend(self, user_query: dict, share_id: str) -> list:
        if share_id is not None:
            recs = self.cache.load_recs(share_id).get('activities', [])
            if len(recs) != 0:
                return recs, None
        mapped_prefs = {}
        user_query = json.loads(user_query)
        for q in user_query:
            print(q['question'], q['answer'])
            mapped_prefs.update({self.mapping[q['question']]: q['answer']})
        print('City %s' % mapped_prefs['location_option'])
        key = self.generate_key(mapped_prefs)
        recs = [
            {k: v for k, v in item.items() if k in ('event', 'event_time_slot')}
            for item in self.db_df[self.db_df['rec_key']==key].sample(1).iloc[0]['schedule']
        ]
        lat_lng = place_recommender.find_place(mapped_prefs['location_option'])
        # for non-cached requests new recs should be generated
        page_link = self.cache.save_recs(recs, location=lat_lng)

        return recs, page_link
