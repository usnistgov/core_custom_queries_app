var update_field_verification = function() {
    var formset = $('#formsetZone').find('.nsorte');
    for (var id = 0; id < formset.length; id++) {
        var begin_id = '#id_form-' + id + "-";

        var field_output_field = $(begin_id + 'output_field');
        var field_target = $(begin_id + 'target');
        var field_value = $(begin_id + 'value');
        var field_data_type = $(begin_id + 'data_type');
        var field_restriction = $(begin_id + 'restriction');
        var field_data_min_range = $(begin_id + 'data_min_range');
        var field_data_max_range = $(begin_id + 'data_max_range');
        var field_data_infinity = $(begin_id + 'data_infinity');
        var field_date_range = $(begin_id + 'date_range');

        if (field_output_field.is(':checked')) {
            field_target.prop('disabled', true);
            field_target.val('attribute');

            field_value.prop('disabled', true);
            field_value.val('');

            field_data_type.prop('disabled', true);
            field_data_type.val('data');

            field_restriction.prop('disabled', true);
            field_restriction.prop('checked', false);

            field_data_min_range.prop('disabled', true);
            field_data_min_range.val('');

            field_data_max_range.prop('disabled', true);
            field_data_max_range.val('');

            field_data_infinity.prop('disabled', true);
            field_data_infinity.prop('checked', false);

            field_date_range.prop('disabled', true);
            field_date_range.val('');
        } else {
            field_target.prop('disabled', false);
            field_data_type.prop('disabled', false);

            if (field_target.val() == 'attribute') {
                field_value.prop('disabled', false);
            } else {
                field_value.prop('disabled', true);
                field_value.val('');
            }
        }

        if (field_restriction.is(':checked')) {
            if (field_data_type.val() == 'data') {
                field_data_min_range.prop('disabled', false);

                field_data_max_range.prop('disabled', false);

                field_data_infinity.prop('disabled', false);

                field_date_range.prop('disabled', true);
                field_date_range.val('');
            } else {
                field_data_min_range.prop('disabled', true);
                field_data_min_range.val('');

                field_data_max_range.prop('disabled', true);
                field_data_max_range.val('');

                field_data_infinity.prop('disabled', true);
                field_data_infinity.prop('checked', false);

                field_date_range.prop('disabled', false);
            }
        } else {
            field_data_min_range.prop('disabled', true);
            field_data_min_range.val('');

            field_data_max_range.prop('disabled', true);
            field_data_max_range.val('');

            field_data_infinity.prop('disabled', true);
            field_data_infinity.prop('checked', false);

            field_date_range.prop('disabled', true);
            field_date_range.val('');
        }
    }
};

var select_query_error = function() {
    $(function() {
        $('#dialog-query-error').dialog({
            modal: true,
            buttons: {
                Ok: function() {
                    $(this).dialog('close');
                }
            }
        });
    });
};

var show_delete_query = function() {
    var $delete_query_modal = $("#delete-query-modal");
    $delete_query_modal.modal("show");
}

var delete_query = function() {
    var $delete_query_modal = $("#delete-query-modal");
    var query_id = $("#query_id").html();

    $delete_query_modal.modal("hide");

    $.ajax({
        url : deleteQueryUrl,
        type : "POST",
        dataType: "json",
        data:{
            id: query_id
        },
        success: function(data){
            window.location = listQueriesUrl;
        },
        error: function(data){
            window.location = listQueriesUrl;
        }
    });
};

var updateLimitRecords = function() {
        var input_number_records = $('input[name=number_records]');
        if( ! document.getElementById('id_is_limited').checked ){
            input_number_records.val('');
            input_number_records.prop('disabled', true);
        }
        else{
            if (input_number_records.val() == ''){
                input_number_records.val(1);
            }

           input_number_records.prop('disabled', false);
        }

    };

var select_all_log_files = function() {
    if ($('#id_form-0-DELETE').is(':checked')){
        $("input:checkbox").prop('checked', false);
    }
    else
    {
        $("input:checkbox").prop('checked', true);
    }
};

var reindex_formset = function(formset_zone) {
    var formset = $(formset_zone).find('.nsorte');
    for (var cpt = 0; cpt < formset.length; cpt++) {
        index_form(formset[cpt], cpt);
    }

    $('#id_form-TOTAL_FORMS').val(parseInt(cpt, 10));
};

var set_event = function() {
        $('.bt_rm_sorte').on('click', function() {
            $(this).parents('.nsorte').remove();
            reindex_formset('#formsetZone');
        });
};

var index_form = function(fset, index) {
    $(fset).find(':input').each(function() {
        var name = $(this).attr('name').replace(new RegExp('(__prefix__|\\d)'), index);
        var id = 'id_' + name;
        $(this).attr({
            'name': name,
            'id': id
        });
    });

    $(fset).find('label').each(function() {
        var newFor = $(this).attr('for').replace(new RegExp('(__prefix__|\\d)'), index);
        var id = 'label_' + newFor;
        $(this).attr({
            'id': id,
            'for': newFor
        });
    });
};



var clean_formset = function(formset_zone) {
    var formset = $(formset_zone).find('.nsorte');
    var last_id = formset.length - 1;

    var begin_id = '[name=form-' + last_id + '-';
    var input_begin_id = 'input' + begin_id;
    var select_begin_id = 'select' + begin_id;

    var field_name = $(input_begin_id + 'name]');
    var field_xpath = $(input_begin_id + 'xpath]');
    var field_output_field = $(input_begin_id + 'output_field]');
    var field_target = $(select_begin_id + 'target]');
    var field_value = $(input_begin_id + 'value]');
    var field_data_type = $(select_begin_id + 'data_type]');
    var field_restriction = $(input_begin_id + 'restriction]');
    var field_data_min_range = $(input_begin_id + 'data_min_range]');
    var field_data_max_range = $(input_begin_id + 'data_max_range]');
    var field_data_infinity = $(input_begin_id + 'data_infinity]');
    var field_date_range = $(input_begin_id + 'date_range]');


    field_name.prop('disabled', false);
    field_name.val('');

    field_xpath.prop('disabled', false);
    field_xpath.val('');

    field_output_field.prop('disabled', false);
    field_output_field.attr('checked', false);

    field_target.prop('disabled', false);
    field_target.value = 'attribute';

    field_value.prop('disabled', false);
    field_value.val('');

    field_data_type.prop('disabled', false);
    field_data_type.value = 'data';

    field_restriction.prop('disabled', false);
    field_restriction.attr('checked', false);

    field_data_min_range.prop('disabled', true);
    field_data_min_range.val('');

    field_data_max_range.prop('disabled', true);
    field_data_max_range.val('');

    field_data_infinity.prop('disabled', true);
    field_data_infinity.attr('checked', false);

    field_date_range.prop('disabled', true);
    field_date_range.val('');
};

var updateFieldsAccessibility = function(from) {
    var nameStr = $(from).attr('name');
    var arr = nameStr.split('-');

    var id_param = arr[1];
    var name_param = arr[2];

    var nameBegin = 'form-' + id_param + '-';

    var select_target = $('select[name=' + nameBegin + 'target]');
    var input_value = $('input[name=' + nameBegin + 'value]');
    var select_data_type = $('select[name=' + nameBegin + 'data_type]');
    var input_restriction = $('input[name=' + nameBegin + 'restriction]');
    var input_data_min_range = $('input[name=' + nameBegin + 'data_min_range]');
    var input_data_max_range = $('input[name=' + nameBegin + 'data_max_range]');
    var input_data_infinity = $('input[name=' + nameBegin + 'data_infinity]');
    var input_date_range = $('input[name=' + nameBegin + 'date_range]');


    if (name_param === 'data_infinity') {
        // Infinity check box changed
        if ($(from).prop('checked') === true) {
            // Infinity check box checked
            input_data_max_range.prop('disabled', true);
            input_data_max_range.val('');
        } else {
            // Infinity check box unchecked
            input_data_max_range.prop('disabled', false);
        }
    } else if (name_param == 'target') {
        // Target list changed
        if (select_target.val() === 'attribute') {
            // The target is an attribute
            input_value.prop('disabled', false);
            input_value.val('');
        } else {
            // The target is not an attribute
            input_value.prop('disabled', true);
            input_value.val('');
        }
    } else if (name_param == 'output_field') {
        // The output field check box changed
        if ($(from).prop('checked') === true) {
            // The output field check box checked
            select_target.prop('disabled', true);

            input_value.prop('disabled', true);
            input_value.val('');

            select_data_type.prop('disabled', true);

            input_restriction.prop('disabled', true);
            input_restriction.attr('checked', false);

            input_data_min_range.prop('disabled', true);
            input_data_min_range.val('');
            input_data_max_range.prop('disabled', true);
            input_data_max_range.val('');
            input_data_infinity.prop('disabled', true);
            input_data_infinity.attr('checked', false);

            input_date_range.prop('disabled', true);
            input_date_range.val('');
        } else {
            // The output field check box unchecked
            select_target.prop('disabled', false);

            input_value.prop('disabled', false);
            input_value.val('');

            select_data_type.prop('disabled', false);

            input_restriction.prop('disabled', false);
            input_restriction.attr('checked', true);
        }
    } else if (input_restriction.prop('checked') === false) {
        // There is no restriction
        input_data_min_range.prop('disabled', true);
        input_data_min_range.val('');
        input_data_max_range.prop('disabled', true);
        input_data_max_range.val('');
        input_data_infinity.prop('disabled', true);
        input_data_infinity.attr('checked', false);

        input_date_range.prop('disabled', true);
        input_date_range.val('');
    } else {
        // There is a restriction
        if (select_data_type.val() === 'date') {
            // It's datetime
            input_data_min_range.prop('disabled', true);
            input_data_min_range.val('');
            input_data_max_range.prop('disabled', true);
            input_data_max_range.val('');
            input_data_infinity.prop('disabled', true);
            input_data_infinity.attr('checked', false);

            input_date_range.prop('disabled', false);
        } else {
            // It's a data
            input_data_min_range.prop('disabled', false);
            input_data_max_range.prop('disabled', false);
            input_data_infinity.prop('disabled', false);

            input_date_range.prop('disabled', true);
            input_date_range.val('');

        }
    }
};


$('select').change(function() {
        updateFieldsAccessibility(this);
    });
$('input').change(function() {
        if (this['name'] == 'is_limited'){
            updateLimitRecords();
        }
        else{
            updateFieldsAccessibility(this);
        }
    });

$('#bt_add_sorte').on('click', function() {
        $('#eform').clone(true).appendTo($('#formsetZone'));
        reindex_formset('#formsetZone');
        clean_formset('#formsetZone');
    });
$('.detail_btn').click(function (event) {
    event.preventDefault();
    var id = "detail_" + $(this).val();
    var $details_modal = $("#" + id);
    $details_modal.modal("show");
});

$(document).ready(update_field_verification());
$(document).ready(updateLimitRecords());
$(document).ready(set_event());

$('.btn.delete-query').on('click', show_delete_query);
$('#btn-delete-query').on('click', delete_query);