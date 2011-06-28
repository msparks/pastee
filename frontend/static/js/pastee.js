// Initialization.
$(function() {
  var pathname = window.location.pathname;
  if (pathname != '/') {
    loadPaste(pathname.substr(1));
  } else {
    $('#newpaste').show();
  }
});


// Hook for clicking paste button.
$('#pb').click(function() {
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
});


function pasteSuccess(data, text_status, jq_xhr) {
  // Update address bar with URL of paste.
  history.pushState(null, null, data['id']);
  loadPaste(data['id']);
}


function pasteError(jq_xhr, text_status, error) {
  alert(text_status + ": " + error);
}


function loadPaste(id) {
  $('#newpaste').hide();
  $('#viewpaste').show();

  $.ajax({
    type: 'GET',
    url: '/api/get/' + id,
    success: function(data) {
      $('.viewpastebox').html(data);
    }
  });
}