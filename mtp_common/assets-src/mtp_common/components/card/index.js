// based on:
// https://github.com/ministryofjustice/prisonstaffhub/blob/2b9b511e758e13e6ef3290c1c1f3db3748339ce1/static/js/card.js

'use strict';

export var Card = {
  init: function () {
    // for clickable cards, forward a click anwhere inside it to single contained link, if it exists
    $('.mtp-card--clickable').each(function () {
      var $links = $('a', this);
      if ($links.length === 1) {
        var $card = $(this);
        $card.on('click', function (e) {
          if (e.target.nodeName !== 'A') {
            e.stopPropagation();
            $links[0].click();
          }
        });
      }
    });
  }
};
