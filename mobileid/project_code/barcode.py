import json
import platform
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def setup_driver():
    chrome_options = Options()
    chrome_options.set_capability("acceptInsecureCerts", False)
    chrome_options.add_argument("--headless")

    if platform.system() == "Linux":
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        chrome_options.binary_location = "/usr/bin/google-chrome"
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    elif platform.system() == "Darwin":
        driver = webdriver.Chrome(options=chrome_options)
    else:
        raise Exception("Unsupported operating system")

    return driver


def send_otc(current_mobile_id_rand, student_id, barcode):
    driver = setup_driver()

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


def auto_send_code(user_cookies):
    server_result = uc_merced_mobile_id(user_cookies)

    for mobile_id_rand in server_result["mobile_id_rand_array"]:
        response = send_otc(mobile_id_rand, server_result["student_id"], server_result["barcode"])
        if response["status"] == "success":
            return {
                "status": "success",
                "code": mobile_id_rand,
            }

    return {
        "status": "failure",
    }


def uc_merced_mobile_id(user_cookie):
    html_source = request_mobile_id(user_cookie)
    mobile_id_rand_array, student_id, barcode = parse_html_data(html_source)
    return {
        "mobile_id_rand_array": mobile_id_rand_array,
        "student_id": student_id,
        "barcode": barcode,
    }


def request_mobile_id(user_cookie):
    driver = setup_driver()
    driver.execute_cdp_cmd("Network.enable", {})

    custom_headers = {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Cache-Control": "max-age=0",
        "Cookie": user_cookie,
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36"
        ),
    }

    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": custom_headers})

    url = "https://icatcard.ucmerced.edu/mobileid/"
    driver.get(url)

    time.sleep(1)

    html_source = driver.page_source
    driver.quit()

    return html_source


def parse_html_data(html_content):
    try:
        # get mobile_id_rand_array
        array_pattern = r"var\s+mobileid_rand_array\s*=\s*(\[[^\]]*\])"
        # get student_id
        student_id_pattern = r"studentid:\s*\"(.*?)\""
        # get barcode
        barcode_pattern = r"barcode:\s*\"(.*?)\""

        array_match = re.search(array_pattern, html_content)
        if array_match:
            array_str = array_match.group(1)
            try:
                mobile_id_rand_array = json.loads(array_str)
            except json.JSONDecodeError:
                mobile_id_rand_array = None
        else:
            mobile_id_rand_array = None

        student_id_match = re.search(student_id_pattern, html_content)
        student_id = student_id_match.group(1) if student_id_match else None

        barcode_match = re.search(barcode_pattern, html_content)
        barcode = barcode_match.group(1) if barcode_match else None

        return mobile_id_rand_array, student_id, barcode

    except Exception as e:
        print(f"Error while parsing HTML content: {e}")
        return None, None, None


if __name__ == "__main__":
    user_cookie = r"_scid=Ic_axybbNapcWu2KQbPQB0XUlkR3FPy2; _tt_enable_cookie=1; _ttp=01JN20PX96CN3HWEEDYE7SEZ03_.tt.1; _fbp=fb.1.1740603356486.499765120694379326; _mkto_trk=id:976-RKA-196&token:_mch-ucmerced.edu-bc9ac74da238b9517b062d67c0cf33be; _ga_MDV0RFSJ6H=GS1.1.1740731352.1.1.1740731475.0.0.0; _ga_ZNSTZ2YGVJ=GS1.1.1742529086.1.1.1742529115.0.0.0; _ScCbts=%5B%5D; _sctr=1%7C1743663600000; _ga_12VFZGH5J2=GS1.2.1743837418.5.0.1743837418.0.0.0; _gid=GA1.2.1624259111.1744140609; _ga=GA1.1.510264552.1740603356; _ga_TSE2LSBDQZ=GS1.1.1744140609.11.1.1744140723.60.0.0; _scid_r=L0_axybbNapcWu2KQbPQB0XUlkR3FPy2DKvteA; _uetsid=e2a114a014af11f09c689fff36e39247; _uetvid=13366c10f48411efb8ba870ea856949e; ttcsid=1744140609467.1.1744140723288; ttcsid_C8LNTT0H473GVAFU5FV0=1744140609466.1.1744140723497; session_for%3Aindex_php=ST-1744141275001-UwXxG4UdwqKfO4RR4Os1mufxS; _pk_ref.1.cb1f=%5B%22%22%2C%22%22%2C1744141276%2C%22https%3A%2F%2Fapi-70cee857.duosecurity.com%2F%22%5D; _pk_ses.1.cb1f=*; _pk_id.1.cb1f=da46508d627083ff.1742872489.34.1744143063.1744141276."

    # print(auto_send_code(user_cookie))
    # print(uc_merced_mobile_id(user_cookie))
