#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import trafilatura
import re
import json

def check_cbbi_website():
    # URL of the CBBI website
    url = "https://colintalkscrypto.com/cbbi/"
    
    # Headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Make the request
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("Successfully fetched the website")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save the full HTML for inspection
        with open("cbbi_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Saved full HTML to cbbi_page.html")
        
        # Let's check for the canvas element which might contain the gauge
        canvas_elements = soup.find_all('canvas')
        print(f"\nFound {len(canvas_elements)} canvas elements")
        for i, canvas in enumerate(canvas_elements):
            canvas_id = canvas.get('id', 'No ID') if hasattr(canvas, 'get') else 'No ID'
            canvas_class = canvas.get('class', 'No classes') if hasattr(canvas, 'get') else 'No classes'
            print(f"{i+1}. Canvas ID: {canvas_id}")
            print(f"   Canvas classes: {canvas_class}")
        
        # Look for scripts that might contain the CBBI value
        scripts = soup.find_all('script')
        print(f"\nFound {len(scripts)} script elements")
        
        # Save scripts to a file for inspection
        with open("cbbi_scripts.js", "w", encoding="utf-8") as f:
            for i, script in enumerate(scripts):
                f.write(f"// Script {i+1}\n")
                f.write(script.string if script.string else "// No inline content\n")
                f.write("\n\n")
        print("Saved scripts to cbbi_scripts.js")
        
        # Check for headers or paragraphs that might contain the score
        potential_score_elements = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'div', 'span']):
            if tag.text and re.search(r'\b\d{1,2}(\.\d{1,2})?\b', tag.text) and len(tag.text.strip()) < 100:
                potential_score_elements.append(tag)
        
        print(f"\nFound {len(potential_score_elements)} elements with potential scores")
        for i, element in enumerate(potential_score_elements):
            element_name = element.name if hasattr(element, 'name') else 'unknown'
            print(f"{i+1}. {element_name} element: {element.text.strip()}")
            parents_path = []
            if hasattr(element, 'parents'):
                for parent in element.parents:
                    if hasattr(parent, 'name') and parent.name:
                        parents_path.append(parent.name)
            parent_path_str = ' > '.join(parents_path) if parents_path else 'No path'
            print(f"   Path: {parent_path_str}")
        
        # Try to find elements with "index" or "score" in their attributes
        def has_index_or_score(tag):
            if not hasattr(tag, 'attrs'):
                return False
            for attr_name, attr_value in tag.attrs.items():
                if isinstance(attr_name, str) and ('index' in attr_name.lower() or 'score' in attr_name.lower()):
                    return True
                if isinstance(attr_value, str) and ('index' in attr_value.lower() or 'score' in attr_value.lower()):
                    return True
            return False
            
        index_elements = soup.find_all(has_index_or_score)
        
        print(f"\nFound {len(index_elements)} elements with 'index' or 'score' in attributes")
        for i, element in enumerate(index_elements):
            element_name = element.name if hasattr(element, 'name') else 'unknown'
            element_attrs = element.attrs if hasattr(element, 'attrs') else {}
            print(f"{i+1}. {element_name} element: {element_attrs}")
            element_text = element.text.strip()[:100] if hasattr(element, 'text') else 'No text'
            print(f"   Text: {element_text}")
        
        # Try to find gauge DOM elements
        print("\nSearching for potential gauge DOM elements...")
        gauge_selectors = [
            "*[class*='gauge']", 
            "*[id*='gauge']", 
            "*[class*='meter']", 
            "*[id*='meter']",
            "*[class*='chart']",
            "*[class*='donut']",
            "*[class*='circle']",
            "*[id*='chart']",
            "*[class*='score']",
            "*[class*='index']"
        ]
        
        for selector in gauge_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Found {len(elements)} elements matching '{selector}'")
                for i, element in enumerate(elements[:3]):  # Limit to first 3
                    element_name = element.name if hasattr(element, 'name') else 'unknown'
                    print(f"  {i+1}. {element_name}: {element.attrs}")
        
        # Try Trafilatura with different output formats
        print("\nUsing Trafilatura to extract structured content...")
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded:
            # Extract as XML
            xml_output = trafilatura.extract(downloaded, output_format="xml", include_comments=True, include_tables=True)
            if xml_output:
                with open("cbbi_trafilatura.xml", "w", encoding="utf-8") as f:
                    f.write(xml_output)
                print("Saved XML extraction to cbbi_trafilatura.xml")
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(downloaded)
            if metadata:
                print("\nMetadata:")
                for key, value in metadata.items():
                    print(f"{key}: {value}")
        
        # Look for number values in attribute values
        print("\nSearching for numbers in attribute values...")
        for tag in soup.find_all():
            if hasattr(tag, 'attrs'):
                for attr_name, attr_value in tag.attrs.items():
                    if isinstance(attr_value, str) and re.search(r'\b\d{1,2}(\.\d{1,2})?\b', attr_value):
                        print(f"{tag.name if hasattr(tag, 'name') else 'unknown'} [{attr_name}]: {attr_value}")
        
        # Look for network requests or JSON data embedded in the page
        print("\nSearching for potential JSON data in scripts...")
        json_pattern = re.compile(r'\{[^{}]*\{[^{}]*\}[^{}]*\}')
        for script in scripts:
            if hasattr(script, 'string') and script.string:
                json_matches = json_pattern.findall(script.string)
                for match in json_matches[:3]:  # Limit to first few matches
                    try:
                        # Try to parse as JSON
                        data = json.loads(match)
                        data_str = str(data).lower()
                        if any(key in data_str for key in ['score', 'index', 'cbbi', 'value']):
                            print(f"Potential JSON data: {match[:200]}...")
                    except json.JSONDecodeError:
                        pass
    else:
        print(f"Failed to retrieve website: {response.status_code}")

if __name__ == "__main__":
    check_cbbi_website()