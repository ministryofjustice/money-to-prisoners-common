/* jshint node: true */

'use strict';

var mainBowerFiles = require('main-bower-files');
var vendorFiles = mainBowerFiles();

var paths = {
  src: 'mtp_cashbook/assets-src/',
  dest: 'mtp_cashbook/assets/',
  styles: [
      'mtp_cashbook/assets-src/stylesheets/**/*.scss',
      'mtp_cashbook/apps/**/assets-src/stylesheets/**/*.scss'
  ],
  cssFiles: [
    'mtp_cashbook/assets-src/bower_components/hopscotch/dist/css/hopscotch.css'
  ],
  scripts: [
    'mtp_cashbook/assets-src/javascripts/**/*',
    '!mtp_cashbook/assets-src/javascripts/templates.js',
    'mtp_cashbook/apps/**/assets-src/javascripts/**/*',
    '!mtp_cashbook/apps/**/assets-src/javascripts/templates.js'
  ],
  vendorScripts: vendorFiles,
  images: [
      'mtp_cashbook/assets-src/images/**/*',
      'mtp_cashbook/apps/**/assets-src/images/**/*'
  ],
  vendorImages: [
      'mtp_cashbook/assets-src/bower_components/hopscotch-highlight/src/images/**/*'
  ],
  templates: [
      'mtp_cashbook/templates/**/*',
      'mtp_cashbook/apps/**/templates/**/*'
  ]
};

module.exports = paths;
