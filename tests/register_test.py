import os
import sys
import time
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class RegisterPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = Options()
        options.add_argument("--ignore-certificate-errors")  # <-- key line
        options.add_argument("--allow-insecure-localhost")  # optional, but useful
        options.add_argument("--headless")  # for CI
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        cls.driver.implicitly_wait(10)
        cls.base_url = "https://localhost"
        cls.base_password = "securepassword"

    def fill_registration_form(self, email, password):
        self.driver.get(f"{self.base_url}/register")
        self.driver.find_element(By.NAME, "name").send_keys("Test User")
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.NAME, "confirm_password").send_keys(password)
        self.driver.find_element(By.CLASS_NAME, "register-btn").click()
        time.sleep(2)

    def test_register_success(self):
        test_email = "success@example.com"  # Use a fixed email for success test
        try:
            self.fill_registration_form(email=test_email, password=self.base_password)
            self.assertIn(
                "A verification link has been sent to your email address.",
                self.driver.page_source,
            )

        except Exception as e:
            os.makedirs("artifacts", exist_ok=True)
            self.driver.save_screenshot("artifacts/register_success.png")
            with open("artifacts/debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise  # Re-raise so the test still fails

    def test_register_duplicate_email(self):
        duplicate_email = (
            "duplicate@example.com"  # Use a fixed email for duplicate test
        )
        try:
            self.fill_registration_form(
                email=duplicate_email, password=self.base_password
            )
            self.assertIn(
                "A verification link has been sent to your email address.",
                self.driver.page_source,
            )
            self.fill_registration_form(
                email=duplicate_email, password=self.base_password
            )
            self.assertIn(
                "Something went wrong. Please try again.", self.driver.page_source
            )

        except Exception as e:
            os.makedirs("artifacts", exist_ok=True)
            self.driver.save_screenshot("artifacts/register_duplicate_email.png")
            with open("artifacts/debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise  # Re-raise so the test still fails

    # def test_register_password_complexity(self):
    #     test_email = self.generate_random_email()
    #     simple_password = "123456"

    #     try:
    #         self.fill_registration_form(email=test_email, password=simple_password)
    #         self.assertIn("Please lengthen this text to 8 characters or more", self.driver.page_source)
    #         self.fill_registration_form(email=test_email, password=self.base_password)
    #         self.assertIn("A verification link has been sent to your email address.", self.driver.page_source)

    #     except Exception as e:
    #         os.makedirs("artifacts", exist_ok=True)
    #         self.driver.save_screenshot("artifacts/register_password_complexity.png")
    #         with open("artifacts/debug.html", "w", encoding="utf-8") as f:
    #             f.write(self.driver.page_source)
    #         raise  # Re-raise so the test still fails

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()


if __name__ == "__main__":
    unittest.main()
