'use strict';

var gulp = require('gulp');
var paths = require('./_paths');
var rename = require('gulp-rename');

gulp.task('vendor-css', function() {
  return gulp
    .src(paths.css_files)
    .pipe(rename({
      prefix: '_',
      extname: '.scss'
    }))
    .pipe(gulp.dest(paths.src + 'stylesheets/vendor/'));
});
