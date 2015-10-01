/* jshint node: true */

'use strict';

var gulp = require('gulp');
var paths = require('../_paths');
var del = require('del');

gulp.task('clean:css', function(cb) {
  // Ensure the files are deleted before calling next task
  del(paths.dest + 'stylesheets').then(function () {
    cb();
  });
});

gulp.task('clean:images', function(cb) {
  // Ensure the files are deleted before calling next task
  del(paths.dest + 'images').then(function () {
    cb();
  });
});

gulp.task('clean:js', function(cb) {
  // Ensure the files are deleted before calling next task
  del(paths.dest + 'javascripts').then(function () {
    cb();
  });
});

gulp.task('clean', [
  'clean:css',
  'clean:images',
  'clean:js',
]);
