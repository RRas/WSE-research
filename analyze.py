import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import pearsonr, spearmanr, kruskal
import matplotlib.pyplot as plt

# Load data
DARK_PATTERN_CSV = "dark_pattern_prod_results.csv"
METRICS_CSV       = "site_metrics.csv"

dark_df    = pd.read_csv(DARK_PATTERN_CSV)
metrics_df = pd.read_csv(METRICS_CSV)

metrics_df['sales'] = pd.to_numeric(metrics_df['sales'], errors='coerce')

# List all dark pattern flag columns
pattern_cols = [
    'urgency', 'confirmshame', 'hidden_costs', 'subscription_trap',
    'social_proof', 'price_anchoring', 'css_strikethrough_price',
    'prechecked_optin', 'countdown_timer', 'app_download_banner',
    'lowest_price_badge', 'checkout_warning', 'bulk_upsell', 'gamified_popup'
]

# mean flags per site
site_patterns = dark_df.groupby('site_domain')[pattern_cols].mean()

# mean total_patterns - density per site
site_density  = dark_df.groupby('site_domain')['total_patterns'].mean().rename('density')

# merge with metrics
df = (
    site_patterns
    .join(site_density)
    .reset_index()
    .merge(metrics_df, on='site_domain')
)

# check for variation, otherwise some analyses might not work
def has_variation(s):
    return s.dropna().nunique() > 1

public_tickers = {
    "amazon.com","temu.com","aliexpress.com","ebay.com","walmart.com",
    "alibaba.com","costco.com","lowes.com","target.com","bestbuy.com",
    "wayfair.com","etsy.com","asos.com","zalando.com","uniqlo.com",
    "hm.com","currys.co.uk","tesco.com","next.co.uk","nordstrom.com",
    "macys.com","kohls.com","sephora.com","ulta.com","newegg.com"
}
df['is_public'] = df['site_domain'].isin(public_tickers)

# ---------- 1. Pearson & Spearman correlations ----------
print("\n=== Correlations ===")
# Ratings
if has_variation(df['rating']):
    r, p   = pearsonr(df['density'], df['rating'])
    rho, ps = spearmanr(df['density'], df['rating'])
    print(f"Pearson(rating, density): r={r:.3f}, p={p:.3f}")
    print(f"Spearman(rating, density): ρ={rho:.3f}, p={ps:.3f}")
else:
    print("[WARN] Skipping rating correlations (no variation).")

sales_df = df.dropna(subset=['sales'])
if has_variation(sales_df['sales']):
    r_s, p_s     = pearsonr(sales_df['density'], sales_df['sales'])
    rho_s, ps_s  = spearmanr(sales_df['density'], sales_df['sales'])
    print(f"Pearson(sales, density): r={r_s:.3f}, p={p_s:.3f}")
    print(f"Spearman(sales, density): ρ={rho_s:.3f}, p={ps_s:.3f}")
else:
    print("[WARN] Skipping sales correlations (no variation or all NaN).")

# ---------- 2. OLS regressions ----------
print("\n=== OLS Regressions ===")
X = sm.add_constant(df['density'])

# Rating regression
if has_variation(df['rating']):
    m1 = sm.OLS(df['rating'], X).fit()
    print("\nOLS: rating ~ density")
    print(m1.summary())
else:
    print("[WARN] Skipping OLS on rating.")

# Sales regression (log+1)
if has_variation(sales_df['sales']):
    y_sales = np.log(sales_df['sales'] + 1)
    X_sales = sm.add_constant(sales_df['density'])
    m2 = sm.OLS(y_sales, X_sales).fit()
    print("\nOLS: log(sales+1) ~ density")
    print(m2.summary())
else:
    print("[WARN] Skipping OLS on sales.")

# ---------- 3. ANOVA ----------
print("\n=== ANOVA: rating by density quartile ===")
if has_variation(df['rating']) and has_variation(df['density']):
    df['quartile'] = pd.qcut(df['density'], 4, labels=False, duplicates='drop')
    aov = smf.ols('rating ~ C(quartile)', data=df).fit()
    print(sm.stats.anova_lm(aov, typ=2))
else:
    print("[WARN] Skipping ANOVA (insufficient variation).")

# ---------- 4. Logistic regression =====
print("\n=== Logistic Regression: high_rating ~ density * is_public ===")
if has_variation(df['rating']):
    df['high_rating'] = (df['rating'] >= 4.0).astype(int)
    if has_variation(df['high_rating']):
        logit = smf.logit('high_rating ~ density * is_public', data=df).fit(disp=False)
        print(logit.summary())
    else:
        print("[WARN] Skipping logistic (high_rating constant).")
else:
    print("[WARN] Skipping logistic (no rating variation).")

# ---------- 5. Quantile regression ===========
print("\n=== Quantile Regression (median): rating ~ density ===")
if has_variation(df['rating']):
    qr = smf.quantreg('rating ~ density', data=df).fit(q=0.5)
    print(qr.summary())
else:
    print("[WARN] Skipping quantile regression (no rating variation).")

# ---------- 6. Kruskal–Wallis ===========
print("\n=== Kruskal-Wallis: sales by density quartile ===")
if has_variation(sales_df['sales']) and 'quartile' in df:
    groups = [g['sales'].values for _, g in df.merge(sales_df[['site_domain']], on='site_domain').groupby('quartile')]
    stat, pval = kruskal(*groups)
    print(f"H = {stat:.3f}, p = {pval:.3f}")
else:
    print("[WARN] Skipping Kruskal-Wallis (insufficient variation).")

# ---------- 7. Co-occurrence heatmap ===========
print("\n=== Plotting Pattern Co-occurrence Heatmap ===")
nonzero = site_patterns.columns[site_patterns.sum() > 0]
cooc = site_patterns[nonzero].corr()
fig, ax = plt.subplots(figsize=(8,8))
cax = ax.imshow(cooc, vmin=-1, vmax=1, cmap='coolwarm')
ax.set_xticks(np.arange(len(nonzero)))
ax.set_xticklabels(nonzero, rotation=90)
ax.set_yticks(np.arange(len(nonzero)))
ax.set_yticklabels(nonzero)
ax.set_title('Pattern Co-occurrence Heatmap')
fig.colorbar(cax, ax=ax)
plt.tight_layout()
plt.savefig("pattern_cooccurrence_heatmap.png")
plt.clf()

# ---------- 8. Bar chart: total_patterns distribution ===========
print("\n=== Distribution of total_patterns per site ===")
counts = df['density'].round().value_counts().sort_index()
dist = pd.DataFrame({
    'patterns': counts.index.astype(int),
    'site_count': counts.values,
    'pct_of_sites': 100 * counts.values / len(df)
})
print(dist.to_string(index=False))

# Make plot
fig, ax = plt.subplots()
ax.bar(dist['patterns'], dist['site_count'])
ax.set_xlabel('Number of Patterns Detected')
ax.set_ylabel('Number of Sites')
ax.set_title('Distribution of Total Dark Patterns per Site')
plt.tight_layout()
plt.savefig("patterns_distribution_bar.png")
plt.clf()


num_ge1 = (df['density'] >= 1).sum()
num_ge2 = (df['density'] >= 2).sum()
if num_ge1:
    cond = num_ge2 / num_ge1
    print(f"\nP(total_patterns ≥ 2 | ≥1) = {cond:.2f} ({num_ge2}/{num_ge1})")
else:
    print("[WARN] No sites with ≥1 pattern.")
