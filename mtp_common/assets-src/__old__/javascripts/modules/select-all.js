// Sticky header module
'use strict';

exports.SelectAll = {
  selector: '.js-SelectAll',

  init: function () {
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
    this.$body
      .on('SelectAll.render', $.proxy(this.render, this))
      .on('change.SelectAll', this.selector, $.proxy(this.onSelectAllChange, this))
      .on('change.SelectAll', this.checksSelector, $.proxy(this.onCheckChange, this))
      .on('keypress.SelectAll', this.checksSelector + ', ' + this.selector, $.proxy(this.onCheckKeypress, this));
  },

  onSelectAllChange: function (e) {
    var clickedEl = e.target;

    this.$checks.each(function () {
      this.checked = clickedEl.checked;
      $(this).change();
    });

    // check all other select all checks,
    // but don't trigger a change to avoid loop
    this.$selectAll.each(function () {
      this.checked = clickedEl.checked;
    });
  },

  onCheckChange: function (e) {
    var $checkEl = $(e.target);
    var $row = $checkEl.closest('tr');

    if ($checkEl.is(':checked')) {
      $row.addClass('mtp-table__highlighted-row');
    } else {
      $row.removeClass('mtp-table__highlighted-row');
    }
  },

  onCheckKeypress: function (e) {
    if (e.keyCode === 13) {
      e.preventDefault();
      return false;
    }
  },

  render: function () {
    this.$checks.each(function () {
      $(this).change();
    });
  }
};
