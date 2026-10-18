import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from PIL import Image
import shutil

# Setup typography and base canvas
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor='#000000')

# ==============================================================================
# 1. TOP HEADER BAR
# ==============================================================================
fig.text(0.04, 0.948, "AEGISFLOW", fontsize=16.5, fontweight='bold', color='#2DD4BF')
fig.text(0.128, 0.948, "/", fontsize=17, color='#444444')
fig.text(0.142, 0.948, "LIMITATIONS, KNOWN VULNERABILITIES & ENGINEERING ROADMAP", fontsize=15.5, fontweight='bold', color='#FFFFFF')
fig.text(0.96, 0.948, "Empirical Flaw Auditing & Enterprise Production Architecture", fontsize=11.5, color='#888888', ha='right')

# Header underline
fig.add_artist(plt.Line2D([0.04, 0.96], [0.930, 0.930], color='#222222', linewidth=1.0))

# ==============================================================================
# MAIN COLUMN BACKGROUND CONTAINERS
# ==============================================================================
# Left Column: x in [0.04, 0.485]
ax_bg_left = fig.add_axes([0.04, 0.040, 0.445, 0.870], facecolor='#080808')
ax_bg_left.set_xticks([])
ax_bg_left.set_yticks([])
for spine in ax_bg_left.spines.values():
    spine.set_color('#1C1C1C')
    spine.set_linewidth(1.0)

ax_bg_left.text(0.04, 0.968, "01 / KNOWN PROTOTYPE WEAKNESSES & RISKS", fontsize=12, fontweight='bold', color='#F59E0B', transform=ax_bg_left.transAxes)
ax_bg_left.text(0.04, 0.940, "Empirical flaws identified during 8,760-hour backtesting & mathematical fail-safes", fontsize=9.2, color='#888888', transform=ax_bg_left.transAxes)

# Right Column: x in [0.515, 0.96]
ax_bg_right = fig.add_axes([0.515, 0.040, 0.445, 0.870], facecolor='#080808')
ax_bg_right.set_xticks([])
ax_bg_right.set_yticks([])
for spine in ax_bg_right.spines.values():
    spine.set_color('#1C1C1C')
    spine.set_linewidth(1.0)

ax_bg_right.text(0.04, 0.968, "02 / NEXT STEPS & PRODUCTION-READY ROADMAP", fontsize=12, fontweight='bold', color='#2DD4BF', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.04, 0.940, "Tactical 1-week extensions and enterprise banking production architecture", fontsize=9.2, color='#888888', transform=ax_bg_right.transAxes)


# ==============================================================================
# LEFT PANEL - 3 HIGHLY DIAGRAMMATIC LIMITATION CARDS (INCREASED BODY TEXT)
# ==============================================================================

# ------------------------------------------------------------------------------
# CARD 1: THE JANUARY PAYDAY TRAP (EWMA DRAIN DISTORTION)
# ------------------------------------------------------------------------------
rect1 = FancyBboxPatch((0.02, 0.640), 0.96, 0.285, boxstyle="round,pad=0.01,rounding_size=0.012",
                       facecolor='#0D0D0D', edgecolor='#222222', linewidth=1.0, transform=ax_bg_left.transAxes)
ax_bg_left.add_patch(rect1)

ax_bg_left.text(0.04, 0.902, "LIMITATION 1 · THE 'JANUARY PAYDAY TRAP' (DRAIN BIAS)", fontsize=10.2, fontweight='bold', color='#EF4444', transform=ax_bg_left.transAxes)
ax_bg_left.text(0.04, 0.864, r"Month 1 payroll inflows artificially flatter rolling EWMA drain rate (-\$94k/hr vs -\$289k/hr true annual)," + "\n" + r"risking premature over-allocation into 2Y bonds before true baseline stabilizes.", fontsize=9.0, color='#B0B0B0', transform=ax_bg_left.transAxes, linespacing=1.28)

# Embedded mini-plot
ax_chart1 = fig.add_axes([0.065, 0.608, 0.395, 0.125], facecolor='#040404')
ax_chart1.tick_params(colors='#777777', labelsize=7.8)
for spine in ax_chart1.spines.values():
    spine.set_color('#262626')

days = np.linspace(0, 60, 120)
true_drain = np.full_like(days, -289)
naive_ewma = -289 + 195 * np.exp(-((days - 15) ** 2) / 75) - 15 * np.sin(days / 6)
enforced_floor = np.full_like(days, -250)

ax_chart1.plot(days, true_drain, color='#F59E0B', linestyle='--', linewidth=1.5, label=r'True Annual Drain (-\$289k/hr)')
ax_chart1.plot(days, naive_ewma, color='#EF4444', linewidth=1.7, label=r'Distorted Naive EWMA (-\$94k/hr)')
ax_chart1.plot(days, enforced_floor, color='#2DD4BF', linestyle=':', linewidth=1.5, label=r'AegisFlow Safety Floor (-\$250k/hr)')

ax_chart1.axvline(35, color='#38BDF8', linestyle='-', linewidth=1.7)
ax_chart1.text(36.5, -115, "35-Day Institutional\nBurn-In Barrier", fontsize=7.8, color='#38BDF8', fontweight='bold')
ax_chart1.set_xlim(0, 60)
ax_chart1.set_ylim(-330, -50)
ax_chart1.set_ylabel(r"Drain Rate (\$k/hr)", fontsize=7.8, color='#999999')
ax_chart1.set_xlabel("Replay Elapsed Days", fontsize=7.8, color='#999999')
ax_chart1.legend(loc='lower left', fontsize=7.5, facecolor='#111111', edgecolor='#333333', labelcolor='#DDDDDD', framealpha=0.92)


# ------------------------------------------------------------------------------
# CARD 2: OVERDRAFT ARBITRAGE VS REGULATORY STIGMA
# ------------------------------------------------------------------------------
rect2 = FancyBboxPatch((0.02, 0.328), 0.96, 0.295, boxstyle="round,pad=0.01,rounding_size=0.012",
                       facecolor='#0D0D0D', edgecolor='#222222', linewidth=1.0, transform=ax_bg_left.transAxes)
ax_bg_left.add_patch(rect2)

ax_bg_left.text(0.04, 0.598, "LIMITATION 2 · OVERDRAFT ARBITRAGE VS SUPERVISORY STIGMA", fontsize=10.2, fontweight='bold', color='#EF4444', transform=ax_bg_left.transAxes)
ax_bg_left.text(0.04, 0.560, r"Theorem 1 proves central bank overdraft is 24.4x cheaper than breaking repo (\$151k vs \$3.70M)," + "\n" + r"but real-world discount window borrowing triggers severe regulatory & rating scrutiny.", fontsize=9.0, color='#B0B0B0', transform=ax_bg_left.transAxes, linespacing=1.28)

# Mini bar chart: Cost comparison on left
ax_chart2 = fig.add_axes([0.065, 0.338, 0.165, 0.130], facecolor='#040404')
ax_chart2.tick_params(colors='#777777', labelsize=7.8)
for spine in ax_chart2.spines.values():
    spine.set_color('#262626')

bars = ax_chart2.bar(['Overdraft\n(Theorem 1)', 'Repo Break\n(100 bps)'], [0.151, 3.700], color=['#10B981', '#EF4444'], width=0.52)
ax_chart2.set_ylabel(r"Penalty Cost (\$M)", fontsize=7.8, color='#999999')
ax_chart2.set_ylim(0, 4.3)
ax_chart2.text(0, 0.35, r"\$151k", ha='center', fontsize=8.2, fontweight='bold', color='#FFFFFF')
ax_chart2.text(1, 3.88, r"\$3.70M", ha='center', fontsize=8.2, fontweight='bold', color='#FFFFFF')
ax_chart2.set_title("24.4x Cost Arbitrage", fontsize=8.2, color='#10B981', fontweight='bold')

# Diagrammatic schematic on right: Stigma & Guarded Mode Circuit Breaker
ax_diag2 = fig.add_axes([0.250, 0.338, 0.210, 0.130], facecolor='#060606')
ax_diag2.set_xticks([])
ax_diag2.set_yticks([])
for spine in ax_diag2.spines.values():
    spine.set_color('#222222')

# Block 1: Discount Window
ax_diag2.add_patch(FancyBboxPatch((0.05, 0.58), 0.90, 0.35, boxstyle="round,pad=0.02", facecolor='#1E1111', edgecolor='#EF4444', linewidth=1.0))
ax_diag2.text(0.50, 0.77, "Discount Window Borrowing", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#FCA5A5')
ax_diag2.text(0.50, 0.65, "Supervisory Stigma & Rating Audit", ha='center', va='center', fontsize=7.2, color='#F87171')

# Down arrow
ax_diag2.text(0.50, 0.48, "▼", ha='center', va='center', fontsize=9, color='#888888')

# Block 2: Circuit Breaker
ax_diag2.add_patch(FancyBboxPatch((0.05, 0.08), 0.90, 0.35, boxstyle="round,pad=0.02", facecolor='#0C1C17', edgecolor='#10B981', linewidth=1.0))
ax_diag2.text(0.50, 0.27, r"Guarded Mode: \$25M Hard Cap", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#6EE7B7')
ax_diag2.text(0.50, 0.15, "Remaining Gap: Needs Private Lines", ha='center', va='center', fontsize=7.2, color='#34D399')


# ------------------------------------------------------------------------------
# CARD 3: 1-YEAR HORIZON & EXECUTION SLIPPAGE ASSUMPTION
# ------------------------------------------------------------------------------
rect3 = FancyBboxPatch((0.02, 0.016), 0.96, 0.295, boxstyle="round,pad=0.01,rounding_size=0.012",
                       facecolor='#0D0D0D', edgecolor='#222222', linewidth=1.0, transform=ax_bg_left.transAxes)
ax_bg_left.add_patch(rect3)

ax_bg_left.text(0.04, 0.288, "LIMITATION 3 · 1-YEAR HORIZON & ZERO-SLIPPAGE ASSUMPTION", fontsize=10.2, fontweight='bold', color='#EF4444', transform=ax_bg_left.transAxes)
ax_bg_left.text(0.04, 0.250, r"Backtest covers 8,760h (1 year), omitting 10-year macro credit cycles (ZIRP, inverted yields)." + "\n" + r"Large sweeps (\$10M - \$40M) assume instant fill at 0 bps slippage without market impact.", fontsize=9.0, color='#B0B0B0', transform=ax_bg_left.transAxes, linespacing=1.28)

# Mini-plot for Limitation 3: Slippage curve
ax_chart3 = fig.add_axes([0.065, 0.065, 0.395, 0.125], facecolor='#040404')
ax_chart3.tick_params(colors='#777777', labelsize=7.8)
for spine in ax_chart3.spines.values():
    spine.set_color('#262626')

order_size = np.linspace(0, 50, 100)
current_slippage = np.zeros_like(order_size)
real_slippage = 4.8 * np.sqrt(order_size)

ax_chart3.plot(order_size, current_slippage, color='#38BDF8', linestyle='--', linewidth=1.5, label='Prototype Assumption (0 bps slippage)')
ax_chart3.plot(order_size, real_slippage, color='#F59E0B', linewidth=1.7, label="Real Market Impact (Kyle's Lambda)")
ax_chart3.fill_between(order_size, current_slippage, real_slippage, color='#F59E0B', alpha=0.12)

ax_chart3.axvline(20, color='#EF4444', linestyle=':', linewidth=1.5)
ax_chart3.text(21.5, 27, r"Critical \$20M+ Threshold" + "\n(Requires TWAP Slicing)", fontsize=7.8, color='#EF4444', fontweight='bold')
ax_chart3.set_xlim(0, 50)
ax_chart3.set_ylim(-3, 42)
ax_chart3.set_ylabel("Slippage (bps)", fontsize=7.8, color='#999999')
ax_chart3.set_xlabel(r"Order Sweep Size (\$M)", fontsize=7.8, color='#999999')
ax_chart3.legend(loc='upper left', fontsize=7.5, facecolor='#111111', edgecolor='#333333', labelcolor='#DDDDDD', framealpha=0.92)


# ==============================================================================
# RIGHT PANEL - DIAGRAMMATIC ROADMAP & ENTERPRISE ARCHITECTURE (BIGGER TEXT)
# ==============================================================================

# ------------------------------------------------------------------------------
# SECTION 1: PHASE 1 · "WHAT WE WOULD BUILD WITH 1 WEEK MORE"
# ------------------------------------------------------------------------------
rect_r1 = FancyBboxPatch((0.02, 0.490), 0.96, 0.440, boxstyle="round,pad=0.01,rounding_size=0.012",
                         facecolor='#0D0D0D', edgecolor='#222222', linewidth=1.0, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(rect_r1)

ax_bg_right.text(0.04, 0.902, "PHASE 1 · WHAT WE WOULD BUILD WITH 1 WEEK MORE", fontsize=10.8, fontweight='bold', color='#38BDF8', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.04, 0.872, "Tactical engineering extensions addressing our 3 identified weaknesses", fontsize=9.0, color='#888888', transform=ax_bg_right.transAxes)

# 3 Stage Pipeline Cards
node_w = 0.282
node_h = 0.335
node_y = 0.518

# Stage 1: Bilateral Credit Lines
n1 = FancyBboxPatch((0.04, node_y), node_w, node_h, boxstyle="round,pad=0.012", facecolor='#111111', edgecolor='#2DD4BF', linewidth=1.2, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(n1)
ax_bg_right.text(0.055, node_y + 0.292, "STAGE 1 · ROUTING", fontsize=7.8, color='#2DD4BF', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.055, node_y + 0.248, "Bilateral Credit Lines", fontsize=9.8, color='#FFFFFF', fontweight='bold', transform=ax_bg_right.transAxes)

# Mini schematic inside Stage 1 card
sch1 = FancyBboxPatch((0.055, node_y + 0.070), node_w - 0.03, 0.165, boxstyle="round,pad=0.008", facecolor='#060606', edgecolor='#222222', linewidth=0.8, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(sch1)
ax_bg_right.text(0.065, node_y + 0.202, "[ Liquidity Deficit Signal ]", fontsize=7.5, color='#A1A1AA', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.065, node_y + 0.155, "  │   Smart Multi-Party Router", fontsize=7.2, color='#2DD4BF', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.065, node_y + 0.110, "  ├──> Interbank Bilateral Repo", fontsize=7.2, color='#F3F4F6', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.065, node_y + 0.082, "  └──> Private Commercial Lines", fontsize=7.2, color='#F3F4F6', transform=ax_bg_right.transAxes)

# Bottom resolution tag
ax_bg_right.text(0.055, node_y + 0.026, "Solves: Limitation 2 (Overdraft Stigma)", fontsize=7.5, color='#2DD4BF', fontweight='bold', transform=ax_bg_right.transAxes)

# Arrow 1 -> 2
ax_bg_right.text(0.337, node_y + 0.165, "➔", fontsize=16, color='#38BDF8', ha='center', va='center', transform=ax_bg_right.transAxes)

# Stage 2: TWAP/VWAP Slicing
n2 = FancyBboxPatch((0.36, node_y), node_w, node_h, boxstyle="round,pad=0.012", facecolor='#111111', edgecolor='#38BDF8', linewidth=1.2, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(n2)
ax_bg_right.text(0.375, node_y + 0.292, "STAGE 2 · EXECUTION", fontsize=7.8, color='#38BDF8', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.375, node_y + 0.248, "TWAP / VWAP Slicing", fontsize=9.8, color='#FFFFFF', fontweight='bold', transform=ax_bg_right.transAxes)

# Mini schematic inside Stage 2 card
sch2 = FancyBboxPatch((0.375, node_y + 0.070), node_w - 0.03, 0.165, boxstyle="round,pad=0.008", facecolor='#060606', edgecolor='#222222', linewidth=0.8, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(sch2)
ax_bg_right.text(0.385, node_y + 0.202, "[ $20M+ Large Bond Sweep ]", fontsize=7.5, color='#A1A1AA', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.385, node_y + 0.155, "  │   Almgren-Chriss Slicer", fontsize=7.2, color='#38BDF8', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.385, node_y + 0.110, "  ├──> Micro-chunk 1: $2.5M (08:00)", fontsize=7.2, color='#F3F4F6', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.385, node_y + 0.082, "  └──> Micro-chunk N: $2.5M (08:15)", fontsize=7.2, color='#F3F4F6', transform=ax_bg_right.transAxes)

ax_bg_right.text(0.375, node_y + 0.026, "Solves: Limitation 3 (Market Slippage)", fontsize=7.5, color='#38BDF8', fontweight='bold', transform=ax_bg_right.transAxes)

# Arrow 2 -> 3
ax_bg_right.text(0.657, node_y + 0.165, "➔", fontsize=16, color='#F59E0B', ha='center', va='center', transform=ax_bg_right.transAxes)

# Stage 3: Multi-Year Chaos Engine
n3 = FancyBboxPatch((0.68, node_y), node_w, node_h, boxstyle="round,pad=0.012", facecolor='#111111', edgecolor='#F59E0B', linewidth=1.2, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(n3)
ax_bg_right.text(0.695, node_y + 0.292, "STAGE 3 · STRESS TEST", fontsize=7.8, color='#F59E0B', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.695, node_y + 0.248, "Multi-Year Chaos Engine", fontsize=9.8, color='#FFFFFF', fontweight='bold', transform=ax_bg_right.transAxes)

# Mini schematic inside Stage 3 card
sch3 = FancyBboxPatch((0.695, node_y + 0.070), node_w - 0.03, 0.165, boxstyle="round,pad=0.008", facecolor='#060606', edgecolor='#222222', linewidth=0.8, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(sch3)
ax_bg_right.text(0.705, node_y + 0.202, "[ 10-Year Markov Regimes ]", fontsize=7.5, color='#A1A1AA', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.705, node_y + 0.155, "  ├──> 2008 Lehman GFC (Freeze)", fontsize=7.2, color='#FDE047', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.705, node_y + 0.118, "  ├──> 2020 COVID (Liquidity Shock)", fontsize=7.2, color='#FDE047', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.705, node_y + 0.082, "  └──> 2023 SVB Run (Digital Flight)", fontsize=7.2, color='#FDE047', transform=ax_bg_right.transAxes)

ax_bg_right.text(0.695, node_y + 0.026, "Solves: Limitation 1 & 3 (Regimes)", fontsize=7.5, color='#F59E0B', fontweight='bold', transform=ax_bg_right.transAxes)


# ------------------------------------------------------------------------------
# SECTION 2: PHASE 2 · "REQUIREMENTS FOR ENTERPRISE PRODUCTION-READINESS"
# ------------------------------------------------------------------------------
rect_r2 = FancyBboxPatch((0.02, 0.016), 0.96, 0.448, boxstyle="round,pad=0.01,rounding_size=0.012",
                         facecolor='#0D0D0D', edgecolor='#222222', linewidth=1.0, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(rect_r2)

ax_bg_right.text(0.04, 0.438, "PHASE 2 · REQUIREMENTS FOR ENTERPRISE PRODUCTION-READINESS", fontsize=10.8, fontweight='bold', color='#10B981', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.04, 0.408, "Full-stack institutional banking infrastructure required for Tier-1 deployment", fontsize=9.0, color='#888888', transform=ax_bg_right.transAxes)

# 3 Stacked Architectural Tiers with Component Sub-Blocks
tier_w = 0.92
tier_h = 0.100

# TIER 3: REGULATORY COMPLIANCE SUITE
t3 = FancyBboxPatch((0.04, 0.285), tier_w, tier_h, boxstyle="round,pad=0.01", facecolor='#0D1814', edgecolor='#10B981', linewidth=1.0, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(t3)
ax_bg_right.text(0.055, 0.355, "TIER 3 · REGULATORY COMPLIANCE SUITE", fontsize=8.2, color='#10B981', fontweight='bold', transform=ax_bg_right.transAxes)

# 3 Component Blocks inside Tier 3
b_w = 0.280
b_h = 0.054
b_y = 0.294

# Block 3A
ax_bg_right.add_patch(FancyBboxPatch((0.055, b_y), b_w, b_h, boxstyle="round,pad=0.006", facecolor='#14231E', edgecolor='#10B981', linewidth=0.6, transform=ax_bg_right.transAxes))
ax_bg_right.text(0.065, b_y + 0.033, "Real-Time LCR Calculator", fontsize=7.8, color='#6EE7B7', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.065, b_y + 0.012, "Enforces LCR > 100% every hour", fontsize=7.0, color='#D1FAE5', transform=ax_bg_right.transAxes)

# Block 3B
ax_bg_right.add_patch(FancyBboxPatch((0.360, b_y), b_w, b_h, boxstyle="round,pad=0.006", facecolor='#14231E', edgecolor='#10B981', linewidth=0.6, transform=ax_bg_right.transAxes))
ax_bg_right.text(0.370, b_y + 0.033, "NSFR Balance Monitor", fontsize=7.8, color='#6EE7B7', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.370, b_y + 0.012, "Matches 1Y+ funding & assets", fontsize=7.0, color='#D1FAE5', transform=ax_bg_right.transAxes)

# Block 3C
ax_bg_right.add_patch(FancyBboxPatch((0.665, b_y), b_w, b_h, boxstyle="round,pad=0.006", facecolor='#14231E', edgecolor='#10B981', linewidth=0.6, transform=ax_bg_right.transAxes))
ax_bg_right.text(0.675, b_y + 0.033, "Fed Regulatory Audit Stream", fontsize=7.8, color='#6EE7B7', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.675, b_y + 0.012, "WORM tamper-evident ledger logs", fontsize=7.0, color='#D1FAE5', transform=ax_bg_right.transAxes)

# Down Connector
ax_bg_right.text(0.50, 0.270, "▼   Real-Time Risk Thresholds & Compliance Guardrails   ▼", fontsize=7.5, color='#6B7280', ha='center', va='center', transform=ax_bg_right.transAxes)


# TIER 2: INSTITUTIONAL SECURITY & MULTI-SIG VAULT
t2 = FancyBboxPatch((0.04, 0.155), tier_w, tier_h, boxstyle="round,pad=0.01", facecolor='#161220', edgecolor='#A78BFA', linewidth=1.0, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(t2)
ax_bg_right.text(0.055, 0.225, "TIER 2 · INSTITUTIONAL SECURITY & MULTI-SIG VAULT", fontsize=8.2, color='#A78BFA', fontweight='bold', transform=ax_bg_right.transAxes)

b2_y = 0.164
# Block 2A
ax_bg_right.add_patch(FancyBboxPatch((0.055, b2_y), b_w, b_h, boxstyle="round,pad=0.006", facecolor='#201930', edgecolor='#A78BFA', linewidth=0.6, transform=ax_bg_right.transAxes))
ax_bg_right.text(0.065, b2_y + 0.033, "FIPS 140-3 Level 4 HSM", fontsize=7.8, color='#DDD6FE', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.065, b2_y + 0.012, "Hardware-isolated key enclaves", fontsize=7.0, color='#EDE9FE', transform=ax_bg_right.transAxes)

# Block 2B
ax_bg_right.add_patch(FancyBboxPatch((0.360, b2_y), b_w, b_h, boxstyle="round,pad=0.006", facecolor='#201930', edgecolor='#A78BFA', linewidth=0.6, transform=ax_bg_right.transAxes))
ax_bg_right.text(0.370, b2_y + 0.033, "MPC Key Sharding", fontsize=7.8, color='#DDD6FE', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.370, b2_y + 0.012, "Multi-party threshold quorum", fontsize=7.0, color='#EDE9FE', transform=ax_bg_right.transAxes)

# Block 2C
ax_bg_right.add_patch(FancyBboxPatch((0.665, b2_y), b_w, b_h, boxstyle="round,pad=0.006", facecolor='#201930', edgecolor='#A78BFA', linewidth=0.6, transform=ax_bg_right.transAxes))
ax_bg_right.text(0.675, b2_y + 0.033, "Dual-Officer Multi-Sig", fontsize=7.8, color='#DDD6FE', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.675, b2_y + 0.012, "Enforced for sweeps >$100M", fontsize=7.0, color='#EDE9FE', transform=ax_bg_right.transAxes)

# Down Connector
ax_bg_right.text(0.50, 0.140, "▼   Cryptographically Signed Sweep Instructions   ▼", fontsize=7.5, color='#6B7280', ha='center', va='center', transform=ax_bg_right.transAxes)


# TIER 1: CORE BANKING & CLEARING RAILS
t1 = FancyBboxPatch((0.04, 0.025), tier_w, tier_h, boxstyle="round,pad=0.01", facecolor='#0D1822', edgecolor='#38BDF8', linewidth=1.0, transform=ax_bg_right.transAxes)
ax_bg_right.add_patch(t1)
ax_bg_right.text(0.055, 0.095, "TIER 1 · CORE BANKING & HIGH-SPEED CLEARING RAILS", fontsize=8.2, color='#38BDF8', fontweight='bold', transform=ax_bg_right.transAxes)

b1_y = 0.034
# Block 1A
ax_bg_right.add_patch(FancyBboxPatch((0.055, b1_y), b_w, b_h, boxstyle="round,pad=0.006", facecolor='#132535', edgecolor='#38BDF8', linewidth=0.6, transform=ax_bg_right.transAxes))
ax_bg_right.text(0.065, b1_y + 0.033, "ISO 20022 Engine", fontsize=7.8, color='#BAE6FD', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.065, b1_y + 0.012, "pacs.008 & camt.053 XML parsers", fontsize=7.0, color='#E0F2FE', transform=ax_bg_right.transAxes)

# Block 1B
ax_bg_right.add_patch(FancyBboxPatch((0.360, b1_y), b_w, b_h, boxstyle="round,pad=0.006", facecolor='#132535', edgecolor='#38BDF8', linewidth=0.6, transform=ax_bg_right.transAxes))
ax_bg_right.text(0.370, b1_y + 0.033, "FedNow & CHIPS Bridge", fontsize=7.8, color='#BAE6FD', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.370, b1_y + 0.012, "Sub-second ledger state sync", fontsize=7.0, color='#E0F2FE', transform=ax_bg_right.transAxes)

# Block 1C
ax_bg_right.add_patch(FancyBboxPatch((0.665, b1_y), b_w, b_h, boxstyle="round,pad=0.006", facecolor='#132535', edgecolor='#38BDF8', linewidth=0.6, transform=ax_bg_right.transAxes))
ax_bg_right.text(0.675, b1_y + 0.033, "SWIFT gpi Tracker", fontsize=7.8, color='#BAE6FD', fontweight='bold', transform=ax_bg_right.transAxes)
ax_bg_right.text(0.675, b1_y + 0.012, "Cross-border liquidity telemetry", fontsize=7.0, color='#E0F2FE', transform=ax_bg_right.transAxes)


# Save high-resolution slide
plt.savefig('assets/aegisflow_limits_and_next_steps_slide.png', dpi=100, facecolor='#000000')
plt.close()

img = Image.open('assets/aegisflow_limits_and_next_steps_slide.png')
img.convert('RGB').save('assets/aegisflow_limits_and_next_steps_slide.jpg', quality=96)

# Copy to brain artifact directory
shutil.copy('assets/aegisflow_limits_and_next_steps_slide.jpg', '/home/idioticspaceman/.gemini/antigravity-cli/brain/98d405f9-01a1-449c-91dc-21e4f690d2c7/aegisflow_limits_and_next_steps_slide.jpg')

print("Successfully regenerated assets/aegisflow_limits_and_next_steps_slide.jpg with enhanced font sizes!")
