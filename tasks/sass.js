/* jshint node: true */

'use strict';

var paths = require('./_paths');
var gulp = require('gulp');
var sass = require('gulp-sass');
var browserSync = require('browser-sync');
var nconf = require('nconf');


function getBowerDir () {
  nconf
    .file({ file: './.bowerrc' })
    .load();

  return __dirname + '/../' + nconf.get('directory') + '/';
}

function getModulePaths (module) {
  var modulePath = getBowerDir() + module + '/paths.json';
  var obj = require(modulePath);

  return obj.import_paths;
}

function getLoadPaths () {
  var bowerDir = getBowerDir();
  var govukImportPaths = getModulePaths('govuk-template');
  var mojularImportPaths = getModulePaths('mojular');
  var joined = govukImportPaths.concat(mojularImportPaths);

  return joined.map(function(path) {
    return bowerDir + '/' + path;
  });
}


gulp.task('sass', ['clean-css', 'vendor-css'], function() {
  var loadPaths = getLoadPaths();

  return gulp.src('mtp_cashbook/assets-src/stylesheets/**/*.scss')
      .pipe(sass({
        outputStyle: 'expanded',
        includePaths: loadPaths
      }).on('error', sass.logError))
      .pipe(gulp.dest(paths.dest + 'stylesheets/'))
      .pipe(browserSync.stream());
});
