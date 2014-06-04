import requests, time, datetime
from geopy.geocoders import GoogleV3

class MBTAClient():
	def __init__(self, api_key, endpoint='http://realtime.mbta.com/developer/api/v1'):
		self.api_key = api_key
		self.endpoint = endpoint
		self.geolocator = GoogleV3()
		self.cache = {}

	#Helpers

	def check_for_method(obj, method):
		f = getattr(obj, method, None)
		return callable(f)

	def format_datetime(_datetime):
		if self.check_for_method(_datetime, "timetuple"):
			_datetime = time.mktime(_datetime.timetuple())
		return _datetime

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

	def get_types(self, stop):
		return set([x['mode_name'] for x in stop['mode']])

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
		return self.make_request('schedulebystop', stop=stop, route=route, direction=direction, datetime=format_datetime(_datetime))

	def schedule_by_route(self, route, direction=None, _datetime=None):
		return self.make_request('schedulebyroute', route=route, direction=direction, datetime=format_datetime(_datetime))

	def schedule_by_trip(self, trip, _datetime=None):
		return self.make_request('schedulebytrip', trip=trip, datetime=format_datetime(_datetime))

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
	
	def closest_stop(self, loc, _type='Subway'):
		if self.check_for_method(loc, 'strip'):
			_, loc = self.geolocator.geocode(address)
		for stop in self.stops_by_location(loc)['stop']:
			routes = self.routes_by_stop(stop['stop_id'])
			if _type in self.get_types(routes):
				return stop

		