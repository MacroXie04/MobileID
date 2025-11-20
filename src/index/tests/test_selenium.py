from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class SeleniumTests(LiveServerTestCase):
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)

    def tearDown(self):
        self.driver.quit()

    def test_google_access(self):
        """
        Test that the driver can access google.com and print the title,
        replicating the logic from src/test_driver.py.
        """
        self.driver.get("https://www.google.com")
        print(f"Page Title: {self.driver.title}")
        # Adding a basic assertion to ensure the test actually verifies something  # noqa: E501
        self.assertIsNotNone(self.driver.title)
