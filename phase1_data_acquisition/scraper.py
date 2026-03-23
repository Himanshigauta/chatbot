import requests
import json
import time
import os
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
}

BASE_URL = "https://groww.in/v1/api/data/mf"

def get_all_amcs() -> List[str]:
    """Fetch all AMC search IDs from the main AMC page."""
    print("Fetching AMC list from Groww.in...")
    url = "https://groww.in/mutual-funds/amc"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            amc_links = soup.find_all('a', href=True)
            amc_ids = []
            for link in amc_links:
                href = link['href']
                if '/mutual-funds/amc/' in href and not href.endswith('/amc'):
                    amc_id = href.split('/')[-1]
                    if amc_id and amc_id not in amc_ids:
                        amc_ids.append(amc_id)
            return amc_ids
    except Exception as e:
        print(f"Error fetching AMC list: {e}")
    return []

def get_amc_extra_info(amc_id: str) -> Dict:
    """Scrape AMC-specific descriptive content."""
    url = f"https://groww.in/mutual-funds/amc/{amc_id}"
    print(f"  Scraping AMC Page: {amc_id}")
    info = {"key_info": "", "closer_look": ""}
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for specific headings
            headers = soup.find_all(['h2', 'h3'])
            for h in headers:
                txt = h.get_text().lower()
                if "key information about" in txt:
                    content = []
                    for sibling in h.find_next_siblings():
                        if sibling.name in ['h2', 'h3']: break
                        content.append(sibling.get_text().strip())
                    info["key_info"] = " ".join(content)
                elif "closer look" in txt or "analysis" in txt:
                    content = []
                    for sibling in h.find_next_siblings():
                        if sibling.name in ['h2', 'h3']: break
                        content.append(sibling.get_text().strip())
                    info["closer_look"] = " ".join(content)
    except Exception as e:
        print(f"    Error scraping AMC {amc_id}: {e}")
    return info

def get_fund_faqs(search_id: str) -> List[Dict]:
    """Scrape FAQs from the fund detail page."""
    url = f"https://groww.in/mutual-funds/{search_id}"
    faqs = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Groww FAQs are often in a section with 'FAQs' title
            faq_section = None
            for h in soup.find_all(['h1', 'h2', 'h3']):
                if "faq" in h.get_text().lower():
                    faq_section = h
                    break
            
            if faq_section:
                # Questions are usually in h3 or bold text
                for sibling in faq_section.find_next_siblings():
                    if sibling.name in ['h3', 'div']:
                        q = sibling.get_text().strip()
                        if q.endswith('?'):
                            a_node = sibling.find_next_sibling()
                            if a_node:
                                faqs.append({"question": q, "answer": a_node.get_text().strip()})
    except Exception:
        pass
    return faqs

def get_funds_for_amc(amc_id: str) -> List[Dict]:
    """Get all fund schemes for a given AMC via Groww API."""
    url = f"https://groww.in/v1/api/data/mf/v1/web/content/v2/page/{amc_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('fund_rows', {}).get('content', [])
    except Exception:
        pass
    return []

def get_fund_details_api(search_id: str) -> Dict:
    """Get full fund details from the scheme/search API."""
    url = f"https://groww.in/v1/api/data/mf/web/v4/scheme/search/{search_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {}

def main():
    # Final data path
    output_file = os.path.join(os.path.dirname(__file__), "mutual_fund_data_full.json")
    
    amc_ids = get_all_amcs()
    if not amc_ids:
        print("Aborting: No AMC IDs found.")
        return
    
    print(f"Found {len(amc_ids)} AMCs. Starting full extraction...")
    all_funds = []
    
    for amc_id in amc_ids:
        amc_extra = get_amc_extra_info(amc_id)
        funds = get_funds_for_amc(amc_id)
        
        print(f"  Processing {len(funds)} funds...")
        for fund in funds:
            sid = fund.get('search_id')
            if not sid: continue
            
            # Skip regular plans
            if "-regular-" in sid: continue
            
            # 1. API Data
            data = get_fund_details_api(sid)
            if not data: continue
            
            # 2. HTML Data (FAQs)
            data['faqs'] = get_fund_faqs(sid)
            data['amc_extra'] = amc_extra
            data['source_url'] = f"https://groww.in/mutual-funds/{sid}"
            
            all_funds.append(data)
            print(f"    + {data.get('scheme_name')} ({len(data['faqs'])} FAQs)")
            
            # Small delay to prevent rate limiting
            time.sleep(0.5)
            
        # Intermediary save
        with open(output_file, "w") as f:
            json.dump(all_funds, f, indent=4)
            
    print(f"Crawl complete. Total funds: {len(all_funds)}")

if __name__ == "__main__":
    main()
