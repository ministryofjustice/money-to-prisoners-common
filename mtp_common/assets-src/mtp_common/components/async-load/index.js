/**
USAGE:
<span class="mtp-async-load" data-path="<url to load>" data-key="<json key to display>">Loading…</span>
*/
'use strict';

export var AsyncLoad = {
  init: function () {
    $('.mtp-async-load').each(this.load);
  },

  load: function (i, elem) {
    var $elem = $(elem);
    $.ajax({
      'url': $elem.data('path'),
      'method': 'GET',
      'dataType': 'json'
    }).done(function (data) {
      var loadedValue = data[$elem.data('key')];
      if (typeof loadedValue !== 'undefined') {
        $elem.text(loadedValue);
      }
    });
  }
};
