var myApp = angular.module('myApp');
myApp.filter('range', function() {
    return function(input, max, min) {
        if(typeof(min)==='undefined') min = 0;
        min = parseInt(min); //Make string input int
        max = parseInt(max);
        for (var i=min; i<max; i++)
            input.push(i);
        return input;
    };
});
