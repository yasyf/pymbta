import requests, time, datetime
from geopy.geocoders import GoogleV3

class MBTAClient():
	def __init__(self, api_key, endpoint='http://realtime.mbta.com/developer/api/v1'):
		self.api_key = api_key
		self.endpoint = endpoint
		self.geolocator = GoogleV3()
		self.cache = {}

	#Helpers

	def check_for_method(self, obj, method):
		f = getattr(obj, method, None)
		return callable(f)

	def format_datetime(self, _datetime):
		if self.check_for_method(_datetime, "timetuple"):
			_datetime = time.mktime(_datetime.timetuple())
		return int(_datetime)

	def default_query_params(self):
		return {'api_key': self.api_key}

	def default_headers(self):
		return {'Accept': 'application/json'}

	def make_request(self, service, **kwargs):
		query_params = self.default_query_params()
		query_params.update(kwargs)
		query_params = ['{}={}'.format(key, value) for key,value in query_params.items() if value]
		url = "{}/{}?{}".format(self.endpoint, service, '&'.join(query_params))
		if url not in self.cache:
			self.cache[url] = requests.get(url, headers=self.default_headers()).json()
		return self.cache[url]

	def get_types_from_stop(self, stop):
		return set([x['mode_name'] for x in stop['mode']])

	def get_route_from_mode(self, modes, mode_name):
		for mode in modes:
			if mode['mode_name'] == mode_name:
				return mode

	def get_dirs_from_schedule(self, schedule, _type):
		routes = self.get_route_from_mode(schedule['mode'], _type)['route']
		return set([int(x['direction'][0]['direction_id']) for x in routes])
	
	def get_dir_strings_from_schedule(self, schedule, _type):
		routes = self.get_route_from_mode(schedule['mode'], _type)['route']
		return set([x['direction'][0]['direction_name'].lower() for x in routes])

	def get_latlon(self, address):
		address = address.strip().lower()
		if address not in self.cache:
			 _, latlon = self.geolocator.geocode(address)
			 self.cache[address] = latlon
		return self.cache[address]

	#Services

	def server_time(self):
		return self.make_request('servertime')

	def routes(self):
		return self.make_request('routes')

	def routes_by_stop(self, stop):
		return self.make_request('routesbystop', stop=stop)

	def stops_by_route(self, route):
		return self.make_request('stopsbyroute', route=route)

	def stops_by_location(self, (lat, lon)):
		return self.make_request('stopsbylocation', lat=lat, lon=lon)

	def schedule_by_stop(self, stop, route=None, direction=None, _datetime=None):
		return self.make_request('schedulebystop', stop=stop, route=route, direction=direction, datetime=self.format_datetime(_datetime))

	def schedule_by_route(self, route, direction=None, _datetime=None):
		return self.make_request('schedulebyroute', route=route, direction=direction, datetime=self.format_datetime(_datetime))

	def schedule_by_trip(self, trip, _datetime=None):
		return self.make_request('schedulebytrip', trip=trip, datetime=self.format_datetime(_datetime))

	def alerts(self):
		return self.make_request('alerts')

	def alerts_by_route(self, route):
		return self.make_request('alertsbyroute', route=route)

	def alerts_by_stop(self, stop):
		return self.make_request('alertsbystop', stop=stop)

	def alert_by_id(self, alert_id):
		return self.make_request('alertbyid', id=alert_id)

	def alert_headers(self):
		return self.make_request('alertheaders')

	def alert_headers_by_route(self, route):
		return self.make_request('alertheadersbyroute', route=route)

	def alert_headers_by_stop(self, stop):
		return self.make_request('alertheadersbystop', stop=stop)

	#Aliases

	def alert(self, alert_id):
		return self.alert_by_id(alert_id)

	#Joins

	def closest_stop(self, loc, _type='Subway', direction=None, _datetime=None):
		if self.check_for_method(loc, 'strip'):
			loc = self.get_latlon(loc)
		for stop in self.stops_by_location(loc)['stop']:
			routes = self.routes_by_stop(stop['stop_id'])
			if _type in self.get_types_from_stop(routes):
				if direction:
					schedule = self.schedule_by_stop(stop['stop_id'], _datetime=_datetime)
					if direction.isdigit():
						in_stop_name = False
						in_direction = int(direction) in self.get_dirs_from_schedule(schedule, _type)
					else:
						in_stop_name = direction.lower() in stop['stop_name'].lower()
						in_direction = True in [(direction.lower() in x) for x in self.get_dir_strings_from_schedule(schedule, _type)]
					if not in_stop_name and not in_direction:
						continue
				return stop

	def nearby_schedule(self, loc, _datetime=None, direction=None):
		stop = self.closest_stop(loc, direction=direction, _datetime=_datetime)
		return self.schedule_by_stop(stop['stop_id'], _datetime=_datetime) if stop else None

	def next_train(self, loc, _datetime=None, direction=None):
		schedule = self.nearby_schedule(loc, direction=direction, _datetime=_datetime)['mode']
		return schedule[0]['route'][0]['direction'][0]['trip'][0]


