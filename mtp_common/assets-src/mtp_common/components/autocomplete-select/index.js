// Find-as-you-type selection menu
'use strict';

import {Analytics} from '../analytics';

export var AutocompleteSelect = {
  init: function () {
    $('.mtp-select--autocomplete').each(this.replaceSelect);
  },

  replaceSelect: function () {
    var $select = $(this);
    var selectID = $select.attr('id');
    var initialValue = $select.val();
    if ($.isArray(initialValue)) {
      initialValue = initialValue.length > 0 ? initialValue[0] : '';
    }
    var initialText = null;
    var choices = $select.find('option').map(function () {
      var $option = $(this);
      var value = $option.val();
      if (value) {
        var name = $option.text();
        if (initialValue === value) {
          initialText = name;
        }
        return {
          name: name,
          value: value
        };
      }
    }).get();
    var $container = $('<div class="mtp-autocomplete-suggestions__container"></div>');
    var $visualInput = $('<input class="govuk-input" type="text" autocomplete="off" />');
    var $suggestions = $('<ul class="mtp-autocomplete-suggestions govuk-list"></ul>');
    var $hiddenInput = $('<input type="hidden" class="mtp-autocomplete-hidden"/>');
    $hiddenInput.data($select.data());
    $hiddenInput.data('visualInput', $visualInput);
    $visualInput.addClass($select.attr('class'));
    if ($visualInput.hasClass('govuk-select--error')) {
      $visualInput.addClass('govuk-input--error');
    }
    $visualInput.removeClass('govuk-select govuk-select--error');
    $hiddenInput.attr('name', $select.attr('name'));
    if (initialText) {
      $visualInput.val(initialText);
      $hiddenInput.val(initialValue);
    }
    $select.after($container);
    $select.remove();
    $container.append($hiddenInput);
    $container.append($visualInput);
    $visualInput.attr('id', selectID);
    $visualInput.after($suggestions);
    $suggestions.attr('aria-controls', selectID);
    $suggestions.attr('aria-label', django.gettext('Suggestions'));
    $suggestions.hide();

    function getSearchTerm () {
      var searchTerm = $visualInput.val() || '';
      return $.trim(searchTerm.replace(/\s+/g, ' ')).toLowerCase();
    }

    var lastSearchTerm = getSearchTerm();

    function clearSuggestions () {
      $suggestions.empty();
      $suggestions.hide();
    }

    function setHiddenValue (value) {
      $hiddenInput.val(value);
      $hiddenInput.change();
    }

    $visualInput.on('change keyup', function () {
      var searchTerm = getSearchTerm();
      if (lastSearchTerm === searchTerm) {
        return;
      }
      lastSearchTerm = searchTerm;
      setHiddenValue('');
      clearSuggestions();
      if (searchTerm.length < 2) {
        return;
      }
      var searchParts = searchTerm.split(' ');
      var suggestions = $.map(choices, function (choice) {
        if (searchParts.length > 0) {
          var results = true;
          $.each(searchParts, function (i, searchPart) {
            results = results && choice.name.toLowerCase().indexOf(searchPart) !== -1;
          });
          if (results) {
            return choice;
          }
        }
      });
      if (suggestions.length > 0 && suggestions.length <= 6) {
        $.each(suggestions, function () {
          var suggestion = this;
          var $suggestion = $('<a href="#"></a>');
          $suggestion.text(suggestion.name);
          $suggestion.click(function (e) {
            e.preventDefault();
            if ($hiddenInput.data('event-category')) {
              var eventCategory = $hiddenInput.data('event-category');
              var eventAction = 'Autocomplete';
              var eventLabel = $visualInput.val() + ' > ' + suggestion.name;
              Analytics.ga4SendEvent(eventCategory, eventAction, eventLabel);
            }

            $visualInput.val(suggestion.name);
            setHiddenValue(suggestion.value);
            clearSuggestions();
            lastSearchTerm = getSearchTerm();
          });
          $suggestions.append($('<li></li>').append($suggestion));
        });
        $suggestions.show();
      }
    });

    return $hiddenInput;
  }
};
