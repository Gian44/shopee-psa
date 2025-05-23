# Shopee PSA

**Shopee PSA** is a Python-based application designed to scrape product prices from Shopee, providing users with up-to-date pricing information for various products.

---

## Features

* **Price Scraping**: Automatically fetches product prices from Shopee.
* **Database Storage**: Stores scraped data in a local SQLite database (`shopee_products.db`) for easy access and analysis.
* **Configurable Settings**: Customize scraping parameters through the `config.py` file.
* **Modular Design**: Organized codebase with separate modules for scraping logic, database interactions, and Shopee-specific functions.

---

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/Gian44/shopee-psa.git
   cd shopee-psa
   ```



2. **Install Dependencies**:

   Ensure you have Python 3 installed. Then, install required packages:

   ```bash
   pip install -r requirements.txt
   ```

   After installing the requirements, run

    ```bash
   playwright install
   ```


---

## Usage

1. **Configure Settings**:

   Edit the `config.py` file to set your desired parameters, such as cookie file and db name.

2. **Run the Scraper**:

   Execute the scraper script:

   ```bash
   python shopee.py
   ```



The script will fetch product data from Shopee and store it in your `.db` file.

---

## Files Overview

* `scraper.py`: Contains functions specific to interacting with Shopee's website.
* `shopee.py`: Main script to initiate the scraping process.
* `database.py`: Handles database connections and operations.
* `config.py`: User-configurable settings for the scraper.
* `shopee_products.db`: SQLite database storing scraped product information.
* `Shopee SPA Sample Demo.mp4`: Demonstration video showcasing the application's functionality.

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

---

*Note: This project is for educational and personal use. Ensure compliance with Shopee's terms of service when using this scraper.*

---
