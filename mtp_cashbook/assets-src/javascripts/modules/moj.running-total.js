// Running Total module
// Dependencies: moj, _, jQuery

(function () {
  'use strict';

  moj.Modules.RunningTotal = {
    selector: '.js-RunningTotal',

    init: function () {
      _.bindAll(this, 'render', 'updateTotal');
      this.cacheEls();

      if (this.$totalsContainer.length) {
        this.bindEvents();
        this.render();
        this.updateTotal();
      }
    },

    cacheEls: function () {
      this.$items = $('.js-RunningTotal-item');
      this.$totalsContainer = $(this.selector);
      this.label = this.$totalsContainer.data('label');

      this.$label = $('<p>').addClass('print-hidden');
      this.$total = $('<strong>');
    },

    bindEvents: function () {
      moj.Events.on('RunningTotal.render', this.render);
      this.$items.on('change', this.updateTotal);
    },

    updateTotal: function () {
      this.$total.html('&pound;' + this.calculateTotal());
      this.$label
        .text(this.label)
        .append(this.$total);
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
        .attr('aria-atomic', 'false');

      this.$totalsContainer
        .append(this.$label);
    }
  };

})();
