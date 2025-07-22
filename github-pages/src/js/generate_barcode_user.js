$(function () {

    /* ---------------- CSRF Helper ---------------- */
    function getCookie(name) {
        const v = document.cookie.match('(^|;)\\s*' + name + '=\\s*([^;]+)');
        return v ? v.pop() : '';
    }

    const csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: (xhr, settings) => {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type) && !settings.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            }
        }
    });

    /* ---------------- UI Elements ---------------- */
    const $btn = $('#show-barcode-button');
    const $btnText = $('#button-text');
    const $btnContent = $('#button-content');
    const $progressOverlay = $('#progress-overlay');
    const $barcodeContainer = $('#barcode-container');

    /* ---------------- UI State Management ---------------- */
    function resetUI() {
        $btn.prop('disabled', false)
            .removeClass('btn-success-custom btn-danger-custom btn-processing-custom pulse-effect')
            .addClass('main-button');
        $progressOverlay.removeClass('active').css('width', '0%');
        $btnContent.html('<span id="button-text">PAY / Check-in</span>');
        $barcodeContainer.fadeOut(function () {
            $(this).empty();
        });
        console.log('UI reset');
    }

    function startProcessing() {
        $btn.prop('disabled', true)
            .removeClass('main-button')
            .addClass('btn-processing-custom pulse-effect');

        // 添加加载旋转器
        $btnContent.html(`
                    <div class="spinner"></div>
                    <span>Processing…</span>
                `);

        // 启动进度条动画 - 使用 active 类而不是 processing
        $progressOverlay.addClass('active');

        console.log('Started processing with visual feedback');
    }

    function showSuccess(message) {
        $btn.removeClass('btn-processing-custom')
            .addClass('btn-success-custom pulse-effect');

        $progressOverlay.addClass('active');

        $btnContent.html(`
                    <i class="fa-solid fa-check"></i>
                    <span>${message || 'Success'}</span>
                `);

        // 3秒后停止动画，然后重置
        setTimeout(() => {
            $progressOverlay.removeClass('active').css('width', '100%');
            setTimeout(resetUI, 7000); // 总共10秒
        }, 3000);
    }

    function showError(message) {
        $btn.removeClass('btn-processing-custom')
            .addClass('btn-danger-custom pulse-effect');

        // 进度条继续动画但改变样式
        $progressOverlay.addClass('active');

        $btnContent.html(`
                    <i class="fa-solid fa-exclamation-triangle"></i>
                    <span>${message || 'Error'}</span>
                `);

        // 2 sec anaimation, then reset
        setTimeout(() => {
            $progressOverlay.removeClass('active').css('width', '100%');
            setTimeout(resetUI, 2000);
        }, 2000);
    }

    /* ---------------- PDF417 Rendering ---------------- */
    function drawPDF417(data) {
        PDF417.init(data);
        const barcode = PDF417.getBarcodeArray();

        const bw = 2.5;
        const bh = 1;

        const canvas = document.createElement('canvas');
        canvas.width = bw * barcode['num_cols'];
        canvas.height = bh * barcode['num_rows'];
        canvas.className = 'pdf417';

        $barcodeContainer.empty().append(canvas);

        const ctx = canvas.getContext('2d');
        for (let r = 0; r < barcode['num_rows']; ++r) {
            for (let c = 0; c < barcode['num_cols']; ++c) {
                if (barcode['bcode'][r][c] == 1) {
                    ctx.fillStyle = '#000';
                    ctx.fillRect(c * bw, r * bh, bw, bh);
                }
            }
        }

        $barcodeContainer.fadeIn();
    }

    /* ---------------- Main Click Handler ---------------- */
    $btn.on('click', function () {
        if ($(this).prop('disabled')) {
            return;
        }

        startProcessing();

        $.post("generate_barcode/", {})
            .done(function (resp) {
                if (resp && resp.status === 'success' && resp.barcode) {
                    drawPDF417(resp.barcode);
                    showSuccess(resp.message);
                } else {
                    showError(resp.message || 'Server Error');
                }
            })
            .fail(function () {
                showError('Network Error');
            });
    });
});