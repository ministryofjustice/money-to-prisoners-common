// Show-hide module
// usage sample:
//   <a class="u-nojs-hidden ShowHide js-ShowHide" href="#target-selector">
//     <span class="ShowHide-hide">Collapse <span class="ShowHide-icon">&minus;</span></span>
//     <span class="ShowHide-show">Collapsed <span class="ShowHide-icon">&plus;</span></span>
//   </a>
// Dependencies: moj, _, jQuery

/* globals exports, require */
'use strict';

var bindAll = require('lodash/function/bindAll');

exports.ShowHide = {
  selector: '.js-ShowHide',

  init: function () {
    bindAll(this, 'onShowHide');
    this.cacheEls();
    this.bindEvents();
    this.setup();
  },

  cacheEls: function () {
    this.$showHideButtons = $(this.selector);
  },

  bindEvents: function () {
    this.$showHideButtons.on('click', this.onShowHide);
  },

  setup: function () {
    this.$showHideButtons.each(function () {
      var $showHideButton = $(this);
      if ($showHideButton.is('.ShowHide-hidden')) {
        $($showHideButton.attr('href')).hide();
      }
    });
  },

  onShowHide: function (e) {
    e.preventDefault();
    var $showHideButton = $(e.target).closest(this.selector),
      $target = $($showHideButton.attr('href'));
    if ($showHideButton.is('.ShowHide-hidden')) {
      $target.show();
    } else {
      $target.hide();
    }
    $showHideButton
      .toggleClass('ShowHide-hidden');
  }
};
