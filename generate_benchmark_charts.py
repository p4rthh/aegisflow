import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

# Set global dark theme for pure black background slides
plt.rcParams['figure.facecolor'] = '#000000'
plt.rcParams['axes.facecolor'] = '#0A0A0A'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.labelcolor'] = '#E0E0E0'
plt.rcParams['xtick.color'] = '#AAAAAA'
plt.rcParams['ytick.color'] = '#AAAAAA'
plt.rcParams['text.color'] = '#FFFFFF'
plt.rcParams['grid.color'] = '#222222'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.7
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'

# Load ticks for equity curves
t_af = pd.read_parquet('artifacts/ticks_aegisflow.parquet')
t_b0 = pd.read_parquet('artifacts/ticks_baseline0_cash.parquet')
t_b1 = pd.read_parquet('artifacts/ticks_baseline1_greedy.parquet')
t_b2 = pd.read_parquet('artifacts/ticks_baseline2_static.parquet')

hours = np.arange(len(t_af))

# --- CHART 1: CUMULATIVE WEALTH HORSE-RACE (STRATEGY CUMULATIVE VALUE) ---
fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
ax.plot(hours, (3e9 + t_af['econ_pnl']) / 1e9, label='AegisFlow Quant (+3.43% APY / +$61.5M)', color='#2DD4BF', linewidth=2.5)
ax.plot(hours, (3e9 + t_b0['econ_pnl']) / 1e9, label='All-Cash Baseline ($0 Yield)', color='#888888', linewidth=1.5, linestyle=':')
ax.plot(hours, (3e9 + t_b2['econ_pnl']) / 1e9, label='Static 20/30/30/20 (-$203.3M / Haircut Spiral)', color='#F59E0B', linewidth=2.0)
ax.plot(hours, (3e9 + t_b1['econ_pnl']) / 1e9, label='Naive Max-Yield Chaser (-$1.36B / Crushed)', color='#EF4444', linewidth=1.8, linestyle='--')

ax.set_title('Institutional Benchmark Horse-Race (8,760-Hour Replay)', fontsize=13, fontweight='bold', pad=12, color='#FFFFFF')
ax.set_xlabel('Simulation Hours (Full Calendar Year)', fontsize=10, labelpad=8)
ax.set_ylabel('Portfolio Strategy NAV ($ Billions)', fontsize=10, labelpad=8)
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('$%.2fB'))
ax.set_xlim(0, 8760)
ax.set_ylim(1.5, 3.2)

ax.grid(True)
legend = ax.legend(frameon=True, facecolor='#111111', edgecolor='#333333', fontsize=9, loc='lower left')
for text in legend.get_texts():
    text.set_color('#FFFFFF')

plt.tight_layout()
plt.savefig('assets/chart_equity_curves.png', dpi=300, facecolor='#000000')
plt.close()

# --- CHART 2: PINBALL LOSS & QUANTILE CALIBRATION ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=300)

# Subplot 1: Pinball Loss Comparison
models = ['Seasonal Naive', 'AegisFlow q50', 'AegisFlow q90', 'AegisFlow q99']
losses = [986.465, 525.380, 293.201, 90.449]
colors = ['#EF4444', '#38BDF8', '#818CF8', '#2DD4BF']

bars = ax1.bar(models, losses, color=colors, edgecolor='#333333', width=0.55)
ax1.set_title('Pinball Loss Benchmark (Lower is Better)', fontsize=11, fontweight='bold', color='#FFFFFF', pad=10)
ax1.set_ylabel('Empirical Pinball Loss ($k / hr)', fontsize=9)
ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('$%.0fk'))
ax1.grid(axis='y')
ax1.tick_params(axis='x', rotation=15, labelsize=8.5)

for bar in bars:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 18, f'${yval:.1f}k', ha='center', va='bottom', fontsize=8, color='#FFFFFF', fontweight='bold')

# Subplot 2: Empirical vs Theoretical Quantile Coverage
quantiles = ['q50 (Median)', 'q90 (Upper Tail)', 'q99 (P99 Extreme)']
target_cov = [50.0, 90.0, 99.0]
empirical_cov = [50.34, 89.14, 98.53]

x = np.arange(len(quantiles))
width = 0.35

rects1 = ax2.bar(x - width/2, target_cov, width, label='Theoretical Target', color='#555555', edgecolor='#333333')
rects2 = ax2.bar(x + width/2, empirical_cov, width, label='AegisFlow Empirical', color='#2DD4BF', edgecolor='#333333')

ax2.set_title('Quantile Calibration & Coverage Alignment', fontsize=11, fontweight='bold', color='#FFFFFF', pad=10)
ax2.set_ylabel('Empirical Coverage Percentage (%)', fontsize=9)
ax2.set_xticks(x)
ax2.set_xticklabels(quantiles, fontsize=8.5)
ax2.set_ylim(0, 115)
ax2.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))
ax2.grid(axis='y')
legend2 = ax2.legend(frameon=True, facecolor='#111111', edgecolor='#333333', fontsize=8.5, loc='upper left')
for text in legend2.get_texts():
    text.set_color('#FFFFFF')

for r1, r2 in zip(rects1, rects2):
    ax2.text(r1.get_x() + r1.get_width()/2.0, r1.get_height() + 2, f'{r1.get_height():.0f}%', ha='center', va='bottom', fontsize=7.5, color='#AAAAAA')
    ax2.text(r2.get_x() + r2.get_width()/2.0, r2.get_height() + 2, f'{r2.get_height():.1f}%', ha='center', va='bottom', fontsize=7.5, color='#2DD4BF', fontweight='bold')

plt.tight_layout()
plt.savefig('assets/chart_model_benchmarks.png', dpi=300, facecolor='#000000')
plt.close()

# --- CHART 3: CAPITAL PRESERVATION & LIQUIDATION HAIRCUT LOSSES ---
fig, ax = plt.subplots(figsize=(9, 4.5), dpi=300)
strategies = ['AegisFlow Quant', 'Static 20/30/30/20', 'Naive Max-Yield']
haircuts = [12.13, 62.51, 1164.89] # in Millions
bar_colors = ['#2DD4BF', '#F59E0B', '#EF4444']

bars = ax.barh(strategies, haircuts, color=bar_colors, edgecolor='#333333', height=0.5)
ax.set_title('Total Liquidation Haircuts & Capital Destruction (Lower is Better)', fontsize=12, fontweight='bold', color='#FFFFFF', pad=10)
ax.set_xlabel('Liquidation Loss Incurred ($ Millions)', fontsize=9.5)
ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('$%.0fM'))
ax.grid(axis='x')

for bar in bars:
    xval = bar.get_width()
    ax.text(xval + 15, bar.get_y() + bar.get_height()/2.0, f'${xval:,.2f}M', ha='left', va='center', fontsize=9, color='#FFFFFF', fontweight='bold')

ax.set_xlim(0, 1300)
plt.tight_layout()
plt.savefig('assets/chart_liquidation_losses.png', dpi=300, facecolor='#000000')
plt.close()

print('Successfully generated all 3 benchmark charts!')
