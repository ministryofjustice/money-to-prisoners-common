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
  ie_styles: 'mtp_cashbook/assets-src/ie/**/*.scss',
  css_files: [
    'mtp_cashbook/assets-src/bower_components/hopscotch/dist/css/hopscotch.css'
  ],
  scripts: [
    'mtp_cashbook/assets-src/javascripts/**/*',
    '!mtp_cashbook/assets-src/javascripts/templates.js',
    'mtp_cashbook/apps/**/assets-src/javascripts/**/*',
    '!mtp_cashbook/apps/**/assets-src/javascripts/templates.js'
  ],
  vendor_scripts: vendorFiles,
  images: [
      'mtp_cashbook/assets-src/images/**/*',
      'mtp_cashbook/apps/**/assets-src/images/**/*'
  ],
  templates: [
      'mtp_cashbook/templates/**/*',
      'mtp_cashbook/apps/**/templates/**/*'
  ]
};

module.exports = paths;
