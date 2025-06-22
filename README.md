# Dark Pattern Detection in E-Commerce

This project analyzes how often dark patterns appear on major e-commerce websites and whether they relate to customer satisfaction or business success. It uses automated scraping, pattern detection, and statistical analysis to provide insights into deceptive design practices in digital commerce.

---

## Overview

- Crawls product pages from top global e-commerce sites.
- Detects **14 types** of dark patterns (e.g. urgency, hidden costs, confirmshaming).
- Correlates pattern usage with:
  - Trustpilot **ratings**
  - Publicly available **sales/revenue**
- Produces visualizations and statistical summaries.

---

## Project Structure

| Filename                      | Description                                                             |
|-------------------------------|-------------------------------------------------------------------------|
| `prodscraper.py`              | Crawls product pages and detects 14 types of dark patterns              |
| `analyze.py`                  | Performs statistical analysis (correlation, regression, ANOVA, plots)   |
| `revenue.py`                  | Fetches annual revenue from Yahoo Finance for public companies          |
| `prodpages.csv`               | Input list of product URLs per e-commerce site                          |
| `dark_pattern_prod_results.csv` | Output of pattern detection flags per product page                   |
| `site_metrics.csv`            | Combined dataset with site ratings and revenue                          |
| `fetched_revenues.csv`        | Output of scraped revenue per domain                                    |
| `anova_rating_by_density_quartile.csv` | ANOVA test results for ratings vs. dark pattern density      |
| `patterns_distribution_bar.png` | Bar chart of pattern count distribution across sites                 |
| `pattern_cooccurrence_heatmap.png` | Heatmap showing correlation between co-occurring patterns       |
| `requirements.txt`            | Lists required Python packages                                          |
| `README.md`                   | This document                                                           |

