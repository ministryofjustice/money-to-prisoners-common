'use strict';

const webpack = require('webpack');

module.exports = {
  mode: 'none',  // overridden with 'production' when app Docker images are built
  entry: './{{ app.javascript_source_path }}/app.js',
  output: {
    path: __dirname + '/{{ app.javascript_build_path }}',
    filename: 'app.js'
  },
  resolve: {
    modules: [
      __dirname + '/node_modules',
      {% for path in app.javascript_include_paths %}
        '{{ path }}'{% if not forloop.last %},{% endif %}
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
