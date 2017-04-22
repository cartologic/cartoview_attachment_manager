/**
 * Created by kamal on 8/11/16.
 */
angular.module('cartoview.userAttachments', ['ngMaterial', 'ngResource', 'cartoview.urlsHelper', 'ngImageAppear', 'lfNgMdFileInput']);
angular.module('cartoview.userAttachments').config(function ($httpProvider,$resourceProvider) {
    $httpProvider.defaults.withCredentials = true;
    $resourceProvider.defaults.stripTrailingSlashes = false;
});
