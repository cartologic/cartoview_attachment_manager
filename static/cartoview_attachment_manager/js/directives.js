/**
 * Created by kamal on 8/11/16.
 */

angular.module('cartoview.userAttachments').directive('cartoviewComments', function (urls, Comment, $rootScope) {
    return {
        restrict: 'E',
        replace: true,
        scope: {
            layerName: "@"
        },
        template: "<div class='cv-comments'><ng-include src='templateUrl'></ng-include></div>",
        link: function (scope, element, attrs) {


            var template = attrs.template || 'default';
            scope.templateUrl = urls.STATIC_URL + "cartoview_attachment_manager/angular-templates/comments/" + "default" + ".html";
            scope.comment = new Comment(attrs.layerName);
            scope.onKeyPress = function (event) {
                if (event.which == 13 && !event.shiftKey) {
                    scope.addComment()
                }
            };
            scope.addComment = function () {
                console.log(attrs);
                scope.comment.addNew(scope.comment.newCommentText.trim(),attrs.appInstance);
                scope.comment.newCommentText = "";
            };
        }
    }
});

angular.module('cartoview.userAttachments').directive('cartoviewFiles', function (urls, File, $mdDialog) {
    return {
        restrict: 'E',
        replace: true,
        template: "<div class='cv-images'><ng-include src='templateUrl'></ng-include></div>",
        link: function (scope, element, attrs) {
            var template = attrs.template || 'default';
            scope.templateUrl = attrs.templateUrl || (urls.STATIC_URL + "cartoview_attachment_manager/angular-templates/images/" + template + ".html");

            scope.file = new File(attrs.layer_name);
            scope.onKeyPress = function (event) {
                if (event.which == 13 && !event.shiftKey) {
                    scope.addImage()
                }
            };
            scope.addImage = function () {
                scope.image.addNew(scope.image.newImageTitle.trim(), scope.image.imageFile[0].lfFile);
                scope.image.newImageTitle = "";
                scope.image.uploadFileApi.removeAll();
            };
            scope.showImage = function (img) {
                $mdDialog.show({
                    template: '<md-dialog class="cv-images-dialog">'
                    + '<md-dialog-content>'
                    + '<img src="' + img.image + '">'
                    + '</md-dialog-content>'
                    + '</md-dialog>',
                    parent: angular.element(document.body),
                    clickOutsideToClose: true
                });
            };
            scope.showUploadImage = function (ev) {
                $mdDialog.show({
                    controller: DialogController,
                    templateUrl: urls.STATIC_URL + 'user_engage/angular-templates/images/images.dialog.tpl.html',
                    parent: angular.element(document.body),
                    targetEvent: ev,
                    clickOutsideToClose: true,
                    locals: {parentScope: scope},
                    fullscreen: false
                });
            };
            function DialogController($scope, parentScope) {
                $scope.parent = parentScope;
                $scope.cancel = function () {
                    $mdDialog.cancel();
                };
            }

        }
    }
});


angular.module('cartoview.userAttachments').directive('fileModel', ['$parse', function ($parse) {
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            var model = $parse(attrs.fileModel);
            var modelSetter = model.assign;

            element.bind('change', function () {
                scope.$apply(function () {
                    modelSetter(scope, element[0].files[0]);
                });
            });
        }
    };
}]);