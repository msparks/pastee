// Initialization.
$(function() {
  var pathname = window.location.pathname;
  if (pathname != '/') {
    loadPaste(pathname.substr(1));
  } else {
    $('#newpaste').show();
  }
});


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
  $(this).css('background-image', 'none');
}
$('.pastearea').focus(pasteAreaFocus);


// Called when the paste textarea loses focus.
function pasteAreaBlur() {
  if ($('#_content').val() == '')
    $(this).css('background-image', 'url(/static/img/pastehere.png)');
}
$('.pastearea').blur(pasteAreaBlur);


// Called on successful paste to the server.
function pasteSuccess(data, text_status, jq_xhr) {
  // Update address bar with URL of paste.
  if (window.history && history.pushState) {
    history.pushState(null, null, data['id']);
    loadPaste(data['id']);
  } else {
    // Brower does not support history.pushState.
    window.location.pathname = '/' + data['id'];
  }
}


// Called on failure to paste to the server.
function pasteError(jq_xhr, text_status, error) {
  if (jq_xhr.status == 403) {
    var error_obj = $.parseJSON(jq_xhr.responseText);
    displayBanner(error_obj['error']);
  } else {
    displayBanner('Error ' + jq_xhr.status + '. Try again later.');
  }
}


// Starts an asynchronous paste load with ID 'id'.
function loadPaste(id) {
  $('#newpaste').hide();
  $('#viewpaste').show();

  $.ajax({
    type: 'GET',
    url: '/api/get/' + id,
    success: loadPasteSuccess,
    error: loadPasteError
  });
}


// Called on successful download of paste content.
function loadPasteSuccess(data, text_status, jq_xhr) {
  $('.viewpastebox').html(data);
}


// Called on error downloading paste content.
function loadPasteError(jq_xhr, text_status, error) {
  if (jq_xhr.status == 404) {
    var id = window.location.pathname.substr(1);
    displayBanner('Paste ID \'' + id + '\' does not exist');
  } else if (jq_xhr.status == 403) {
    var error_obj = $.parseJSON(jq_xhr.responseText);
    displayBanner(error_obj['error']);
  } else {
    displayBanner('Error ' + jq_xhr.status + '. Try again later.');
  }

  $('#viewpaste').hide();
  $('#newpaste').show();
}