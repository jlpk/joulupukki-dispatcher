"use strict";

angular.module("joulupukki.live").service("getProject", [ "$http", function($http) {
    return function($user, $project_name, $get_last_build) {
        var $url = "/v3/users/" + $user + "/" + $project_name + "?get_last_build=1";
        return 0 == $get_last_build && ($url = "/v3/users/" + $user + "/" + $project_name), 
        $http.get($url).error(function() {
            throw new Error("getProject : GET Request failed");
        });
    };
} ]);