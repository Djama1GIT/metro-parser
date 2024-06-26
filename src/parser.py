from functools import lru_cache, wraps
from time import sleep
from typing import List

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from webdriver_manager.firefox import GeckoDriverManager

from .config import Settings
from .logger import logger
from .utils import retry


def open_new_window(func):
    """
    A decorator that opens a new browser window before
    the decorated function is called and closes it after the function completes.

    This decorator is useful for functions that need to perform
    operations in a new window, such as navigating to a link,
    extracting data, and then closing the window.
    It ensures that the window management logic is encapsulated within the decorator,
    making the decorated function cleaner and more focused on its specific task.

    Args:
        func (function): The function to be decorated. This function should accept at least two parameters:
            - `self`: The instance of the class that the function belongs to.
            - `driver`: An instance of Selenium WebDriver.
            - `link`: The URL to navigate to in the new window.

    Returns:
        function: The decorated function.
    """
    @wraps(func)
    def wrapper(self, driver: WebDriver, link: str, *args, **kwargs):
        logger.info(f"Opening new window for link: {link}")
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])

        try:
            return func(self, driver, link, *args, **kwargs)
        finally:
            logger.info("Closing the new window")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    return wrapper


class MetroParser:
    """
    A class to parse product information from the Metro store.

    Methods:
        __init__(self, _env_file: str = '') -> None: Initializes the MetroParser with the specified environment file.
        initialize_driver(self) -> WebDriver: Initializes and configures the web browser driver.
        select_address_in_city(self, driver: WebDriver, city: str) -> None: Selects the first address in the city.
        scrape_price(text: str) -> str: Static method to extract price information from a given text.
        get_item_data(self, driver: WebDriver, link: str) -> dict: Retrieves item data for a given product link.
        scroll_to_the_bottom(self, driver: WebDriver) -> None: Scrolls to the bottom of the page to load more items.
        parse_chocolate_category(self, city: str) -> List[dict]: Parses the chocolate category for the specified city.
    """
    HOST = "https://online.metro-cc.ru/"
    ADDRESS_BTN = (By.XPATH, "(//button[contains(@class, 'header-address__receive-button')])")
    SHOW_MORE = (By.XPATH, "(//button[contains(@class, 'subcategory-or-type__load-more')])")
    PICKUP_BTN = (By.XPATH, "(//div[contains(@class, 'delivery__tab')])[3]")
    RESET_BTN = (By.XPATH, "(//span[contains(@class, 'reset-link')])")
    CITY_INPUT = (By.XPATH, "(//input[contains(@label, 'Введите название города')])")
    CITY_ITEM = (By.XPATH, "(//div[contains(@class, 'city-item')])")
    SELECT_BTN = (By.XPATH, "(//button[contains(@type, 'button')])/span[contains(., 'Выбрать')]")
    PRODUCT_ITEM = (By.XPATH, "(//div[contains(@class, 'subcategory-or-type__products-item')])")
    PRODUCT_PHOTO_ITEM = (By.XPATH, "(//a[contains(@class, 'product-card-photo__link')])")
    PRODUCT_ARTICLE = (By.XPATH, "(//p[contains(@itemprop, 'productID')])")
    PRODUCT_ITEM_NAME = (By.XPATH, "(//h1[contains(@class, 'product-page-content__product-name')])")
    PRODUCT_ITEM_PROMO_PRICE = (By.XPATH, "(//div[contains(@class, 'product-unit-prices__actual-wrapper')])")
    PRODUCT_ITEM_REGULAR_PRICE = (By.XPATH, "(//div[contains(@class, 'product-unit-prices__old-wrapper')])")
    PRODUCT_BRAND_NAME = (By.XPATH, "(//a[contains(@class, 'product-attributes__list-item')])[4]")

    def __init__(self, _env_file: str = '') -> None:
        """
        Initializes the MetroParser.

        Args:
            _env_file (str, optional): Path to the environment file. Defaults to ''.
        """
        settings = Settings(_env_file=_env_file)

        if settings.WEBDRIVER == "CHROMIUM":
            self.DriverManager = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM)
            self.options = webdriver.ChromeOptions()
            self.web_driver = webdriver.Chrome
        elif settings.WEBDRIVER == "CHROME":
            self.DriverManager = ChromeDriverManager()
            self.options = webdriver.ChromeOptions()
            self.web_driver = webdriver.Chrome
        else:
            self.DriverManager = GeckoDriverManager()
            self.options = webdriver.FirefoxOptions()
            self.web_driver = webdriver.Firefox

        self.service = Service(executable_path=self.DriverManager.install())

        self.options.add_argument(f"--disable-blink-features={settings.DISABLE_BLINK_FEATURES}")
        self.options.add_argument(f"--user-agent={settings.USER_AGENT}")
        self.options.add_argument(f"--window-size={settings.WINDOW_SIZE}")
        self.options.page_load_strategy = settings.LOAD_STRATEGY
        if settings.NO_SANDBOX:
            self.options.add_argument(f"--no-sandbox")
        if settings.DISABLE_DEV_SHM_USAGE:
            self.options.add_argument(f"--disable-dev-shm-usage")
        if settings.HEADLESS:
            self.options.add_argument("--headless")
        if settings.DISABLE_CACHE:
            self.options.add_argument("--disable-cache")

    def initialize_driver(self) -> WebDriver:
        """
        Initializes and configures the web browser driver.

        Returns:
            WebDriver: The configured web driver.
        """
        logger.info("Initializing web driver")
        driver = self.web_driver(service=self.service, options=self.options)
        logger.info("Web driver initialized successfully")
        return driver

    def select_address_in_city(self, driver: WebDriver, city: str) -> None:
        """
        Selects the first address in the specified city.

        Args:
            driver (WebDriver): The web driver instance.
            city (str): The city name.
        """
        logger.info(f"Selecting address in city: {city}")
        driver.find_element(*self.ADDRESS_BTN).click()
        logger.info("Address button clicked")

        driver.find_element(*self.PICKUP_BTN).click()
        logger.info("Pickup button clicked")

        driver.find_element(*self.RESET_BTN).click()
        logger.info("Reset button clicked")

        driver.find_element(*self.CITY_INPUT).send_keys(city)
        logger.info(f"City input: {city}")

        sleep(2)
        driver.find_element(*self.CITY_ITEM).click()
        logger.info("City item clicked")

        sleep(1)
        driver.find_element(*self.SELECT_BTN).click()
        logger.info("Select button clicked")

        sleep(3)
        logger.info("Address selection completed")

    @staticmethod
    def scrape_price(text: str) -> str:
        """
        Static method to extract price information from a given text.

        Args:
            text (str): The text containing the price information.

        Returns:
            str: The extracted price.
        """
        return text.replace(" ", "").split("д")[0]

    @lru_cache(maxsize=None)
    @retry(tries=10, log=True)
    @open_new_window
    def get_product_data(self, driver: WebDriver, link: str) -> dict:
        """
        Retrieves item data for a given product link.

        Args:
            driver (WebDriver): The web driver instance.
            link (str): The product link.

        Returns:
            dict: The item data.
        """
        logger.info(f"Navigating to link: {link}")
        driver.get(link)

        try:
            logger.info("Extracting item data")
            data = {
                "id": driver.find_element(*self.PRODUCT_ARTICLE).text.split(':')[-1].strip(),
                "name": driver.find_element(*self.PRODUCT_ITEM_NAME).text.strip(),
                "link": link,
                "regular_price": self.scrape_price(driver.find_element(*self.PRODUCT_ITEM_REGULAR_PRICE).text),
                "promo_price": self.scrape_price(driver.find_element(*self.PRODUCT_ITEM_PROMO_PRICE).text),
                "brand_name": driver.find_element(*self.PRODUCT_BRAND_NAME).text.strip(),
            }
            if not data.get("regular_price"):
                data["regular_price"] = data["promo_price"]
            logger.info(f"Item data extracted: {data}")
            return data
        except NoSuchElementException:
            logger.info("The product is out of stock")
            return {}

    def get_products_data(
            self, driver: WebDriver,
            product_items: List[WebElement],
            product_photo_items: List[WebElement]
    ) -> List[dict]:
        """
        Retrieves product data for a list of product items and their corresponding photo items.

        This method iterates over pairs of product items and their photo items, extracts the product link,
        and checks if the product is not marked as "Раскупили" (sold out). If the product is available,
        it retrieves the product data using the `get_product_data` method and appends it to the `products` list.

        Args:
            driver (WebDriver): The Selenium WebDriver instance used for browser automation.
            product_items (List[WebElement]): A list of WebElement instances representing product items.
            product_photo_items (List[WebElement]): A list of WebElement instances representing product photo items.
                                                    It is only used to get a link to the product

        Returns:
            List[dict]: A list of dictionaries containing the product data for each available product.
        """
        products = []
        for item, photo_item in zip(product_items, product_photo_items):
            link = photo_item.get_attribute("href")
            if "Раскупили" not in item.text:
                data = self.get_product_data(driver, link)
                if data:
                    products.append(data)

        return products

    def scroll_to_the_bottom(self, driver: WebDriver) -> None:
        """
        Scrolls to the bottom of the page to load more items.

        Args:
            driver (WebDriver): The web driver instance.
        """
        logger.info("Starting to scroll to the bottom of the page")
        while True:
            try:
                logger.info("Attempting to click 'Show More' button")
                driver.find_element(*self.SHOW_MORE).click()
                sleep(3)
            except NoSuchElementException:
                logger.info("'Show More' button not found, scrolling complete")
                break

    @retry(tries=10, log=True)
    def parse_chocolate_category(self, city: str) -> List[dict]:
        """
        Parses the chocolate category for the specified city.

        Args:
            city (str): The city name.

        Returns:
            List[dict]: A list of dictionaries containing product data.
        """
        logger.info(f"Starting to parse chocolate category for city: {city}")
        with self.initialize_driver() as driver:
            logger.info("Navigating to chocolate category page")
            driver.get("https://online.metro-cc.ru/category/sladosti-chipsy-sneki/shokolad-batonchiki")
            driver.implicitly_wait(6)

            logger.info(f"Selecting the first turned up address in city: {city}")
            self.select_address_in_city(driver, city)

            logger.info("Scrolling to the bottom of the page")
            self.scroll_to_the_bottom(driver)

            logger.info("Finding products")
            products = driver.find_elements(*self.PRODUCT_ITEM)
            product_photos = driver.find_elements(*self.PRODUCT_PHOTO_ITEM)

            products_data = self.get_products_data(driver, products, product_photos)

            logger.info(f"Parsed {len(products_data)} products")
            return products_data
