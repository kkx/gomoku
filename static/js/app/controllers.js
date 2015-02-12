var app=angular.module("myApp");

app.controller('GameController', ['$scope', '$rootScope', '$location', '$routeParams', '$http', 'WebsocketService', function ($scope, $rootScope, $location, $routeParams, $http, WebsocketService) {
    $scope.actual_turn = ''
    $scope.chat_text = ''
    $scope.message_input_text = ''
    if ($routeParams.game_id){
        $scope.game_id = $routeParams.game_id
        $rootScope.game_id = $routeParams.game_id
        $http.get('/game/'+$routeParams.game_id).
            success(function(response) {
                console.log(response.status)
                if (response.status === 0){
                  $scope.game_id == ''
                  $location.url('/game/')
                }
            }).
            error(function(data, status, headers, config) {
            });

        if(!$scope.$$phase) {
            $scope.$apply();
        }
    }

    $scope.restart_game = function(){
        WebsocketService.send_message(
           {'action':'restart_game', 'game_id': $scope.game_id, 'loser': $scope.role} 
        )
    };

    function readResponse(message){
        console.log(message)
        if (message.action == 'start_game' || message.action == 'board_status' || message.action == 'restart_game'){
            $scope.actual_turn =  message.board_info.actual_turn
            console.log(message.role)
            $scope.role = message.role
            console.log($scope.role)
            if ($scope.role == 'host'){
                $scope.role_colour = message.board_info.host_colour
                $scope.role_opponet_colour = message.board_info.opponent_colour
            }
            else if ($scope.role == 'opponent'){
                $scope.role_colour = message.board_info.opponent_colour
                $scope.role_opponet_colour = message.board_info.host_colour
            }
            $scope.board = message.board_info.board
            $scope.actual_turn = message.board_info.actual_turn
            console.log(message.board_info.board)
        }else if (message.action == 'board_status_after_click'){
            $scope.actual_turn =  message.board_info.actual_turn
            $scope.board = message.board_info.board
            $scope.board_check_status = message.board_check_status
        }else if (message.action == 'receive_chat_message'){
            $scope.chat_text += message.sender + ' said: '+ message.chat_message + '\n'
            textarea = angular.element('#chat_text_area');
            textarea.scrollTop(textarea[0].scrollHeight);
        }
        if (message.action == 'restart_game'){
            alert('Game is restarted');
        }
        if(!$scope.$$phase) {
            $scope.$apply();
        }
        if ($scope.board_check_status){
            alert('Winner is ' + $scope.board_check_status['colour'])
        }

    }

    WebsocketService.callback = readResponse


    $scope.box_clicked = function(e){
        var box_id = $(e.target).attr('id');
        //box-i-j
        box = box_id.split("-")
        i = parseInt(box[1])
        j = parseInt(box[2])
        if ($scope.actual_turn != $scope.role || $scope.board[i][j] != ''){
            return false
        }
        console.log($scope.role_colour)
        $scope.board[i][j] == $scope.role
        $scope.actual_turn = $scope.role == 'host' ? 'opponent' : 'host'
        //angular.element('#'+box_id).toggleClass($scope.role_colour+'-clicked', $scope.board[i][j])
        WebsocketService.send_message(
           {'action':'select_box', 'game_id': $scope.game_id, 'i': i, 'j': j, 'role': $scope.role} 
        )

    };
    $scope.add_chat_message = function(e){
        WebsocketService.send_message(
           {'action':'send_chat_message', 'game_id':$scope.game_id, 'message': $scope.message_input_text, 'sender': $scope.role} 
        )
        $scope.message_input_text = ''
    };
}]);



app.controller('FakeGameController', ['$scope', '$rootScope', '$location', '$routeParams', '$http', function ($scope, $rootScope, $location, $routeParams, $http) {
    var UNCLICKED = 0, CLICKED=1
    $scope.create_game = function(){
        $http.get('/new-game/').
        success(function(response) {
          $location.url('/game/' + response.game_id)
          console.log($location.url())
        })
        .error(function(response) {
        });
    };

    function update_principal_board(board){
      if (!board){
        console.log(1)
        $http.get('/principal-board-clicked/').
        success(function(response) {
          $scope.board = response.board
          console.log($scope.board)
        })
        .error(function(response) {
        });
      }else{
        console.log(board)
        $scope.board = board
        
      }
      console.log($scope.board)
      
    }
    $scope.box_clicked = function(e){
        var box_id = $(e.target).attr('id');
        console.log(box_id)
        //angular.element('#'+box_id).toggleClass('black-clicked', $scope.board[i][j]) 
        $http.post('/principal-board-clicked/', {'box_id': box_id} ).
        success(function(response) {
          update_principal_board(response.board)
        })
        .error(function(response) {
        });
    };
    update_principal_board()
}]);

