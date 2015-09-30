/* jshint node: true */

'use strict';

var gulp = require('gulp');
var paths = require('./_paths');
var filter = require('gulp-filter');
var concat = require('gulp-concat');

gulp.task('scripts', ['clean-js'], function() {
  var jsFilter = filter('**/*.js');
  var scripts = paths.vendorScripts.concat(paths.scripts);

  return gulp.src(scripts)
    .pipe(jsFilter)
    .pipe(concat('app.js'))
    .pipe(gulp.dest(paths.dest + 'javascripts'));
});
