# -*- coding: utf-8 -*-

def POST_request(url, input_data):
	headers = {'Content-type': 'application/json'}

	# --

	import requests

	response = requests.post(url, data=input_data, headers=headers)

	return response.text

def enable_cors(fn):
	def _enable_cors(*args, **kwargs):
		from bottle import request, response

		# set CORS headers
		response.headers['Access-Control-Allow-Origin'] = '*'
		response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
		response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

		if request.method != 'OPTIONS':
			# actual request; reply with the actual response
			return fn(*args, **kwargs)
		
	return _enable_cors

from bottle import route

# --

@route(path='/check_A', method=['OPTIONS', 'POST'])
@enable_cors
def do_service(): # for wisekb
	from bottle import request

	i_text = request.body.read()

	# --

	import json

	try:
		i_json = json.loads(i_text)

	except TypeError:
		i_json = json.loads(i_text.decode('utf-8'))

	# ==

	o_json = {'PL': {'triples': []}, 'KV': []}

	# --

	for triple in i_json['PL']['triples']:
		s = triple['s']
		p = triple['p']
		o = triple['o']

		# --

		import re

		s_ = re.split('/', s)[0]
		p_ = re.split('/', p)[0]
		o_ = re.split('/', o)[0]

		# --

		label, score = rf.validate(s_, p_, o_, used_for='demo-wisekb')

		# --

		if label not in [rf.F]:
			o_json['PL']['triples'].append(triple)

		# --

		o_json['KV'].append([s, p, o, label, score])

	# ==

	o_text = json.dumps(o_json, indent=4, separators=(',', ': '), ensure_ascii=False, default=default)	

	return o_text

# --

@route(path='/check_B', method=['OPTIONS', 'POST'])
@enable_cors
def do_service(): # for flagship
	from bottle import request

	i_text = request.body.read()

	# --

	import json

	try:
		i_json = json.loads(i_text)

	except TypeError:
		i_json = json.loads(i_text.decode('utf-8'))

	# ==

	s, p, o = i_json

	# --
	
	import re

	s_ = re.split('/', s)[0]
	p_ = re.split('/', p)[0]
	o_ = re.split('/', o)[0]

	# --

	label, score, evidence = rf.validate(s_, p_, o_, used_for='demo-flagship')

	# --

	o_json = [label, score, evidence]

	# ==

	o_text = json.dumps(o_json, indent=4, separators=(',', ': '), ensure_ascii=False, default=default)	

	return o_text

# --

@route(path='/reason', method=['OPTIONS', 'POST'])
@enable_cors
def do_service(): # for flagship
	from bottle import request

	i_text = request.body.read()

	# --

	import json

	try:
		i_json = json.loads(i_text)

	except TypeError:
		i_json = json.loads(i_text.decode('utf-8'))

	# ==

	o_json = {'o': []}

	# --

	s = i_json['s']
	p = i_json['p']

	# --

	result = rr.reason_object(s, p)

	# --

	if result:
		o_json['o'] = result

	# ==

	o_text = json.dumps(o_json, indent=4, separators=(',', ': '), ensure_ascii=False, default=default)	

	return o_text

# --

def default(value):
	import datetime

	# --

	if isinstance(value, datetime.date): 
		return value.strftime('%Y-%m-%d') 

	raise TypeError('not JSON serializable')

# --

import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-cn')

args = parser.parse_args()

# --

conf_name = args.cn

print(conf_name)

# --

with open(conf_name) as i_file:
	import json

	# --

	conf = json.loads(i_file.read())

# --

ip = conf['ip']
port = conf['port']

# --

import filter as filter_

rf = filter_.RF(conf)

# --

import reasoner

rr = reasoner.RR(conf, rf)

# --

from bottle import run

run(host=ip, port=port)