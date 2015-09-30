/* jshint node: true */

'use strict';

var gulp = require('gulp');
var paths = require('./_paths');
var del = require('del');

gulp.task('clean-css', function(cb) {
  del(paths.dest + 'stylesheets').then(function () {
    cb();
  });
});
