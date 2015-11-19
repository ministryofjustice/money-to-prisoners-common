// Messages module
/* globals exports, require */
'use strict';

var bindAll = require('lodash/function/bindAll');

exports.Messages = {
  selector: '.messages[role=alert]',

  init: function () {
    bindAll(this, 'render');
    this.bindEvents();
    this.render(null, {wrap: 'body'});
  },

  bindEvents: function () {
    this.base.Events.on('Messages.render', this.render);
  },

  render: function (e, params) {
    var $el = $(this.selector, $(params.wrap));

    if ($el.length > 0) {
      $el.focus();
    }
  }
};
