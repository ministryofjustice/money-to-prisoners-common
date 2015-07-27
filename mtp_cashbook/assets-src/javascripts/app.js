/* global $, _, hopscotch, window, Cookies, tourSteps */
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
      var h = $('<div/>').attr('id', 'hopscotch-highlight').appendTo('body');

      h.css({
        'top': el.offset().top,
        'left': el.offset().left,
        'width': el.outerWidth(),
        'height': el.outerHeight()
      });

      if (typeof table !== 'undefined') {
        // Resize highlight to column height
        h.css('height', el.closest('table').height());
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

  var tour;

  var tourBase = {
    i18n: {
      closeTooltip: 'Dismiss'
    },
    onNext: hopscotch.highlight.remove,
    onEnd: function() {
      hopscotch.highlight.remove();
      Cookies.remove('hopscotch.' + tour.id);
      Cookies.set('hopscotch.state.' + tour.id, 'dismissed');
    },
    onClose: function() {
      var stepNo = hopscotch.getCurrStepNum();

      hopscotch.highlight.remove();

      Cookies.set('hopscotch.state.' + tour.id, 'dismissed');

      if (tour.steps[stepNo].dismissTo) {
        setTimeout(function(){
          hopscotch.startTour(tour, tour.steps[stepNo].dismissTo);
        }, 300);
      }
    },
    onShow: function() {
      var stepNo = hopscotch.getCurrStepNum();

      if (tour.steps[stepNo].highlight) {
        hopscotch.highlight.show();
      }

      if (tour.steps[stepNo].fadeout) {
        setTimeout(function(){
          $('.hopscotch-bubble').fadeOut(300, function(){
            hopscotch.endTour(false);
          });
        }, 5000);
      }

      if (tour.steps[stepNo].target === 'tour-intro') {
        $('.hopscotch-bubble-arrow-container').remove();
        $('.hopscotch-nav-button').text('Yes please');
        $('.hopscotch-bubble-close').text('Not now');
      }

      Cookies.set('hopscotch.' + tour.id, stepNo);
    }
  };

  if (typeof tourSteps !== 'undefined') {
    tour = _.extend(tourBase, tourSteps);

    var runTour = function(){
      hopscotch.startTour(tour, parseInt(Cookies.get('hopscotch.' + tour.id) || 0));
      Cookies.remove('hopscotch.state.' + tour.id);
    };

    if (Cookies.get('hopscotch.state.' + tour.id) !== 'dismissed') {
      runTour();
    }

    $('.start-tour').on('click', function(e){
      e.preventDefault();
      runTour();
    });
  }

})();
