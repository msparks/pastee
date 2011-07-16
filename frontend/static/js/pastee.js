var _active_paste;


// Initialization.
function init() {
  var pathname = window.location.pathname;

  // Handle redirection.
  if (pathname.indexOf('/x/') == 0) {
    var url = window.location.hash.substr(1);
    redirect(url);
    return;
  }

  if (pathname != '/') {
    loadPaste(pathname.substr(1));
  } else {
    showOnly('new');
  }

  _active_paste = { };

  noWrapMode();
  noLinkifyMode();
}
$(init);


// Re-initialize page state if the back button is clicked.
$(window).bind('popstate', init);


// Short-circuit 'new paste' link.
$('a.new').unbind('click');
$('a.new').click(function(e) {
  // Browsers that support history modification can change the page state
  // without a refresh.
  if (window.history && history.pushState) {
    $('#_content').val('');  // clear only the content field
    showOnly('new');
    history.pushState(null, null, '/');

    // Stop propagation.
    return false;
  }

  return true;
});


// Redirects to 'url'. Employs deep magic to hide the referrer URL.
function redirect(url) {
  if (window.history && history.replaceState) {
    history.replaceState(null, null, '/');
  }
  window.location.href = url;
}


// Shows the view of the given string name and hides all others.
function showOnly(view) {
  var views = new Array('new', 'view');

  // Hide all views.
  for (var v in views)
    $('#' + views[v] + 'paste').hide();

  // Show given view.
  $('#' + view + 'paste').show();
}


// Shows paste-not-found banner.
function displayNotFoundBanner(id) {
  displayBanner('Paste ID \'' + id + '\' does not exist');
}


// Shows message banner with given content.
function displayBanner(html) {
  $('.banner').html(html);
  $('.banner').slideDown();
  setTimeout('hideBanner()', 3000);
}


// Hides the message banner.
function hideBanner() {
  $('.banner').slideUp();
}


// Called when the paste button is clicked.
function pasteClick() {
  var content = $('#_content').val();
  var lexer = $('#_lexer').val();
  var ttl = $('#_ttl').val();
  var encrypt = $('#_encrypt').val();
  var key = $('#_key').val();

  var post_data = {
    content: content,
    lexer: lexer,
    ttl: ttl,
    encrypted: (encrypt == 'yes') ? true : false
  };

  // Disable the 'Paste' button while the request processes.
  $('#pb').attr('disabled', 'disabled');
  $('#pb').html('Pasting');

  $.ajax({
    type: 'POST',
    url: '/api/submit',
    data: post_data,
    success: pasteSuccess,
    error: pasteError,
    complete: pasteComplete
  });
}
$('#pb').click(pasteClick);


// Called when the paste textarea gets focus.
function pasteAreaFocus() {
  $(this).addClass('blur');
}
$('.pastearea').focus(pasteAreaFocus);


// Called when the paste textarea loses focus.
function pasteAreaBlur() {
  if ($('#_content').val() == '')
    $(this).removeClass('blur');
}
$('.pastearea').blur(pasteAreaBlur);


// Called on successful paste to the server.
function pasteSuccess(data, text_status, jq_xhr) {
  // Update address bar with URL of paste.
  if (window.history && history.pushState) {
    history.pushState(null, null, data.id);
    loadPaste(data.id);
  } else {
    // Brower does not support history.pushState.
    window.location.pathname = '/' + data.id;
  }
}


// Called when the paste operation completes, either successfully or
// unsuccessfully.
function pasteComplete(jq_xhr, text_status) {
  // Re-enable paste button.
  $('#pb').removeAttr('disabled');
  $('#pb').html('Paste');
}


// Called on failure to paste to the server.
function pasteError(jq_xhr, text_status, error) {
  if (jq_xhr.status == 403) {
    var error_obj = $.parseJSON(jq_xhr.responseText);
    displayBanner(error_obj.error);
  } else {
    displayBanner('Error ' + jq_xhr.status + '. Try again later.');
  }
}


// Starts an asynchronous paste load with ID 'id'.
function loadPaste(id) {
  showOnly('view');

  // Request paste metadata and content.
  $.ajax({
    type: 'GET',
    url: '/api/get/' + id,
    success: loadPasteSuccess,
    error: loadPasteError
  });
}


function loadPasteSuccess(data, text_status, jq_xhr) {
  // Stop on expired pastes.
  if (expired(data)) {
    displayNotFoundBanner(data.id);
    showOnly('new');
    return;
  }

  // Save paste data to enable reverting.
  _active_paste = data;

  // Set page title.
  $('title').html('Pastee: ' + data.id);

  // Show info bar.
  displayInfoBar(_active_paste);

  // Reset info bar buttons.
  $('.linkify').show();
  $('.wrap').show();

  // Show paste content.
  displayPaste(_active_paste);

  // Update raw and download links.
  $('#viewpaste a.raw').show();
  $('#viewpaste a.raw').attr('href', '/api/get/' + data.id + '/raw');
  $('#viewpaste a.download').show();
  $('#viewpaste a.download').attr('href', '/api/get/' + data.id + '/download');

  // Determine if line-wrapping should be enabled on this paste.
  var lines = data.raw.split('\n');
  var long_lines = 0;
  var nonblank_lines = 0;
  var max_line_length = 0;
  for (i in lines) {
    if (lines[i] != '')
      ++nonblank_lines;
    if (lines[i].length > 82)
      ++long_lines;
    max_line_length = Math.max(max_line_length, lines[i].length);
  }
  var toolong_ratio = long_lines / nonblank_lines;

  var wrap_mode = (toolong_ratio >= 0.5);

  if (wrap_mode)
    wrapMode();
  else if (max_line_length > 82)
    noWrapMode();
  else
    // Don't bother showing wrap button if all lines are short.
    $('.wrap').hide();

  // Determine if linkify mode should be enabled on this paste.
  var linkify_mode = false;
  if (linkify(data.html) != data.html)
    linkify_mode = true;

  if (linkify_mode)
    linkifyMode();
  else
    // No links were found anyway.
    $('.linkify').hide();

  // Show viewmode buttons after possibly hiding some of them.
  $('.viewmodes').show();
}


// Returns true if the given paste is expired (TTL <= 0).
function expired(paste) {
  var now = new Date();
  var epoch = now.getTime() / 1000;        // epoch in seconds
  var expiry = paste.ttl + paste.created;
  var ttl = expiry - epoch;                // ttl in seconds
  return (ttl <= 0);
}


function loadPasteError(jq_xhr, text_status, error) {
  // Reset the page title.
  $('title').html('Pastee');

  if (jq_xhr.status == 404) {
    var id = window.location.pathname.substr(1);
    displayNotFoundBanner(id);
  } else if (jq_xhr.status == 403) {
    var error_obj = $.parseJSON(jq_xhr.responseText);
    displayBanner(error_obj.error);
  } else {
    displayBanner('Error ' + jq_xhr.status + '. Try again later.');
  }

  // Show new paste box.
  showOnly('new');
}


// Updates and displays the paste info bar.
function displayInfoBar(paste) {
  // Calculate TTL in days.
  var now = new Date();
  var epoch = now.getTime() / 1000;        // epoch in seconds
  var expiry = paste.ttl + paste.created;
  var ttl = expiry - epoch;                // ttl in seconds
  var ttl_text;
  var expired = (ttl <= 0);

  if (!expired) {
    // Divide into component parts.
    var ttl_s = ttl;
    var ttl_d_rounded = Math.round(ttl_s / 86400);
    var ttl_d = Math.floor(ttl_s / 86400);
    ttl_s -= ttl_d * 86400;
    var ttl_h = Math.floor(ttl_s / 3600);
    ttl_s -= ttl_h * 3600;
    var ttl_m = Math.floor(ttl_s / 60);
    ttl_s -= ttl_m * 60;
    ttl_s = Math.floor(ttl_s);

    // Friendly TTL text.
    var update_timeout = 60 * 60 * 1000;     // 1 hour by default
    if (ttl_d > 0) {
      // At least one full day left. Don't bother displaying countdown.
      ttl_text = ttl_d_rounded + ' ';
      ttl_text += (ttl_d_rounded == 1) ? 'day' : 'days';
    } else {
      // Less than a day. Countdown.
      ttl_text = (zeroPad(ttl_h, 2) + ':' +
                  zeroPad(ttl_m, 2) + ':' +
                  zeroPad(ttl_s, 2));

      // Update every second.
      update_timeout = 1000;
    }

    // Update the TTL periodically.
    setTimeout(function() { displayInfoBar(paste); }, update_timeout);
  } else {
    ttl_text = 'expired';
  }

  // Show paste info bar.
  $('.viewinfo .viewid').attr('href', '/' + paste.id);
  $('.viewinfo .viewid').html(paste.id);
  if (expired)
    $('.viewinfo .viewid').addClass('expired');
  else
    $('.viewinfo .viewid').removeClass('expired');

  $('.viewinfo .viewlexer').html(paste.lexer);
  $('.viewinfo .viewttl').html(ttl_text);
  $('.viewinfo').show();
}

function zeroPad(n, digits) {
  n = n.toString();
  while (n.length < digits)
    n = '0' + n;
  return n;
}


// Updates and displays the paste content.
function displayPaste(paste) {
  if (paste.linkify_mode) {
    $('.linkify').addClass('selected');
    $('.viewpastebox').html(linkify(paste.html));
  } else {
    $('.linkify').removeClass('selected');
    $('.viewpastebox').html(paste.html);
  }

  if (paste.wrap_mode) {
    $('.linenos').hide();
    $('.syntax pre').addClass('wrapped');
    $('.wrap').addClass('selected');
  } else {
    $('.linenos').show();
    $('.syntax pre').removeClass('wrapped');
    $('.wrap').removeClass('selected');
  }
}


// Turns on word-wrapping for the paste.
function wrapMode() {
  _active_paste.wrap_mode = true;
  displayPaste(_active_paste);
  $('.wrap').unbind('click');
  $('.wrap').click(noWrapMode);
}


// Disables word-wrapping mode for the paste.
function noWrapMode() {
  _active_paste.wrap_mode = false;
  displayPaste(_active_paste);
  $('.wrap').unbind('click');
  $('.wrap').click(wrapMode);
}


// Turns on linkify mode (adds hyperlinks).
function linkifyMode() {
  _active_paste.linkify_mode = true;
  displayPaste(_active_paste);
  $('.linkify').unbind('click');
  $('.linkify').click(noLinkifyMode);

  // Rewrite links to go through cloaking redirection.
  $('.syntax pre a').each(function(idx, e) {
    var href = $(e).attr('href');
    $(e).attr('href', '/x/#' + href);
    $(e).attr('title', href);
    $(e).attr('target', '_blank');
  });
}


// Turns off linkify mode.
function noLinkifyMode() {
  _active_paste.linkify_mode = false;
  displayPaste(_active_paste);
  $('.linkify').unbind('click');
  $('.linkify').click(linkifyMode);
}
