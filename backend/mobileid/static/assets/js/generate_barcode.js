/* CSRF Token */
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

/* Generate Barcode */
$('#show-info-button').click(function () {
    // set button to processing
    $('#server_status').text("Processing");
    $('#show-info-button button').prop('disabled', true);
    $.ajax({
        type: "POST",
        url: "generate_barcode/",
        data: {},
        success: function (response) {
            console.log(response);

            $('#server_status').text(response.content);

            if (response.status === "success") {
                // if the server returns success, we can proceed to generate the barcode
                var magstripWithTimestamp = response.barcode;
                // init PDF417
                PDF417.init(magstripWithTimestamp);
                var barcode = PDF417.getBarcodeArray();

                // set canvas
                var bw = 2.5;
                var bh = 1;

                // create canvas
                var container = document.getElementById('qrcode-div');
                if (container.firstChild) {
                    container.removeChild(container.firstChild);
                }
                var canvas = document.createElement('canvas');
                canvas.setAttribute("id", "canvas");
                canvas.width = bw * barcode['num_cols'];
                canvas.height = bh * barcode['num_rows'];
                container.appendChild(canvas);

                var ctx = canvas.getContext('2d');
                var y = 0;
                for (var r = 0; r < barcode['num_rows']; r++) {
                    var x = 0;
                    for (var c = 0; c < barcode['num_cols']; c++) {
                        if (barcode['bcode'][r][c] == 1) {
                            ctx.fillStyle = '#000000';
                            ctx.fillRect(x, y, bw, bh);
                        } else {
                            ctx.fillStyle = '#FFFFFF';
                            ctx.fillRect(x, y, bw, bh);
                        }
                        x += bw;
                    }
                    y += bh;
                }

                var isFaded = $('#show-info-button').css('display') == 'none';
                if (isFaded) {
                    setTimeout(function () {
                        $('#show-info-button').fadeIn();
                    }, 400);
                    $('#information_id').fadeOut();
                    $('#qrcode-code').fadeOut();
                    $('#qrcode-div').fadeOut();
                } else {
                    $('#show-info-button').fadeOut();
                    setTimeout(function () {
                        $('#qrcode-div').fadeIn();
                        $('#qrcode-code').fadeIn();
                        $('#information_id').fadeIn();

                        // reset progress bar
                        $('.progress-bar').css({
                            "transition": "none",
                            "width": "100%"
                        });
                        setTimeout(function () {
                            $('.progress-bar').css({
                                "transition": "width 10s linear",
                                "width": "0%"
                            });
                        }, 50);
                    }, 400);
                    setTimeout(function () {
                        $('#qrcode-div').fadeOut(400);
                        $('#qrcode-code').fadeOut(400);
                        $('#information_id').fadeOut(400);

                        $('#show-info-button button').prop('disabled', false);
                        $('#server_status').text("Emergency");
                        setTimeout(function () {
                            $('#show-info-button').fadeIn();
                        }, 400);
                    }, 10400);
                }
            } else {
                // show error message
                $('#show-info-button button').prop('disabled', false);
            }
        },
        error: function (xhr, status, error) {
            $('#show-info-button button').prop('disabled', false);
            $('#server_status').text("Error");
        }
    });
});
