import base64
import json
import logging
import os
import platform
import re
import time
from dataclasses import dataclass
from textwrap import shorten
from typing import Dict, List, Optional, Union
from urllib.parse import quote

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class MobileIdData:
    """Data class for mobile ID information."""
    mobile_id_rand_array: Optional[List[str]]
    student_id: Optional[str]
    barcode: Optional[str]
    profile_img_base64: Optional[str]
    username: Optional[str] = None


@dataclass
class ApiResponse:
    """Data class for API response information."""
    status: str
    code: Optional[str] = None
    response: Optional[str] = None
    error: Optional[str] = None


class UCMercedConfig:
    """Configuration class for UC Merced Mobile ID system."""

    # URLs
    BASE_URL = "https://icatcard.ucmerced.edu"
    MOBILE_ID_URL = f"{BASE_URL}/mobileid/"
    RAND_API_URL = f"{BASE_URL}/mobileid/rand.php"

    # Timeouts
    IMPLICIT_WAIT = 10
    EXPLICIT_WAIT = 15
    SLEEP_DURATION = 2

    # Session cookie
    DEFAULT_SESSION_COOKIE = "session_for%3Aindex_php=8e6df98bc61073a5ac6ba55eb92a9045"

    # Headers
    DEFAULT_HEADERS = {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Cache-Control": "max-age=0",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36"
        ),
    }


class WebDriverManager:
    """Context manager for WebDriver to ensure proper cleanup."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    def __enter__(self) -> webdriver.Chrome:
        self.driver = self._setup_driver()
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")

    def _setup_driver(self) -> webdriver.Chrome:
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.set_capability("acceptInsecureCerts", False)

        if self.headless:
            chrome_options.add_argument("--headless=new")

        # for linux server and docker
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-software-rasterizer")
        # avoid DevToolsActivePort
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--user-data-dir=/tmp/chrome-user-data")
        chrome_options.add_argument("--data-path=/tmp/chrome-data")
        chrome_options.add_argument("--disk-cache-dir=/tmp/chrome-cache")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-zygote")

        # use google chrome first
        if os.path.exists("/usr/bin/google-chrome"):
            chrome_options.binary_location = "/usr/bin/google-chrome"
            logger.info("Using Google Chrome at /usr/bin/google-chrome")
        elif os.path.exists("/snap/bin/chromium"):
            chrome_options.binary_location = "/snap/bin/chromium"
            logger.info("Using Chromium (snap) at /snap/bin/chromium")
        elif os.path.exists("/usr/bin/chromium"):
            chrome_options.binary_location = "/usr/bin/chromium"
            logger.info("Using Chromium (apt) at /usr/bin/chromium")
        else:
            raise FileNotFoundError("No Chrome/Chromium found at /usr/bin or /snap/bin")

        try:
            service = Service(ChromeDriverManager().install())
            logger.info("Using ChromeDriver from webdriver-manager (auto-matched)")
        except Exception as e:
            logger.warning(f"webdriver-manager failed ({e}); falling back to /usr/bin/chromedriver")
            service = Service("/usr/bin/chromedriver")

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(UCMercedConfig.IMPLICIT_WAIT)
        logger.info(f"WebDriver initialized successfully on {platform.system()}")
        return driver


class UCMercedMobileIdClient:
    """Main client for UC Merced Mobile ID system interactions."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.config = UCMercedConfig()

    def send_otc(self, mobile_id_rand: str, student_id: str, barcode: str, user_cookies: str) -> ApiResponse:
        """
        Send OTC (One-Time Code) using provided parameters.

        Args:
            mobile_id_rand: Random mobile ID code
            student_id: Student ID number
            barcode: Barcode string
            user_cookies: Raw Cookie header string from the authenticated browser session

        Returns:
            ApiResponse object with status and details
        """
        logger.info(f"Attempting to send OTC with code: {mobile_id_rand}")

        try:
            with WebDriverManager(self.headless) as driver:
                # Enable network and set headers to mirror the provided cURL as closely as possible
                driver.execute_cdp_cmd("Network.enable", {})

                # Some headers (like Cookie) are best applied via CDP extra headers
                ajax_headers = {
                    "Accept": "*/*",
                    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Origin": self.config.BASE_URL,
                    "Referer": self.config.MOBILE_ID_URL,
                    "DNT": "1",
                    "X-Requested-With": "XMLHttpRequest",
                    # UA hints and sec headers are best-effort; harmless if ignored
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                    "sec-ch-ua": '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"macOS"',
                    # Include the authenticated cookies captured from the user
                    "Cookie": user_cookies,
                }

                try:
                    # Attempt to mirror the UA from the user's curl example
                    driver.execute_cdp_cmd(
                        "Network.setUserAgentOverride",
                        {
                            "userAgent": (
                                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
                            )
                        },
                    )
                except Exception:
                    # Non-fatal if UA override fails
                    pass

                driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": ajax_headers})

                # Navigate to the same-origin page first to avoid CORS issues
                logger.info(f"Navigating to: {self.config.MOBILE_ID_URL}")
                driver.get(self.config.MOBILE_ID_URL)

                # Wait for page to be ready
                WebDriverWait(driver, self.config.EXPLICIT_WAIT).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )

                # Prepare the JavaScript payload using fetch()
                js_payload = self._build_js_payload(mobile_id_rand, student_id, barcode)

                # Execute the AJAX request
                driver.execute_script(js_payload)

                # Wait for response and extract it
                wait = WebDriverWait(driver, self.config.EXPLICIT_WAIT)
                response_element = wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "pre"))
                )

                response_text = response_element.text.strip()
                logger.info(f"Server response: {response_text}")

                # Determine success/failure
                if self._is_success_response(response_text):
                    logger.info(f"OTC sent successfully with code: {mobile_id_rand}")
                    return ApiResponse(
                        status="success",
                        code=mobile_id_rand,
                        response=response_text,
                    )
                else:
                    logger.warning(f"OTC failed with code: {mobile_id_rand}")
                    return ApiResponse(
                        status="failed",
                        code=mobile_id_rand,
                        response=response_text,
                    )

        except TimeoutException:
            error_msg = f"Timeout waiting for response with code: {mobile_id_rand}"
            logger.error(error_msg)
            return ApiResponse(status="error", error=error_msg)

        except WebDriverException as e:
            error_msg = f"WebDriver error with code {mobile_id_rand}: {e}"
            logger.error(error_msg)
            return ApiResponse(status="error", error=error_msg)

        except Exception as e:
            error_msg = f"Unexpected error with code {mobile_id_rand}: {e}"
            logger.error(error_msg)
            return ApiResponse(status="error", error=error_msg)

    def _build_js_payload(self, mobile_id_rand: str, student_id: str, barcode: str) -> str:
        """Build JavaScript fetch payload for AJAX request, mirroring the provided cURL.

        Ensures student ID is prefixed with 'S'.
        """
        # Ensure the student ID starts with 'S'
        student_id_formatted = f"S{re.sub(r'^s?', '', student_id, flags=re.IGNORECASE)}"

        # Safely encode parameters for x-www-form-urlencoded
        encoded_params = (
            f"mobileidrand={quote(mobile_id_rand)}"
            f"&studentid={quote(student_id_formatted)}"
            f"&barcode={quote(barcode)}"
        )

        return f"""
        try {{
            fetch("/mobileid/rand.php", {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest"
                }},
                body: "{encoded_params}",
                credentials: "include"
            }})
                .then(function(resp) {{ return resp.text(); }})
                .then(function(text) {{
                    document.body.innerHTML = "<pre>" + text + "</pre>";
                }})
                .catch(function(err) {{
                    document.body.innerHTML = "<pre>ERROR: Request failed</pre>";
                }});
        }} catch (e) {{
            document.body.innerHTML = "<pre>ERROR: Request failed</pre>";
        }}
        """

    def _is_success_response(self, response_text: str) -> bool:
        """Check if response indicates success."""
        success_indicators = ["added", "success", "complete"]
        return any(indicator in response_text.lower() for indicator in success_indicators)

    def auto_send_code(self, user_cookies: str) -> ApiResponse:
        """
        Automatically try sending codes until one succeeds.

        Args:
            user_cookies: User session cookies

        Returns:
            ApiResponse with final result
        """
        logger.info("Starting automatic code sending process")

        try:
            mobile_data = self.get_mobile_id_data(user_cookies)

            if not mobile_data.mobile_id_rand_array:
                error_msg = "No mobile ID codes available"
                logger.error(error_msg)
                return ApiResponse(status="error", error=error_msg)

            if not mobile_data.student_id or not mobile_data.barcode:
                error_msg = "Missing required student ID or barcode"
                logger.error(error_msg)
                return ApiResponse(status="error", error=error_msg)

            logger.info(f"Trying {len(mobile_data.mobile_id_rand_array)} codes")

            for i, mobile_id_rand in enumerate(mobile_data.mobile_id_rand_array, 1):
                logger.info(f"Attempting code {i}/{len(mobile_data.mobile_id_rand_array)}: {mobile_id_rand}")

                response = self.send_otc(
                    mobile_id_rand,
                    mobile_data.student_id,
                    mobile_data.barcode,
                    user_cookies
                )

                if response.status == "success":
                    logger.info(f"Successfully authenticated with code: {mobile_id_rand}")
                    return response

                # Brief delay between attempts
                time.sleep(1)

            error_msg = "All codes failed"
            logger.error(error_msg)
            return ApiResponse(status="failure", error=error_msg)

        except Exception as e:
            error_msg = f"Error in auto_send_code: {e}"
            logger.error(error_msg)
            return ApiResponse(status="error", error=error_msg)

    def get_mobile_id_data(self, user_cookie: str) -> MobileIdData:
        """
        Get mobile ID data from UC Merced system.

        Args:
            user_cookie: User session cookie

        Returns:
            MobileIdData object with extracted information
        """
        logger.info("Fetching mobile ID data")

        try:
            html_source = self._request_mobile_id_page(user_cookie)
            mobile_data = self._parse_html_data(html_source)

            # Print fetch results to terminal
            self._print_fetch_results(mobile_data)

            return mobile_data

        except Exception as e:
            logger.error(f"Error getting mobile ID data: {e}")
            return MobileIdData(None, None, None, None)

    def _print_fetch_results(self, mobile_data: MobileIdData):
        """Print fetch results to terminal in a clean, formatted way."""

        COL = 70
        LABEL_W = 25

        def line(label, value, prefix="     "):
            print(f"{prefix}{label:<{LABEL_W}} : {value}")

        def status_line(label, value):
            if value:
                print(f"[OK]   {label:<{LABEL_W}} : {value}")
            else:
                print(f"[MISS] {label:<{LABEL_W}} : Not found")

        def _supports_inline_images():
            # Currently support iTerm2 inline images
            return os.environ.get("TERM_PROGRAM") == "iTerm.app"

        def _print_inline_image_from_base64(b64_str):
            """Render an inline image in iTerm2 using its escape sequence."""
            try:
                raw = base64.b64decode(b64_str, validate=False)
                size = len(raw)
                # Re-encode to ensure clean, unbroken base64 for the escape sequence
                b64_clean = base64.b64encode(raw).decode("ascii")
                # iTerm2 inline image escape
                # \033]1337;File=inline=1;size=<bytes>;width=auto;height=auto:<base64>\a
                esc = f"\033]1337;File=inline=1;size={size};width=auto;height=auto;preserveAspectRatio=1:{b64_clean}\a"
                print(esc)
                return True
            except Exception:
                return False

        print("\n" + "=" * COL)
        print(" UC MERCED MOBILE ID - FETCH RESULTS ".center(COL, " "))
        print("=" * COL)

        # Student ID / User ID
        status_line("Student ID (User ID)", mobile_data.student_id)

        # Username
        status_line("Username", mobile_data.username)

        # Barcode
        if mobile_data.barcode:
            barcode_preview = shorten(mobile_data.barcode, width=30, placeholder="...")
            print(f"[OK]   {'Barcode':<{LABEL_W}} : {barcode_preview}")
        else:
            print(f"[MISS] {'Barcode':<{LABEL_W}} : Not found")

        # Mobile ID Codes
        if mobile_data.mobile_id_rand_array:
            print(f"[OK]   {'Mobile ID Codes':<{LABEL_W}} : {len(mobile_data.mobile_id_rand_array)} found")
            line("Sample Codes", mobile_data.mobile_id_rand_array[:3])
        else:
            print(f"[MISS] {'Mobile ID Codes':<{LABEL_W}} : None found")

        # Profile Image (formatted exactly as requested)
        if mobile_data.profile_img_base64:
            img_info = self._analyze_profile_image(mobile_data.profile_img_base64)  # e.g., "PNG 128x128"
            print(f"[OK]   {'Profile Image':<{LABEL_W}} : Found ({img_info})")
            line("Data Length", f"{len(mobile_data.profile_img_base64)} chars")
            preview = shorten(mobile_data.profile_img_base64, width=60, placeholder="...")
            line("Preview", preview)

            # Attempt inline rendering for iTerm2
            if _supports_inline_images():
                # Spacer so the image isn't glued to text lines
                print("     " + "-" * (COL - 5))
                _print_inline_image_from_base64(mobile_data.profile_img_base64)
                print("     " + "-" * (COL - 5))
        else:
            print(f"[MISS] {'Profile Image':<{LABEL_W}} : Not found")

        print("=" * COL + "\n")

    def _analyze_profile_image(self, img_base64: str) -> str:
        """Analyze profile image to get format and approximate size."""
        try:
            if img_base64.startswith('data:image/'):
                # Extract format
                format_match = re.search(r'data:image/([^;]+)', img_base64)
                img_format = format_match.group(1).upper() if format_match else "Unknown"

                # Extract base64 data
                base64_data = img_base64.split(',')[1] if ',' in img_base64 else img_base64

                # Calculate approximate size in KB
                size_bytes = len(base64_data) * 3 / 4  # Base64 is ~33% larger than binary
                size_kb = size_bytes / 1024

                return f"{img_format} format, ~{size_kb:.1f}KB"
            else:
                return "Unknown format"
        except Exception:
            return "Analysis failed"

    def _request_mobile_id_page(self, user_cookie: str) -> str:
        """Request mobile ID page with custom headers."""
        try:
            with WebDriverManager(self.headless) as driver:
                # Enable network interception
                driver.execute_cdp_cmd("Network.enable", {})

                # Set custom headers
                headers = self.config.DEFAULT_HEADERS.copy()
                headers["Cookie"] = user_cookie

                driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})

                # Navigate to the page
                logger.info(f"Navigating to: {self.config.MOBILE_ID_URL}")
                driver.get(self.config.MOBILE_ID_URL)

                # Wait for page to load
                WebDriverWait(driver, self.config.EXPLICIT_WAIT).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )

                time.sleep(self.config.SLEEP_DURATION)

                html_source = driver.page_source
                logger.info("Successfully retrieved mobile ID page")
                return html_source

        except Exception as e:
            logger.error(f"Error requesting mobile ID page: {e}")
            raise

    def _parse_html_data(self, html_content: str) -> MobileIdData:
        """
        Parse HTML content to extract mobile ID data.

        Args:
            html_content: Raw HTML content

        Returns:
            MobileIdData object with parsed information
        """
        logger.info("Parsing HTML data")

        try:
            # Updated regex patterns for data extraction
            patterns = {
                'array': r"var\s+mobileid_rand_array\s*=\s*(\[[^\]]*\])",
                'student_id': r"studentid:\s*[\"'](.*?)[\"']",
                'barcode': r"barcode:\s*[\"'](.*?)[\"']",
                'profile_img_js': r"var\s+profile_img_base64\s*=\s*[\"'](data:image\/[a-zA-Z]+;base64,[^\"']*)[\"']",
                'profile_img_tag': r"<img[^>]*src=[\"'](data:image\/[^;]+;base64,[A-Za-z0-9+\/=]+)[\"'][^>]*>",
                # Enhanced username patterns based on your updated HTML structure
                'username_h4_primary': r'<h4[^>]*class="white-w4"[^>]*style="[^"]*color:\s*white[^"]*"[^>]*>([^<]+)</h4>',
                # Exact match for your structure
                'username_h4_flexible': r'<h4[^>]*class=["\']?[^"\']*white-w4[^"\']*["\']?[^>]*>([^<]+)</h4>',
                # More flexible class matching
                'username_h4_style': r'<h4[^>]*style="[^"]*color:\s*white[^"]*"[^>]*>([^<]+)</h4>',
                # Style-based matching
                'username_h4_any': r'<h4[^>]*>([A-Za-z\s]+(?:Xie|[A-Z][a-z]+))</h4>',  # Any h4 with name-like content
                'username_js': r"(?:username|name|fullname):\s*[\"'](.*?)[\"']",  # JavaScript variables
                'display_name': r"<.*?class=[\"'][^\"']*(?:name|username|user-name)[^\"']*[\"'][^>]*>([^<]+)<",
                # Generic name classes
            }

            # Extract mobile_id_rand_array
            mobile_id_rand_array = None
            array_match = re.search(patterns['array'], html_content)
            if array_match:
                try:
                    array_str = array_match.group(1)
                    mobile_id_rand_array = json.loads(array_str)
                    logger.info(f"Found {len(mobile_id_rand_array)} mobile ID codes")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse mobile ID array: {e}")

            # Extract student_id
            student_id = None
            student_id_match = re.search(patterns['student_id'], html_content)
            if student_id_match:
                raw_student_id = student_id_match.group(1)
                # Clean student ID - keep only digits
                student_id = re.sub(r'[^0-9]', '', raw_student_id)
                if student_id:
                    logger.info(f"Found student ID: {student_id} (cleaned from: {raw_student_id})")
                else:
                    logger.warning(f"Student ID contained no digits: {raw_student_id}")
                    student_id = None

            # Extract username with multiple fallback patterns
            username = None

            # Try primary exact match pattern first (most specific for your HTML structure)
            username_primary_match = re.search(patterns['username_h4_primary'], html_content, re.IGNORECASE)
            if username_primary_match:
                username = username_primary_match.group(1).strip()
                logger.info(f"Found username with primary pattern: {username}")
            else:
                # Try flexible class-based pattern
                username_flexible_match = re.search(patterns['username_h4_flexible'], html_content, re.IGNORECASE)
                if username_flexible_match:
                    username = username_flexible_match.group(1).strip()
                    logger.info(f"Found username with flexible pattern: {username}")
                else:
                    # Try style-based pattern
                    username_style_match = re.search(patterns['username_h4_style'], html_content, re.IGNORECASE)
                    if username_style_match:
                        username = username_style_match.group(1).strip()
                        logger.info(f"Found username with style pattern: {username}")
                    else:
                        # Try any h4 with name-like content
                        username_any_match = re.search(patterns['username_h4_any'], html_content, re.IGNORECASE)
                        if username_any_match:
                            username = username_any_match.group(1).strip()
                            logger.info(f"Found username with any h4 pattern: {username}")
                        else:
                            # Try JavaScript variable pattern
                            username_js_match = re.search(patterns['username_js'], html_content, re.IGNORECASE)
                            if username_js_match:
                                username = username_js_match.group(1).strip()
                                logger.info(f"Found username in JS variable: {username}")
                            else:
                                # Try generic name class pattern
                                display_name_match = re.search(patterns['display_name'], html_content, re.IGNORECASE)
                                if display_name_match:
                                    username = display_name_match.group(1).strip()
                                    logger.info(f"Found username in name class: {username}")
                                else:
                                    logger.warning("No username pattern matched")

            # Clean up username if found
            if username:
                # Remove any HTML entities and extra whitespace
                username = re.sub(r'&[a-zA-Z]+;', '', username)  # Remove HTML entities
                username = re.sub(r'\s+', ' ', username).strip()  # Normalize whitespace
                # Remove any remaining HTML tags
                username = re.sub(r'<[^>]+>', '', username)
                if username:
                    logger.info(f"Cleaned username: {username}")
                else:
                    username = None

            # Extract barcode
            barcode = None
            barcode_match = re.search(patterns['barcode'], html_content)
            if barcode_match:
                barcode = barcode_match.group(1)
                logger.info("Found barcode information")

            # Extract profile image
            profile_img_base64 = None
            profile_img_match = re.search(patterns['profile_img_js'], html_content)
            if profile_img_match:
                profile_img_base64 = profile_img_match.group(1)
                logger.info("Found profile image in JavaScript variable")
            else:
                # Try img tag as fallback
                img_src_match = re.search(patterns['profile_img_tag'], html_content)
                if img_src_match:
                    profile_img_base64 = img_src_match.group(1)
                    logger.info("Found profile image in img tag")

            return MobileIdData(
                mobile_id_rand_array=mobile_id_rand_array,
                student_id=student_id,
                barcode=barcode,
                profile_img_base64=profile_img_base64,
                username=username
            )

        except Exception as e:
            logger.error(f"Error parsing HTML data: {e}")
            return MobileIdData(None, None, None, None)


# ---------------------------------------------------------------------------
# Module-level convenience wrappers
# ---------------------------------------------------------------------------
def auto_send_code(user_cookies: str, headless: bool = True) -> Optional[Dict[str, str]]:
    """Send OTC codes automatically using a headless browser session.

    Returns a dict like {"code": str, "response": str} on success, otherwise None.
    """
    client = UCMercedMobileIdClient(headless=headless)
    response = client.auto_send_code(user_cookies)
    if response and response.status == "success":
        return {"code": response.code or "", "response": response.response or ""}
    return None


# Interface for direct script execution
if __name__ == "__main__":
    # Initialize the client
    client = UCMercedMobileIdClient(headless=True)

    # Example: Get mobile ID data
    user_cookie = r"""_scid=njgcOEfixQa9v_yNlmcaS7NN2LiUwg2g; _tt_enable_cookie=1; _ttp=01K10A60004X4B79PVZSMB962Z_.tt.1; _fbp=fb.1.1753431080973.171835158316531023; _mkto_trk=id:976-RKA-196&token:_mch-ucmerced.edu-287fe55e56c57e83ed76955576ad8151; _ga_TSE2LSBDQZ=GS2.1.s1753542745$o1$g0$t1753542745$j60$l0$h0; _ga_QHQ86LM5JZ=GS2.1.s1753680653$o2$g0$t1753680653$j60$l0$h0; _ga=GA1.2.34565484.1753431075; _ga_8F7K2W04Y2=GS2.2.s1753691907$o1$g1$t1753691916$j51$l0$h0; _sctr=1%7C1755014400000; nmstat=874ae77e-31c0-3db1-0a94-7e352a5a73c8; _scid_r=orgcOEfixQa9v_yNlmcaS7NN2LiUwg2gUV8nhQ; _uetvid=f2200fb0692e11f0b0554f688142cbe8; ttcsid=1755528621758::Pn-65uLzJipQ9aU0ZH4c.8.1755528621758; ttcsid_C8LNTT0H473GVAFU5FV0=1755528621758::r0ESk1Wqvt3l0_j7-MKw.8.1755528622487; session_for%3Aindex_php=ST-1756008062765-2c0fAHpXLQQ9a5BADCK0UHU4l; _pk_ref.1.cb1f=%5B%22%22%2C%22%22%2C1756008063%2C%22https%3A%2F%2Fapi-70cee857.duosecurity.com%2F%22%5D; _pk_ses.1.cb1f=*; _pk_id.1.cb1f=8fd908bc11af365d.1750952586.12.1756008776.1756008063."""
    mobile_data = client.get_mobile_id_data(user_cookie)

    print(mobile_data.profile_img_base64)

    # The fetch results will be automatically printed by the enhanced get_mobile_id_data method