import json
import requests
from bs4 import BeautifulSoup

def normalize_whitespace(string):
	import re
	string = string.strip()
	string = re.sub(r'\s+', ' ', string)
	return string

def to_key(string):
	return normalize_whitespace(string).lower().replace(' ', '_')

def write_as_json(variable, path):
	with open(path, 'w') as file:
		json.dump(variable, file, ensure_ascii=False, indent=2)

def table_to_text(table):
	'''
	some assumptions:
	- all data exists (even if 0 or empty) in dict
	- col_keys are longer than data columns (else probably shortened)

	design:
	- do not show '0'
	- everything is right aligned
	'''

	text = ''

	row_keys = [key for key in table.keys()]
	row_key_max = max([len(key) for key in row_keys]);
	col_keys = [key for key in table[row_keys[0]].keys()]
	col_key_max = max([len(key) for key in col_keys]);

	header_prefix = ' ' * (row_key_max + 2) + '|'
	formatted_col_keys = ['  {0: >{length}}'.format(key, length=col_key_max) for key in col_keys]
	header_content = ''.join(formatted_col_keys)
	header = header_prefix + header_content + '\n'
	text += header

	divider_prefix = '-' * (row_key_max + 2) + '|'
	divider_element = ' ' + ('-' * (col_key_max + 1))
	divider_content = divider_element * len(col_keys)
	divider = divider_prefix + divider_content + '\n'
	text += divider

	def create_content(key):
		row_prefix = ' {0: >{length}} |'.format(key, length=row_key_max)
		data = [table[key][col_key] for col_key in col_keys]
		data_filtered = [datum if datum != 0 else '' for datum in data]
		row_contents = ['  {0: >{length}}'.format(datum, length=col_key_max) for datum in data_filtered]
		return row_prefix + ''.join(row_contents) + '\n'

	for key in row_keys:
		text += create_content(key)

	return text


URL = 'https://www.uva.nl/en/about-the-uva/about-the-university/facts-and-figures/facts-and-figures.html'

r = requests.get(URL)
result = {'_desc': {'programmes': 'Degree programmes'}, 'programmes': {}}

soup = BeautifulSoup(r.content, 'html5lib')



#
# DEGREE PROGRAMME's
#
table = soup.find('table')
rows = table.find_all('tr')

head = rows[0]
body = rows[1:]

titles = head.find_all('th', scope='col')
# ['Total', 'English-taught', 'Joint degree with VU', 'Joint degree with Aarhus Universitet']
title_desc = [normalize_whitespace(title.text) for title in titles]
title_keys = [to_key(title.text) for title in titles]
# make keys shorter
key_map = {
	'english-taught': 'english',
	'joint_degree_with_vu': 'joint_vu',
	'joint_degree_with_aarhus_universitet': 'joint_aarhus'
}
title_keys = [key_map[key] if (key in key_map) else key for key in title_keys]

# add proper description of key to results
for key, desc in list(zip(title_keys, title_desc)):
	result['_desc'][key] = desc

for row in body:
	desc = normalize_whitespace(row.find('th').text)

	def desc_to_key(desc):
		# hackish way to generate a meaningful key - remove everything
		# either after "'s" or "programmes"
		raw_key = desc.split("'")[0].split(" program")[0]
		return to_key(raw_key)

	key = desc_to_key(desc)

	result['_desc'][key] = desc

	data_cells = row.find_all('td')

	def convert_to_int(string):
		try:
			return int(string)
		except ValueError:
			return 0

	data = [convert_to_int(cell.text) for cell in data_cells]

	result['programmes'][key] = {}
	for title_key, datum in zip(title_keys, data):
		result['programmes'][key][title_key] = datum

#
# REST
#

# ...

#
# OUTPUT
#
write_as_json(result, 'facts_and_figures.json')

with open('programmes.txt', 'w') as file:
	file.write(table_to_text(result['programmes']))
