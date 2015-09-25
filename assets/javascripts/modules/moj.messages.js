// Messages module
// Dependencies: moj, _, jQuery

(function () {
  'use strict';

  moj.Modules.Messages = {
    selector: '.messages[role=alert]',

    init: function () {
      _.bindAll(this, 'render');
      this.bindEvents();
      this.render(null, {wrap: 'body'});
    },

    bindEvents: function () {
      moj.Events.on('Messages.render', this.render);
    },

    render: function (e, params) {
      var $el = $(this.selector, $(params.wrap));

      if ($el.length > 0) {
        $el.focus();
      }
    }
  };

})();
