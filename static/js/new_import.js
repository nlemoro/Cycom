$(document).ready(function () {

    var default_offer_spot_duration = 2; // in month

    function formatFunc(data) {
        return data.name;
    }

    function formatSelectionFunc(data) {
        return data.name;
    }

    var d = new Date();
    var curr_year = d.getFullYear();
    var curr_month = ("0" + (d.getMonth() + 1)).slice(-2);
    var curr_date = ("0" + d.getDate()).slice(-2);
    var curr_hour = ("0" + d.getHours()).slice(-2);
    var curr_minutes = ("0" + d.getMinutes()).slice(-2);
    var curr_seconds = ("0" + d.getSeconds()).slice(-2);
    var curr_milliseconds = ("00" + d.getMilliseconds()).slice(-3);

    var today = curr_year + "-" + curr_month + "-" + curr_date;
    $('#date_import').val(today);


    $('form').submit(function (event) {
            var path = $('#file').val();
            var fileName = path.split('/').pop();
            if (fileName == path) {
                fileName = path.split('\\').pop();
            }
            $('#fileName').val(fileName);
        }
    );


});
