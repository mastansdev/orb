from curl_cffi import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nseindia.com/get-quotes/equity",
}

symbol = "SBIN"

try:
    session = requests.Session(impersonate="chrome")
    session.headers.update(HEADERS)

    # Get NSE cookies
    session.get("https://www.nseindia.com", timeout=10)

    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    response = session.get(url, timeout=10)

    print("Status Code:", response.status_code)

    data = response.json()

    print("\nCompany :", data["info"].get("companyName"))
    print("Sector  :", data.get("industryInfo", {}).get("sector"))
    print("Industry:", data.get("industryInfo", {}).get("industry"))
    print("Price   :", data.get("priceInfo", {}).get("lastPrice"))

except Exception as e:
    print("\nERROR:")
    print(e)