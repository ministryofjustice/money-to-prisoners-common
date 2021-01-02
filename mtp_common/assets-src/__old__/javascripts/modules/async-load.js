// Async loading of page details
'use strict';

exports.AsyncLoad = {
  init: function () {
    $('.js-async-load').each(this.load);
  },

  load: function (i, elem) {
    var $elem = $(elem);
    $.ajax({
      'url': $elem.data('path'),
      'method': 'GET',
      'dataType': 'json'
    }).success(function (data) {
      var loaded_value = data[$elem.data('key')];
      if (typeof loaded_value !== 'undefined') {
        $elem.text(loaded_value);
      }
    });
  }
};
