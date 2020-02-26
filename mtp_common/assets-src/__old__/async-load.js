// Async loading of page details
'use strict';

export var AsyncLoad = {
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
      var loadedValue = data[$elem.data('key')];
      if (typeof loadedValue !== 'undefined') {
        $elem.text(loadedValue);
      }
    });
  }
};
