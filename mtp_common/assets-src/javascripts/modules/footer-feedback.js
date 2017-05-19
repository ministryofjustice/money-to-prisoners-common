// Feedback form that goes in footer and is submitted using AJAX
'use strict';

exports.FooterFeedback = {
  init: function () {
    $('.mtp-footer-feedback').each(this.bind);
  },

  bind: function (i, form) {
    var $form = $(form);
    var returnErrorsParam = $form.data('return-errors-param');
    var $ticketInput = $form.find('[name=ticket_content]');
    var $submitButton = $form.find('[type=submit]');
    var $successMessage = $form.find('.mtp-footer-feedback__success');
    var $errorMessage = $form.find('.mtp-footer-feedback__error');
    $errorMessage.data('fallback-error', $errorMessage.text());

    function errorField (field) {
      $form.find('[name=' + field + ']').addClass('form-control-error')
        .closest('.form-group').addClass('form-group-error');
    }

    $form.submit(function (e) {
      e.preventDefault();

      $errorMessage.hide();
      $successMessage.hide();
      $errorMessage.text($errorMessage.data('fallback-error'));
      $form.find('.form-group-error').removeClass('form-group-error');
      $form.find('.form-control-error').removeClass('form-control-error');

      if ($ticketInput.val().replace(/^\s+|\s+$/g, '').length === 0) {
        errorField('ticket_content');
        return;
      }

      $submitButton.prop('disabled', true);
      $.ajax({
        'url': $form.attr('action'),
        'method': 'POST',
        'data': $form.serializeArray()
      }).done(function (data) {
        var errors = data[returnErrorsParam];
        if (!$.isEmptyObject(errors)) {
          // field errors
          $.each(errors, errorField);
          // non-field errors
          if (errors.__all__) {
            $errorMessage.empty();
            $.each(errors.__all__, function (i, error) {
              var $errorLine = $('<span></span>');
              $errorLine.text(error.message || error);
              $errorMessage.append($errorLine);
              if (i < errors.__all__.length - 1) {
                $errorMessage.append('<br>');
              }
            });
          }
          $errorMessage.show();
        } else {
          $ticketInput.val('');
          $successMessage.show();
        }
      }).fail(function () {
        $errorMessage.show();
      }).always(function () {
        $submitButton.prop('disabled', false);
      });
    });
  }
};
