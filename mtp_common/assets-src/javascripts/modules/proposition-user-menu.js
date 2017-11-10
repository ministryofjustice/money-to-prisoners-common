// Header user menu
'use strict';

exports.PropositionUserMenu = {
  init: function () {
    var $body = $('body');
    var $userNav = $('#mtp-user-menu');
    var $linksMenu = $('#mtp-user-menu__links');
    var $linksMenuToggle = $('.mtp-user-menu__toggle');

    if (!$linksMenuToggle.length) {
      $linksMenu.remove();
      return;
    }

    $linksMenuToggle.attr({
      'aria-controls': 'mtp-user-menu__links',
      'aria-haspopup': 'true'
    });
    $linksMenu.attr({
      'aria-expanded': 'false',
      'role': 'menu'
    });
    $linksMenu.find('a').attr('role', 'menuitem');

    var closed = true;
    $linksMenuToggle.click(function (e) {
      e.preventDefault();
      closed = !closed;
      if (closed) {
        $linksMenu.attr('aria-expanded', 'true');
        $userNav.removeClass('mtp-user-menu--open');
      } else {
        $linksMenu.attr('aria-expanded', 'false');
        $userNav.addClass('mtp-user-menu--open');
      }
    });

    $body.on('click', function (e) {
      if (!closed && e.target !== $linksMenuToggle[0]) {
        $linksMenuToggle.click();
      }
    })
  }
};
