'use strict';

var gulp = require('gulp');
var paths = require('./_paths');
var filter = require('gulp-filter');
var concat = require('gulp-concat');

gulp.task('scripts', ['clean-js'], function() {
  var scripts = paths.vendor_scripts.concat(paths.scripts);

  var stream = gulp.src(scripts)
    .pipe(concat('app.js'))
    .pipe(gulp.dest(paths.dest + 'javascripts'));

  return stream;
});
