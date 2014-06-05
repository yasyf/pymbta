var MBTAApp = angular.module('MBTAApp',['angularLocalStorage']);
MBTAApp.controller('MBTACtrl', function ($scope, $sce, storage) {
	storage.bind($scope,'trains', {defaultValue: {}});
	$scope.hidden = true;
	storage.bind($scope,'updated');
	storage.bind($scope,'stop', {defaultValue: {}});

	$scope.args = {};
	storage.bind($scope,'args.offset', {defaultValue: 0});
	storage.bind($scope,'args.direction');
	storage.bind($scope,'args.line');

	$scope.go = function () {
		navigator.geolocation.getCurrentPosition(function (position) {
			args = {lat: position.coords.latitude, lon: position.coords.longitude};
			angular.extend(args, $scope.args);
			args.dt = Math.round(new Date() / 1000) + 60*60*args.offset;
			showPosition(args);
			getStop(args);
		});
	}
	$scope.getName = function (stop) {
		return stop.parent_station_name ? stop.parent_station_name : stop.stop_name;
	}
	$scope.getDistance = function (stop) {
		kilometers = (stop.distance*1.60934);
		if (kilometers > 1){
			return kilometers.toFixed(2);
		}
		else {
			return (kilometers*1000).toFixed();
		}
	}
	$scope.getArrivalTime = function (train) {
		return new moment(train.sch_arr_dt*1000).format('h:mm A');
	}
	$scope.tripDetails = function(train) {
		details = train.trip_name.split(' - ');
		details = _.filter(details, function (item) {
			return !_.contains(item.toLowerCase(), 'line');
		});
	    return trust(details.join('<br>'));
	}
	$scope.getColor = function(trains) {
	    return trains.route_name.split(' ')[0].toLowerCase();
	}
	function trust(html) {
	    return $sce.trustAsHtml(html);
	}
	function showPosition(args) {
	    $.post( "/api/next_trains", args, function( data ) {
		  $scope.trains = data;
		  $scope.updated = moment().format('h:mm A');
		  $scope.$apply();
		});
	}
	function getStop(args) {
	    $.post( "/api/nearby_stop", args, function( data ) {
		  $scope.stop = data;
		  $scope.$apply();
		});
	}
	$scope.go();
});