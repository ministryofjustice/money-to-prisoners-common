// Messages module
'use strict';

exports.Messages = {
  selector: '.messages[role=alert]',

  init: function () {
    this.bindEvents();
    this.render(null, {wrap: 'body'});
  },

  bindEvents: function () {
    this.base.Events.on('Messages.render', $.proxy(this.render, this));
  },

  render: function (e, params) {
    var $el = $(this.selector, $(params.wrap));

    if ($el.length > 0) {
      $el.focus();
    }
  }
};
