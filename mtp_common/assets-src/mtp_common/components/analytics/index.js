// Google Analytics Utility module
// This module offers ways to send custom events to Google Analytics:
// - by calling Analytics.send. Eg. Analytics.send('event', 'tick', 'checkbox')
// - by adding the data-analytics attribute to any element that can be clicked
//   eg <div data-analytics="pageview,/virtual/pageview/,user clicked there"/>
// It needs the google analytics tracking code to be enabled on the page
/* globals ga gtag */
'use strict';

export var Analytics = {
  attrName: 'analytics',
  ga4EventName: 'mtp_event',

  init: function () {
    if (this._gaExists()) {
      $('*[data-' + this.attrName + ']').on('click', $.proxy(this._sendFromEvent, this));
    }
    if (this._ga4Exists()) {
      $('*[data-' + this.attrName + ']').on('click', $.proxy(this._ga4SendFromEvent, this));
    }
  },

  /**
   * Sends a custom GA4 'mtp_event' event with category/action/lavel params.
   *
   * NOTE: `category`/`action`/`label` need to be configured in
   * Google Analytics under Admin > Custom definitions.
   *
   * Example
   * ```JavaScript
   * Analytics.ga4SendEvent('PrisonConfirmation', 'Confirm', eventLabel);
   * ```
   *
   * @param {string} category Event category
   * @param {string} action Event action
   * @param {string} label Event label
   */
  ga4SendEvent: function (category, action, label) {
    if (this._ga4Exists()) {
      gtag.apply(window, [
        'event', this.ga4EventName,
        {
          category: category || '',
          action: action || '',
          label: label || '',
        },
      ]);
    }
  },

  /** Sends a GA4 'page_view' event with the give 'page_location'
   *
   * @param {string} pageLocation page location associated to the event
   */
  ga4SendPageView: function (pageLocation) {
    if (this._ga4Exists()) {
      gtag.apply(window, ['event', 'page_view', { 'page_location': pageLocation || '' }]);
    }
  },

  /**
   * Sends a legacy GA custom event or `pageview` event
   *
   * @deprecated GA is deprecated in favour of GA4, use `ga4SendEvent()` or `ga4SendPageView()` instead
   */
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

  /**
   * Sends a legacy GA custom event or `pageview` event
   *
   * @deprecated GA is deprecated in favour of GA4, use `ga4SendEvent()` or `ga4SendPageView()` instead
   */
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

  /** Event handler attached to `data-analytics`'s clicks
   *
   * the `data-analytics` attribute value determines whether a custom `mtp_event` is sent or a
   * `page_view` one.
   *
   * Examples:
   * - `data-analytics="pageview,/batch/-dialog_close/"` sends a `page_view` event with
   *   page_location='/batch/-dialog_close/'
   * - `data-analytics="event,PrisonConfirmation,Add,{{ form.all_prisons_code }}"` sends a
   *   custom `mtp_event` event with category='PrisonConfirmation', action='Add' and
   *   label='{{ form.all_prisons_code }}'
   */
  _ga4SendFromEvent: function (event) {
    var [command, category, action, label] = $(event.currentTarget).data(this.attrName).split(',');
    switch (command) {
      case 'event':
        this.ga4SendEvent(category, action, label);
        break;
      // NOTE: The command in the legacy GA (`ga()`) was called `pageview`. The code still
      //       checks for `pageview` commands to maintain compatibility with existing
      //       markup/`data-analytics` attributes.
      //       This will still send the new GA4 event called `page_view` for page views.
      case 'pageview' :
        this.ga4SendPageView(category);
        break;
    }

    return true;
  },

  /**
   * Returns true if GA's `ga()` (legacy) is available
   *
   * @returns {boolean} true if GA is available
   */
  _gaExists: function () {
    return typeof ga === typeof Function;
  },

  /**
   * Returns true if GA4's `gtag()` is available
   *
   * @returns {boolean} true if GA4 is available
   */
  _ga4Exists: function () {
    return typeof gtag === typeof Function;
  },
};
