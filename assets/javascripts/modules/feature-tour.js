// Feature tour module
/* globals require, exports, tour */
'use strict';

var bindAll = require('lodash/function/bindAll');
var extend = require('lodash/object/extend');
var hopscotch = require('hopscotch');
var hopscotchHighlight = require('hopscotch-highlight').hopscotchHighlight;
var cookie = require('js-cookie');

exports.FeatureTour = {
  init: function () {
    bindAll(this, 'render', 'startOnClick', 'hopscotchOnEnd', 'hopscotchOnClose', 'hopscotchOnShow');
    this.cacheEls();
    this.bindEvents();
  },

  cacheEls: function () {
   this.$startTour = $('.js-FeatureTour-start');

   if (typeof tour !== 'undefined') {
      this.tour = extend(this.hopscotchBase(), tour);
   }

  },

  bindEvents: function () {
    this.base.Events.on('FeatureTour.render', this.render);
    this.$startTour.on('click', this.startOnClick);
    $(window).on('resize', hopscotchHighlight.onresize.bind(hopscotchHighlight));
  },

  startOnClick: function (e) {

    e.preventDefault();

    // if a tour object doesn't exist, return
    if (!this.tour) {
      return;
    }

    // remove any existing cookies for this tour
    cookie.remove('hopscotch.state.' + this.tour.id);
    this.render();
  },

  render: function () {
    // if a tour object doesn't exist, return
    if (!this.tour) {
      return;
    }

    // if already dismissed, return
    if (cookie.get('hopscotch.state.' + this.tour.id) === 'dismissed') {
      return;
    }

    var startStep = parseInt(cookie.get('hopscotch.' + this.tour.id) || 0);
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
      onNext: hopscotchHighlight.remove,
      onEnd: this.hopscotchOnEnd,
      onClose: this.hopscotchOnClose,
      onShow: this.hopscotchOnShow
    };
  },

  hopscotchOnEnd: function () {
    hopscotchHighlight.remove();
    cookie.remove('hopscotch.' + this.tour.id);
    cookie.set('hopscotch.state.' + this.tour.id, 'dismissed');
  },

  hopscotchOnClose: function () {
    var stepNo = hopscotch.getCurrStepNum();

    hopscotchHighlight.remove();
    cookie.set('hopscotch.state.' + this.tour.id, 'dismissed');

    if (this.tour.steps[stepNo].dismissTo) {
      window.setTimeout(function(){
        hopscotch.startTour(this.tour, this.tour.steps[stepNo].dismissTo);
      }, 300);
    }
  },

  hopscotchOnShow: function () {
    var stepNo = hopscotch.getCurrStepNum();

    if (this.tour.steps[stepNo].highlight) {
      hopscotchHighlight.show();
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

    cookie.set('hopscotch.' + this.tour.id, stepNo);
  }
};
