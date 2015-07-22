/* global $, hopscotch, window */
(function(){
  'use strict';

  var selectAll = $('#select-all'),
      checks = $('.check :checkbox');

  selectAll.on('change', function() {
    var all = this;

    checks.each(function() {
      this.checked = all.checked;
      $(this).change();
    });
  });

  checks.on('change', function() {
    var check = $(this);
    check.closest('tr')[check.is(':checked') ? 'addClass' : 'removeClass']('is-selected');
  });

  hopscotch.highlight = {

    settings: {
      padding: 7
    },

    getStep: function() {
      var stepNo = hopscotch.getCurrStepNum();
      return tour.steps[stepNo];
    },

    getTarget: function(step) {
      var target = step.target;
      return $(typeof target === 'string' ? '#' + target : target);
    },

    show: function() {
      var step = hopscotch.highlight.getStep();
      var target = hopscotch.highlight.getTarget(step);

      target.addClass('hopscotch-highlighted');

      hopscotch.highlight.showHighlight(target, step.table);
      hopscotch.highlight.showOverlay();
    },

    remove: function() {
      $('.hopscotch-highlighted').removeClass('hopscotch-highlighted');
      $('#hopscotch-overlay, #hopscotch-highlight').remove();
    },

    showHighlight: function(el, table) {

      hopscotch.highlight.positionHighlight(el, table);

      // Highlight entire table column
      if (typeof table !== 'undefined') {
        // Bring each cell to foreground
        var i = el.index();
        el.closest('table').find('tbody tr').each(function() {
          $(this).find('td').eq(i).addClass('hopscotch-highlighted');
        });
      }
    },

    positionHighlight: function(el, table) {
      var h = $('#hopscotch-highlight');
      var p = hopscotch.highlight.settings.padding;

      h.css({'top': el.offset().top - p, 'left': el.offset().left - p});
      h.css({'width': el.width() + p * 2, 'height': el.height() + p * 2});

      if (typeof table !== 'undefined') {
        // Resize highlight to column height
        h.css('height', el.closest('table').height() + hopscotch.highlight.settings.padding * 2);
      }
    },

    showOverlay: function() {
      $('<div/>').attr('id', 'hopscotch-overlay').appendTo('body');
    }

  };

  window.onresize = function() {
    // reposition highlight
    var step = hopscotch.highlight.getStep();
    var target = hopscotch.highlight.getTarget(step);
    hopscotch.highlight.positionHighlight(target, step.table);
  };

  var tour = {
    id: 'batch',
    multipage: true,
    steps: [
      {
        content: '<p>You can see what needs to be credited to prisoners in NOMIS by clicking ‘New payments’.</p><p>You’ll get a batch of payment to credit. No-one else in your team will be able to see the batch you’re working on.</p>',
        target: 'tour-step-1',
        padding: 10,
        placement: 'bottom',
        xOffset: 'center'
      },
      {
        content: '<p>You can see all payments you’ve credited to NOMIS in your history.</p>',
        target: 'tour-step-2',
        padding: 10,
        placement: 'bottom',
        xOffset: 'center'
      },
      {
        content: '<p>The table shows payments to be credited to NOMIS.</p>',
        target: 'tour-step1',
        padding: 10,
        placement: 'right'
      },
      {
        content: '<p>Start be entering the prisoner number in NOMIS.</p>',
        target: 'tour-step2',
        padding: 10,
        placement: 'top',
        xOffset: 'center',
        table: 'column'
      },
      {
        content: '<p>Check it matches the prisoner name.</p>',
        target: 'tour-step3',
        padding: 10,
        placement: 'top',
        xOffset: 'center',
        table: 'column'
      },
      {
        content: '<p>Add payment amount as usual.</p>',
        target: 'tour-step4',
        padding: 10,
        placement: 'top',
        xOffset: 'center',
        table: 'column'
      },
      {
        content: '<p>Keep track by ticking payments you’ve credited.</p>',
        target: 'tour-step5',
        padding: 10,
        placement: 'top',
        xOffset: 'center',
        table: 'column'
      },
      {
        content: '<p>Click this button when you’ve finished.</p><p>Any unticked payments will be released for other people in your team to work on. They won’t stay ‘checkout out’ to you.</p>',
        target: 'tour-step6',
        padding: 10,
        placement: 'bottom',
        xOffset: 'center'
      },
      {
        content: '<p>Click ‘Discard’ to stop crediting payments on this page. This will release them to be credited by other people in your team.</p>',
        target: 'tour-step7',
        padding: 10,
        placement: 'bottom',
        xOffset: 'center'
      }
    ],
    i18n: {
      closeTooltip: 'Dismiss'
    },
    onNext: hopscotch.highlight.remove,
    onEnd: hopscotch.highlight.remove,
    onClose: hopscotch.highlight.remove,
    onShow: hopscotch.highlight.show
  };

  // Start the tour!
  hopscotch.startTour(tour);

})();
