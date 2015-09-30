// Feature tour module
// Dependencies: moj, _, jQuery, Hopscotch, Cookies

/* globals Cookies, hopscotch, tour */
(function () {
  'use strict';

  moj.Modules.FeatureTour = {
    init: function () {
      _.bindAll(this, 'render', 'startOnClick', 'hopscotchOnEnd', 'hopscotchOnClose', 'hopscotchOnShow');
      this.cacheEls();
      this.bindEvents();
      this.render();
    },

    cacheEls: function () {
     this.$startTour = $('.js-FeatureTour-start');

     if (typeof tour !== 'undefined') {
        this.tour = _.extend(this.hopscotchBase(), tour);
     }
    },

    bindEvents: function () {
      moj.Events.on('FeatureTour.render', this.render);
      this.$startTour.on('click', this.startOnClick);
    },

    startOnClick: function (e) {
      e.preventDefault();

      // if a tour object doesn't exist, return
      if (!this.tour) {
        return;
      }

      // remove any existing cookies for this tour
      Cookies.remove('hopscotch.state.' + this.tour.id);
      this.render();
    },

    render: function () {
      // if a tour object doesn't exist, return
      if (!this.tour) {
        return;
      }

      // if already dismissed, return
      if (Cookies.get('hopscotch.state.' + this.tour.id) === 'dismissed') {
        return;
      }

      var startStep = parseInt(Cookies.get('hopscotch.' + this.tour.id) || 0);
      hopscotch.startTour(this.tour, startStep);
    },

    //
    // Hopscotch patches
    //
    hopscotchBase: function () {
      return {
        i18n: {
          closeTooltip: 'Dismiss'
        },
        onNext: hopscotch.highlight.remove,
        onEnd: this.hopscotchOnEnd,
        onClose: this.hopscotchOnClose,
        onShow: this.hopscotchOnShow
      };
    },

    hopscotchOnEnd: function () {
      hopscotch.highlight.remove();
      Cookies.remove('hopscotch.' + this.tour.id);
      Cookies.set('hopscotch.state.' + this.tour.id, 'dismissed');
    },

    hopscotchOnClose: function () {
      var stepNo = hopscotch.getCurrStepNum();

      hopscotch.highlight.remove();
      Cookies.set('hopscotch.state.' + this.tour.id, 'dismissed');

      if (this.tour.steps[stepNo].dismissTo) {
        window.setTimeout(function(){
          hopscotch.startTour(this.tour, this.tour.steps[stepNo].dismissTo);
        }, 300);
      }
    },

    hopscotchOnShow: function () {
      var stepNo = hopscotch.getCurrStepNum();

      if (this.tour.steps[stepNo].highlight) {
        hopscotch.highlight.show();
      }

      if (this.tour.steps[stepNo].fadeout) {
        window.setTimeout(function(){
          $('.hopscotch-bubble').fadeOut(300, function(){
            hopscotch.endTour(false);
          });
        }, 5000);
      }

      // override the button language for intro step
      if (this.tour.steps[stepNo].target === 'tour-intro') {
        $('.hopscotch-bubble-arrow-container').remove();
        $('.hopscotch-nav-button').text('Yes please');
        $('.hopscotch-bubble-close').text('Not now');
      }

      // focus on next button (prevent keyboard traps)
      $('.hopscotch-next').focus();

      Cookies.set('hopscotch.' + this.tour.id, stepNo);
    }
  };

})();
