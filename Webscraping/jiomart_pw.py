from playwright.sync_api import sync_playwright
import time
import json

def enter_pincode(page, pincode="400020"):
    try:
        print("Checking for pincode input...")
        # Wait for pincode input to appear (adjust selector if needed)
        page.wait_for_selector("input[placeholder*='Pincode']", timeout=10000)
        
        # Fill the pincode
        page.fill("input[placeholder*='Pincode']", pincode)
        
        # Click the confirm/submit button (adjust selector or text if needed)
        page.click("button:has-text('Confirm')")
        
        print(f"Pincode {pincode} entered and submitted.")
        
        # Wait for products to load after pincode submit
        page.wait_for_selector(".plp-card-container", timeout=30000)
    except Exception as e:
        print("Pincode prompt not found or submit failed:", e)

def scroll_to_bottom(page, scroll_pause=3, max_scrolls=30):
    """
    Scrolls to the bottom of the page until no new content is loaded or max_scrolls is reached.
    """
    last_count = 0
    for i in range(max_scrolls):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)

        product_cards = page.query_selector_all(".plp-card-container")
        current_count = len(product_cards)
        print(f"Scroll {i+1}/{max_scrolls}: {current_count} products loaded")

        if current_count == last_count:
            print("No more new products loaded. Stopping scroll.")
            break
        last_count = current_count

def extract_products(page):
    """
    Extracts product details from the page.
    """
    products = []
    product_cards = page.query_selector_all(".plp-card-container")
    print(f"Found {len(product_cards)} product cards.")

    for card in product_cards:
        name = card.query_selector(".plp-card-details-name")
        price_discounted = card.query_selector("span.jm-heading-xxs.jm-mb-xxs")
        price_original = card.query_selector("span.jm-body-xxs.jm-fc-primary-grey-60.line-through.jm-mb-xxs")
        offer_percent = card.query_selector(".plp-card-details-discount.jm-mb-xxs")
        bank_offer = card.query_selector("span.jm-badge.jm-badge-offer.jm-body-xxs")
        limited_time = card.query_selector("span.jm-fc-primary-grey-100")
        
        product = {
            'name': name.inner_text().strip() if name else "",
            'price_discounted': price_discounted.inner_text().strip() if price_discounted else "",
            'price_original': price_original.inner_text().strip() if price_original else "",
            'offer_percent': offer_percent.inner_text().strip() if offer_percent else "",
            'bank_offer': bank_offer.inner_text().strip() if bank_offer else "",
            'limited_time': limited_time.inner_text().strip() if limited_time else "",
        }
        products.append(product)
    return products

def save_products_to_json(products, filename="jiomart_tvs.json"):
    """
    Saves the list of products to a JSON file.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(products)} products to {filename}")

def scrape_jiomart_tvs(url, max_scrolls=30, pincode="400020"):
    """
    Scrapes JioMart TV products using infinite scrolling after entering pincode.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        print(f"Loading {url}")
        page.goto(url, timeout=120000)
        time.sleep(60)
        print("Page loaded, checking for pincode input...")
        # Wait for the page to load and check for pincode input

        # Enter pincode to unlock full product list
        enter_pincode(page, pincode)

        # Scroll to load all products
        scroll_to_bottom(page, max_scrolls=max_scrolls)

        # Extract product info
        products = extract_products(page)
        browser.close()
    return products

if __name__ == "__main__":
    JIOMART_TV_URL = "https://www.jiomart.com/c/electronics/tv-home-entertainment/televisions/32152?prod_mart_master_vertical_products_popularity%5Bpage%5D"
    print("Starting JioMart TV scraping...")

    products = scrape_jiomart_tvs(JIOMART_TV_URL, max_scrolls=20, pincode="110001")
    
    if products:
        print(f"Extracted {len(products)} products.")
        save_products_to_json(products)
    else:
        print("No products found.")
