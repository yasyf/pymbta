import requests, time, datetime
from mongocache import MongoCache, MongoTrips
from geopy.geocoders import GoogleV3

class MBTAClient():
	def __init__(self, api_key, endpoint='http://realtime.mbta.com/developer/api/v1'):
		self.api_key = api_key
		self.endpoint = endpoint
		self.geolocator = GoogleV3()
		self.cache = MongoCache()
		self.trips = MongoTrips()

	#Helpers

	def check_for_method(self, obj, method):
		f = getattr(obj, method, None)
		return callable(f)

	def format_datetime(self, _datetime):
		if self.check_for_method(_datetime, "timetuple"):
			_datetime = time.mktime(_datetime.timetuple())
		if _datetime:
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
		if '_datetime' in kwargs:
			return requests.get(url, headers=self.default_headers()).json()
		if url not in self.cache:
			self.cache[url] = requests.get(url, headers=self.default_headers()).json()
		return self.cache[url]

	def get_types_from_routes(self, routes):
		return set([x['mode_name'] for x in routes])

	def get_routes_from_mode(self, modes, mode_name):
		routes = []
		for mode in modes:
			if mode['mode_name'] == mode_name:
				routes.extend(mode['route'])
		return routes

	def format_line(self, line):
		return line.lower().replace('line','').strip()

	def get_dirs_from_schedule(self, schedule, _type):
		routes = self.get_routes_from_mode(schedule['mode'], _type)
		return set([int(x['direction'][0]['direction_id']) for x in routes])
	
	def get_dir_strings_from_schedule(self, schedule, _type):
		routes = self.get_routes_from_mode(schedule['mode'], _type)
		return set([x['direction'][0]['direction_name'].lower() for x in routes])

	def get_lines_from_routes(self, routes):
		return set([self.format_line(x['route'][0]['route_name']) for x in routes])

	def get_latlon(self, address):
		address = address.strip().lower()
		if address not in self.cache:
			 _, latlon = self.geolocator.geocode(address)
			 self.cache[address] = latlon
		return self.cache[address]

	def get_earliest_train(self, trains):
		earliest = trains[0]
		for train in trains:
			if int(train['sch_arr_dt']) < int(earliest['sch_arr_dt']):
				earliest = train
		return earliest

	def validate_line(self, line, routes):
		return line.lower() in self.get_lines_from_routes(routes)

	def validate_direction(self, direction, schedule, _type):
		if direction.isdigit():
			in_stop_name = False
			in_direction = int(direction) in self.get_dirs_from_schedule(schedule, _type)
		else:
			in_stop_name = direction.lower() in schedule['stop_name'].lower()
			in_direction = True in [(direction.lower() in x) for x in self.get_dir_strings_from_schedule(schedule, _type)]
		return in_stop_name or in_direction

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

	def closest_stop(self, loc, _type='Subway', direction=None, _datetime=None, line=None):
		if self.check_for_method(loc, 'strip'):
			loc = self.get_latlon(loc)
		for stop in self.stops_by_location(loc)['stop']:
			routes = self.routes_by_stop(stop['stop_id'])['mode']
			if _type in self.get_types_from_routes(routes):
				if line:
					if not self.validate_line(line, routes):
						continue
				if direction:
					schedule = self.schedule_by_stop(stop['stop_id'], _datetime=_datetime)
					if not self.validate_direction(direction, schedule, _type):
						continue
				return stop

	def nearby_schedule(self, loc, _datetime=None, direction=None, line=None):
		stop = self.closest_stop(loc, direction=direction, _datetime=_datetime, line=line)
		return self.schedule_by_stop(stop.get('parent_station', stop['stop_id']), _datetime=_datetime) if stop else None

	def next_routes(self, loc, _datetime=None, direction=None, line=None):
		schedule = self.nearby_schedule(loc, direction=direction, _datetime=_datetime, line=line)
		valid_routes = []
		if schedule:
			routes = self.get_routes_from_mode(schedule['mode'], 'Subway')
			for route in routes:
				if line:
					if not self.validate_line(line, [{'route': [route]}]):
						continue
				if direction:
					if not self.validate_direction(direction, schedule, 'Subway'):
						continue
				info = {'stop_id': schedule['stop_id'], 'stop_name': schedule['stop_name']}
				info.update(route)
				valid_routes.append(info)
		return valid_routes

	def next_trains(self, loc, _datetime=None, direction=None, line=None):
		routes = self.next_routes(loc, direction=direction, _datetime=_datetime, line=line)
		train_info = []
		if routes:
			for route in routes:
				info = {'stop_id': route['stop_id'], 'stop_name': route['stop_name'], 'route_id': route['route_id'], 'route_name': route['route_name']}
				if len(route['direction']) > 0:
					info['headsign'] = self.trips[route['direction'][0]['trip'][0]['trip_id']]['trip_headsign']
				trains = []
				for direction in route['direction']:
					train = {'direction_id': direction['direction_id'], 'direction_name': direction['direction_name']}
					train.update(direction['trip'][0])
					trains.append(train)
				info['trains'] = trains
				train_info.append(info)
		return train_info

	def next_train(self, loc, _datetime=None, direction=None, line=None):
		trains_list = self.next_trains(loc, direction=direction, _datetime=_datetime, line=line)
		if trains_list:
			return self.get_earliest_train([self.get_earliest_train(trains['trains']) for trains in trains_list])
