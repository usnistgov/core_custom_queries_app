function getCookie (name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = jQuery.trim(cookies[i]);
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) == (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

var myRedirect = function (redirectUrl, arg, value, csrf_token) {
  var form = $('<form action="' + redirectUrl + '" method="post">' + '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf_token + '" />' +
    '<input type="hidden"name="' + arg + '"value="' + value + '"></input>' + '</form>');
  $('body').append(form);
  $(form).submit();
};

var InitBuildRequest = function () {
  $('#id_timeTo').datetimepicker({
    weekStart: 1,
    todayBtn: 1,
    autoclose: 1,
    todayHighlight: 1,
    startView: 2,
    forceParse: 0,
    showMeridian: 1
  });
  $('#id_timeFrom').datetimepicker({
    weekStart: 1,
    todayBtn: 1,
    autoclose: 1,
    todayHighlight: 1,
    startView: 2,
    forceParse: 0,
    showMeridian: 1
  });
};

var previewFile = function () {
  var csv = document.getElementById('id_formats_0').checked;
  var json = document.getElementById('id_formats_1').checked;
  var xml = document.getElementById('id_formats_2').checked;
  var content = '';

  $('#filePreviewCustomQueries').value = content;
  if (csv === true) {
    content = $('#id_preview_file_csv').val() + '...';
  } else if (json === true) {
    content = $('#id_preview_file_json').val() + '...';
  } else if (xml === true) {
    content = $('#id_preview_file_xml').val() + '...';
  }

  content = content.replace(/(?:\\[rn]|[\r\n]+)+/g, '</p>');
  content = content.replace(/(?:\\[t])/g, '    ');
  content = content.replace(/(?:\\)/g, '');

  content = content.split('</p>');

  var textArea = document.getElementById('filePreviewCustomQueries');
  textArea.value = content.join('\n');
};

function getCookie (name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = jQuery.trim(cookies[i]);
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) == (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

var downloadfile = function () {
  var csv = document.getElementById('id_formats_0').checked;
  var json = document.getElementById('id_formats_1').checked;
  var xml = document.getElementById('id_formats_2').checked;
  var csrftoken = getCookie('csrftoken');

  if (csv === true || json === true || xml === true) {
    $('input[name=csrfmiddlewaretoken]').val(csrftoken);
    $('#form_custom_queries').submit();
  }
};

var select_result_error = function () {
  $(function () {
    $('#dialog-result-message').dialog({
      modal: true,
      buttons: {
        Ok: function () {
          $(this).dialog('close');
        }
      }
    });
  });
};

var back_to_query = function (url) {
  var queryName = $('#id_hidden_query_name').val();
  window.location.href = url + '?queryName=' + queryName;
};

var previous_step = function () {
    $('#id_step_back').val('True');
};

var first_step = function () {
  if ($('input[id="id_first_step"]').length > 0) {
    if (document.getElementById('id_first_step').value === "True") {
      document.getElementById('id_prev_button').disabled = true;
    }
  }

  if ($('input[id="id_query_0"]').length > 0) {
    document.getElementById('button_select_query').disabled = false;
  }
};

$.fn.buttonLoader = function (action) {
    var self = $(this);
    //start loading animation
    if (action == 'start') {
        //disable buttons when loading state
//        $('.has-spinner').attr("disabled", "disabled");
        $(self).attr('data-btn-text', $(self).text());
        //binding spinner element to button and changing button text
        $(self).html('<span class="spinner"><i class="fa fa-spinner fa-spin"></i></span> Loading');
        $(self).addClass('active');
    }
    //stop loading animation
    if (action == 'stop') {
        $(self).html($(self).attr('data-btn-text'));
        $(self).removeClass('active');
        //enable buttons after finish loading
        $('.has-spinner').removeAttr("disabled");
    }
};

$(document).ready(function () {
    $('.button-right').buttonLoader('stop');
    $('.button-left').buttonLoader('stop');
    first_step();

    $('.button-right').click(function () {
     var btn = $(this);
        $(btn).buttonLoader('start');
    });

    $('.button-left').click(function () {
     var btn = $(this);
        previous_step();
        $(btn).buttonLoader('start');
    });

});

$(document).on('click', '.recover_btn', function (event) {
    event.preventDefault();
    $('input[id="to_recover"]').val($(this).val());
    $('form[id="form_history"]').submit();
});

$(document).on('click', '.btn_all_history', function (event) {
    if ($('#id_form-0-DELETE').is(':checked')){
        $("input:checkbox").prop('checked', false);
    }
    else
    {
        $("input:checkbox").prop('checked', true);
    }
});
