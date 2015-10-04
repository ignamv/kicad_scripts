var real_regex = /^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$/;
real = ["Must be a real number", function (string) {
    return real_regex.test(string);
}];
var int_regex = /^[0-9]+$/
integer = ["Must be an integer", function (string) {
    return int_regex.test(string);
}];
positive = ["Must be positive", function(string) {
    return parseFloat(string) > 0;
}];
open_x = ["Spiral doesn't fit in given width", function() {
    return (parseFloat($('#pitch')[0].value) *
            (2 * parseInt($('#turns')[0].value) - 1) + 
            parseFloat($('#pad_size')[0].value)) < parseFloat($('#width')[0].value);
}];
open_y = ["Spiral doesn't fit in given height", function() {
    return (2 * parseFloat($('#pitch')[0].value) *
            parseInt($('#turns')[0].value) + 
            parseFloat($('#pad_size')[0].value)) < parseFloat($('#height')[0].value);
}];
overlapping_traces = ["Trace width must be less than pitch", function() {
    return parseFloat($('#trace_width')[0].value) < parseFloat($('#pitch')[0].value);
}];
fields = { 

};

function validate(tests) 
{
    
    for (var field in tests)
    {
        for (var ii = 0; ii < tests[field].length; ii++)
        {
            condition = tests[field][ii];
            if (!condition[1]($('#'+field)[0].value)) 
            {
                $('#error_'+field).text(condition[0]);
                $('#'+field).addClass('invalid_field');
                return false;
            }
        }
        $('#error_'+field).text('');
        $('#'+field).removeClass('invalid_field');
    }
    return true;
}

function validate_all() 
{
    $('#calculate').prop('disabled', true)
    $('#download').prop('disabled', true)
    if (!validate({
        width: [real, positive],
        height: [real, positive],
        pitch: [real, positive],
        turns: [integer, positive],
        trace_width: [real, positive],
        trace_height: [real, positive],
        frequency: [real, positive],
        pad_size: [real, positive]}))
    {
        return;
    }
    if (!validate({
        width: [open_x],
        height: [open_y],
        trace_width: [overlapping_traces]}))
    {
        return;
    }
    $('#calculate').removeProp('disabled')
    $('#download').removeProp('disabled')
}

var request = null;
function form_submitted(ev)
{
    // TODO: cancel existing requests?
    a = ev;
    b = this;
    if (action == 'download')
    {
        return true;
    }
    request = $.post(ev.target.action, $(this).serialize(), process_response,
            'html');
    request.fail(process_error);
    $('#request_status').text('Request sent...')
    return false;
}

function process_response(data, textStatus, request)
{
    $('#results').html(data);
    $('#request_status').text(' ')
    console.log(data);
    console.log(textStatus);
}

function process_error()
{
    $('#request_status').text('Error: ' + request.statusText);
}

var action;
function save_action() {
    action = this.name;
    return true;
}

$(document).ready(function() {
    fields = [ 'width', 'height', 'pitch', 'turns', 'trace_width', 'trace_height', 'frequency', 'pad_size'];
    for (ii in fields)
    {
        field = fields[ii];
        // Attach validation functions to input change events
        $('#' + field).keyup(function(ev) { validate_all(); });
        $('#' + field).blur(function(ev) { validate_all(); });
        // Create error labels next to the inputs
        var field_error = document.createElement('span');
        field_error.id = 'error_' + field;
        field_error.className = 'field_error';
        $('#' + field).after(field_error);
    }
    //$('#buttons').
    // Create request status label next to the submit button
    var request_status = document.createElement('div');
    request_status.id = 'request_status';
    request_status.appendChild(document.createTextNode(' '));
    $('#buttons').after(request_status);
    // Intercept form submission
    $('#form').submit(form_submitted);
    ajax_tag = document.createElement('input');
    ajax_tag.type = 'hidden';
    ajax_tag.name = 'ajax';
    ajax_tag.value = 'true';
    $('#form').append(ajax_tag);
    $('#download').click(save_action)
    $('#calculate').click(save_action)
})

