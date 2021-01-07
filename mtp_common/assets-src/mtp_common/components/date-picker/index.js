'use strict';

function MTPDatePicker () {
  this.$picker = null;
  this.$field = null;
}

MTPDatePicker.prototype.buildPicker = function () {
  if (this.$picker) {
    return;
  }
  var $picker = $(
    '<div class="mtp-date-picker" aria-hidden="true">' +
    '<div class="mtp-date-picker__top">' +
    '<a href="#" class="mtp-date-picker__prev"></a>' +
    '<span class="mtp-date-picker__label"></span>' +
    '<a href="#" class="mtp-date-picker__next"></a>' +
    '</div>' +
    '<div class="mtp-date-picker__days">' +
    '<span>M</span><span>T</span><span>W</span><span>T</span><span>F</span><span>S</span><span>S</span>' +
    '</div>' +
    '<div class="mtp-date-picker__dates">' +
    '</div>' +
    '</div>'
  );

  $picker.on('keyup', $.proxy(function (e) {
    if (e.keyCode === 27) {
      e.preventDefault();
      this.hide();
    } else if (e.keyCode === 37) {
      e.preventDefault();
      this.previousMonth();
    } else if (e.keyCode === 39) {
      e.preventDefault();
      this.nextMonth();
    }
  }, this));

  $picker.on('click', '.mtp-date-picker__prev', $.proxy(this.previousMonth, this));
  $picker.on('click', '.mtp-date-picker__next', $.proxy(this.nextMonth, this));

  $picker.find('.mtp-date-picker__dates').on('click', 'a', $.proxy(this.selectDate, this));

  $('body').append($picker);
  this.$picker = $picker;
};

MTPDatePicker.prototype.hide = function () {
  if (this.$picker) {
    $('body').off('click.date-picker');
    $(document).off('scroll.date-picker');
    $(window).off('resize.date-picker');
    this.$picker.remove();
    this.$picker = null;
  }
  if (this.$field) {
    this.$field.off('click.date-picker focus.date-picker');
    this.$field = null;
  }
};

MTPDatePicker.prototype.showForField = function ($field) {
  this.buildPicker();

  this.initialDate = null;
  var date = new Date();
  var initial = $field.val();
  var matches = /^(\d\d?)\/(\d\d?)\/(\d\d(\d\d)?)$/.exec(initial);
  if (matches) {
    var year = parseInt(matches[3], 10);
    if (year < 100) {
      var currentYear = new Date().getFullYear();
      year += 100 * Math.floor(currentYear / 100);
      if (year > currentYear) {
        year -= 100;
      }
    }
    var month = parseInt(matches[2], 10) - 1;
    var day = parseInt(matches[1], 10);
    initial = new Date(year, month, day);
    if (initial.getDate() === day && initial.getMonth() === month && initial.getFullYear() === year) {
      date = initial;
      this.initialDate = initial;
    }
  }
  this.year = date.getFullYear();
  this.month = date.getMonth();
  this.drawCalendar();

  this.$field = $field;
  this.$picker.show();
  this.reposition();
  this.$picker.attr('tabindex', '0');
  this.$picker.focus();

  var hideAction = $.proxy(this.hide, this);
  $field.on('click.date-picker focus.date-picker', hideAction);
  $('body').on('click.date-picker', function (e) {
    var $target = $(e.target);
    if (
      !$target.hasClass('mtp-date-picker') && $target.parents('.mtp-date-picker').length === 0 &&
      !$target.hasClass('mtp-date-picker__control') && $target.parents('.mtp-date-picker__control').length === 0
    ) {
      // click is not on picker control and not within picker
      hideAction();
    }
  });
  var repositionAction = $.proxy(this.reposition, this);
  $(document).on('scroll.date-picker', repositionAction);
  $(window).on('resize.date-picker', repositionAction);
};

MTPDatePicker.prototype.reposition = function () {
  var $field = this.$field;
  var position = $field.offset();
  position.top += $field.height() +
    parseInt($field.css('paddingTop'), 10) + parseInt($field.css('paddingBottom'), 10) +
    parseInt($field.css('borderTopWidth'), 10);
  this.$picker.offset(position);
};

MTPDatePicker.prototype.previousMonth = function (e) {
  e && e.preventDefault();
  this.month--;
  if (this.month < 0) {
    this.month = 11;
    this.year--;
  }
  this.drawCalendar();
};

MTPDatePicker.prototype.nextMonth = function (e) {
  e && e.preventDefault();
  this.month++;
  if (this.month > 11) {
    this.month = 0;
    this.year++;
  }
  this.drawCalendar();
};

MTPDatePicker.prototype.selectDate = function (e) {
  e.preventDefault();
  var day = $(e.target).text();
  if (day.length === 1) {
    day = '0' + day;
  }
  var month = (this.month + 1) + '';
  if (month.length === 1) {
    month = '0' + month;
  }
  this.$field.val(day + '/' + month + '/' + this.year);
  this.$field.focus();
  this.hide();
};

MTPDatePicker.prototype.drawCalendar = function () {
  this.$picker.find('.mtp-date-picker__label').text(this.monthLabels[this.month] + ' ' + this.year);

  var today = new Date();
  var $calendar = this.$picker.find('.mtp-date-picker__dates');
  $calendar.empty();
  var i;
  var date;
  var firstDay = new Date(this.year, this.month, 1).getDay() || 7;
  for (i = 1; i < firstDay; i++) {
    $calendar.append('<span></span>');
  }
  for (i = 1; i < 32; i++) {
    date = new Date(this.year, this.month, i);
    if (date.getMonth() !== this.month) {
      break;
    }
    var $dateButton = $('<a href="#"></a>').text(date.getDate());
    if (
      this.initialDate &&
      date.getFullYear() === this.initialDate.getFullYear() &&
      date.getMonth() === this.initialDate.getMonth() &&
      date.getDate() === this.initialDate.getDate()
    ) {
      $dateButton.addClass('mtp-date-picker__initial');
    }
    if (
      date.getFullYear() === today.getFullYear() &&
      date.getMonth() === today.getMonth() &&
      date.getDate() === today.getDate()
    ) {
      $dateButton.addClass('mtp-date-picker__today');
    }
    $calendar.append($dateButton);
  }
};

export var DatePicker = {
  selector: '.mtp-date-picker__control',
  $calendar: null,

  init: function () {
    var $controls = $(this.selector);
    if ($controls.length === 0) {
      return;
    }

    MTPDatePicker.prototype.monthLabels = [
      django.gettext('January'), django.gettext('February'), django.gettext('March'), django.gettext('April'),
      django.gettext('May'), django.gettext('June'), django.gettext('July'), django.gettext('August'),
      django.gettext('September'), django.gettext('October'), django.gettext('November'), django.gettext('December')
    ];

    var picker = new MTPDatePicker();
    $controls.each(function () {
      var $control = $(this);
      var $field = $($control.attr('href'));

      $control.click(function (e) {
        e.preventDefault();
        picker.showForField($field);
      });
    });
  }
};
