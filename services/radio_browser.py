
import requests
API='https://de1.api.radio-browser.info/json'

def search(query, limit=25):
    try:
        r = requests.get(f'{API}/stations/search',
            params={'name':query,'hidebroken':'true','limit':limit},
            timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Radio Browser API Error (Search): {e}")
        return []

def country(code, limit=25):
    try:
        r = requests.get(f'{API}/stations/search',
            params={'countrycode':code,'order':'clickcount','reverse':'true','hidebroken':'true','limit':limit},
            timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Radio Browser API Error (Country): {e}")
        return []
