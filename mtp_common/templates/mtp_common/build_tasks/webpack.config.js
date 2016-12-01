/* eslint-disable */

var webpack = require('webpack');

module.exports = {
  entry: {
    app: './{{ app.javascript_source_path }}/main.js'
  },
  output: {
    path: './{{ app.javascript_build_path }}',
    filename: '[name].bundle.js'
  },
  module: {
    loaders: [
      {
        include: /\.json$/,
        loaders: ['json-loader']
      }
    ],
    noParse: [
      /\.\/node_modules\/checked-polyfill\/checked-polyfill\.js$/
    ]
  },
  resolve: {
    root: [
      __dirname + '/node_modules'
    ],
    modulesDirectories: [
      {% for path in app.javascript_include_paths %}
        '{{ path }}'{% if not forloop.last %},{% endif %}
      {% endfor %}
    ],
    extensions: ['', '.json', '.js']
  },
  plugins: [
    new webpack.optimize.DedupePlugin(),
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery'
    })
  ]
};
