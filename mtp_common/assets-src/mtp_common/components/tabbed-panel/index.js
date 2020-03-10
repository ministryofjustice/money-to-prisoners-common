'use strict';

import Cookie from 'js-cookie';

export var TabbedPanel = {
  init: function () {
    this.bindEvents($('.mtp-tab'));
  },

  bindEvents: function ($tabButtons) {
    if ($tabButtons.length === 0) {
      return;
    }

    var selectedIndex = 0;
    var closed = true;
    var $tabContainer = $tabButtons.closest('.mtp-tab-container');
    var $tabPanels = $tabContainer.find('.mtp-tabpanel');
    var $tabPanelContainer = $tabPanels.closest('.mtp-tabpanels');
    var tabCookieName = $tabContainer.data('tab-cookie-name');
    var tabCollapsable = $tabContainer.data('tab-collapsable');

    function resetTabsAndPanels (allowTabFocus) {
      $tabButtons.attr({
        'tabindex': '-1',
        'aria-selected': 'false'
      }).removeClass('mtp-tab--selected');
      $tabPanels.attr('aria-hidden', 'true');
      $tabPanels.hide();
      if (allowTabFocus) {
        $tabButtons.eq(selectedIndex).attr('tabindex', '0');
      }
    }

    resetTabsAndPanels(true);

    $tabButtons.each(function () {
      var $tabButton = $(this);
      var $tabPanel = $($tabButton.attr('href'));
      $tabButton.data('mtp-tabpanel', $tabPanel);
      $tabPanel.data('mtp-tab', $tabButton);
    });

    $tabButtons.on('click', function (e) {
      var $tabButton = $(this);
      var $tabPanel = $tabButton.data('mtp-tabpanel');
      var wasSelected = $tabButton.hasClass('mtp-tab--selected');

      $tabButton.focus();
      if (wasSelected) {
        if (tabCollapsable) {
          resetTabsAndPanels(true);
          closed = true;
          $tabContainer.addClass('mtp-tab-container--collapsed');
          $tabPanelContainer.attr('aria-expanded', 'false');
          if (tabCookieName) {
            Cookie.remove(tabCookieName);
          }
        }
      } else {
        resetTabsAndPanels(false);

        closed = false;
        selectedIndex = $tabButtons.index($tabButton);
        $tabButton.attr({
          'tabindex': '0',
          'aria-selected': 'true'
        }).addClass('mtp-tab--selected');
        $tabPanel.attr('aria-hidden', 'false');
        $tabPanel.show();
        $tabContainer.removeClass('mtp-tab-container--collapsed');
        $tabPanelContainer.attr('aria-expanded', 'true');
        if (tabCookieName) {
          Cookie.set(tabCookieName, selectedIndex);
        }
      }

      e.preventDefault();
    });

    $tabContainer.on('keydown', '.mtp-tab', function (e) {
      var key = e.which;

      if (key < 37 || key > 40) {
        return;
      }

      var maxIndex = $tabButtons.length - 1;

      if (key === 37 || key === 38) {
        if (selectedIndex > 0) {
          selectedIndex--;
        } else {
          selectedIndex = maxIndex;
        }
      } else if (key === 39 || key === 40) {
        if (selectedIndex < maxIndex) {
          selectedIndex++;
        } else {
          selectedIndex = 0;
        }
      }

      var $tabButton = $tabButtons.eq(selectedIndex);
      $tabButton.focus();
      if (closed) {
        $tabButtons.attr('tabindex', '-1');
        $tabButton.attr('tabindex', '0');
      } else {
        $tabButton.click();
      }

      e.preventDefault();
    });

    var $tabPanelsWithErrors = $tabPanels.has('.govuk-error-message');
    $tabPanelsWithErrors.each(function () {
      var $tabPanel = $(this);
      $tabPanel.data('mtp-tab').addClass('govuk-error-message');
    });
    if ($tabPanelsWithErrors.length) {
      $tabPanelsWithErrors.first().data('mtp-tab').click();
    } else if (tabCookieName) {
      var lastOpenTab = parseInt(Cookie.get(tabCookieName), 10);
      if ($.isNumeric(lastOpenTab) && lastOpenTab >= 0 && lastOpenTab < $tabButtons.length) {
        $tabButtons.eq(lastOpenTab).click().blur();
      } else if (!tabCollapsable) {
        // if collapsing not allowed and first time on this page, expand first tab
        $tabButtons.eq(0).click().blur();
      }
    }

    $('.mtp-error-summary__field-error a').click(function () {
      var $errorLink = $(this);
      var $fieldLabel = $($errorLink.attr('href'));
      var $tabPanel = $fieldLabel.closest('.mtp-tabpanel');
      if ($tabPanel.is(':hidden')) {
        $tabPanel.data('mtp-tab').click();
      }
    });
  }
};
