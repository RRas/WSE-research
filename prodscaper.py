import re
import time
import csv
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By

# Config

PRODUCTS_CSV      = "prodpages.csv"       # looks like: domain;product_url
OUTPUT_CSV        = "dark_pattern_prod_results.csv"
PAGE_LOAD_TIMEOUT = 30   
JS_WAIT_TIME      = 3   

# Set up headless browser (selenium)

def launch_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    # suppress WebRTC/STUN warnings
    opts.add_argument("--disable-webrtc")
    opts.add_argument("--disable-features=NetworkService,NetworkServiceInProcess")
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver

# close popups
def close_modal_overlays(driver):
    selectors = [
        (By.XPATH, "//button[contains(@aria-label, 'Close')]"),
        (By.CSS_SELECTOR, ".modal-close"),
        (By.CSS_SELECTOR, ".close-button"),
        (By.XPATH, "//button[contains(text(),'×')]")
    ]
    for by, sel in selectors:
        try:
            for e in driver.find_elements(by, sel):
                if e.is_displayed() and e.is_enabled():
                    e.click()
                    time.sleep(1)
                    return
        except:
            continue

def fetch_page(driver, url):
    try:
        driver.get(url)
        time.sleep(JS_WAIT_TIME)
        close_modal_overlays(driver)
        return driver.page_source
    except (TimeoutException, WebDriverException):
        return None

# ---------- Language detection ----------

def detect_language(html):
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("html")
    if tag and tag.has_attr("lang"):
        lang = tag["lang"].lower()
        if lang.startswith("nl"):
            return "nl"
    return "en"

# Regex patterns for detectors
# Both Dutch and English since some sites are location based

URGENCY_PATTERNS = {
    "en":[r"\bonly\s+\d+\s+(left|remaining)\b",r"\blimited time\b",r"\bhurry\b",
          r"\bact now\b",r"\bwhile supplies last\b",r"\bselling fast\b",
          r"\bends (today|in \d+ (hours?|minutes?))\b",r"\bscarcity\b"],
    "nl":[r"\bnog maar\s+\d+\s+over\b",r"\bbeperkte tijd\b",r"\bsnel\b",
          r"\bhandel snel\b",r"\bbijna uitverkocht\b",r"\bnu bestellen\b"]
}
CONFIRMSHAME_PATTERNS = {
    "en":[r"\bno\s+thanks\b.*\b(hate|don’t want|don’t need)\b",
          r"\bskip (this )?offer\b",r"\bnot now\b.*\bsave\b",r"\bi refuse\b"],
    "nl":[r"\bnee dank\b.*\b(wil niet|wil geen|haat)\b",
          r"\boké, later\b.*\bbesparen\b",r"\boverslaan aanbod\b"]
}
HIDDEN_COST_PATTERNS = {
    "en":[r"\bshipping\b.*\b(total|checkout)\b",r"\btax(es)?\b.*\b(total|checkout)\b",
          r"\bhandling fee\b",r"\badditional fee(s)?\b"],
    "nl":[r"\bverzendkosten\b.*\b(totaal|afrekenen)\b",r"\bbelasting\b.*\b(totaal|afrekenen)\b",
          r"\bhandlingskosten\b"]
}
SUBSCRIPTION_TRAP_PATTERNS = {
    "en":[r"\bfree trial\b",r"\b(automatically )?renew(s|al)?\b",r"\bcancel anytime\b"],
    "nl":[r"\bgratis proefversie\b",r"\b(wordt )?automatisch verlengd\b",r"\bte allen tijde annuleren\b"]
}
SOCIAL_PROOF_PATTERNS = {
    "en":[r"\bpeople\s+are\s+viewing\s+this\b",r"\bonly\s+\d+\s+left\s+in\s+stock\b",
          r"\btrending now\b",r"\b\d+\s+bought this (today|in last \d+ (hours?|minutes?))\b"],
    "nl":[r"\bx mensen bekijken dit\b",r"\bnog maar\s+\d+\s+op voorraad\b",
          r"\bhitlijsten\b",r"\b\d+\s+keer verkocht\b"]
}
APP_DOWNLOAD_PATTERNS = {"en":[r"\b(download|use|install)\s+(our\s+)?app\b",r"\bmobile app discount\b"]}
LOWEST_PRICE_PATTERNS = {"en":[r"lowest price (in \d+ days|ever)\b",r"best price (today|this week)\b"]}
CHECKOUT_WARNING_PATTERNS = {
    "en":[r"\b(tax(?:es)?|shipping).{0,20}\b(checkout|at checkout)\b",r"\bwill apply (at checkout)\b"],
    "nl":[r"\b(belasting|verzendkosten).{0,20}\b(afrekenen|bij afrekening)\b"]
}
BULK_UPSELL_PATTERNS = {"en":[r"buy\s+\d+\s+and\s+save\s+\d+%?\b",r"order\s+\d+\s+to\s+get\s+\d+%?\s+off"]}
GAMIFICATION_PATTERNS = {"en":[r"\bcongratulations\b",r"\b(earned|earn) (points|rewards)\b",
                              r"\bspin to win\b",r"\benter to win\b"]}

def detect_pattern(html, pats):
    txt = BeautifulSoup(html, "lxml").get_text(" ")
    return any(re.search(p, txt, re.IGNORECASE) for p in pats)

# All detectors

def detect_urgency(html, lang):          return detect_pattern(html, URGENCY_PATTERNS.get(lang, URGENCY_PATTERNS["en"]))
def detect_confirmshame(html, lang):     return detect_pattern(html, CONFIRMSHAME_PATTERNS.get(lang, CONFIRMSHAME_PATTERNS["en"]))
def detect_hidden_costs(html, lang):     return detect_pattern(html, HIDDEN_COST_PATTERNS.get(lang, HIDDEN_COST_PATTERNS["en"]))
def detect_subscription_trap(html, lang):return detect_pattern(html, SUBSCRIPTION_TRAP_PATTERNS.get(lang, SUBSCRIPTION_TRAP_PATTERNS["en"]))
def detect_social_proof(html, lang):     return detect_pattern(html, SOCIAL_PROOF_PATTERNS.get(lang, SOCIAL_PROOF_PATTERNS["en"]))
def detect_price_anchoring(html):
    soup = BeautifulSoup(html, "lxml")
    return any(re.search(r"(\$|€|£|¥|₹)\s*\d+", t.get_text()) for t in soup.find_all(['del','s']))
def detect_css_strikethrough_pricing(html):
    soup = BeautifulSoup(html, "lxml")
    if any(re.search(r"(\$|€|£|¥|₹)\s*\d+", t.get_text()) for t in soup.find_all(style=re.compile(r"line-?through", re.IGNORECASE))):
        return True
    return any(soup.select(f".{cls}") for cls in ['old-price','price-del','strike-price'])
def detect_prechecked_optin(html, lang):
    opts = {"en":[r"\bsubscribe\b",r"\bwarranty\b",r"\bgift wrap\b",r"\bnewsletter\b"],
            "nl":[r"\babonneer\b",r"\bgarantie\b",r"\bcadeauverpakking\b",r"\bnieuwsbrief\b"]}
    soup = BeautifulSoup(html, "lxml")
    for inp in soup.find_all('input',{'type':'checkbox'}):
        if inp.has_attr('checked') or inp.get('checked') in ['checked','true','yes']:
            label = ""
            if inp.has_attr('id'):
                lbl = soup.find('label',{'for':inp['id']})
                label = lbl.get_text(" ") if lbl else ""
            if not label:
                label = inp.parent.get_text(" ")
            if detect_pattern(label, opts.get(lang, opts["en"])):
                return True
    return False
def detect_countdown_timer(html):
    txt = BeautifulSoup(html, "lxml").get_text(" ")
    if re.search(r"\b\d{1,2}:\d{2}:\d{2}\b", txt): return True
    soup = BeautifulSoup(html, "lxml")
    return bool(soup.find(attrs={'class':re.compile(r'countdown|timer',re.I)}))
def detect_app_download_banner(html, lang):    return detect_pattern(html, APP_DOWNLOAD_PATTERNS["en"])
def detect_lowest_price_badge(html, lang):    return detect_pattern(html, LOWEST_PRICE_PATTERNS["en"])
def detect_checkout_warning(html, lang):      return detect_pattern(html, CHECKOUT_WARNING_PATTERNS.get(lang, CHECKOUT_WARNING_PATTERNS["en"]))
def detect_bulk_upsell(html, lang):          return detect_pattern(html, BULK_UPSELL_PATTERNS["en"])
def detect_gamified_popup(html, lang):       return detect_pattern(html, GAMIFICATION_PATTERNS["en"])

# Run detection per product page

def analyze_page(domain, html):
    lang = detect_language(html)
    flags = {
        "urgency": detect_urgency(html, lang),
        "confirmshame": detect_confirmshame(html, lang),
        "hidden_costs": detect_hidden_costs(html, lang),
        "subscription_trap": detect_subscription_trap(html, lang),
        "social_proof": detect_social_proof(html, lang),
        "price_anchoring": detect_price_anchoring(html),
        "css_strikethrough_price": detect_css_strikethrough_pricing(html),
        "prechecked_optin": detect_prechecked_optin(html, lang),
        "countdown_timer": detect_countdown_timer(html),
        "app_download_banner": detect_app_download_banner(html, lang),
        "lowest_price_badge": detect_lowest_price_badge(html, lang),
        "checkout_warning": detect_checkout_warning(html, lang),
        "bulk_upsell": detect_bulk_upsell(html, lang),
        "gamified_popup": detect_gamified_popup(html, lang),
    }
    total = sum(flags.values())
    return {
        "site_domain": domain,
        "language": lang,
        **flags,
        "total_patterns": total,
        "timestamp": pd.Timestamp.now()
    }

# Main

def run():
    driver = launch_driver()
    headers = ["site_domain","language"] + list(analyze_page("", "<html></html>").keys())[2:]
    # write header
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as out:
        csv.DictWriter(out, fieldnames=headers).writeheader()

    df = pd.read_csv(PRODUCTS_CSV, sep=';')
    for _, row in df.iterrows():
        domain = row["domain"].strip()
        url = row["product_url"].strip()

        html = fetch_page(driver, url)
        if not html:
            print(f"[WARN] Failed to load {url} — skipping.")
            continue

        try:
            result = analyze_page(domain, html)
        except Exception as e:
            print(f"[ERROR] Analysis failed for {url}: {e} — skipping.")
            continue

        with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as out:
            csv.DictWriter(out, fieldnames=headers).writerow(result)

        print(f"[INFO] {domain} → patterns={result['total_patterns']}")

    driver.quit()
    print("[INFO] Done.")

if __name__ == "__main__":
    run()
