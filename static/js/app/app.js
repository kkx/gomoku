var app = angular.module('myApp', ['ngRoute']);

app.run(function($rootScope, $templateCache) {
   $rootScope.$on('$viewContentLoaded', function() {
      $templateCache.removeAll();
   });
});

//This configures the routes and associates each route with a view and a controller
app.config(function ($routeProvider) {
    $routeProvider
        .when('/',
            {
                controller: 'FakeGameController',
                templateUrl: 'static/js/app/partials/index.html'
            })
        .when('/about/',
            {
                templateUrl: 'static/js/app/partials/about.html'
            })

        .when('/game/:game_id/',
            {
                controller: 'GameController',
                templateUrl: 'static/js/app/partials/game.html'
            })

        .otherwise({
            redirectTo: '/-'
        });
});




