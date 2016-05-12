#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
import unicodecsv as csv
from difflib import get_close_matches
import requests

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


filename = '/Users/olegair/Documents/Hobby/data_analyst/p3/final project/gastein.osm'
json_file = '/Users/olegair/Documents/Hobby/data_analyst/p3/final project/gastein.osm.json'
street_std_file = '/Users/olegair/Documents/Hobby/data_analyst/p3/final project/streets.csv'
street_std_list = []

pos_dict = {}


def shape_element(element):
    """
    funtion shape_element takes an element of the osm file and, if the element is ndoe or way, 
    returns the accommodation dictionary. The dictionary consists from the element's attributes and attributes of the child elements tag and nd.
    Here is the example of the dictionary:
    {
      "website": "http://www.hotel-bismarck.com/", 
      "fax": "+43643266810", 
      "name": "Bismarck", 
      "created": {
        "uid": "390669", 
        "changeset": "8344170", 
        "version": "1", 
        "user": "KrilleOSM", 
        "timestamp": "2011-06-04T23:12:14Z"
      }, 
      "tourism": "hotel", 
      "pos": [
        47.1678054, 
        13.1094715
      ], 
      "id": "1312435304", 
      "phone": "+43643266810", 
      "source": "survey", 
      "address": {
        "city": "Bad Hofgastein", 
        "street": "Alpenstraße", 
        "housenumber": "6", 
        "postcode": "5630", 
        "country": "AT"
      }, 
      "type": "node", 
      "email": "info@hotel-bismarck.com"
    }
    """
    node = {}
    if element.tag == "node" or element.tag == "way" :
        node["id"] = element.attrib["id"]
        node["type"] = element.tag
        if "visible" in element.attrib:
            node["visible"] = element.attrib["visible"]
        node["created"] = {}
        node["created"]["version"] = element.attrib["version"]
        node["created"]["changeset"] = element.attrib["changeset"]
        node["created"]["timestamp"] = element.attrib["timestamp"]
        node["created"]["user"] = element.attrib["user"]
        node["created"]["uid"] = element.attrib["uid"]
        if "lat" in element.attrib and "lon" in element.attrib:
            node["pos"] = [float(element.attrib["lat"]), float(element.attrib["lon"])]
            pos_dict[node['id']] = node['pos']
        for tag in element.iter("tag"):
				if problemchars.search(tag.attrib['k']):
				    continue
				elif re.search(r':',tag.attrib['k']):
				    l1 = tag.attrib['k'].split(':')
				    if len(l1) > 2:
				        continue
				    else:
				        if l1[0] == "addr":
				            l1[0] = "address"
				        try:
				            node[l1[0]][l1[1]] = unicode(tag.attrib['v'])
				        except:
				            node[l1[0]] = {}
				            node[l1[0]][l1[1]] = unicode(tag.attrib['v'])
				            
				else:
				    node[tag.attrib['k']] = unicode(tag.attrib['v'])
        for tag in element.iter("nd"):
            try:
                node["node_refs"].append(tag.attrib['ref'])

            except:
                node["node_refs"] = []
                node["node_refs"].append(tag.attrib['ref'])
                node["pos"] = pos_dict[node["node_refs"][0]]
        return node
    else:
        return None

accommodation = ['hotel', 'chalet', 'guest_house', 'apartment', 'hostel']

def postcode_audit(el):
    """
    function postcode_audit takes the element as a parameter and, it's a postcode,
    returns the 4 digits code of the austrian postcode and deleter all other symbols if they occur
    """
    if 'postcode' in el['address']:
        if len(el['address']['postcode'])>4:
            m = re.search(r'\d\d\d\d$',el['address']['postcode'])
            if m:
                el['address']['postcode'] = m.group()
    return el

def google_adr(el):
    """
    function google_adr is trying to get address of the aacoomodation using google places api 
    It takes an accommodation dictionary as a parameter, updates it with the address information if possible and returns the dictionary back.
    Function tries to find the place first by lat and lon from the dictionary and radius 25 meters.
    If the response file contains object with the type "lodging", it takes the place id and creates another request to get data about the place.
    If response contains address information in address_components element, function updates the dictionary.
    """
    API_KEY = 'AIzaSyBbFvfR8WjfnGaV3bSu2pjtdxtXWiEbfHQ'
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%f,%f&radius=25&key='%(el["pos"][0],el["pos"][1]) + API_KEY
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        for response in r.json()['results']:
            if "lodging" in response['types']:
                place_id = response['place_id']
                url2 = 'https://maps.googleapis.com/maps/api/place/details/json?placeid=%s&key='%(place_id)+API_KEY
                r2 = requests.get(url2)
                if r2.status_code == requests.codes.ok:
                    if 'result' in r2.json():
                        el['address']={}
                        for elem in r2.json()['result']['address_components']:
                            if elem['types'][0] == 'street_number':
                                el['address']['housenumber'] = elem['long_name']
                            if elem['types'][0] == 'route':
                                el['address']['street'] = elem['long_name']    
                            if elem['types'][0] == 'locality':
                                el['address']['city'] = elem['long_name']
                            if elem['types'][0] == 'country':
                                el['address']['country'] = elem['short_name']            
                            if elem['types'][0] == 'postal_code':
                                el['address']['postcode'] = elem['short_name']   
                    el = street_std(el)
                    el = postcode_audit(el)
    else:
        print "error"

    return el

def get_street_std_list():
    """
    function uses the csv file with standard writing of the cities, streets and postcodes, created by the government,
    and create the list street_std_list of the reference writing of the street names
    """
    with open(street_std_file,'rb') as f:
        addr = csv.DictReader(f,delimiter=';')
        for elem in addr:
            street_std_list.append(elem['Straßenname'.decode('utf-8')].encode('utf-8'))
    
def street_std(el):
    """
    the function compares the street spelling in accommodation dictionary with the reference list of the streets.
    If the spelling is incorrect, the function use get_close_matches from difflib library to return the closest 
    street from the reference street list and updates the street in the accommodation dictionary
    """
    if len(street_std_list) == 0:
        get_street_std_list()
    if el and 'address' in el and 'street' in el['address'] and el['address']['street'].encode('utf-8') not in street_std_list:
        el['address']['street'] = get_close_matches(el['address']['street'].encode('utf-8'), street_std_list, n=1)[0].decode('utf-8')        
    return el

def addr_audit(el):
    """
    the function performs the address audit of the accommodation dictionary.
    If the accommodation doesn't have address at all of the street is missing, than the function calls google_adr function to get the
    address from the google.
    Else the function calls street_std function and postcode_audit function 
    """
    if 'address' not in el or 'street' not in el['address']:
        el = google_adr(el)
    else:
        el = street_std(el)
        el = postcode_audit(el)
    return el

def phone_audit(el):
    """
    function takes the phone and fax numbers in the accommodation dictionaries (if exist) and harmonize it to the single format:
    +43*********.
    Function uses 4 regular expressions to do that:
    1) if the number starts from 0043 instead of +43, change to +43
    2) if the number has (0) after +43, takes it away
    3) deletes all spaces, - and / symbols from the phone
    4) deletes the 0 after +43 if it was in the number without parenthesis
    """
    if "phone" in el:
        # 1
        el['phone'] = re.sub(r'^00','+',el['phone'])
        # 2
        el['phone'] = re.sub(r'\(0\)','',el['phone'])
        # 3
        el['phone'] = '+'+re.sub(r'[ -//]','',el['phone'])
        # 4
        el['phone'] = re.sub(r'^\+430',"+43",el['phone'])
    if "fax" in el:
        el['fax'] = re.sub(r'^00','+',el['phone'])
        el['fax'] = re.sub(r'\(0\)','',el['phone'])
        el['fax'] = '+'+re.sub(r'[ -//]','',el['phone'])
        el['fax'] = re.sub(r'^\+430',"+43",el['phone'])
    return el    

def additional_cleaning(el):
    """
    function takes just created dictionary from osm file, checks if it contains information about the accommodations
    and performs address and phone audit. If the dictionary is empty or doesn't contain information about the accommodation,
    returns False, else it returns the updated dictionary
    """
    if el:
        if 'tourism' not in el or el['tourism'] not in accommodation:
            return False
        else:
            el = addr_audit(el)
            el = phone_audit(el)
            return el
    else:
        return False

def process_map(file_in, pretty = False):
    """
    the function reads the elements from the osm file, calls shape_elem and additional cleaning functions,
    and writes the processed accommodation dictionaries to the json file
    """
    
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w", encoding='utf-8') as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            el = additional_cleaning(el)
            if el:                
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2, ensure_ascii=False)+"\n")
                else:
                    fo.write(json.dumps(el, ensure_ascii=False) + "\n")
    return data

def insert_to_mongodb(data):
    """
    the function takes the list of accommodation dictionaries as a parameter, inserts it to mongodb and 
    returns the result of the insert_many operation
    """
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017")
    db = client.examples
    return db.accommodations.insert_many(data)

def get_db(database):
    """
    the funtion connects to the database of local mongodb instance and return the instance
    """
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017")
    db = client[database]
    return db    

def make_pipeline():
    """
    the function creates 2 pipelines for the aggregate function of mongodb
    """
    
    #pipeline = [{"$group" : {"_id" : "$address.city", "count" : {"$sum" : 1}}},
    #            {"$sort" : {"count" : -1}},
    #            {"$limit" : 1}]
    
    pipeline = [{"$group" : {"_id" : "$address.postcode", "count" : {"$sum" : 1}}},
                {"$sort" : {"count" : -1}},
                {"$limit" : 2}]
    return pipeline

def aggregate(db, pipeline):
    """
    function gets db and pipeline as parameteres, calls aggregate method of mongodb and returns the result
    """
    return [doc for doc in db.accommodations.aggregate(pipeline)]

def test():
    """
    the main function of the code, where I first read and process osm file, load data to mongodb 
    and performs aggregation function in mongodb
    """
    #read osm file, create the list of accommodation dictionaries, save to json file
    #data = process_map(filename, True)
    # load data to mongodb
    #print insert_to_mongodb(data)
    #db = get_db('examples')
    #print db.accommodations.find({"created.user"} ).length()
    #print results
    #pprint.pprint(data)
    #users = unique_users(filename)
    #print len(users),users
    

if __name__ == "__main__":
    test()