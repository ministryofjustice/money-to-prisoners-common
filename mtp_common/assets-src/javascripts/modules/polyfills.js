// (IE) Polyfills module
'use strict';

require('checked-polyfill');

exports.Polyfills = {
  init: function () {
    this.bindEvents();
    this.render();
  },

  bindEvents: function () {
    $('body').on('Polyfills.render', this.render);
  },

  render: function () {
    // :checked selector polyfill for IE 7/8
    $('input:radio, input:checkbox').checkedPolyfill();
  }
};
