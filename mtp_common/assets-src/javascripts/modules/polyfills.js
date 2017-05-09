// (IE) Polyfills module
'use strict';

require('checked-polyfill');

exports.Polyfills = {
  init: function () {
    this.bindEvents();
    this.render();
    this.bind();
  },

  bindEvents: function () {
    $('body').on('Polyfills.render', this.render);
  },

  render: function () {
    // :checked selector polyfill for IE 7/8
    $('input:radio, input:checkbox').checkedPolyfill();
  },

  bind: function () {
    if (!Function.prototype.bind) {
      Function.prototype.bind = function (oThis) {
        if (typeof this !== 'function') {
          // closest thing possible to the ECMAScript 5
          // internal IsCallable function
          throw new TypeError('Function.prototype.bind - what is trying to be bound is not callable');
        }

        var aArgs = Array.prototype.slice.call(arguments, 1);
        var fToBind = this;
        var fNOP = function () {};
        var fBound = function () {
          return fToBind.apply(
            this instanceof fNOP ? this : oThis,
            aArgs.concat(Array.prototype.slice.call(arguments))
          );
        };

        if (this.prototype) {
          // Function.prototype doesn't have a prototype property
          fNOP.prototype = this.prototype;
        }
        fBound.prototype = new fNOP();

        return fBound;
      };
    }
  }
};
