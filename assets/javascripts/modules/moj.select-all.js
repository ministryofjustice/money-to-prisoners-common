// Sticky header module
// Dependencies: moj, _, jQuery

(function () {
  'use strict';

  moj.Modules.SelectAll = {
    selector: '.js-SelectAll',

    init: function () {
      _.bindAll(this, 'render', 'onSelectAllChange', 'onCheckChange');
      this.cacheEls();
      this.bindEvents();
      this.render();
    },

    cacheEls: function () {
      this.$body = $('body');
      this.$selectAll = $(this.selector);
      this.fieldName = this.$selectAll.data('name');
      this.checksSelector = '[name="' + this.fieldName + '"]';
      this.$checks = $(this.checksSelector);
    },

    bindEvents: function () {
      moj.Events.on('SelectAll.render', this.render);
      this.$body
        .on('change.SelectAll', this.selector, this.onSelectAllChange)
        .on('change.SelectAll', this.checksSelector, this.onCheckChange)
        .on('keypress.SelectAll', this.checksSelector + ', ' + this.selector, this.onCheckKeypress);
    },

    onSelectAllChange: function (e) {
      var clickedEl = e.target;

      this.$checks.each(function() {
        this.checked = clickedEl.checked;
        $(this).change();
      });

      // check all other select all checks,
      // but don't trigger a change to avoid loop
      this.$selectAll.each(function() {
        this.checked = clickedEl.checked;
      });
    },

    onCheckChange: function (e) {
      var $checkEl = $(e.target);
      var $row = $checkEl.closest('tr');

      if ($checkEl.is(':checked')) {
        $row.addClass('is-selected');
      } else {
        $row.removeClass('is-selected');
      }
    },

    onCheckKeypress: function (e) {
      if (e.keyCode === 13) {
        e.preventDefault();
        return false;
      }
    },

    render: function () {
      this.$checks.each(function() {
        $(this).change();
      });
    }
  };

})();
