// Show a warning when an email address domain might be misspelled
'use strict';

import Mailcheck from 'mailcheck';

export var MailcheckWarning = {
  init: function (selector, domains, topLevelDomains, secondLevelDomains) {
    $(selector || '.mtp-mailcheck-warning__input').each(function () {
      var timer;
      var $field = $(this);
      var $messageBox = $('<span class="govuk-hint mtp-mailcheck-warning" aria-live="polite"></span>');
      $field.after($messageBox);

      function showSuggestion (suggestion) {
        if (suggestion && suggestion.domain && suggestion.domain.indexOf('.') > 0) {
          var suggestedEmail = $field.val().split('@');
          suggestedEmail.pop();
          suggestedEmail.push(suggestion.domain);
          suggestedEmail = suggestedEmail.join('@');
          var suggestedEmailLink = $('<a href="#"></a>').text(suggestedEmail).prop('outerHTML');
          $messageBox.html(
            django.interpolate(django.gettext('Did you mean %s?'), [suggestedEmailLink])
          );
          $messageBox.find('a').click(function (e) {
            e.preventDefault();
            $field.val(suggestedEmail);
            $messageBox.empty();
          });
        } else {
          $messageBox.empty();
        }
      }

      function check () {
        Mailcheck.run({
          email: $field.val(),
          domains: domains,
          topLevelDomains: topLevelDomains,
          secondLevelDomains: secondLevelDomains,
          suggested: showSuggestion,
          empty: showSuggestion
        });
      }

      function delayedCheck () {
        if (timer) {
          clearTimeout(timer);
        }
        timer = setTimeout(check, 750);
      }

      $field.blur(check);
      $field.keyup(delayedCheck);
    });
  }
};
