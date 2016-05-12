# -*- coding: utf-8 -*-	
import xml.etree.cElementTree as ET
import pprint
from collections import Counter
from collections import defaultdict
import re
import unicodecsv as csv
from difflib import get_close_matches
import codecs

filename = '/Users/olegair/Documents/Hobby/data_analyst/p3/final project/gastein.osm'
street_std = '/Users/olegair/Documents/Hobby/data_analyst/p3/final project/streets.csv'

problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\.\t\r\n]')

def print_sorted_dict(d):
	"""
	function sorts the dictionary by numeric value elements and prints it
	"""
	d_view = [ (v,k) for k,v in d.iteritems() ]
	d_view.sort(reverse=True) # natively sort tuples by first element
	for v,k in d_view:
		print k,v

def count_tags(filename):
    """
    function takes the osm file as a parameter, read it using iterparse function from xml.etree.cElementTree library
    and counts all child elements. Returns Counter object with the tags and number of the tags in the file
    """
    cnt = Counter()
    for event, elem in ET.iterparse(filename):
        cnt[elem.tag] += 1
        elem.clear()
    print_sorted_dict(cnt)
    return cnt

def unique_users(filename):
    """
    function unique_users takes path to osm file as a parameter and
    returns set of unique users, who contributed to the data
    """
    users = set()
    for _, element in ET.iterparse(filename):
        if 'uid' in element.attrib:
            users.add(element.attrib['uid'])

    return users

def audit_node(filename):
	"""
	the function explores the "k" attributes of the child elements in the "way" element
	"""
	cnt = Counter()	
	for event, elem in ET.iterparse(filename, events=("start",)):
		if elem.tag == 'way':
			for tag in elem.iter("tag"):
				cnt[tag.attrib['k'].encode('utf-8')] += 1
		elem.clear()
	print_sorted_dict(cnt)
	

def audit_node_tag_v(filename):
	"""
	the function explores the "v" attributes of the child elements in the "way" element when "k" attribut is "tourism"
	"""
	cnt = Counter()
	for event, elem in ET.iterparse(filename,events=("start",)):
		if elem.tag == 'way':
			for tag in elem.iter("tag"):
				if tag.attrib['k'].encode('utf-8') == 'tourism':
					cnt[tag.attrib['v'].encode('utf-8')] += 1
	print cnt

def is_addr_pcode(elem):
	"""
	the function checks if the element contains postcode information
	"""
	if elem.attrib['k'] == 'addr:postcode':
		return True
	else:
		return False

def is_addr_street(elem):
	"""
	the function checks if the element contains street information
	"""
	if elem.attrib['k'] == 'addr:street':
		return True
	else:
		return False 

def is_addr_housenumber(elem):
	"""
	the function checks if the element contains postcode housenumber
	"""
	if elem.attrib['k'] == 'addr:housenumber':
		return True
	else:
		return False

def is_city(elem):
	"""
	the function checks if the element contains city information
	"""
	if elem.attrib['k'] == 'addr:city':
		return True
	else:
		return False 

def audit_addr_pcode(elem):
	"""
	the function checks if the postcode contains from 4 digits
	"""
	if elem.attrib['k'] == 'addr:postcode':
		postcode = elem.attrib['v']
		if len(postcode) != 4:
			return False
		if re.search(r'\D', postcode):
			return False
	return True


def main():
	count_tags(filename)
	#audit_node(filename)
	#audit_addr(filename)
	#audit_node_tag_v(filename)
	#audit_hospitality(filename)
	#audit_tag(filename)

if __name__ == '__main__':
	main()