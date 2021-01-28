'use strict';

import Cookie from 'js-cookie';

export var CookieBanner = {
  cookieName: 'seen_cookie_message',
  selector: '.mtp-cookie-banner',

  init: function () {
    var $banner = $(this.selector);
    if ($banner && Cookie.get(this.cookieName) === undefined) {
      $banner.show();
    }
    Cookie.set(this.cookieName, 'yes', {
      expires: 28
    });
  }
};
