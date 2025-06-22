import yfinance as yf
import pandas as pd

# 1) ticker map
domain_to_ticker = {
    "amazon.com":      "AMZN",
    "temu.com":        "PDD",        
    "aliexpress.com":  "BABA",
    "ebay.com":        "EBAY",
    "walmart.com":     "WMT",
    "alibaba.com":     "BABA",
    "flipkart.com":    None,         
    "shein.com":       None,         
    "ikea.com":        None,         
    "costco.com":      "COST",
    "lowes.com":       "LOW",
    "target.com":      "TGT",
    "bestbuy.com":     "BBY",
    "wayfair.com":     "W",
    "etsy.com":        "ETSY",
    "asos.com":        "ASOS.L", 
    "zalando.com":     "ZAL.DE", 
    "uniqlo.com":      "9983.T",     
    "hm.com":          "HM-B.ST",    
    "argos.co.uk":     None,         
    "currys.co.uk":    "CURY.L",     
    "tesco.com":       "TSCO.L",     
    "johnlewis.com":   None,         
    "next.co.uk":      "NXT.L",
    "nordstrom.com":   "JWN",
    "macys.com":       "M",
    "kohls.com":       "KSS",
    "neimanmarcus.com":None,         
    "sephora.com":     "LVMH.PA",    
    "ulta.com":        "ULTA",
    "newegg.com":      "NEGG",
    "bhphotovideo.com":None,         
    "banggood.com":    None,         
    "myntra.com":      None,         
    "ajio.com":        None,         
}

rows = []
for domain, ticker in domain_to_ticker.items():
    try:
        stock = yf.Ticker(ticker)
        fin = stock.financials
        rev_line = next(idx for idx in fin.index if "Total Revenue" in idx)
        latest_year = fin.columns[0]
        revenue = fin.loc[rev_line, latest_year]
        rows.append((domain, int(revenue)))
    except Exception as e:
        print(f"[WARN] Could not fetch {ticker}: {e}")


df = pd.DataFrame(rows, columns=["site_domain","annual_revenue_usd"])
df.to_csv("fetched_revenues.csv", index=False)
print(df.to_csv(index=False))