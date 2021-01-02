/* eslint-disable */
'use strict';

var webpack = require('webpack');

module.exports = {
  mode: 'none',  // overridden with 'production' when app Docker images are built
  entry: '{{ app.root_path }}/{{ app.javascript_source_path }}/app.js',
  output: {
    path: '{{ app.root_path }}/{{ app.javascript_build_path }}',
    filename: 'app.js'
  },
  resolve: {
    modules: [
      '{{ app.root_path }}/node_modules',
      {% for path in app.javascript_include_paths %}
        '{{ app.root_path }}/{{ path }}'{% if not forloop.last %},{% endif %}
      {% endfor %}
    ]
  },
  plugins: [
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery'
    })
  ]
};
