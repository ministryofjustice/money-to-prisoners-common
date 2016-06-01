// Collapsing tables module
/* globals exports */
'use strict';

exports.CollapsingTableShowHide = {
  init: function () {
    var showHideFunction = this.onShowHide;

    $('.CollapsingTableHeader').each(function() {
      var $header = $(this),
        collapseText = $header.data('collapse-text'),
        expandText = $header.data('expand-text'),
        $button = $('<span class="CollapsingTableShowHide CollapsingTableHeader-aside print-hidden"></span>');

      $button.text(collapseText);
      $button.on('click', $.proxy(showHideFunction, {
        $button: $button,
        $collapseElements: $header.closest('table').find('tbody,thead'),
        collapseText: collapseText,
        expandText: expandText
      }));
      $header.append($button);
    });
  },

  onShowHide: function (e) {
    e.preventDefault();
    if (this.$button.hasClass('CollapsingTableShowHide-hidden')) {
      this.$button.text(this.collapseText);
      this.$button.removeClass('CollapsingTableShowHide-hidden');
    } else {
      this.$button.text(this.expandText);
      this.$button.addClass('CollapsingTableShowHide-hidden');
    }
    this.$collapseElements.toggle();
  }
};
