import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from PIL import Image
import textwrap

# Typography & styling setup
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor='#000000')

# ==============================================================================
# 1. TOP HEADER BAR
# ==============================================================================
fig.text(0.04, 0.950, "AEGISFLOW", fontsize=16.5, fontweight='bold', color='#2DD4BF')
fig.text(0.128, 0.950, "/", fontsize=17, color='#444444')
fig.text(0.142, 0.950, "PROBLEM FRAMING: OBJECTIVE, TRADE-OFFS & AVOIDED RISKS", fontsize=15.5, fontweight='bold', color='#FFFFFF')
fig.text(0.96, 0.950, "The Fundamental Liquidity Dilemma in High-Velocity Autonomous Banking", fontsize=11, color='#888888', ha='right')

# Header underline
fig.add_artist(plt.Line2D([0.04, 0.96], [0.932, 0.932], color='#222222', linewidth=1.0))


# ==============================================================================
# 2. TOP KPI ROW: 5 PROBLEM CONTEXT METRICS
# ==============================================================================
ax_kpi = fig.add_axes([0.04, 0.810, 0.92, 0.105], facecolor='#080808')
ax_kpi.set_xticks([])
ax_kpi.set_yticks([])
for spine in ax_kpi.spines.values():
    spine.set_color('#1C1C1C')
    spine.set_linewidth(1.0)

kpi_data = [
    {"label": "STRUCTURAL DRAIN RATE", "val": r"-\$288.9k / hr", "sub": r"-\$2.53B Net Outflow Across 8,760h", "color": "#EF4444"},
    {"label": "INTRADAY FLOW VELOCITY", "val": r">\$20M / hr", "sub": "High-Frequency Clearing Volumes", "color": "#38BDF8"},
    {"label": "REPO BREAK ASYMMETRY", "val": "71.2x Cost", "sub": "0.50% Penalty vs 0.007% Overnight Yield", "color": "#F59E0B"},
    {"label": "EQUITY LIQUIDATION HAIRCUT", "val": "15.0% Exit Fee", "sub": "Requires 2.48 Years to Break Even", "color": "#EC4899"},
    {"label": "AUTOCORRELATED DRAIN", "val": r"0.695 ACF(1)", "sub": "Intraday Runs Cascade Overnight", "color": "#A78BFA"}
]

n_kpis = len(kpi_data)
for i, d in enumerate(kpi_data):
    cx = (i + 0.5) / n_kpis
    ax_kpi.text(cx, 0.76, d["label"], ha='center', va='center', fontsize=8.2, fontweight='bold', color='#777777', transform=ax_kpi.transAxes)
    ax_kpi.text(cx, 0.44, d["val"], ha='center', va='center', fontsize=18, fontweight='bold', color=d["color"], transform=ax_kpi.transAxes)
    ax_kpi.text(cx, 0.15, d["sub"], ha='center', va='center', fontsize=8.0, color='#AAAAAA', transform=ax_kpi.transAxes)
    if i < n_kpis - 1:
        sep_x = (i + 1) / n_kpis
        ax_kpi.plot([sep_x, sep_x], [0.12, 0.88], color='#1C1C1C', linewidth=1.0, transform=ax_kpi.transAxes)


# ==============================================================================
# 3. MIDDLE SECTION: DUAL DIAGRAMMATIC PANELS
# Left: The Friction Spectrum & Trade-Off Matrix (x: 0.04 to 0.49)
# Right: The 4 Catastrophic Failure Modes (x: 0.51 to 0.96)
# ==============================================================================

# ------------------------------------------------------------------------------
# MIDDLE-LEFT PANEL: ASSET TIER FRICTION SPECTRUM & TRADE-OFFS
# ------------------------------------------------------------------------------
ax_tiers = fig.add_axes([0.040, 0.380, 0.465, 0.405], facecolor='#080808')
ax_tiers.set_xticks([])
ax_tiers.set_yticks([])
for spine in ax_tiers.spines.values():
    spine.set_color('#1C1C1C')
    spine.set_linewidth(1.0)

ax_tiers.text(0.04, 0.940, "THE ASSET TIER FRICTION SPECTRUM & TRADE-OFF TRILEMMA", fontsize=10.5, fontweight='bold', color='#38BDF8', transform=ax_tiers.transAxes)
ax_tiers.text(0.04, 0.885, "The Fundamental Conflict: Yield demands lockup and imposes severe exit liquidation penalties", fontsize=8.0, color='#777777', transform=ax_tiers.transAxes)

# Table Header for Tiers
tier_y = 0.81
ax_tiers.plot([0.04, 0.96], [tier_y, tier_y], color='#222222', linewidth=1.0, transform=ax_tiers.transAxes)
ax_tiers.text(0.04, tier_y - 0.045, "FACILITY / TIER", fontsize=8.0, fontweight='bold', color='#777777', transform=ax_tiers.transAxes)
ax_tiers.text(0.30, tier_y - 0.045, "YIELD", fontsize=8.0, fontweight='bold', color='#777777', transform=ax_tiers.transAxes)
ax_tiers.text(0.42, tier_y - 0.045, "LOCKUP", fontsize=8.0, fontweight='bold', color='#777777', transform=ax_tiers.transAxes)
ax_tiers.text(0.59, tier_y - 0.045, "EXIT HAIRCUT", fontsize=8.0, fontweight='bold', color='#777777', transform=ax_tiers.transAxes)
ax_tiers.text(0.78, tier_y - 0.045, "BREAK-EVEN (t)", fontsize=8.0, fontweight='bold', color='#777777', transform=ax_tiers.transAxes)

tier_rows = [
    {
        "name": "Tier 0 · Operational Cash",
        "yield": "0.00%",
        "lock": "Instant",
        "haircut": "0.0%",
        "be": "0 Hours",
        "dilemma": "Zero liquidation risk, but idle hoarding forfeits ~$2.1M/year in risk-free yield.",
        "bar_w": 0.01,
        "color": "#10B981"
    },
    {
        "name": "Tier 1 · Overnight Repo",
        "yield": "4.10%",
        "lock": "15h (Overnight)",
        "haircut": "0.50% Early",
        "be": "107 Hours",
        "dilemma": "0.50% early-exit fee is 71.2x higher than overnight interest earned (0.00702%).",
        "bar_w": 0.035,
        "color": "#2DD4BF"
    },
    {
        "name": "Tier 2 · 2Y Sovereign Bonds",
        "yield": "4.75%",
        "lock": "T+1 Liquid",
        "haircut": "2.00% Exit",
        "be": "7,900h (~11 mo)",
        "dilemma": "Requires 10.8 months holding time to amortize 2% secondary liquidation loss.",
        "bar_w": 0.075,
        "color": "#F59E0B"
    },
    {
        "name": "Tier 3 · Blue-Chip Equities",
        "yield": "10.0%",
        "lock": "Market Open",
        "haircut": "15.0% Exit",
        "be": "2.48 Years",
        "dilemma": "Chasing 10% headline yield in a draining book guarantees 15% fire-sale wipeout.",
        "bar_w": 0.140,
        "color": "#EF4444"
    }
]

t_start_y = 0.69
t_row_h = 0.160
for i, tr in enumerate(tier_rows):
    ry = t_start_y - i * t_row_h
    ax_tiers.plot([0.04, 0.96], [ry + 0.055, ry + 0.055], color='#141414', linewidth=0.8, transform=ax_tiers.transAxes)
    ax_tiers.text(0.04, ry + 0.015, tr["name"], fontsize=8.6, fontweight='bold', color=tr["color"], transform=ax_tiers.transAxes)
    ax_tiers.text(0.30, ry + 0.015, tr["yield"], fontsize=8.4, color='#FFFFFF', transform=ax_tiers.transAxes)
    ax_tiers.text(0.42, ry + 0.015, tr["lock"], fontsize=8.0, color='#CCCCCC', transform=ax_tiers.transAxes)
    ax_tiers.text(0.59, ry + 0.015, tr["haircut"], fontsize=8.4, fontweight='bold', color='#FCA5A5' if '15' in tr['haircut'] or '0.5' in tr['haircut'] else '#FDE68A', transform=ax_tiers.transAxes)
    ax_tiers.text(0.78, ry + 0.015, tr["be"], fontsize=8.4, color='#E2E8F0', transform=ax_tiers.transAxes)
    ax_tiers.text(0.04, ry - 0.042, tr["dilemma"], fontsize=7.7, color='#8E8E8E', transform=ax_tiers.transAxes)

# Bottom Formula Badge in Left Container
ax_tiers.plot([0.04, 0.96], [0.08, 0.08], color='#1A1A1A', linewidth=0.8, transform=ax_tiers.transAxes)
formula_text = r"$\mathrm{Break\text{-}Even\ Horizon:}\quad \tau_i = \frac{h_i - h_{i-1}}{y_i - y_{i-1}} \Rightarrow \mathrm{Illiquid\ tiers\ demand\ multi\text{-}month\ survival}$"
ax_tiers.text(0.50, 0.038, formula_text, ha='center', va='center', fontsize=8.2, color='#38BDF8', transform=ax_tiers.transAxes)


# ------------------------------------------------------------------------------
# MIDDLE-RIGHT PANEL: THE 4 CATASTROPHIC FAILURE MODES (PROBLEMS AVOIDED)
# ------------------------------------------------------------------------------
ax_traps = fig.add_axes([0.525, 0.380, 0.435, 0.405], facecolor='#080808')
ax_traps.set_xticks([])
ax_traps.set_yticks([])
for spine in ax_traps.spines.values():
    spine.set_color('#1C1C1C')
    spine.set_linewidth(1.0)

ax_traps.text(0.04, 0.940, "THE 4 CATASTROPHIC FAILURE MODES (PROBLEMS TO AVOID)", fontsize=10.5, fontweight='bold', color='#EF4444', transform=ax_traps.transAxes)
ax_traps.text(0.04, 0.885, "Systemic failure modes observed in naive treasury models during financial market stress", fontsize=8.0, color='#777777', transform=ax_traps.transAxes)

traps = [
    {
        "code": "TRAP 01",
        "title": "THE IDLE CASH DRAG (Over-Hedging)",
        "mech": "Hoarding $40M–$50M in zero-yield operational accounts to eliminate overdraft risk.",
        "conseq": "Wastes ~$2.1M/year in risk-free yield, depressing institutional bank return on equity.",
        "tag": "OPPORTUNITY LOSS",
        "color": "#F59E0B"
    },
    {
        "code": "TRAP 02",
        "title": "THE REPO BREAK PENALTY (Premature Crack)",
        "mech": "Sweeping too aggressively into 15h repo, then cracking lockup during late-night payment runs.",
        "conseq": "A 0.50% penalty destroys 71.2 days of interest in a single tick; wipes out overnight yield.",
        "tag": "71.2x PENALTY",
        "color": "#EF4444"
    },
    {
        "code": "TRAP 03",
        "title": "THE EQUITY HORIZON TRAP (Greedy Chasing)",
        "mech": "Allocating 20% to equities chasing ~10% APY inside an institution draining -$289k/hr.",
        "conseq": "Forces 15% fire-sale liquidations during downturns; leads to -$1.36B catastrophic collapse.",
        "tag": "FIRE-SALE DISASTER",
        "color": "#EC4899"
    },
    {
        "code": "TRAP 04",
        "title": "THE I.I.D. RUN CASCADE (Gaussian Fallacy)",
        "mech": "Assuming hourly flows are independent Gaussian noise; ignoring 0.695 flow autocorrelation.",
        "conseq": "17:00 corporate payment runs continue draining at 20:00 & 01:00, causing SVB-style defaults.",
        "tag": "RUN CONTAGION",
        "color": "#A78BFA"
    }
]

trap_spacing = 0.190
trap_start_y = 0.725
for idx, tr in enumerate(traps):
    ty = trap_start_y - idx * trap_spacing
    ax_traps.text(0.04, ty + 0.075, f"{tr['code']} · {tr['title']}", fontsize=8.6, fontweight='bold', color=tr['color'], transform=ax_traps.transAxes)
    ax_traps.text(0.96, ty + 0.075, f"[{tr['tag']}]", ha='right', fontsize=7.4, fontweight='bold', color='#777777', transform=ax_traps.transAxes)
    ax_traps.text(0.04, ty + 0.025, f"Root Cause: {tr['mech']}", fontsize=7.8, color='#D4D4D4', transform=ax_traps.transAxes)
    ax_traps.text(0.04, ty - 0.025, f"Consequence Avoided: {tr['conseq']}", fontsize=7.8, color='#FCA5A5', transform=ax_traps.transAxes)
    if idx < len(traps) - 1:
        ax_traps.plot([0.04, 0.96], [ty - 0.055, ty - 0.055], color='#141414', linewidth=0.8, transform=ax_traps.transAxes)


# ==============================================================================
# 4. BOTTOM SECTION: THE AEGISFLOW SOLUTION OBJECTIVE
# Spanning across x in [0.04, 0.96], y in [0.045, 0.355]
# ==============================================================================
ax_sol = fig.add_axes([0.04, 0.045, 0.92, 0.305], facecolor='#080808')
ax_sol.set_xticks([])
ax_sol.set_yticks([])
for spine in ax_sol.spines.values():
    spine.set_color('#1C1C1C')
    spine.set_linewidth(1.0)

ax_sol.text(0.03, 0.920, "THE AEGISFLOW SYSTEM OBJECTIVE: CAPITAL AS EXPIRING INVENTORY", fontsize=10.5, fontweight='bold', color='#10B981', transform=ax_sol.transAxes)
ax_sol.text(0.03, 0.850, "Transforming treasury management from naive static asset allocation into an autonomous inventory need-time engine", fontsize=8.0, color='#777777', transform=ax_sol.transAxes)

sol_pillars = [
    {
        "num": "PILLAR 01",
        "title": "CAPITAL AS INVENTORY (NOT A PIE)",
        "headline": "Continuous Friction Minimization",
        "formula": r"$\min \sum_{t=1}^T \left[ \mathrm{Haircuts}(t) + \mathrm{Overdraft}(t) - \mathrm{Yield}(t) \right]$",
        "desc": "Deposits are not an idle pool to divide into fixed percentages (20/30/30/20). In a book draining -$289k/hr, capital is inventory with an expiration countdown.",
        "color": "#10B981"
    },
    {
        "num": "PILLAR 02",
        "title": "THE NEED-TIME LADDER (tau)",
        "headline": "Break-Even Horizon Sizing Rule",
        "formula": r"$\mathrm{Fund\ Tier\ } i \Leftrightarrow \tau_{\mathrm{projected}} > \tau_i^* = \frac{h_i - h_{i-1}}{y_i - y_{i-1}}$",
        "desc": "Only capital with a projected survival time exceeding 10.8 months is allocated to 2Y bonds. Eliminates secondary liquidation haircuts during structural cash drawdown.",
        "color": "#38BDF8"
    },
    {
        "num": "PILLAR 03",
        "title": "THE DUAL MATHEMATICAL THEOREMS",
        "headline": "Theorem 1 Arbitrage & Theorem 2 Blacklist",
        "formula": r"$c_{OD} \approx 0.0205\% \ll 0.50\% \Rightarrow 24.4\times\ \mathrm{cheaper} \quad | \quad \mathrm{Equity} = 0\%$",
        "desc": "Theorem 1 uses overnight central-bank overdraft to cure 15h deficits at 1/24th the cost of breaking repo. Theorem 2 blacklists equities, avoiding a -36.6% market crash.",
        "color": "#F59E0B"
    }
]

for c_idx, col in enumerate(sol_pillars):
    col_x = 0.03 + c_idx * 0.325
    ax_sol.text(col_x, 0.73, f"{col['num']} · {col['title']}", fontsize=8.6, fontweight='bold', color=col['color'], transform=ax_sol.transAxes)
    ax_sol.text(col_x, 0.62, col['formula'], fontsize=8.8, color='#FFFFFF', transform=ax_sol.transAxes)
    
    desc_wrapped = textwrap.fill(col['desc'], width=52)
    ax_sol.text(col_x, 0.49, desc_wrapped, fontsize=7.9, color='#A3A3A3', va='top', transform=ax_sol.transAxes, linespacing=1.25)
    
    if c_idx < len(sol_pillars) - 1:
        sep_x = col_x + 0.310
        ax_sol.plot([sep_x, sep_x], [0.47, 0.75], color='#1C1C1C', linewidth=1.0, transform=ax_sol.transAxes)
        ax_sol.plot([sep_x, sep_x], [0.10, 0.37], color='#1C1C1C', linewidth=1.0, transform=ax_sol.transAxes)
        # Directional arrow indicator showing pipeline flow
        ax_sol.text(sep_x, 0.42, "▶", ha='center', va='center', fontsize=9.0, color='#2DD4BF', transform=ax_sol.transAxes)


# Save high-resolution slide
plt.savefig('assets/aegisflow_problem_framing_slide.png', dpi=100, facecolor='#000000')
plt.close()

img = Image.open('assets/aegisflow_problem_framing_slide.png')
img.convert('RGB').save('assets/aegisflow_problem_framing_slide.jpg', quality=96)

# Copy to brain artifact directory
img.convert('RGB').save('/home/idioticspaceman/.gemini/antigravity-cli/brain/98d405f9-01a1-449c-91dc-21e4f690d2c7/aegisflow_problem_framing_slide.jpg', quality=96)
print("Successfully regenerated assets/aegisflow_problem_framing_slide.jpg with enhanced typography and directional flow!")
