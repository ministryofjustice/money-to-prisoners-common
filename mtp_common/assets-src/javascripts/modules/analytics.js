// Google Analytics Utility module
// This module offers ways to send custom events to Google Analytics:
// - by calling analytics.send. Eg. analytics.send('event', 'tick', 'checkbox')
// - by adding the data-analytics attribute to any element that can be clicked
//   eg <div data-analytics="pageview,/virtual/pageview/,user clicked there"/>
// It needs the google analytics tracking code to be enabled on the page
/* globals ga */
'use strict';

exports.Analytics = {
  attrName: 'analytics',

  init: function () {
    if (this._gaExists()) {
      $('*[data-' + this.attrName + ']').on('click', $.proxy(this._sendFromEvent, this));
    }
  },

  send: function () {
    if (this._gaExists()) {
      [].unshift.call(arguments, 'send');
      ga.apply(window, arguments);
    }
  },

  _sendFromEvent: function (event) {
    var analyticsParams = $(event.currentTarget).data(this.attrName).split(',');
    this.send.apply(this, analyticsParams);
    return true;
  },

  _gaExists: function () {
    return typeof ga === typeof Function;
  }

};
