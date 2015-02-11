angular.module("myApp").factory('WebsocketService', ['$q', '$location', '$rootScope', function($q, $location, $rootScope) {
        var Service = {};
        var callbacks = {};
        var host = 'ws://'+$location.host()+'/websocket';
        var websocket
        Service.callback = function(){
        }

        websocket = new WebSocket(host);

        websocket.onopen = function (evt) { 
            console.log($rootScope.game_id)
            sendRequest({
                                  'game_id': $rootScope.game_id,
                                  'action': 'bind_cookie',
                                  'cookie': document.cookie
                                  })
        };
        websocket.onmessage = function(message) {
            console.log('received', message)
            Service.callback(JSON.parse(message.data));
        };
        websocket.onerror = function (evt) {
        };

        function sendRequest(request) {
          var defer = $q.defer();
          console.log('Sending request', request);
          if (websocket.readyState === 1){
            websocket.send(JSON.stringify(request));
          }
          return defer.promise;
        }
        Service.send_message = sendRequest
        return Service;
}])
