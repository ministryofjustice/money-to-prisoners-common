/* jshint node: true */

'use strict';

var gulp = require('gulp');
var paths = require('./_paths');
var jshint = require('gulp-jshint');
var stylish = require('jshint-stylish');

gulp.task('lint', function() {
  var toLint = paths.scripts.concat(['tasks/*.js', 'gulpfile.js']);

  return gulp
    .src(toLint)
    .pipe(jshint())
    .pipe(jshint.reporter(stylish));
});
