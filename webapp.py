from flask import Flask, send_file, jsonify, request
from pymbta import MBTAClient
import os
app = Flask(__name__)

client = MBTAClient('wX9NwuHnZU2ToO7GmGR9uw')

@app.route('/')
def index():
    return send_file('templates/index.html')

@app.route('/api/next_trains', methods=['GET', 'POST'])
def next_trains():
	lat = request.values.get('lat')
	lon = request.values.get('lon')
	dt = request.values.get('dt')
	direction = request.values.get('direction')
	line = request.values.get('line')

	next_trains = client.next_trains((lat, lon), _datetime=dt, direction=direction, line=line)
	if next_trains:
		return jsonify({'all_trains': next_trains})
	else:
		return jsonify({'route_name': 'Nothing!'})

@app.route('/api/nearby_stop', methods=['GET', 'POST'])
def nearby_stops():
	lat = request.values.get('lat')
	lon = request.values.get('lon')
	dt = request.values.get('dt')
	direction = request.values.get('direction')
	line = request.values.get('line')
	
	nearest_stop = client.closest_stop((lat, lon), _datetime=dt, direction=direction, line=line)
	if nearest_stop:
		return jsonify(nearest_stop)
	else:
		return jsonify({'route_name': 'Nothing!'})

if __name__ == '__main__':
	if os.environ.get('PORT'):
		app.run(host='0.0.0.0',port=int(os.environ.get('PORT')),debug=False)
	else:
		app.run(host='0.0.0.0',port=5000,debug=True)