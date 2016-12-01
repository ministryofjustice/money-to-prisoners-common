// Collapsing tables module
'use strict';

exports.CollapsingTable = {
  init: function () {
    var showHideFunction = this.onShowHide;

    $('.CollapsingTableHeader').each(function () {
      var $header = $(this),
        collapseText = $header.data('collapse-text'),
        expandText = $header.data('expand-text'),
        $button = $('<a href="#" class="CollapsingTableShowHide CollapsingTableHeader-aside print-hidden"></a>');

      $button.text(collapseText);
      $button.on('click', $.proxy(showHideFunction, {
        $button: $button,
        $collapseElements: $header.closest('table').find('tbody, thead'),
        collapseText: collapseText,
        expandText: expandText
      }));
      $header.append($button);
    });
  },

  collapseAll: function () {
    $('.CollapsingTableShowHide').each(function () {
      var $header = $(this).parent('.CollapsingTableHeader');
      $(this).text($header.data('expand-text'));
      $(this).addClass('CollapsingTableShowHide-hidden');
      $(this).closest('table').find('tbody, thead').hide();
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
