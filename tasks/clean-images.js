/* jshint node: true */

'use strict';

var gulp = require('gulp');
var paths = require('./_paths');
var del = require('del');

gulp.task('clean-images', function(cb) {
  del(paths.dest + 'images').then(function () {
    cb();
  });
});
