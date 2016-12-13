Design components
=================

This lists the design components that were designed specifically for the Money
to Prisoners services, and explains why we created them on top of
`GOV.UK Elements <http://govuk-elements.herokuapp.com/>`_.

Collapsing Tables
-----------------

.. image:: static/collapsing-tables-open.png
  :align: center

.. image:: static/collapsing-tables-closed.png
  :align: center

.. code-block:: html

  <table class="CollapsingTable">
    <caption class="CollapsingTableHeader" data-collapse-text="Collapse" data-expand-text="Expand">
      Unknown sender (uncredited)
      <span class="CollapsingTableHeader-aside CollapsingTableHeader-aside-right">
        Total: £215.00
      </span>
    </caption>
  <thead>...</thead>
  <tbody>
    ...

Dialogs
-------

Modal dialog
~~~~~~~~~~~~

.. image:: static/dialog.png
  :align: center

.. code-block:: html

  <div id="incomplete-batch-dialog" class="Dialog u-nojs-hidden" data-hide-close="true" data-disable-backdrop-close="true" open="open" tabindex="-1" role="dialog">
    <div class="Dialog-inner">
      <p><strong>Do you want to submit only the selected credits?</strong></p>
      <button type="submit" class="button" value="override">Yes</button>
      <button type="button" class="button button-secondary js-Dialog-close"
              data-analytics="pageview,/batch/-dialog_close/">
        No, continue processing
      </button>
    </div>
  </div>

The dialog will appear on calling the `Dialog.render` function or by using a
link:

.. code-block:: html

  <a href="#some-dialog" class="js-Dialog">Print</a>

Help popup
~~~~~~~~~~

Does what `<details>` does in modern browsers but works in IE8 and also triggers analytics event when used.
C.f. `progressive disclosure <http://govuk-elements.herokuapp.com/typography/#typography-hidden-text>`_

.. image:: static/help-popup-closed.png
  :align: center

.. image:: static/help-popup-open.png
  :align: center

.. code-block:: html

  <div class="help-box help-box-collapsed">
    <div class="help-box-title" aria-controls="help-box-contents" aria-expanded="false" role="heading">
      <div></div><a href="#">Which is right for me?</a>
    </div>
    <div class="panel panel-border-narrow help-box-contents" id="help-box-contents">
      ...

Check boxes
-----------

Purpose: make check boxes more visible than the default IE8 checkbox, and make
the area around them larger than the box itself for easier clicking.

.. image:: static/checkboxes.png
  :align: center

.. code-block:: html

  <td class="check">
    <input type="checkbox" name="credits" id="check-123" class="Checkbox"/>
    <label for="check-123">Credited</label>
  </td>

Form Unload
-----------

Pops up a message if a form is modified and then unloaded (by pressing the back
button or going to another page)

.. image:: static/unload.png
  :align: center

.. code-block:: html

  <form class="js-BeforeUnload" data-unload-msg="Do you want to leave this site?">

Upload
------

Hides the default upload file control and shows something more inline with GOV.UK design

.. image:: static/upload.png
  :align: center

.. image:: static/upload-chosen.png
  :align: center

.. code-block:: html

  <label for="id_location_file" id="id_location_file-label" class="upload-choose button button-secondary">
    Choose file
  </label>

Year field completion
---------------------

Turn a 2-digits year into a 4-digit year when focus leaves a field. E.g. 83 -> 1983.

.. code-block:: html

  <input class="form-control form-year-field" id="id_prisoner_dob_2" name="prisoner_dob_2" value="" type="number">

Pagination
----------

This pattern differs from the `recommendation for GOV.UK <https://designpatterns.hackpad.com/Pagination-erRdhBW8sAK>`_
as it doesn't flush the page links to the right. This was found to be an accessibility issue for
users with screen magnifiers, who don't scroll horizontally much and often miss
links that are on the right hand side of a page.

.. image:: static/pagination.png
  :align: center

.. code-block:: html

  <ul class="Pagination print-hidden">
    <li>
      <a href="?page=1" class="Pagination-current-page">
        <span class="screenreader-only">Page </span><span>1</span>
      </a>
    </li>
    <li>
      <a href="?page=2">
        <span class="screenreader-only">Page </span><span>2</span>
      </a>
    </li>
    <li>
      <a href="?page=3">
        <span class="screenreader-only">Page </span><span>3</span>
      </a>
    </li>
    ...

Sticky header
-------------

A yellow bar that appears as the user scrolls down the credits table, in
order to always show the total amount of credits processed.

.. image:: static/sticky-header.png
  :align: center

.. code-block:: html

  <div class="js-StickyHeader">
    ...
  </div>
