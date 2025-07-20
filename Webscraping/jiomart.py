from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json


def safe_text(driver, selector, element=None):
    """
    Safely extract text from an element using CSS selector
    Returns empty string if element not found
    """
    try:
        if element:
            # Search within a specific element
            found_element = element.find_element(By.CSS_SELECTOR, selector)
        else:
            # Search in the entire page
            found_element = driver.find_element(By.CSS_SELECTOR, selector)
        return found_element.text.strip()
    except (NoSuchElementException, TimeoutException):
        return ""

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Uncomment the next line to run in headless mode
    # chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scroll_and_load_products(driver, max_scrolls=10, scroll_pause_time=3):
    """
    Scroll down to load more products dynamically
    Returns when no more products are loading or max_scrolls reached
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    products_loaded = 0
    
    for scroll_count in range(max_scrolls):
        print(f"Scroll {scroll_count + 1}/{max_scrolls}")
        
        # Count current products before scrolling
        current_products = len(driver.find_elements(By.CSS_SELECTOR, ".plp-card-details-name"))
        
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Wait for new content to load
        time.sleep(scroll_pause_time)
        
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        new_products = len(driver.find_elements(By.CSS_SELECTOR, ".plp-card-details-name"))
        
        print(f"Products loaded: {new_products} (added {new_products - current_products})")
        
        # Break if no more content is loading
        if new_height == last_height and new_products == current_products:
            print("No more products loading, stopping scroll")
            break
            
        # Also try waiting for loading indicators to disappear
        try:
            # Wait for any loading spinners/indicators to disappear
            WebDriverWait(driver, 5).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [data-testid='loading']"))
            )
        except TimeoutException:
            # No loading indicators found or they didn't disappear, continue anyway
            pass
        
        last_height = new_height
        products_loaded = new_products
    
    return products_loaded

def extract_all_products(driver):
    """
    Extract all product details after scrolling is complete
    """
    products = []
    
    try:
        # Wait for products to load initially
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".plp-card-details-name"))
        )
        
        # Find all product cards - you may need to adjust this selector based on the actual structure
        product_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid='plp-card'], .plp-card, .product-card")
        
        if not product_cards:
            # Fallback: try to find products by name selector and work backwards
            product_names = driver.find_elements(By.CSS_SELECTOR, ".plp-card-details-name")
            if product_names:
                # If we found names, try to get their parent containers
                product_cards = []
                for name in product_names:
                    try:
                        # Try different parent selectors
                        parent_selectors = [
                            "./ancestor::*[contains(@class, 'card')]",
                            "./ancestor::*[contains(@class, 'product')]", 
                            "./ancestor::div[position()<=3]",  # Go up max 3 div levels
                            "./.."  # Direct parent
                        ]
                        
                        for selector in parent_selectors:
                            try:
                                parent = name.find_element(By.XPATH, selector)
                                product_cards.append(parent)
                                break
                            except:
                                continue
                    except:
                        # If we can't find parent, use the name element itself
                        product_cards.append(name)
        
        print(f"Found {len(product_cards)} total products after scrolling")
        
        seen_products = set()  # To avoid duplicates
        
        for i, card in enumerate(product_cards):
            try:
                product = {
                    'name': safe_text(driver, '.plp-card-details-name', card),
                    'price_discounted': safe_text(driver, 'span.jm-heading-xxs.jm-mb-xxs', card),
                    'price_original': safe_text(driver, 'span.jm-body-xxs.jm-fc-primary-grey-60.line-through.jm-mb-xxs', card),
                    'offer_percent': safe_text(driver, '.plp-card-details-discount.jm-mb-xxs', card) or safe_text(driver, 'span.jm-badge', card),
                    'bank_offer': safe_text(driver, 'span.jm-badge.jm-badge-offer.jm-body-xxs', card),
                    'limited_time': safe_text(driver, 'span.jm-fc-primary-grey-100', card),
                    'position': i + 1
                }
                
                # Only add products that have at least a name and avoid duplicates
                if product['name'] and product['name'] not in seen_products:
                    products.append(product)
                    seen_products.add(product['name'])
                    print(f"Product {len(products)}: {product['name'][:50]}...")
                
            except Exception as e:
                print(f"Error extracting product {i+1}: {str(e)}")
                continue
    
    except TimeoutException:
        print("Timeout waiting for products to load")
    except Exception as e:
        print(f"Error during extraction: {str(e)}")
    
    return products

def scrape_jiomart_tvs(url, max_scrolls=10):
    """
    Main function to scrape JioMart TV products using infinite scroll
    """
    driver = setup_driver()
    all_products = []
    
    try:
        print(f"Loading: {url}")
        driver.get(url)
        
        # Wait for initial page load
        time.sleep(30)  # Adjust this if needed, or use WebDriverWait for specific elements
        print("Page loaded, waiting for products to appear...")
        
        print("Starting infinite scroll to load all products...")
        
        # Scroll and load all products
        total_products_loaded = scroll_and_load_products(driver, max_scrolls)
        print(f"Finished scrolling. Total products visible: {total_products_loaded}")
        
        # Extract all products after scrolling is complete
        all_products = extract_all_products(driver)
        
        print(f"Successfully extracted {len(all_products)} unique products")
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    
    finally:
        driver.quit()
    
    return all_products

def save_products_to_json(products, filename="jiomart_tvs.json"):
    """Save products to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(products)} products to {filename}")

# Example usage
if __name__ == "__main__":
    # Replace with actual JioMart TV page URL
    JIOMART_TV_URL = "https://www.jiomart.com/c/electronics/tv-home-entertainment/televisions/32152?prod_mart_master_vertical_products_popularity%5Bpage%5D"
    
    print("Starting JioMart TV scraping...")
    print("Make sure you have ChromeDriver installed and in PATH")
    
    # Scrape products (adjust max_pages as needed)
    products = scrape_jiomart_tvs(JIOMART_TV_URL, max_scrolls=5)
    
    # Display results
    print(f"\n=== SCRAPING COMPLETE ===")
    print(f"Total products extracted: {len(products)}")
    
    if products:
        print("\nSample product:")
        print(json.dumps(products[0], indent=2))
        
        # Save to file
        save_products_to_json(products)
        
        # Display summary
        print(f"\nSummary:")
        print(f"- Products with names: {len([p for p in products if p['name']])}")
        print(f"- Products with discounted price: {len([p for p in products if p['price_discounted']])}")
        print(f"- Products with original price: {len([p for p in products if p['price_original']])}")
        print(f"- Products with offers: {len([p for p in products if p['offer_percent']])}")
        print(f"- Products with bank offers: {len([p for p in products if p['bank_offer']])}")
    else:
        print("No products extracted. Please check:")
        print("1. The URL is correct and accessible")
        print("2. The CSS selectors match the current page structure")
        print("3. The page loads completely before scraping")


