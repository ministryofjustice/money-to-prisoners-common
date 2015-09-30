// Sticky header module
// Dependencies: moj, _, jQuery

(function () {
  'use strict';

  moj.Modules.StickyHeader = {
    selector: '.js-StickyHeader',

    stickyClass: 'is-sticky',

    init: function () {
      _.bindAll(this, 'render', 'onScroll');
      this.cacheEls();

      if (this.$originalHeader.length) {
        this.bindEvents();
        this.render();
      }
    },

    cacheEls: function () {
      this.$originalHeader = $(this.selector);

      if (this.$originalHeader.length) {
        this.$window = $(window);
        this.$body = $('body');
        this.$stickyHeader = this.$originalHeader.clone().addClass(this.stickyClass);
        this.offsetPosition = this.$originalHeader.offset().top + this.$originalHeader.height();
      }
    },

    bindEvents: function () {
      moj.Events.on('StickyHeader.render', this.render);
      this.$window.scroll(this.onScroll);
    },

    onScroll: function () {
      if (this.$window.scrollTop() >= this.offsetPosition) {
        if (!this.$stickyHeader.is(':visible')) {
          this.$stickyHeader
            .css({
              top: -this.$originalHeader.height()
            })
            .show()
            .stop()
            .animate({
              top: 0
            }, 500);
        }
      } else {
        this.$stickyHeader
          .stop()
          .animate({
            top: -this.$originalHeader.height()
          }, 150, 'linear', function () {
            $(this).hide();
          });
      }
    },

    render: function () {
      this.$stickyHeader.hide();
      this.$body.append(this.$stickyHeader);
    }
  };

})();
