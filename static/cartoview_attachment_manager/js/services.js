const API_URL = '/api/';
angular.module('cartoview.userAttachments').factory('Comment', function ($resource, urls) {
    var CommentResource = $resource(API_URL + 'comment/:commentId/', {
        layer_name: '@layeName'
    }, {
        update: {
            method: 'PUT'
        }
    });
    var Comment = function (layer_name) {
        var self = this;
        self.layer_name = layer_name;
        self.list = {};
        this.loadAll = function () {
            CommentResource.get({layer_name: layer_name}).$promise.then(function (res) {
                self.list = res;
            });
        };
        this.addNew = function (comment, app_instance_pk) {
            self.saving = true;
            console.log(comment);
            new CommentResource({
                comment: comment,
                app_instance: '/apps/rest/app_manager/appinstances/' + app_instance_pk + '/'
            }).$save({layer_name: layer_name}, function (newComment) {
                self.saving = false;
                self.loadAll();
            }, this);
        };
        this.loadAll();
    };
    return Comment
});

angular.module('cartoview.userAttachments').factory('File', function ($resource, urls, $http) {
    var url = API_URL + 'file/';
    var FileResource = $resource(url + ':imageId', {
        layer_name: '@layer_name'
    }, {
        update: {
            method: 'PUT'
        }
    });
    var File = function (layer_name) {
        var self = this;
        self.layer_name = layer_name;
        self.list = {};
        this.loadAll = function () {
            ImageResource.get({
                layer_name: this.layer_name
            }).$promise.then(function (res) {
                self.list = res;
            });
        };
        this.addNew = function (File,app_instance_pk) {
            self.saving = true;

            new FileResource({
                file: File,
                layer_name: layer_name,
                app_instance:'/apps/rest/app_manager/appinstances/' + app_instance_pk + '/'
            }).$save(function (newComment) {
                self.saving = false;
                self.loadAll();
            }, this);
            // new ImageResource({
            //     title: title,
            //     image:image,
            //     identifier: this.identifier
            // }).$save(function (newImage) {
            //     self.saving = false;
            //     self.loadAll();
            // }, this);
        };
        this.loadAll();
    };
    return Image
});
