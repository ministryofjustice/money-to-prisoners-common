// BeforeUnload module
// Dependencies: moj, _, jQuery

(function () {
  'use strict';

  moj.Modules.BeforeUnload = {
    selector: '.js-BeforeUnload',

    init: function () {
      _.bindAll(this, 'beforeUnload', 'formSubmit');
      this.cacheEls();
      this.bindEvents();
    },

    cacheEls: function () {
      this.$form = $(this.selector);
      this.initialData = this.$form.serialize();
      this.message = this.$form.data('unload-msg') || '';
      this.submitting = false;
    },

    bindEvents: function () {
      if (this.$form.length > 0) {
        $(window).on('beforeunload', this.beforeUnload);
        this.$form.on('click', ':submit', this.formSubmit);
      }
    },

    formSubmit: function (e) {
      var $btn = $(e.target);
      var type = $btn.val();

      if (type === 'submit' || type === 'override') {
        this.submitting = true;
      } else {
        this.submitting = false;
      }
    },

    beforeUnload: function () {
      if (this.$form.serialize() !== this.initialData && !this.submitting) {
        return this.message;
      }
    }
  };

})();
