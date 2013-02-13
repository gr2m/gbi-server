$(document).ready(function() {
    $('#verified').click(function() {
        if($(this).attr("checked")) {
            $('#activate').removeAttr('disabled');
        } else {
            $('#activate').attr('disabled', 'disabled');
        }
    });
    $('#activate').attr('disabled', 'disabled');
});