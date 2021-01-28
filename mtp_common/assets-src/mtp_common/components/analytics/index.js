// Google Analytics Utility module
// This module offers ways to send custom events to Google Analytics:
// - by calling Analytics.send. Eg. Analytics.send('event', 'tick', 'checkbox')
// - by adding the data-analytics attribute to any element that can be clicked
//   eg <div data-analytics="pageview,/virtual/pageview/,user clicked there"/>
// It needs the google analytics tracking code to be enabled on the page
/* globals ga */
'use strict';

export var Analytics = {
  attrName: 'analytics',

  init: function () {
    if (this._gaExists()) {
      $('*[data-' + this.attrName + ']').on('click', $.proxy(this._sendFromEvent, this));
    }
  },

  send: function () {
    /*
      Sends to GA passing through all specified arguments.
      It appends an object with page, location and title to the call, if you don't want
      this use rawSend instead.
    */
    if (this._gaExists()) {
      var gaData = $('span.mtp-ga-data');
      if (gaData) {
        var page = gaData.data('page');
        if (arguments[0] === 'pageview' && arguments.length > 1 && $.type(arguments[1]) === 'string') {
          page = arguments[1];
        }
        var gaOverride = {
          page: page,
          location: gaData.data('location'),
          title: gaData.data('title') || document.title
        };
        [].push.call(arguments, gaOverride);
      }
      [].unshift.call(arguments, 'send');
      ga.apply(window, arguments);
    }
  },

  rawSend: function () {
    /*
      Sends to GA passing through all specified arguments.
      Unlike send, it does NOT modify any arguments.
    */
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
