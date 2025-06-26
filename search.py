from playwright.sync_api import sync_playwright
import json

# Function to convert text to camel case (proper title case)
def to_camel_case(text):
    return ' '.join(word.capitalize() for word in text.split())

# Function to parse raw card content and extract specific fields with desired labels
def parse_card_content(card_content):
    lines = card_content.splitlines()  # Split the content into lines
    data = {}

    # Extracting specific fields based on their labels and structure
    for i, line in enumerate(lines):
        if line == 'Chipnummer':
            data['Chipnummer'] = lines[i + 1].strip() if i + 1 < len(lines) else "Not found"
        elif line == 'Tilltalsnamn':
            data['Djurnamn'] = lines[i + 1].strip() if i + 1 < len(lines) else "Not found"
        elif line == 'Ras':
            data['Ras'] = lines[i + 1].strip() if i + 1 < len(lines) else "Not found"
        elif line == 'Kön':
            data['Kön'] = lines[i + 1].strip() if i + 1 < len(lines) else "Not found"
        elif line == 'Född':
            data['Födelsedatum'] = lines[i + 1].strip() if i + 1 < len(lines) else "Not found"
        elif line == 'Färg':
            data['Färg'] = lines[i + 1].strip() if i + 1 < len(lines) else "Not found"
        elif line == 'Ägaren':
            owner_name = lines[i + 1].strip() if i + 1 < len(lines) else "Not found"
            data['Ägarnamn'] = to_camel_case(owner_name)
        elif line == 'Mobil':
            data['Mobil'] = lines[i + 1].strip() if i + 1 < len(lines) else "Not found"
        elif line == 'E-post':
            data['Email'] = lines[i + 1].strip().lower() if i + 1 < len(lines) else "Not found"

    return data

# Vercel serverless function entry point
def handler(request):
    # Get chip ID from query parameters
    chip_id = request.query_params.get('chip_id')
    
    if not chip_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Chip ID is required"})
        }

    # Launch Playwright and fetch the data
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to the TASS public search page
        page.goto("https://etjanst.sjv.se/tasspub/#/")

        # Wait for the chip number input field to be available
        page.wait_for_selector("#input1")

        # Select the animal type radio button (e.g., Hund)
        page.click("label[for='1']")  # Clicking on the "Hund" radio button (id="1")

        # Locate the search input field and enter the chip number
        page.fill("#input1", chip_id)

        # Click the search button
        page.click("button[type='submit']")

        # Wait for the result card to appear
        page.wait_for_selector(".c-card--medium")

        # Extract the entire card content
        try:
            # Grab all the text inside the result card
            card_content = page.query_selector(".c-card__main").inner_text()

            # Now parse the card content into the custom dictionary format
            parsed_data = parse_card_content(card_content)
            browser.close()

            # Return parsed data as JSON
            return {
                "statusCode": 200,
                "body": json.dumps(parsed_data)
            }
        
        except AttributeError:
            browser.close()
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Card content not found"})
            }
