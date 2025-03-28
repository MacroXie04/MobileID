import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import re
import json


def uc_merced_mobile_id(user_cookie):
    html_source = request_mobile_id(f"{user_cookie}")
    mobile_id_rand_array, student_id, barcode = parse_html_data(html_source)

    return {
        "mobile_id_rand_array": mobile_id_rand_array,
        "student_id": student_id,
        "barcode": barcode,
    }


def request_mobile_id(user_cookie):
    # initialize Chrome WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

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
        "Cookie": (user_cookie),
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
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
        # mobile_id_rand_array
        array_pattern = r"var\s+mobileid_rand_array\s*=\s*(\[[^\]]*\])"
        # student_id
        student_id_pattern = r"studentid:\s*\"(.*?)\""
        # barcode
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
    user_cookie = r"_scid=Ic_axybbNapcWu2KQbPQB0XUlkR3FPy2; _tt_enable_cookie=1; _ttp=01JN20PX96CN3HWEEDYE7SEZ03_.tt.1; _fbp=fb.1.1740603356486.499765120694379326; _mkto_trk=id:976-RKA-196&token:_mch-ucmerced.edu-bc9ac74da238b9517b062d67c0cf33be; _ga_MDV0RFSJ6H=GS1.1.1740731352.1.1.1740731475.0.0.0; _ga_TSE2LSBDQZ=GS1.1.1742426043.7.0.1742426043.60.0.0; _ga_ZNSTZ2YGVJ=GS1.1.1742529086.1.1.1742529115.0.0.0; _ga=GA1.2.510264552.1740603356; _gid=GA1.2.939168309.1743120107; _ga_12VFZGH5J2=GS1.2.1743120107.1.1.1743121716.0.0.0; _scid_r=M0_axybbNapcWu2KQbPQB0XUlkR3FPy2DKvtXg; _uetsid=23d4d9f00b8211f09342e9a3a7334d45; _uetvid=13366c10f48411efb8ba870ea856949e; _ScCbts=%5B%5D; _sctr=1%7C1743058800000; session_for%3Aindex_php=ST-1743136697376-36lj2wO4vhDV1sdr5tem6OHrM; _pk_ref.1.cb1f=%5B%22%22%2C%22%22%2C1743136693%2C%22https%3A%2F%2Fapi-70cee857.duosecurity.com%2F%22%5D; _pk_ses.1.cb1f=*; _pk_id.1.cb1f=da46508d627083ff.1742872489.4.1743136707.1743136693.; session_for%3Aindex_php=8e6df98bc61073a5ac6ba55eb92a9045"
    # html = request_mobile_id(
    #     "_scid=Ic_axybbNapcWu2KQbPQB0XUlkR3FPy2; _tt_enable_cookie=1; _ttp=01JN20PX96CN3HWEEDYE7SEZ03_.tt.1; _fbp=fb.1.1740603356486.499765120694379326; _mkto_trk=id:976-RKA-196&token:_mch-ucmerced.edu-bc9ac74da238b9517b062d67c0cf33be; _ga_MDV0RFSJ6H=GS1.1.1740731352.1.1.1740731475.0.0.0; _ga_TSE2LSBDQZ=GS1.1.1742426043.7.0.1742426043.60.0.0; _ga_ZNSTZ2YGVJ=GS1.1.1742529086.1.1.1742529115.0.0.0; _ga=GA1.2.510264552.1740603356; _gid=GA1.2.939168309.1743120107; _ga_12VFZGH5J2=GS1.2.1743120107.1.1.1743121716.0.0.0; _scid_r=M0_axybbNapcWu2KQbPQB0XUlkR3FPy2DKvtXg; _uetsid=23d4d9f00b8211f09342e9a3a7334d45; _uetvid=13366c10f48411efb8ba870ea856949e; _ScCbts=%5B%5D; _sctr=1%7C1743058800000; session_for%3Aindex_php=ST-1743136697376-36lj2wO4vhDV1sdr5tem6OHrM; _pk_ref.1.cb1f=%5B%22%22%2C%22%22%2C1743136693%2C%22https%3A%2F%2Fapi-70cee857.duosecurity.com%2F%22%5D; _pk_ses.1.cb1f=*; _pk_id.1.cb1f=da46508d627083ff.1742872489.4.1743136707.1743136693.; session_for%3Aindex_php=8e6df98bc61073a5ac6ba55eb92a9045")
    # print(parse_html_data(html))

    print(uc_merced_mobile_id(user_cookie))
