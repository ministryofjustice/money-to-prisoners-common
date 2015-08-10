(function(){
  'use strict';

  var selectAll = $('#select-all'),
      checks = $('.check :checkbox');

  selectAll.on('change', function() {
    var all = this;

    checks.each(function() {
      this.checked = all.checked;
      $(this).change();
    });
  });

  checks.on('change', function() {
    var check = $(this);
    check.closest('tr')[check.is(':checked') ? 'addClass' : 'removeClass']('is-selected');
  });

})();
