$(document).ready(function() {
    $('#verified').click(function() {
        if($(this).attr("checked")) {
            $('#activate').removeAttr('disabled');
        } else {
            $('#activate').attr('disabled', 'disabled');
        }
    });
    $('#activate').attr('disabled', 'disabled');
    $('#type').change(function() {
        if($(this).val() != 0) {
            $('#florlp_name').parents('div.control-group:first').hide();
        } else {
            $('#florlp_name').parents('div.control-group:first').show();
        }
    });
});