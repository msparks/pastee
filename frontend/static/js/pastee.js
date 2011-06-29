var _active_paste;


// Initialization.
function init() {
  var pathname = window.location.pathname;
  if (pathname != '/') {
    loadPaste(pathname.substr(1));
  } else {
    $('#newpaste').show();
  }

  _active_paste = { };

  noWrapMode();
  noLinkifyMode();
}
$(init);


// Shows message banner with given content.
function displayBanner(html) {
  $('.banner').html(html);
  $('.banner').slideDown();
  setTimeout("hideBanner()", 3000);
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

  $.ajax({
    type: 'POST',
    url: '/api/submit',
    data: post_data,
    success: pasteSuccess,
    error: pasteError
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
  $('#newpaste').hide();
  $('#viewpaste').show();
  $('.viewinfo').hide();
  $('.viewmodes').hide();

  // Request paste metadata and content.
  $.ajax({
    type: 'GET',
    url: '/api/get/' + id,
    success: loadPasteSuccess,
    error: loadPasteError
  });
}


function loadPasteSuccess(data, text_status, jq_xhr) {
  // Save paste data to enable reverting.
  _active_paste = data;

  // Calculate TTL in days.
  var d = new Date();
  var epoch = d.getTime() / 1000;              // epoch in seconds
  var expiry = data.ttl + data.created;
  var ttl = expiry - epoch;                    // ttl in seconds
  var ttl_days = ttl / 86400;                  // ttl in days
  ttl_days = Math.round(ttl_days * 100) / 100;

  // Show paste info bar.
  var link_html = '<a href="/' + data.id + '">' + data.id + '</a>';
  $('.viewinfo').html('Paste ID <tt>' + link_html + '</tt> (' +
                      data.lexer + ', TTL: ' + ttl_days + ' days)');
  $('.viewinfo').show();

  // Show paste content.
  displayPaste(_active_paste);

  // Determine if line-wrapping should be enabled on this paste.
  var lines = data.raw.split('\n');
  var total_length = 0;
  var max_line_length = 0;
  for (i in lines) {
    total_length += lines[i].length;
    max_line_length = Math.max(max_line_length, lines[i].length);
  }
  var avg_line_length = total_length / lines.length;
  var wrap_mode = (avg_line_length > 82);  // narrow enough for the viewer

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


function loadPasteError(jq_xhr, text_status, error) {
  if (jq_xhr.status == 404) {
    var id = window.location.pathname.substr(1);
    displayBanner('Paste ID \'' + id + '\' does not exist');
  } else if (jq_xhr.status == 403) {
    var error_obj = $.parseJSON(jq_xhr.responseText);
    displayBanner(error_obj.error);
  } else {
    displayBanner('Error ' + jq_xhr.status + '. Try again later.');
  }

  // Show new paste box.
  $('#viewpaste').hide();
  $('#newpaste').show();
}


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
}


// Turns off linkify mode.
function noLinkifyMode() {
  _active_paste.linkify_mode = false;
  displayPaste(_active_paste);
  $('.linkify').unbind('click');
  $('.linkify').click(linkifyMode);
}
