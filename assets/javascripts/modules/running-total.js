// Running Total module
/* globals require, exports */
'use strict';

var bindAll = require('lodash/function/bindAll');

exports.RunningTotal = {
  selector: '.js-RunningTotal',

  init: function () {
    bindAll(this, 'render', 'updateTotal');
    this.cacheEls();

    if (this.$totalsContainer.length) {
      this.bindEvents();
      this.render();
    }
  },

  cacheEls: function () {
    this.$items = $('.js-RunningTotal-item');
    this.$totalsContainer = $(this.selector);
    this.labelText = this.$totalsContainer.data('label');

    this.$label = $('<p>').addClass('print-hidden');
    this.$total = $('<span>').addClass('js-RunningTotal-total');
  },

  bindEvents: function () {
    this.base.Events.on('RunningTotal.render', this.render);
    this.$items.on('change', this.updateTotal);
  },

  updateTotal: function () {
    var total = this.calculateTotal();

    $('.js-RunningTotal-total').html('&pound;' + total);
  },

  calculateTotal: function () {
    var total = 0;

    this.$items.each(function (i, el) {
      var $el = $(el);
      var amount = $el.data('amount');

      if ($el.is(':checked')) {
        total += parseFloat(amount);
      }
    });

    return total.toFixed(2);
  },

  render: function () {
    this.$label
      .attr('aria-live', 'polite')
      .attr('aria-atomic', 'false')
      .html('<span>' + this.labelText + '</span>')
      .append(this.$total);

    this.$totalsContainer
      .append(this.$label);

    this.updateTotal();
  }
};
