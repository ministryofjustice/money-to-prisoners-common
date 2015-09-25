/* jshint node: true */

'use strict';

var path = require('path');
var paths = require('./_paths');
var gulp = require('gulp');
var sass = require('gulp-sass');
var browserSync = require('browser-sync');
var nconf = require('nconf');


function getBowerDir () {
  nconf
    .file({ file: './.bowerrc' })
    .load();

  return path.join(process.cwd(), nconf.get('directory'));
}

function getModulePaths (module) {
  var modulePath = path.join(getBowerDir(), module, 'paths.json');
  var obj = require(modulePath);

  /* jshint camelcase: false */
  return obj.import_paths;
}

function getLoadPaths () {
  var bowerDir = getBowerDir();
  var govukImportPaths = getModulePaths('govuk-template');
  var mojularImportPaths = getModulePaths('mojular');
  var mtpImportPaths = getModulePaths('money-to-prisoners-common');
  var joined = govukImportPaths.concat(mojularImportPaths).concat(mtpImportPaths);

  joined = joined.map(function(originalPath) {
    return path.join(bowerDir, originalPath);
  });

  return joined.concat(bowerDir);
}


gulp.task('sass', ['clean-css', 'vendor-css'], function() {
  var loadPaths = getLoadPaths();

  return gulp.src(paths.styles)
      .pipe(sass({
        outputStyle: 'expanded',
        includePaths: loadPaths
      }).on('error', sass.logError))
      .pipe(gulp.dest(paths.dest + 'stylesheets/'))
      .pipe(browserSync.stream());
});
