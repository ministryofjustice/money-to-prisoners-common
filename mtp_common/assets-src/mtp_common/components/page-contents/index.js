// Sticky page contents
'use strict';

export var PageContents = {
  init: function () {
    this.$anchorContainer = $('.mtp-page-contents');
    if (this.$anchorContainer.length !== 1) {
      return;
    }

    this.$window = $(window);
    this.$anchors = $('.mtp-page-contents__list a');
    this.$headings = this.$anchors.map(function () {
      return $($(this).attr('href'));
    });
    this.$headingContainerParent = $(this.$headings[0]).parent();

    this.update();
    this.$window.on('scroll resize', $.proxy(this.update, this));
  },

  update: function () {
    this.$anchors.removeClass('mtp-page-contents__active-link');
    if (this.$window.width() <= 768) {
      this.dockContents();
      return;
    }

    var containerTop = this.$headingContainerParent.offset().top;
    var scrollOffset = this.$window.scrollTop() - containerTop;
    if (scrollOffset > 0) {
      var offsetPastEnd = this.$headingContainerParent.height() - this.$anchorContainer.height() - scrollOffset - 10;
      if (offsetPastEnd < 0) {
        this.$anchorContainer.css('top', offsetPastEnd + 'px');
      } else {
        this.$anchorContainer.css('top', '0');
      }
      this.floatContents();
    } else {
      this.dockContents();
    }

    var index = -1;
    this.$headings.each(function (i) {
      var $heading = $(this);
      if ($heading.offset().top + $heading.height() - containerTop > scrollOffset) {
        index = i;
        return false;
      }
    });
    $(this.$anchors.get(index)).addClass('mtp-page-contents__active-link');
  },

  floatContents: function () {
    this.$anchorContainer.width(this.$anchorContainer.parent().width());
    this.$anchorContainer.addClass('mtp-page-contents--floated');
  },

  dockContents: function () {
    this.$anchorContainer.width('auto');
    this.$anchorContainer.removeClass('mtp-page-contents--floated');
  }
};
