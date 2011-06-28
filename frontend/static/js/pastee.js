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


function pasteError(jq_xhr, text_status, error) {
  if (jq_xhr.status == 403) {
    var error_obj = $.parseJSON(jq_xhr.responseText);
    displayBanner(error_obj['error']);
  } else {
    displayBanner('Error ' + jq_xhr.status + '. Try again later.');
  }
}


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


function loadPasteSuccess(data, text_status, jq_xhr) {
  $('.viewpastebox').html(data);
}


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