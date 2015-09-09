'use strict';

var gulp = require('gulp');
var paths = require('./_paths');
var browserSync = require('browser-sync');
var argv = require('yargs').argv;


// Proxy existing server via brower-sync and serve on localhost:3000
gulp.task('serve', ['build'], function() {
  var host = argv.host || argv.h || 'localhost';
  var port = argv.port || argv.p || 8001;

  browserSync.init({
    proxy: host + ':' + port,
    open: false,
    port: 3000
  });

  gulp.watch(paths.templates).on('change', browserSync.reload);;
  gulp.watch(paths.images, ['img-watch']);
  gulp.watch(paths.styles, ['sass']);
  gulp.watch(paths.scripts, ['js-watch']);
});

gulp.task('img-watch', ['images'], browserSync.reload);
gulp.task('js-watch', ['scripts'], browserSync.reload);
