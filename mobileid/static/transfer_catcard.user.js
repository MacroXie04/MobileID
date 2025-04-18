// ==UserScript==
// @name         Transfer CatCard Toolkit
// @namespace    http://tampermonkey.net/
// @version      2.1
// @description  Transfer CatCard Toolkit
// @match        https://connect.ucmerced.edu/student/mymerced/_/mymerced*
// @match        https://icatcard.ucmerced.edu/mobileid/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_deleteValue
// @grant        GM_addValueChangeListener
// @connect      catcard.online
// @connect      https://catcard.online/transfer/
// ==/UserScript==

(function () {
    'use strict';

    const myMercedPattern = "connect.ucmerced.edu/student/mymerced";
    const icatcardPattern = "icatcard.ucmerced.edu/mobileid";

    function updateDisplay(text) {
        var liElem = document.getElementById("kgoui_Rcontent_I0_Rcontent_I0_Rcontent_I0_Ritems_I1_OTTransfer");
        if (liElem) {
            liElem.innerHTML = `
                <a href="https://icatcard.ucmerced.edu/mobileid/" class="kgo-grid-item-content" target="_blank" rel="noopener noreferrer">
                  <div class="kgo-image-wrapper">
                    <div id="kgoui_Rcontent_I0_Rcontent_I0_Rcontent_I0_Ritems_I1_Fimage"
                         class="kgoui_object kgoui_image is_be97d55a9b72b7b5f2408a1dd6780679 kgo-crop-style-fill kgo-image">
                      <div class="kgo-image-inner" style="display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 1.5em; font-weight: bold;">${text}</span>
                      </div>
                    </div>
                  </div>
                  <div class="kgo-textblock kgo-margin-xxtight kgo-margin-bottom-xtight">
                    <div class="kgo-title kgo-text kgo-font-style-normal kgo-font-weight-normal">OneTime Transfer CatCard</div>
                  </div>
                </a>
            `;
        }
    }

    // ===============================
    // Display the One-time transfer CatCard link
    // ===============================
    if (window.location.href.indexOf(myMercedPattern) !== -1) {
        function addTransferCatCardLink() {
            var ulElem = document.getElementById("kgoui_Rcontent_I0_Rcontent_I0_Rcontent_I0_Ritems");
            if (!ulElem) return;
            var liElem = document.createElement("li");
            // link a new id to the <li> element
            liElem.id = "kgoui_Rcontent_I0_Rcontent_I0_Rcontent_I0_Ritems_I1_OTTransfer";
            liElem.className = "kgoui_object kgoui_grid_grid_item is_369225fa301c602ae622eaa25adbbe06 kgo-font-size-xsmall kgo-grid-item kgo-has-link";
            liElem.setAttribute("data-type", "content");

            // initial HTML content
            liElem.innerHTML = `
                <a href="https://icatcard.ucmerced.edu/mobileid/" class="kgo-grid-item-content" target="_blank" rel="noopener noreferrer">
                  <div class="kgo-image-wrapper">
                    <div id="kgoui_Rcontent_I0_Rcontent_I0_Rcontent_I0_Ritems_I1_Fimage"
                         class="kgoui_object kgoui_image is_be97d55a9b72b7b5f2408a1dd6780679 kgo-crop-style-fill kgo-image">
                      <div class="kgo-image-inner">
                        <img src="https://kgo-asset-cache.modolabs.net/ucmerced/production/resource_storage/proxy/modulepage/mymerced-_/mymerced/kgoui_Rcontent_I0_Rcontent_I3_Rcontent_I0_Ritems_I3%3Aproperty%3Aimage_common/Icon%20-%20CatCard.34837c1e4601ac1ed.34837c1e4601ac1edb69de51f5292713.png" alt="" aria-hidden="true">
                      </div>
                    </div>
                  </div>
                  <div class="kgo-textblock kgo-margin-xxtight kgo-margin-bottom-xtight">
                    <div class="kgo-title kgo-text kgo-font-style-normal kgo-font-weight-normal">CatCard Transfer Toolkit</div>
                  </div>
                </a>
            `;
            ulElem.appendChild(liElem);

            liElem.addEventListener('click', function () {
                GM_setValue("TransferCatCard", "true");
                GM_setValue("TransferCatCardTime", Date.now().toString());
                GM_deleteValue("TransferResult");
                window.location.href = "https://icatcard.ucmerced.edu/mobileid/";
            });
        }

        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", addTransferCatCardLink);
        } else {
            addTransferCatCardLink();
        }

        var immediateResult = GM_getValue("TransferResult", "");
        if (immediateResult) {
            updateDisplay(immediateResult);
            GM_deleteValue("TransferResult");
        }

        var checkInterval = setInterval(function () {
            var result = GM_getValue("TransferResult", "");
            if (result) {
                updateDisplay(result);
                GM_deleteValue("TransferResult");
                clearInterval(checkInterval);
            }
        }, 500);

        GM_addValueChangeListener("TransferResult", function (name, old_value, new_value) {
            if (new_value) {
                updateDisplay(new_value);
            }
        });
    }

    // ===============================
    // update the display of the transfer result
    // ===============================
    else if (window.location.href.indexOf(icatcardPattern) !== -1) {
        if (GM_getValue("TransferCatCard") === "true") {
            var cookieContent = document.cookie;
            var responded = false;
            // 5 秒计时器：若 5 秒内无响应则显示 "Error"
            var timer = setTimeout(function () {
                if (!responded) {
                    responded = true;
                    GM_setValue("TransferResult", "Error");
                    window.location.href = "https://connect.ucmerced.edu/student/mymerced/_/mymerced";
                }
            }, 5000);

            GM_xmlhttpRequest({
                method: "POST",
                url: "https://catcard.online/transfer/",
                headers: {
                    "Content-Type": "application/json"
                },
                data: JSON.stringify({ cookie: cookieContent }),
                onload: function (response) {
                    if (responded) return;
                    responded = true;
                    clearTimeout(timer);
                    try {
                        var res = JSON.parse(response.responseText);
                        if (res.unique_code) {
                            GM_setValue("TransferResult", res.unique_code);
                        } else {
                            GM_setValue("TransferResult", "Transfer failed");
                        }
                    } catch (e) {
                        GM_setValue("TransferResult", "Error processing response");
                    }
                    GM_deleteValue("TransferCatCard");
                    GM_deleteValue("TransferCatCardTime");
                    window.location.href = "https://connect.ucmerced.edu/student/mymerced/_/mymerced";
                },
                onerror: function (err) {
                    if (responded) return;
                    responded = true;
                    clearTimeout(timer);
                    GM_setValue("TransferResult", "Request error");
                    window.location.href = "https://connect.ucmerced.edu/student/mymerced/_/mymerced";
                }
            });
        }
    }
})();