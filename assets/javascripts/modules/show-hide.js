// Show-hide module

/* globals exports */
'use strict';

exports.ShowHide = {
  collapsedText: '&ominus; Collapsed',
  expandedText: '&oplus; Collapse',

  init: function () {
    $('.HistoryHeader').append('<span class="ShowHide HistoryHeader-aside">'+this.expandedText+'</span>');

    this.$showHideButtons = $('.ShowHide');
    this.$showHideButtons.on('click', this.onShowHide.bind(this));
  },

  onShowHide: function (e) {
    var $target = $(e.target);
    e.preventDefault();
    if ($target.hasClass('ShowHide-hidden')) {
      $target.html(this.expandedText);
      $target.removeClass('ShowHide-hidden');
    } else {
      $target.html(this.collapsedText);
      $target.addClass('ShowHide-hidden');
    }
    $target.closest('table').find('tbody,thead').toggle();

  }
};
