//  ~ JavaScript Kung-FU, with an excess chunky bacon dose! ~
// This plugin allows seamless ajax file uploads without having
// a fixed file input button. It achieves this by installing an
// OnMouseMove handler over the interested elements, and moving
// the input button under the cursor. <<If Muhammad won't go to
// the the mountain, the mountain will come to Muhammad.>> :-).
//
// This approach is needed on the majority of browser, except
// Safari, on which the coder is allowed to trigger a "click"
// event onto an input type=file element. On other browsers,
// you can not, that's why the complicated mousemove approach
// was chosen.
//
// Either way, when the value of the input type=file changes,
// handlers are disabled, and a user-provided callback is then
// called (passed via the "upload" option). Handlers are then
// re-enabled again when the upload succeeds or fails.
//
// IE has additional problems, because, quite unexplicably,
// when submitting a form that causes a page load, the change
// event on the file input is triggered AGAIN, thus triggering
// a new file upload. To circumvent this, you can pass a "linked"
// option, that contains the jQuery selector of the form, and
// whenever an input under this form is hovered, ajax upload
// handlers are temporarily cleared and thus the spurious form
// submission.
//
// The jquery Form plugin is a perfect companion of this one,
// because of its .ajaxSubmit method. Have a look at its home
// page: http://malsup.com/jquery/form/.
// 
// Have fun!
// - vjt@openssl.it
//
$.fn.ajaxFormUpload = function(options) {
  var positioning = { top: 0, left: 0,
    position: 'absolute', cursor: 'pointer', 'z-index': 2 };

  var form = $(options.form || '#ajax_upload');
  form.css(positioning)

  var input = form.find('input[type=file]');
  input.css($.extend(positioning, { width: '10px', opacity: 0, 'font-size':'0px' }));

  var hovering_element = null;

  var elements = $(this);

  var handler, event_;
  if ($.browser.safari) {
    event_ = 'click', handler = function() {
      hovering_element = $(this);
      input.click();
    };
  } else {
    event_ = 'mousemove', handler = function(event) {
      hovering_element = $(this);
      form.css({ left: event.pageX - 10, top: event.pageY - 5 });
    };
  }

  function enable()  { $(elements).bind(event_, handler);   }
  function disable() { $(elements).unbind(event_, handler); }

  input.change(function() {
    var element = hovering_element;
    if (!element) return;
    disable();

    options.upload(element, form);

    enable();
  });

  enable();

  if (options.linked) {
    $(document).ready(function() {
      $(options.linked).find('input').mouseover(function() { hovering_element = null; });
    });
  }
}