import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def send_otc(current_mobile_id_rand, student_id, barcode):
    # using selenium on linux server
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.set_capability("acceptInsecureCerts", False)

    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    #
    # # using selenium on laptop computer
    # chrome_options = Options()
    # chrome_options.set_capability("acceptInsecureCerts", False)
    # chrome_options.add_argument("--headless")
    # driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://icatcard.ucmerced.edu/mobileid/rand.php")

        # using selenium to send the code
        driver.execute_script(
            f"""
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "https://icatcard.ucmerced.edu/mobileid/rand.php", true);
            xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

            xhr.setRequestHeader("Cookie", "session_for%3Aindex_php=8e6df98bc61073a5ac6ba55eb92a9045");

            xhr.onload = function () {{
                document.body.innerHTML = "<pre>" + xhr.responseText + "</pre>";
            }};

            xhr.send("mobileidrand={current_mobile_id_rand}&studentid={student_id}&barcode={barcode}");
            """
        )

        time.sleep(1)

        response_text = driver.find_element(By.TAG_NAME, "pre").text
        print("content：\n", response_text)

        if "added" in response_text.lower():
            print(f"Success with code: {current_mobile_id_rand}")
            return {
                "status": "success",
                "code": current_mobile_id_rand,
                "response": response_text,
            }
        else:
            print(f"Failed with code: {current_mobile_id_rand}")
            return {
                "status": "failed",
                "code": current_mobile_id_rand,
                "response": response_text,
            }

    finally:
        driver.quit()


if __name__ == "__main__":
    # 确保你的系统/浏览器已经信任此站点证书
    # 否则 Selenium 会看到证书错误页面，脚本无法正常访问。
    send_otc(
        current_mobile_id_rand="2992", student_id="S205350209", barcode="62400634511403"
    )
