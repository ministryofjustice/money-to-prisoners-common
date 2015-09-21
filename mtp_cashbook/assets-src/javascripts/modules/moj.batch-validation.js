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
      this.$form.on('click', ':submit', this.onSubmit);
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
      var $el = $(e.target);
      var type = $el.val();
      var checkedValid = this._allChecked();
      var numChecked = this._numChecked();

      if(type !== 'submit') {
        return;
      }

      if (numChecked === 0) {
        e.preventDefault();
        moj.Events.trigger({
          type: 'Dialog.render',
          target: e.target,
          targetSelector: '#empty-selection-dialog'
        });
        return;
      }

      if (!checkedValid) {
        e.preventDefault();
        moj.Events.trigger({
          type: 'Dialog.render',
          target: e.target,
          targetSelector: '#incomplete-batch-dialog'
        });
        return;
      }
    }
  };

})();
