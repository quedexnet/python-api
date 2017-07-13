'use strict';

var gulp = require('gulp');
var gutil = require('gulp-util');
var writ = require('gulp-writ');
var rename = require('gulp-rename2');
var del = require('del');
var path = require('path');

var config = {};

config.dir = {
  tutorials: './docs/tutorials',
  examples: './examples',
};

config.files = {
  tutorials: path.join(config.dir.tutorials, '*.md'),
  examples: path.join(config.dir.examples, '*.py'),
  deps: './node_modules/**/*',
};

gulp.task('clean', function(callback) {
  return del([ config.files.examples ], { force: true }, callback);
});

gulp.task('generate-examples', [ 'clean' ], function() {
  return gulp.src(config.files.tutorials)
    .pipe(writ().on('error', gutil.log))
    .pipe(rename(function(pathObj, filePath) {
      var basename = pathObj.basename(filePath).replace(/^[0-9]+_/, '');
      return pathObj.dirname(filePath) +'/'+ basename;
    }))
    .pipe(gulp.dest(config.dir.examples))
  ;
});

gulp.task('integration', [ 'generate-examples' ], function() {
  // run generated integration test
});

gulp.task('default', [ 'integration' ]);

gulp.task('watch', [ 'default' ], function() {
  gulp.watch(config.files.tutorials, [ 'integration' ]);
  gulp.watch(config.files.deps, [ 'dist' ]);
});

