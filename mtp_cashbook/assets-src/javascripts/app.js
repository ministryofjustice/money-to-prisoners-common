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
        window.setTimeout(function(){
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
        window.setTimeout(function(){
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
    var tour = window.tour = _.extend(tourBase, tourSteps);

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
