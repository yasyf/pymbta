import pymongo, os

class MongoCache():
	def __init__(self):
		self.db = pymongo.MongoClient(os.environ['db']).mbta.cache
		self.cache = {}

	def __get__(self, key):
		if key not in self.cache:
			try:
				self.cache[key] = self.db.find_one({'_hash': key})['value']
			except TypeError:
				return None
		return self.cache[key]

	def __getitem__(self, key):
		return self.__get__(key)

	def __set__(self, key, value):
		self.db.remove({'_hash': key})
		if key in self.cache:
			del self.cache[key]
		self.db.insert({'_hash': key, 'value': value})
		self.cache[key] = value

	def __setitem__(self, key, val):
		return self.__set__(key, val)
	
	def __iter__(self):
		return self.cache

	def __len__(self):
		return len(self.cache)

	def __contains__(self, v):
		return bool(self.__get__(v))

class MongoTrips():
	def __init__(self):
		self.db = pymongo.MongoClient(os.environ['db']).mbta.trips
		self.cache = {}

	def __get__(self, key):
		if key not in self.cache:
			try:
				self.cache[key] = self.db.find_one({'trip_id': key})
			except TypeError:
				return None
		return self.cache[key]

	def __getitem__(self, key):
		return self.__get__(key)
