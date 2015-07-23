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

  var path = window.location.pathname,
      tour;

  var tourBase = {
    i18n: {
      closeTooltip: 'Dismiss'
    },
    onNext: hopscotch.highlight.remove,
    onEnd: function() {
      hopscotch.highlight.remove();
      Cookies.remove('hopscotch', { path: path });
      Cookies.set('hopscotch.state', 'dismissed', { path: path });
    },
    onClose: function() {
      hopscotch.highlight.remove();
      Cookies.set('hopscotch.state', 'dismissed', { path: path });
    },
    onShow: function() {
      hopscotch.highlight.show();
      Cookies.set('hopscotch', hopscotch.getCurrStepNum(), { path: path });
    }
  };

  if (typeof tourSteps !== 'undefined') {
    tour = _.extend(tourBase, tourSteps);

    var runTour = function(){
      hopscotch.startTour(tour, parseInt(Cookies.get('hopscotch') || 0));
      Cookies.remove('hopscotch.state', { path: path });
    };

    if (Cookies.get('hopscotch.state') !== 'dismissed') {
      runTour();
    }

    $('.start-tour').on('click', function(e){
      e.preventDefault();
      runTour();
    });
  }

})();
