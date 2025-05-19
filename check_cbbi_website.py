import requests
from bs4 import BeautifulSoup

def check_cbbi_website():
    """
    Debug function to check the CBBI website's current structure and extract the score
    """
    try:
        # Get the CBBI website content
        response = requests.get('https://colintalkscrypto.com/cbbi/', 
                               headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        
        # Save the HTML for inspection
        with open('cbbi_page.html', 'w') as f:
            f.write(response.text)
            
        print(f"Page saved to cbbi_page.html")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try different ways to find the score
        print("Searching for score in different ways...")
        
        # Look for h1 tags
        h1_tags = soup.find_all('h1')
        print(f"Found {len(h1_tags)} h1 tags")
        for i, tag in enumerate(h1_tags):
            print(f"H1 tag {i+1}: {tag.text.strip()}")
        
        # Look for the score using content matching
        def has_index_or_score(tag):
            return tag.name in ['h1', 'h2', 'div'] and ('77' in tag.text or 'confidence' in tag.text.lower())
        
        score_candidates = soup.find_all(has_index_or_score)
        print(f"\nFound {len(score_candidates)} potential score elements")
        for i, element in enumerate(score_candidates):
            print(f"Candidate {i+1}: {element.name} - '{element.text.strip()}'")
            
        # Check for any div with class containing the word 'score'
        score_divs = soup.find_all(lambda tag: tag.name == 'div' and tag.has_attr('class') and any('score' in cls.lower() for cls in tag['class']))
        print(f"\nFound {len(score_divs)} divs with 'score' in class")
        for i, div in enumerate(score_divs):
            print(f"Score div {i+1}: classes={div.get('class')}, text='{div.text.strip()}'")
            
        # Try to find the main content section
        main_section = soup.find('main') or soup.find('div', id='main') or soup.find('div', class_='main')
        if main_section:
            print("\nFound main content section, extracting children:")
            for i, child in enumerate(list(main_section.children)[:10]):  # First 10 children
                if hasattr(child, 'name') and child.name is not None:
                    print(f"Child {i+1}: {child.name} - '{child.text.strip()[:50]}'...")
        
        return "Inspection complete, check the output for details"
        
    except Exception as e:
        print(f"Error inspecting CBBI website: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = check_cbbi_website()
    print(result)