// Batch validation module
// Dependencies: moj, _, jQuery

(function () {
  'use strict';

  moj.Modules.BatchValidation = {
    selector: '.js-BatchValidation',

    init: function () {
      _.bindAll(this, 'onSubmit');
      this.cacheEls();
      this.bindEvents();
    },

    cacheEls: function () {
      this.$body = $('body');
      this.$form = $(this.selector);
      this.transactionsName = this.$form.data('transactions-name');
      this.$transactions = $('[name="' + this.transactionsName + '"]');
    },

    bindEvents: function () {
      moj.Events.on('BatchValidation.render', this.render);
      this.$body
        .on('submit.BatchValidation', this.selector, this.onSubmit);
    },

    _allChecked: function () {
      var allChecked = true;

      this.$transactions.each(function (i, el) {
        var $item = $(el);

        if (!$item.is(':checked')) {
          allChecked = false;
          return false;
        }
      });

      return allChecked;
    },

    _numChecked: function () {
      var count = 0;

      this.$transactions.each(function (i, el) {
        var $item = $(el);

        if ($item.is(':checked')) {
          count += 1;
        }
      });

      return count;
    },

    onSubmit: function (e) {
      var checkedValid = this._allChecked();
      var numChecked = this._numChecked();

      if (numChecked === 0) {
        e.preventDefault();
        // TODO: handle error
      }

      if (!checkedValid) {
        e.preventDefault();
        // TODO: handle error
      }
    }
  };

})();
