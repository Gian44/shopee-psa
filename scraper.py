import os
import random
import time
import json
import threading
import tkinter as tk
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from config import *
from database import DatabaseManager

class ShopeeScraper:
    def __init__(self, root):
        self.root = root
        self.wait_time = 25
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.playwright = None
        self.browser = None
        self.page = None
        self.locale = "en-US,en;q=0.9"
        self.cookie_file = COOKIE_FILE

    def _human_like_delay(self, min_sec=1, max_sec=4):
        time.sleep(random.uniform(min_sec, max_sec))

    def _typing_delay(self):
        time.sleep(random.uniform(0.05, 0.3))

    def _move_mouse_naturally(self, element):
        box = element.bounding_box()
        x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
        y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
        
        self.page.mouse.move(
            x + random.randint(-50, 50),
            y + random.randint(-50, 50),
            steps=random.randint(3, 10)
        )
        self._human_like_delay(0.2, 0.5)
        self.page.mouse.move(x, y, steps=random.randint(2, 5))
        self._human_like_delay(0.1, 0.3)

    def _handle_captcha_manually(self):
        """Handle CAPTCHA with GUI popup instead of console input"""
        if "captcha" in self.page.content().lower():
            # Create a simple Tkinter popup
            captcha_window = tk.Toplevel()
            captcha_window.title("CAPTCHA Required")
            
            # Center the window
            window_width = 300
            window_height = 120
            screen_width = captcha_window.winfo_screenwidth()
            screen_height = captcha_window.winfo_screenheight()
            x = int((screen_width/2) - (window_width/2))
            y = int((screen_height/2) - (window_height/2))
            captcha_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Add message and button
            message = ("CAPTCHA detected!\n\n"
                    "Please solve it manually in the browser window,\n"
                    "then click OK to continue.")
            tk.Label(captcha_window, text=message, padx=20, pady=10).pack()
            
            # This variable will track if the user clicked OK
            captcha_solved = threading.Event()
            
            def on_ok_click():
                captcha_solved.set()
                captcha_window.destroy()
            
            ok_button = tk.Button(captcha_window, text="OK", command=on_ok_click)
            ok_button.pack(pady=10)
            
            # Make the window modal
            captcha_window.grab_set()
            
            # Wait for the user to click OK
            self.root.wait_window(captcha_window)
            return True
        return False

    def _save_cookies(self):
        cookies = self.page.context.cookies()
        with open(self.cookie_file, 'w') as f:
            json.dump(cookies, f)
        print(f"Cookies saved to: {self.cookie_file}")

    def _load_cookies(self):
        if not os.path.exists(self.cookie_file):
            return False
            
        with open(self.cookie_file, 'r') as f:
            cookies = json.load(f)
        
        self.page.context.add_cookies(cookies)
        print(f"Cookies loaded from: {self.cookie_file}")
        return True

    def _is_logged_in(self):
        try:
            self.page.wait_for_selector('img.shopee-avatar__img', timeout=5000)
            return True
        except:
            return False
    def delete_cookies(self):
        try:
            if os.path.exists(self.cookie_file):
                os.remove(self.cookie_file)
                print("Cookies deleted successfully")
                return True
            print("No cookies file found")
            return False
        except Exception as e:
            print(f"Error deleting cookies: {e}")
            return False
        
    def login(self, username=None, password=None):
        try:
            # Try to load cookies first
            if self._load_cookies():
                print("Attempting to use saved cookies...")
                self.page.goto("https://shopee.ph", timeout=60000)
                self._human_like_delay(2, 4)
                
                if self._is_logged_in():
                    print("Logged in successfully with cookies")
                    return True

            # If cookie login fails and credentials provided, do manual login
            if username and password:
                print("Loading login page...")
                self.page.goto("https://shopee.ph/buyer/login", timeout=60000)
                self._human_like_delay(2, 4)

                print("Entering username...")
                username_field = self.page.wait_for_selector(
                    "input[name='loginKey'], input[placeholder='Email/Phone/Username']",
                    timeout=self.wait_time * 1000
                )
                self._move_mouse_naturally(username_field)
                username_field.click()
                self._human_like_delay(0.5, 1.5)
                
                for char in username:
                    username_field.press(char)
                    self._typing_delay()
                    if random.random() < 0.1:
                        username_field.press(random.choice(['a', 's', 'd', 'f']))
                        self._human_like_delay(0.2, 0.5)
                        username_field.press('Backspace')
                        self._human_like_delay(0.1, 0.3)

                print("Entering password...")
                password_field = self.page.wait_for_selector(
                    "input[type='password']",
                    timeout=self.wait_time * 1000
                )
                self._move_mouse_naturally(password_field)
                password_field.click()
                self._human_like_delay(0.5, 1.2)
                
                for char in password:
                    password_field.press(char)
                    self._typing_delay()
                    if random.random() < 0.15:
                        self._human_like_delay(0.5, 1.2)

                self._human_like_delay(1, 3)

                print("Clicking login button...")
                login_btn = self.page.wait_for_selector(
                    "button:has-text('Login'), button:has-text('Log In')",
                    timeout=15000
                )
                login_btn.click()

                if self._handle_captcha_manually():
                    print("Continuing after CAPTCHA...")
                    self._human_like_delay(5, 8)

                if self._is_logged_in():
                    self._save_cookies()
                    print("Login successful! Cookies saved.")
                    return True

            return False

        except Exception as e:
            print("Login failed:", str(e))
            return False

    def search_and_scrape(self, keyword, max_pages):
        try:
            self._human_like_delay(3, 5)

            # Initialize database connection
            db = DatabaseManager(DB_NAME)
            table_name = f"products_{keyword.replace(' ', '_')}"
            
            # Check if table exists and clear it if it does
            db.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if db.cursor.fetchone():
                db.clear_table(table_name)
                db.create_table(keyword)
            else:
                # Create new table if it doesn't exist
                db.create_table(keyword)

            print(f"Searching for '{keyword}'...")
            search_box = self.page.wait_for_selector(
                "input.shopee-searchbar-input__input",
                timeout=self.wait_time * 1000
            )
            self._move_mouse_naturally(search_box)
            search_box.click()
            self._human_like_delay(0.5, 1.2)
            search_box.fill("")

            for char in keyword:
                search_box.press(char)
                self._typing_delay()
                if random.random() < 0.1:
                    self._human_like_delay(0.5, 1.5)

            print("Submitting search...")
            search_btn = self.page.wait_for_selector(
                "button.shopee-searchbar__search-button",
                timeout=10000
            )
            search_btn.click()
            self._human_like_delay(3, 6)

            print("Sorting by Top Sales...")
            try:
                sort_btn = self.page.wait_for_selector(
                    "button:has-text('Top Sales')",
                    timeout=10000
                )
                sort_btn.click()
                self._human_like_delay(2, 4)
            except:
                print("Could not find Top Sales button")
                return []

            products = []
            current_page = 1

            while current_page <= max_pages:
                print(f"\nProcessing page {current_page}...")

                print(f"Loading more products... on page {current_page}")
                for _ in range(6):
                    self.page.mouse.wheel(0, random.randint(500, 1000))
                    self._human_like_delay(1.5, 3)
                
                # Scrape products from the current page
                print(f"Scraping product information on page {current_page}...")
                soup = BeautifulSoup(self.page.content(), 'html.parser')

                for card in soup.select('li.shopee-search-item-result__item'):
                    try:
                        name = card.select_one('div.line-clamp-2.break-words.min-w-0.min-h-\\[2\\.5rem\\].text-sm').get_text(strip=True)
                        price = card.select_one('span.font-medium.text-base\\/5.truncate').get_text(strip=True)
                        sold = card.select_one('div.truncate.text-shopee-black87.text-xs.min-h-4').get_text(strip=True)
                        link = "https://shopee.ph" + card.select_one('a.contents')['href'].split('?')[0] 
                        
                        products.append({
                            'name': name,
                            'price': price,
                            'sold': sold,
                            'link': link
                        })
                    except Exception as e:
                        print(f"Error scraping product: {e}")
                        continue

                print(f"Successfully scraped {len(products)} products on page {current_page}.")

                # Check if there is a next page button
                try:
                    next_page_btn = self.page.wait_for_selector('.shopee-icon-button--right', timeout=3000)
                    if not next_page_btn.is_enabled():
                        print("No more pages available")
                        break
                        
                    # Go to next page
                    print("Moving to next page...")
                    self._move_mouse_naturally(next_page_btn)
                    next_page_btn.click()
                    self._human_like_delay(2, 4)
                    current_page += 1
                    
                except Exception as e:
                    print(f"Failed to find next page button: {str(e)}")
                    break

            print(f"\nTotal products scraped from {current_page - 1} pages: {len(products)}")
            
            db = DatabaseManager(DB_NAME)
            for product in products:
                db.insert_product(table_name, product)

            db.close()
            return products

        except Exception as e:
            print(f"Search and scrape failed: {str(e)}")
            return []

    def scrape(self, keyword, username=None, password=None, max_pages=3):
        try:
            with sync_playwright() as playwright:
                self.playwright = playwright
                self.browser = playwright.chromium.launch(
                    headless=False,
                    args=[
                        f'--user-agent={self.user_agent}',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        f'--lang={self.locale.split(",")[0]}',
                        '--start-maximized'
                    ],
                    channel="chrome",
                    chromium_sandbox=False,
                    ignore_default_args=["--enable-automation"]
                )
                self.page = self.browser.new_page()
                print("\nStarting Shopee scraping process...")

                # Try to load cookies first
                if self._load_cookies():
                    self.page.goto("https://shopee.ph", timeout=60000)
                    self._human_like_delay(2, 4)
                    
                    # If not logged in but we have credentials, do manual login
                    if not self._is_logged_in() and username and password:
                        if not self.login(username, password):
                            print("\n[ERROR] Login failed. Exiting.")
                            return []
                
                # If no cookies or login failed, try to login with credentials
                elif username and password:
                    if not self.login(username, password):
                        print("\n[ERROR] Login failed. Exiting.")
                        return []
                
                # If no cookies and no credentials, just proceed (will hit login page)
                else:
                    self.page.goto("https://shopee.ph", timeout=60000)
                    if not self._is_logged_in():
                        print("\n[INFO] Not logged in and no credentials provided")
                        return []
                
                products = self.search_and_scrape(keyword, max_pages)
                return products

        except Exception as e:
            print("\n[FATAL ERROR]", e)
            return []