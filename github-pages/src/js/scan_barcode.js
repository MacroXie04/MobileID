document.addEventListener('DOMContentLoaded', function () {
    let codeReader = null;
    let isScanning = false;

    // Debug: Check if ZXing is available
    console.log('ZXing available:', typeof ZXing);
    console.log('Window object keys containing "ZX":', Object.keys(window).filter(k => k.includes('ZX')));

    // Wait for ZXing library to be available with better detection
    function waitForZXing() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 100; // 10 seconds total

            function check() {
                // Check multiple possible ways ZXing might be exposed
                const zxing = window.ZXing || window.zxing || (window.ZXingBrowser && window.ZXingBrowser);

                if (zxing && (zxing.BrowserMultiFormatReader || zxing.BrowserCodeReader)) {
                    console.log('ZXing found:', zxing);
                    resolve(zxing);
                } else if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(check, 100);
                } else {
                    console.error('Available global objects:', Object.keys(window).filter(k => k.toLowerCase().includes('zx')));
                    reject(new Error('ZXing library failed to load after ' + (maxAttempts * 100) + 'ms'));
                }
            }

            check();
        });
    }

    // Initialize scanner when ZXing is ready
    waitForZXing().then((ZXingLib) => {
        try {
            // Try different constructor patterns
            if (ZXingLib.BrowserMultiFormatReader) {
                codeReader = new ZXingLib.BrowserMultiFormatReader();
            } else if (ZXingLib.BrowserCodeReader) {
                codeReader = new ZXingLib.BrowserCodeReader();
            } else {
                throw new Error('No suitable reader found in ZXing library');
            }
            console.log('ZXing scanner initialized successfully:', codeReader);
        } catch (error) {
            console.error('Failed to create scanner:', error);
            codeReader = null;
        }
    }).catch(err => {
        console.error('Failed to initialize scanner:', err);
        // Show user-friendly error
        const scanButton = document.getElementById('toggle-scan-btn');
        if (scanButton) {
            scanButton.innerHTML = 'Scanner Unavailable';
            scanButton.disabled = true;
            scanButton.classList.remove('btn-outline-secondary');
            scanButton.classList.add('btn-outline-danger');
        }
    });

    // Attach event listener to scan button
    const scanButton = document.getElementById('toggle-scan-btn');
    if (scanButton) {
        scanButton.addEventListener('click', function () {
            if (!scanButton.disabled) {
                toggleScan();
            }
        });
    }

    function toggleScan() {
        if (!isScanning) {
            startScanning();
        } else {
            stopScanning();
        }
    }

    function startScanning() {
        if (!codeReader) {
            alert('Scanner not ready. The barcode scanning library failed to load. Please refresh the page and try again.');
            return;
        }

        isScanning = true;
        const btn = document.getElementById('toggle-scan-btn');
        const container = document.getElementById('video-container');
        const video = document.getElementById('scanner-video');
        const overlay = document.getElementById('scanning-overlay');
        const status = document.getElementById('scanner-status');

        if (btn) {
            btn.innerHTML = 'Cancel Scan';
            btn.classList.remove('btn-outline-secondary');
            btn.classList.add('btn-outline-danger');
        }

        if (status) {
            status.textContent = 'Starting camera...';
        }

        if (container) {
            // Show container with animation
            container.style.display = 'block';
            // Force reflow to ensure display:block is applied
            container.offsetHeight;
            setTimeout(() => container.classList.add('show'), 10);
        }

        // Clear any previous video source
        if (video) {
            video.srcObject = null;
            // Set explicit dimensions to prevent overflow
            video.style.width = '100%';
            video.style.height = '100%';
        }

        codeReader.decodeOnceFromVideoDevice(null, 'scanner-video')
            .then(result => {
                console.log('Scanned result:', result.text);

                if (status) {
                    status.textContent = 'Barcode detected! Processing...';
                }

                // Try to find the appropriate input field
                const textInputs = document.querySelectorAll('input[type="text"], input[type="number"], textarea');
                let targetInput = null;

                // Look for input with barcode-related names
                for (let input of textInputs) {
                    const name = input.name.toLowerCase();
                    const id = input.id.toLowerCase();
                    if (name.includes('barcode') || name.includes('code') ||
                        id.includes('barcode') || id.includes('code') ||
                        name.includes('input_value') || name.includes('value')) {
                        targetInput = input;
                        break;
                    }
                }

                // Fallback to last text input
                if (!targetInput && textInputs.length > 0) {
                    targetInput = textInputs[textInputs.length - 1];
                }

                if (targetInput) {
                    targetInput.value = result.text;
                    targetInput.focus();
                    targetInput.dispatchEvent(new Event('input', {bubbles: true}));
                }

                stopScanning();
            })
            .catch(err => {
                console.error('Scanning error:', err);

                if (status) {
                    if (err.name === 'NotAllowedError') {
                        status.textContent = 'Camera access denied';
                    } else if (err.name === 'NotFoundError') {
                        status.textContent = 'No camera found';
                    } else {
                        status.textContent = 'Scanning failed';
                    }
                }

                if (err.name !== 'NotFoundError' && err.name !== 'NotAllowedError') {
                    // Don't alert for common errors
                    setTimeout(() => {
                        alert('Scanning error: ' + err.message)
                    }, 100);
                } else if (err.name === 'NotAllowedError') {
                    setTimeout(() => {
                        alert('Camera access denied. Please allow camera permissions and try again.');
                    }, 100);
                }

                setTimeout(() => stopScanning(), 2000);
            });

        // Show scanning overlay after video starts
        setTimeout(() => {
            if (overlay && isScanning) {
                overlay.style.display = 'block';
                if (status) {
                    status.textContent = 'Looking for barcode...';
                }
            }
        }, 1000);
    }

    function stopScanning() {
        isScanning = false;
        const btn = document.getElementById('toggle-scan-btn');
        const container = document.getElementById('video-container');
        const video = document.getElementById('scanner-video');
        const overlay = document.getElementById('scanning-overlay');
        const status = document.getElementById('scanner-status');

        if (btn) {
            btn.innerHTML = 'Scan Barcode';
            btn.classList.remove('btn-outline-danger');
            btn.classList.add('btn-outline-secondary');
        }

        if (overlay) {
            overlay.style.display = 'none';
        }

        if (status) {
            status.textContent = 'Position the barcode within the camera view';
        }

        if (container) {
            container.classList.remove('show');
            setTimeout(() => {
                container.style.display = 'none';
            }, 500);
        }

        // Stop video stream and clear source
        if (video && video.srcObject) {
            const stream = video.srcObject;
            const tracks = stream.getTracks();
            tracks.forEach(track => {
                track.stop();
                console.log('Stopped camera track:', track.kind);
            });
            video.srcObject = null;
            video.src = '';
            video.load(); // Reset video element
        }

        if (codeReader) {
            try {
                codeReader.reset();
            } catch (err) {
                console.warn('Error resetting scanner:', err);
            }
        }
    }

    /* Disable barcode <select> when pull == "Yes" */
    const pull = document.querySelector('#id_settings-barcode_pull');
    const select = document.querySelector('#id_settings-barcode');

    function toggleSelect() {
        if (!pull || !select) return;
        select.disabled = pull.value === "True";
    }

    if (pull) {
        toggleSelect();
        pull.addEventListener('change', toggleSelect);
    }
});