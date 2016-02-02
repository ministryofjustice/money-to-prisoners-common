// Help popup module
/* globals exports, $ */
'use strict';

exports.HelpPopup = {

  init: function () {
    var $helpBoxes = $('.help-box');
    var $helpTitle = $('.help-box h3');
    if ($helpBoxes.length) {
      $helpBoxes.addClass('help-box-popup help-box-hidden');
      $helpTitle.on('click', this.toggle);
    }
  },

  toggle: function(event) {
    var $helpBox = $(event.target).closest('div.help-box');
    var $contents = $helpBox.find('.help-box-contents');
    event.preventDefault();
    $contents.toggle();
    $helpBox.toggleClass('help-box-hidden');
    return false;
  }
};
