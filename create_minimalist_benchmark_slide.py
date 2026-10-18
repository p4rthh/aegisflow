import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from PIL import Image

# 1. Plot parameters
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

# Load actual backtest tick data
t_af = pd.read_parquet('artifacts/ticks_aegisflow.parquet')
t_b0 = pd.read_parquet('artifacts/ticks_baseline0_cash.parquet')
t_b1 = pd.read_parquet('artifacts/ticks_baseline1_greedy.parquet')
t_b2 = pd.read_parquet('artifacts/ticks_baseline2_static.parquet')
hours = np.arange(len(t_af))

# --- CREATE 1920x1080 COMPLETE SLIDE WITH MATPLOTLIB ---
fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor='#000000')

# Outer layout: GridSpec
gs = fig.add_gridspec(
    nrows=3, ncols=2,
    height_ratios=[1.15, 3.8, 2.5],
    width_ratios=[1.08, 0.92],
    left=0.04, right=0.96,
    top=0.88, bottom=0.05,
    wspace=0.08, hspace=0.25
)

# 1. HEADER
fig.text(0.04, 0.942, "AEGISFLOW", fontsize=15, fontweight='bold', color='#2DD4BF')
fig.text(0.125, 0.942, "/", fontsize=16, color='#444444')
fig.text(0.14, 0.942, "QUANTITATIVE BENCHMARKS & MODEL ACCURACY", fontsize=15, fontweight='bold', color='#FFFFFF')
fig.text(0.96, 0.942, "8,760-Hour Realized Execution & Causal Quantile ML Validation", fontsize=11.5, color='#888888', ha='right')

# Top subtle divider line
line = plt.Line2D([0.04, 0.96], [0.920, 0.920], transform=fig.transFigure, color='#222222', linewidth=1.0)
fig.add_artist(line)

# 2. KPI METRICS ROW
ax_kpi = fig.add_subplot(gs[0, :])
ax_kpi.set_facecolor('#090909')
ax_kpi.set_xticks([])
ax_kpi.set_yticks([])
for spine in ax_kpi.spines.values():
    spine.set_color('#222222')
    spine.set_linewidth(1.0)

kpis = [
    ("+$61.47M", "+3.43% Realized Net APY", "NET STRATEGY PROFIT", "#2DD4BF"),
    ("+$264.81M", "+3.43% vs -11.35% Static", "ALPHA OVER STATIC RULE", "#38BDF8"),
    ("-46.7%", "$525k vs $986k/hr Naive", "PINBALL LOSS REDUCTION", "#F59E0B"),
    ("98.53%", "Nominal Target: 99.00%", "P99 TAIL SOLVENCY COVERAGE", "#A78BFA"),
    ("<1.20ms", "41x Faster than 50ms SLA", "INFERENCE LATENCY / TICK", "#10B981"),
]

x_positions = np.linspace(0.10, 0.90, 5)
for i, (val, sub, title, color) in enumerate(kpis):
    xp = x_positions[i]
    ax_kpi.text(xp, 0.74, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color='#777777', transform=ax_kpi.transAxes)
    ax_kpi.text(xp, 0.44, val, ha='center', va='center', fontsize=21, fontweight='bold', color=color, transform=ax_kpi.transAxes)
    ax_kpi.text(xp, 0.17, sub, ha='center', va='center', fontsize=9, color='#AAAAAA', transform=ax_kpi.transAxes)
    if i < 4:
        sep_x = (x_positions[i] + x_positions[i+1]) / 2.0
        ax_kpi.plot([sep_x, sep_x], [0.15, 0.85], color='#222222', transform=ax_kpi.transAxes, linewidth=1.0)

# 3. CHART LEFT: INSTITUTIONAL HORSE-RACE
ax_race = fig.add_subplot(gs[1, 0])
ax_race.set_facecolor('#090909')
for spine in ax_race.spines.values():
    spine.set_color('#222222')

ax_race.plot(hours, (3e9 + t_af['econ_pnl']) / 1e9, label='AegisFlow Quant (+3.43% APY / +$61.5M)', color='#2DD4BF', linewidth=2.2)
ax_race.plot(hours, (3e9 + t_b0['econ_pnl']) / 1e9, label='All-Cash Baseline ($0 Yield)', color='#777777', linewidth=1.2, linestyle=':')
ax_race.plot(hours, (3e9 + t_b2['econ_pnl']) / 1e9, label='Static 20/30/30/20 (-$203.3M / Haircut Bleed)', color='#F59E0B', linewidth=1.8)
ax_race.plot(hours, (3e9 + t_b1['econ_pnl']) / 1e9, label='Naive Max-Yield Chaser (-$1.36B / Crushed)', color='#EF4444', linewidth=1.5, linestyle='--')

ax_race.set_title('Cumulative Strategy Wealth Value ($3B Initial Allocation)', fontsize=11, fontweight='bold', color='#FFFFFF', loc='left', pad=10)
ax_race.set_xlabel('Simulation Hours (Full Calendar Year: 1 to 8,760)', fontsize=9, color='#888888', labelpad=6)
ax_race.set_ylabel('Portfolio Strategy NAV ($B)', fontsize=9, color='#888888')
ax_race.set_xlim(0, 8760)
ax_race.set_ylim(1.5, 3.2)
ax_race.yaxis.set_major_formatter(ticker.FormatStrFormatter('$%.2fB'))
ax_race.grid(True, color='#1A1A1A', linestyle='--', linewidth=0.8)
ax_race.tick_params(colors='#888888', labelsize=8.5)

legend_race = ax_race.legend(frameon=True, facecolor='#111111', edgecolor='#2A2A2A', fontsize=8.5, loc='lower left')
for text in legend_race.get_texts():
    text.set_color('#E0E0E0')

# 4. CHART RIGHT: QUANTILE ML ACCURACY (Vertical Bar Plot with clean spacing)
ax_ml = fig.add_subplot(gs[1, 1])
ax_ml.set_facecolor('#090909')
for spine in ax_ml.spines.values():
    spine.set_color('#222222')

models = ['Seasonal Naive', 'AegisFlow q50\n(Median)', 'AegisFlow q90\n(Tail)', 'AegisFlow q99\n(P99 Bound)']
losses = [986.5, 525.4, 293.2, 90.4]
colors = ['#EF4444', '#38BDF8', '#818CF8', '#2DD4BF']

x_bars = np.arange(len(models))
bars = ax_ml.bar(x_bars, losses, color=colors, edgecolor='#222222', width=0.52)
ax_ml.set_xticks(x_bars)
ax_ml.set_xticklabels(models, fontsize=8.5, color='#CCCCCC')
ax_ml.set_title('Outflow Pinball Loss ($k / hr) - Lower is Better', fontsize=11, fontweight='bold', color='#FFFFFF', loc='left', pad=10)
ax_ml.set_ylabel('Empirical Pinball Loss ($k)', fontsize=9, color='#888888')
ax_ml.yaxis.set_major_formatter(ticker.FormatStrFormatter('$%.0fk'))
ax_ml.set_ylim(0, 1150)
ax_ml.grid(axis='y', color='#1A1A1A', linestyle='--', linewidth=0.8)
ax_ml.tick_params(colors='#888888', labelsize=8.5)

for bar in bars:
    h = bar.get_height()
    ax_ml.text(bar.get_x() + bar.get_width()/2.0, h + 22, f"${h:.1f}k", ha='center', va='bottom', fontsize=8.5, color='#FFFFFF', fontweight='bold')

# 5. BOTTOM SECTION: COMPARISON MATRIX TABLE
ax_tbl = fig.add_subplot(gs[2, :])
ax_tbl.set_facecolor('#090909')
ax_tbl.set_xticks([])
ax_tbl.set_yticks([])
for spine in ax_tbl.spines.values():
    spine.set_color('#222222')

col_labels = [
    "Treasury Strategy",
    "Realized APY",
    "Net Annual PnL",
    "Generated Alpha",
    "Liquidation Haircuts",
    "Overdraft Cost",
    "Max Drawdown"
]

table_rows = [
    ["AegisFlow Quant Engine", "+3.43%", "+$61,472,258", "+$264.81M (Lead)", "$12,129,913 (99% saved)", "$151,282 (24x cheaper)", "0.00% (No Loss)"],
    ["Static 20/30/30/20 Rule", "-11.35%", "-$203,336,347", "$0.00 (Baseline)", "$62,506,508", "$0.00 (Repo Broken)", "-11.35%"],
    ["Naive Max-Yield Chaser", "-76.16%", "-$1,364,160,830", "-$1,160.82M", "$1,164,886,876 (Crushed)", "$17,598,967 (Punitive)", "-76.16%"],
    ["All-Cash Buffer (Zero Risk)", "0.00%", "$0.00", "-$61.47M", "$0.00", "$0.00", "0.00%"],
]

text_colors = ['#2DD4BF', '#F59E0B', '#EF4444', '#AAAAAA']

col_widths = [0.22, 0.12, 0.14, 0.16, 0.16, 0.12, 0.08]
col_x = [0.02]
for w in col_widths[:-1]:
    col_x.append(col_x[-1] + w)

# Table Header
ax_tbl.text(0.02, 0.90, "STRATEGY PERFORMANCE & RISK BENCHMARK MATRIX", fontsize=9.5, fontweight='bold', color='#777777', transform=ax_tbl.transAxes)
for j, (header, xpos) in enumerate(zip(col_labels, col_x)):
    ax_tbl.text(xpos, 0.74, header.upper(), fontsize=8.5, fontweight='bold', color='#555555', transform=ax_tbl.transAxes)

# Subtle row divider lines
ax_tbl.plot([0.02, 0.98], [0.66, 0.66], color='#1C1C1C', transform=ax_tbl.transAxes, linewidth=0.8)

# Table Rows
y_rows = [0.52, 0.37, 0.22, 0.07]
for i, (row_data, ypos, tcolor) in enumerate(zip(table_rows, y_rows, text_colors)):
    for j, (val, xpos) in enumerate(zip(row_data, col_x)):
        fontw = 'bold' if (j in [0, 1, 2, 3] or i == 0) else 'normal'
        c = tcolor if j in [0, 1, 2, 3] else '#CCCCCC'
        ax_tbl.text(xpos, ypos, val, fontsize=9.5, fontweight=fontw, color=c, transform=ax_tbl.transAxes)

# Save high-resolution minimalist slide image
plt.savefig('assets/aegisflow_benchmarks_minimalist_slide.png', dpi=100, facecolor='#000000')
plt.close()

# Also save as JPG
img = Image.open('assets/aegisflow_benchmarks_minimalist_slide.png')
img.convert('RGB').save('assets/aegisflow_benchmarks_minimalist_slide.jpg', quality=96)
print("Successfully updated assets/aegisflow_benchmarks_minimalist_slide.jpg!")
