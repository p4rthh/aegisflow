import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# 1. Setup typography and canvas
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor='#000000')

# Outer layout: GridSpec
# Header: top 8%
# Body: 2 main columns (Left: Limitations & Vulnerabilities; Right: Next Steps & Roadmap)
gs = fig.add_gridspec(
    nrows=1, ncols=2,
    width_ratios=[1.0, 1.0],
    left=0.04, right=0.96,
    top=0.88, bottom=0.05,
    wspace=0.04
)

# 1. HEADER
fig.text(0.04, 0.942, "AEGISFLOW", fontsize=15, fontweight='bold', color='#2DD4BF')
fig.text(0.125, 0.942, "/", fontsize=16, color='#444444')
fig.text(0.14, 0.942, "SYSTEM LIMITS, KNOWN WEAKNESSES & NEXT STEPS", fontsize=15, fontweight='bold', color='#FFFFFF')
fig.text(0.96, 0.942, "Institutional Self-Awareness & Engineering Roadmap", fontsize=11.5, color='#888888', ha='right')

# Top subtle divider line
line = plt.Line2D([0.04, 0.96], [0.920, 0.920], transform=fig.transFigure, color='#222222', linewidth=1.0)
fig.add_artist(line)

# ==========================================
# LEFT PANEL: KNOWN WEAKNESSES & PROTOTYPE FLAWS
# ==========================================
ax_left = fig.add_subplot(gs[0, 0])
ax_left.set_facecolor('#090909')
ax_left.set_xticks([])
ax_left.set_yticks([])
for spine in ax_left.spines.values():
    spine.set_color('#222222')
    spine.set_linewidth(1.0)

ax_left.text(0.04, 0.95, "01 / KNOWN PROTOTYPE WEAKNESSES & RISKS", fontsize=11, fontweight='bold', color='#F59E0B', transform=ax_left.transAxes)
ax_left.text(0.04, 0.915, "Self-identified flaws from empirical auditing of our 8,760-hour backtest", fontsize=8.5, color='#777777', transform=ax_left.transAxes)

# Card 1: The January Payday Trap
y_c1 = 0.88
ax_left.plot([0.04, 0.96], [y_c1, y_c1], color='#1A1A1A', transform=ax_left.transAxes, linewidth=0.8)
ax_left.text(0.04, 0.84, "LIMITATION 1 · THE 'JANUARY PAYDAY TRAP' (DRAIN BIAS)", fontsize=9.5, fontweight='bold', color='#EF4444', transform=ax_left.transAxes)
ax_left.text(0.04, 0.795, "• Vulnerability: Month 1 payroll surges biased rolling EWMA drain estimates to -$94k/hr\n  (vs true -$289k/hr annual trend), risking premature over-allocation into 2Y bonds.", fontsize=8.5, color='#CCCCCC', transform=ax_left.transAxes, linespacing=1.4)
ax_left.text(0.04, 0.735, "• Prototype Mitigation: Enforced 35-day institutional burn-in & explicit floor prior (min -$250k/hr).\n• Residual Risk: Still sensitive to non-stationary structural corporate client deposit flight.", fontsize=8.5, color='#38BDF8', transform=ax_left.transAxes, linespacing=1.4)

# Card 2: Discount Window Stigma & Single-Lender Overdraft
y_c2 = 0.68
ax_left.plot([0.04, 0.96], [y_c2, y_c2], color='#1A1A1A', transform=ax_left.transAxes, linewidth=0.8)
ax_left.text(0.04, 0.64, "LIMITATION 2 · OVERDRAFT STIGMA & REGULATORY CONSTRAINTS", fontsize=9.5, fontweight='bold', color='#EF4444', transform=ax_left.transAxes)
ax_left.text(0.04, 0.595, "• Vulnerability: Theorem 1 mathematically proves overdraft is 24.4x cheaper than repo breaks.\n  However, real-world discount window borrowing carries severe supervisory & credit stigma.", fontsize=8.5, color='#CCCCCC', transform=ax_left.transAxes, linespacing=1.4)
ax_left.text(0.04, 0.535, "• Prototype Mitigation: Built executive 'Guarded' risk mode capping overdraft to $25M.\n• Residual Risk: Lacks multi-counterparty private bilateral credit facilities.", fontsize=8.5, color='#38BDF8', transform=ax_left.transAxes, linespacing=1.4)

# Card 3: 1-Year Truncation & Zero-Slippage Assumption
y_c3 = 0.48
ax_left.plot([0.04, 0.96], [y_c3, y_c3], color='#1A1A1A', transform=ax_left.transAxes, linewidth=0.8)
ax_left.text(0.04, 0.44, "LIMITATION 3 · 1-YEAR HORIZON & ZERO-SLIPPAGE ASSUMPTION", fontsize=9.5, fontweight='bold', color='#EF4444', transform=ax_left.transAxes)
ax_left.text(0.04, 0.395, "• Vulnerability: Dataset spans 8,760 hours (1 calendar year). It lacks a full 5-10 year credit\n  cycle (prolonged ZIRP, quantitative tightening, multi-year inverted yield curves).", fontsize=8.5, color='#CCCCCC', transform=ax_left.transAxes, linespacing=1.4)
ax_left.text(0.04, 0.335, "• Vulnerability: Assumes large $10M-$40M bond & repo sweeps execute with zero market impact.\n• Prototype Mitigation: Closed-form break-even mathematics prevent empirical curve-fitting.", fontsize=8.5, color='#38BDF8', transform=ax_left.transAxes, linespacing=1.4)

# Bottom Summary Pill in Left Panel
ax_left.plot([0.04, 0.96], [0.15, 0.15], color='#1A1A1A', transform=ax_left.transAxes, linewidth=0.8)
ax_left.text(0.04, 0.08, "AUDIT TAKEAWAY: We designed AegisFlow around conservative closed-form break-evens rather\nthan overfitted ML parameters, ensuring our known flaws have mathematical fail-safes.", fontsize=8.5, color='#888888', transform=ax_left.transAxes, linespacing=1.3)


# ==========================================
# RIGHT PANEL: NEXT STEPS & PRODUCTION ROADMAP
# ==========================================
ax_right = fig.add_subplot(gs[0, 1])
ax_right.set_facecolor('#090909')
ax_right.set_xticks([])
ax_right.set_yticks([])
for spine in ax_right.spines.values():
    spine.set_color('#222222')
    spine.set_linewidth(1.0)

ax_right.text(0.04, 0.95, "02 / NEXT STEPS & PRODUCTION-READY ROADMAP", fontsize=11, fontweight='bold', color='#2DD4BF', transform=ax_right.transAxes)
ax_right.text(0.04, 0.915, "Concrete engineering deliverables for immediate iteration and enterprise rollout", fontsize=8.5, color='#777777', transform=ax_right.transAxes)

# Section A: "WHAT WE WOULD DO WITH 1 WEEK MORE"
y_r1 = 0.88
ax_right.plot([0.04, 0.96], [y_r1, y_r1], color='#1A1A1A', transform=ax_right.transAxes, linewidth=0.8)
ax_right.text(0.04, 0.84, "PHASE 1 · WHAT WE WOULD BUILD WITH 1 WEEK MORE", fontsize=9.5, fontweight='bold', color='#38BDF8', transform=ax_right.transAxes)

# Flowchart-like 3 blocks for "1 Week More"
box_y = 0.59
box_w = 0.28
box_h = 0.21

# Step 1
ax_right.add_patch(plt.Rectangle((0.04, box_y), box_w, box_h, transform=ax_right.transAxes, facecolor='#111111', edgecolor='#222222', linewidth=1.0))
ax_right.text(0.06, box_y + 0.16, "1. Bilateral Credit Lines", fontsize=8.5, fontweight='bold', color='#2DD4BF', transform=ax_right.transAxes)
ax_right.text(0.06, box_y + 0.04, "Add automated routing\nacross interbank repo &\nprivate commercial lines\nto bypass central bank\ndiscount stigma.", fontsize=7.5, color='#CCCCCC', transform=ax_right.transAxes, linespacing=1.3)

# Arrow 1->2
ax_right.text(0.33, box_y + 0.10, "→", fontsize=12, color='#555555', transform=ax_right.transAxes)

# Step 2
ax_right.add_patch(plt.Rectangle((0.36, box_y), box_w, box_h, transform=ax_right.transAxes, facecolor='#111111', edgecolor='#222222', linewidth=1.0))
ax_right.text(0.38, box_y + 0.16, "2. TWAP/VWAP Slicing", fontsize=8.5, fontweight='bold', color='#38BDF8', transform=ax_right.transAxes)
ax_right.text(0.38, box_y + 0.04, "Implement micro-order\nexecution algorithms\nfor $20M+ bond liquidations\nto eliminate slippage\n& market impact.", fontsize=7.5, color='#CCCCCC', transform=ax_right.transAxes, linespacing=1.3)

# Arrow 2->3
ax_right.text(0.65, box_y + 0.10, "→", fontsize=12, color='#555555', transform=ax_right.transAxes)

# Step 3
ax_right.add_patch(plt.Rectangle((0.68, box_y), box_w, box_h, transform=ax_right.transAxes, facecolor='#111111', edgecolor='#222222', linewidth=1.0))
ax_right.text(0.70, box_y + 0.16, "3. Multi-Year Chaos Engine", fontsize=8.5, fontweight='bold', color='#F59E0B', transform=ax_right.transAxes)
ax_right.text(0.70, box_y + 0.04, "Synthesize 10-year macro\nshocks (2008 GFC, 2020\nCOVID, 2023 SVB run)\nwith non-stationary\nregime Markov shifts.", fontsize=7.5, color='#CCCCCC', transform=ax_right.transAxes, linespacing=1.3)


# Section B: "WHAT THE APP NEEDS TO BE PRODUCTION READY"
y_r2 = 0.52
ax_right.plot([0.04, 0.96], [y_r2, y_r2], color='#1A1A1A', transform=ax_right.transAxes, linewidth=0.8)
ax_right.text(0.04, 0.48, "PHASE 2 · REQUIREMENTS FOR ENTERPRISE PRODUCTION-READINESS", fontsize=9.5, fontweight='bold', color='#10B981', transform=ax_right.transAxes)

# Flowchart-like 3 blocks for "Production Ready"
box2_y = 0.22
# Step 1
ax_right.add_patch(plt.Rectangle((0.04, box2_y), box_w, box_h, transform=ax_right.transAxes, facecolor='#111111', edgecolor='#222222', linewidth=1.0))
ax_right.text(0.06, box2_y + 0.16, "1. Real-Time Core Rails", fontsize=8.5, fontweight='bold', color='#10B981', transform=ax_right.transAxes)
ax_right.text(0.06, box2_y + 0.04, "Direct ISO 20022 message\nconnectors into FedNow,\nSWIFT gpi, & CHIPS for\ncontinuous sub-second\nbalance synchronization.", fontsize=7.5, color='#CCCCCC', transform=ax_right.transAxes, linespacing=1.3)

# Arrow 1->2
ax_right.text(0.33, box2_y + 0.10, "→", fontsize=12, color='#555555', transform=ax_right.transAxes)

# Step 2
ax_right.add_patch(plt.Rectangle((0.36, box2_y), box_w, box_h, transform=ax_right.transAxes, facecolor='#111111', edgecolor='#222222', linewidth=1.0))
ax_right.text(0.38, box2_y + 0.16, "2. HSM Multi-Sig Vaults", fontsize=8.5, fontweight='bold', color='#A78BFA', transform=ax_right.transAxes)
ax_right.text(0.38, box2_y + 0.04, "Hardware Security Modules\n(FIPS 140-3 Level 4)\nwith automated Multi-Party\nComputation (MPC) for\n>$100M sweep signatures.", fontsize=7.5, color='#CCCCCC', transform=ax_right.transAxes, linespacing=1.3)

# Arrow 2->3
ax_right.text(0.65, box2_y + 0.10, "→", fontsize=12, color='#555555', transform=ax_right.transAxes)

# Step 3
ax_right.add_patch(plt.Rectangle((0.68, box2_y), box_w, box_h, transform=ax_right.transAxes, facecolor='#111111', edgecolor='#222222', linewidth=1.0))
ax_right.text(0.70, box2_y + 0.16, "3. Basel III Regulatory API", fontsize=8.5, fontweight='bold', color='#2DD4BF', transform=ax_right.transAxes)
ax_right.text(0.70, box2_y + 0.04, "Automated compliance feeds\ncomputing real-time LCR\n(Liquidity Coverage Ratio)\n& NSFR metrics with audit-\nready regulatory logs.", fontsize=7.5, color='#CCCCCC', transform=ax_right.transAxes, linespacing=1.3)

# Bottom Summary Pill in Right Panel
ax_right.plot([0.04, 0.96], [0.15, 0.15], color='#1A1A1A', transform=ax_right.transAxes, linewidth=0.8)
ax_right.text(0.04, 0.08, "DEPLOYMENT GOAL: Transition from an algorithmic simulation engine to a certified Layer-1\nliquidity copilot integrated directly behind commercial digital bank core ledger rails.", fontsize=8.5, color='#888888', transform=ax_right.transAxes, linespacing=1.3)

# Save high-resolution minimalist slide image
plt.savefig('assets/aegisflow_limits_and_next_steps_slide.png', dpi=100, facecolor='#000000')
plt.close()

# Also save as JPG
img = Image.open('assets/aegisflow_limits_and_next_steps_slide.png')
img.convert('RGB').save('assets/aegisflow_limits_and_next_steps_slide.jpg', quality=96)
print("Successfully generated assets/aegisflow_limits_and_next_steps_slide.jpg!")
