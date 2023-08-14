// Shows a warning message if a form has been filled in but not submitted when navigating away
'use strict';

import {Analytics} from '../analytics';

export var BeforeUnload = {
  selector: '.mtp-form--before-unload',

  init: function () {
    $(this.selector).each(function () {
      var $form = $(this);
      var initialData = $form.serialize();
      var message = $form.data('unload-msg') || '';
      var submitting = false;

      $form.on('click', ':submit', function (e) {
        var $btn = $(e.target);
        var type = $btn.val();

        if (type === 'submit' || type === 'override') {
          submitting = true;
        } else {
          submitting = false;
        }
      });

      $(window).on('beforeunload', function () {
        if ($form.serialize() !== initialData && !submitting) {
          var pageLocation = '/-leaving_page_dialog/';
          Analytics.ga4SendPageView(pageLocation);
          return message;
        }
      });
    });
  }
};
