import os
import sys
import time
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class LoginPageTest(unittest.TestCase):
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

    def fill_login_form(self, email, password):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CLASS_NAME, "login-btn").click()
        time.sleep(2)

    def test_login_success(self):
        test_email = "success@example.com"  # Use a fixed email for success test
        try:
            self.fill_login_form(email=test_email, password=self.base_password)
            self.assertIn(
                "You must verify your email before logging in. Please check your inbox.",
                self.driver.page_source,
            )

        except Exception as e:
            os.makedirs("artifacts", exist_ok=True)
            self.driver.save_screenshot("artifacts/login_success.png")
            with open("artifacts/debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise  # Re-raise so the test still fails

    def test_login_nonexistent_email(self):
        test_email = "nonexistent@example.com"  # Use an nonexistent email for this test
        try:
            self.fill_login_form(email=test_email, password=self.base_password)
            self.assertIn("Invalid email or password.", self.driver.page_source)

        except Exception as e:
            os.makedirs("artifacts", exist_ok=True)
            self.driver.save_screenshot("artifacts/login_nonexistent_email.png")
            with open("artifacts/debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise  # Re-raise so the test still fails

    def test_login_incorrect_password(self):
        test_email = (
            "success@example.com"  # Use a fixed email to test incorrect password
        )
        incorrect_password = "wrongpassword"
        try:
            self.fill_login_form(email=test_email, password=incorrect_password)
            self.assertIn("Invalid email or password.", self.driver.page_source)

        except Exception as e:
            os.makedirs("artifacts", exist_ok=True)
            self.driver.save_screenshot("artifacts/incorrect_password.png")
            with open("artifacts/debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise  # Re-raise so the test still fails

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()


if __name__ == "__main__":
    unittest.main()
