// allow linking directly to an expanded accordion section
'use strict';

export var AccordionDirectLink = {
  init: function () {
    var anchor = window.location.hash;
    if (anchor.length > 0) {
      try {
        var $anchor = $(anchor);
        var $section = null;
        var $sectionHeader = null;
        if ($anchor.hasClass('govuk-accordion__section-header')) {
          // linked to trigger element directly
          $sectionHeader = $anchor;
          $section = $sectionHeader.parents('.govuk-accordion__section').first();
        } else {
          // find containing section and trigger element
          $section = $anchor.parents('.govuk-accordion__section').first();
          $sectionHeader = $section.find('.govuk-accordion__section-heading');
        }
        if ($sectionHeader) {
          $('html, body').scrollTop($section.offset().top - 10);
          if (!$section.hasClass('govuk-accordion__section--expanded')) {
            $sectionHeader.click();
          }
          $sectionHeader.find('button').focus();
        }
      } catch (e) {
        // eslint-disable-line no-empty
      }
    }
  }
};
