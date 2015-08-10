'use strict';

var paths = require('./_paths');
var gulp = require('gulp');
var filter = require('gulp-filter');
var sass = require('gulp-ruby-sass');
var browserSync = require('browser-sync');
var nconf = require('nconf');
var reload = browserSync.reload;

gulp.task('sass', ['clean-css', 'vendor-css'], function() {
  nconf.use('file', { file: './.bowerrc' });
  nconf.load();
  var bowerDir = nconf.get('directory');

  nconf.use('file', { file: './' + bowerDir + '/govuk-template/paths.json' });
  nconf.load();

  var govUkImportPaths = nconf.get('import_paths');

  nconf.use('file', { file: './' + bowerDir + '/mojular/paths.json' });
  nconf.load();

  var mojImportPaths = nconf.get('import_paths');

  return gulp
    .src(paths.styles)
    .pipe(sass({
      lineNumbers: true,
      loadPath: govUkImportPaths.concat(mojImportPaths).map(function(i) {
        return bowerDir + '/' + i;
      })
    }))
    .on('error', function (err) { console.log(err.message); })
    .pipe(gulp.dest(paths.dest + 'stylesheets/'))
    .pipe(filter('**/*.css'))  // don't react to .map files when reloading browser
    .pipe(reload({ stream:true }));
});
