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
fig.text(0.04, 0.952, "AEGISFLOW", fontsize=16.5, fontweight='bold', color='#2DD4BF')
fig.text(0.128, 0.952, "/", fontsize=17, color='#444444')
fig.text(0.142, 0.952, "VALUE PROPOSITION: USPS, IMPACT, FEASIBILITY & COMPETITIVE MOAT", fontsize=15.0, fontweight='bold', color='#FFFFFF')
fig.text(0.96, 0.952, "Architectural Unfair Advantages, Real-World Banking Impact & Enterprise Readiness", fontsize=11, color='#888888', ha='right')

# Header underline
fig.add_artist(plt.Line2D([0.04, 0.96], [0.935, 0.935], color='#222222', linewidth=1.0))


# ==============================================================================
# 2. TOP SECTION: THE 3 CORE ARCHITECTURAL USPS (DIAGRAMMATIC CARDS)
# Spanning across x in [0.04, 0.96], y in [0.730, 0.915]
# ==============================================================================
ax_usps = fig.add_axes([0.04, 0.730, 0.92, 0.185], facecolor='#080808')
ax_usps.set_xticks([])
ax_usps.set_yticks([])
for spine in ax_usps.spines.values():
    spine.set_color('#1C1C1C')
    spine.set_linewidth(1.0)

usps = [
    {
        "num": "USP 01",
        "tag": "PARADIGM SHIFT",
        "title": "NEED-TIME INVENTORY LADDER",
        "summary": "Capital as Expiring Inventory (Not a Static Pie)",
        "desc": "Auditing all 8,760h revealed a structural drain of -$289k/hr (-$2.53B/yr). Capital is inventory with a countdown: every dollar is deployed to bonds only if survival time tau > 10.8 months.",
        "flow": [r"-\$289k/hr Drain", r"Need-Time $\tau$", "2Y Bonds (>10.8mo)"],
        "color": "#10B981"
    },
    {
        "num": "USP 02",
        "tag": "MATHEMATICAL PROOFS",
        "title": "DUAL MATHEMATICAL THEOREMS",
        "summary": "Theorem 1 Arbitrage & Theorem 2 Equity Blacklist",
        "desc": "Theorem 1 proves overnight overdraft ($0.0205%) is 24.4x cheaper than cracking 15h repo early ($0.50%). Theorem 2 proves equities require 2.48 years to amortize 15% exit haircuts, blacklisting equities to avoid crashes.",
        "flow": [r"Overdraft $\ll$ Repo Break", "24.4x Cheaper", "0% Equity Blacklist"],
        "color": "#38BDF8"
    },
    {
        "num": "USP 03",
        "tag": "CLOSED-FORM SPEED",
        "title": "FRACTIONAL KNAPSACK SOLVER",
        "summary": "Deterministic O(N log N) vs Slow Iterative LPs",
        "desc": "Replaces slow, fragile interior-point linear programs with a closed-form continuous knapsack. Dynamically sorts tiers by cure-time unit penalty, achieving global optimality in <0.08ms on commodity CPUs.",
        "flow": ["Deficit Inflow", r"$\mathcal{O}(N \log N)$ Unit Sort", "<0.08ms Optimum"],
        "color": "#F59E0B"
    }
]

for idx, u in enumerate(usps):
    ux = 0.020 + idx * 0.330
    
    # Outer card outline
    card = FancyBboxPatch((ux, 0.06), 0.300, 0.88, boxstyle="round,pad=0.008,rounding_size=0.015",
                          facecolor='#0C0C0C', edgecolor='#222222', linewidth=0.8, transform=ax_usps.transAxes)
    ax_usps.add_patch(card)
    
    # Card Header
    ax_usps.text(ux + 0.012, 0.84, f"{u['num']} · {u['title']}", fontsize=8.4, fontweight='bold', color=u['color'], transform=ax_usps.transAxes)
    ax_usps.text(ux + 0.288, 0.84, f"[{u['tag']}]", ha='right', fontsize=7.0, fontweight='bold', color='#777777', transform=ax_usps.transAxes)
    ax_usps.text(ux + 0.012, 0.69, u['summary'], fontsize=7.8, fontweight='bold', color='#FFFFFF', transform=ax_usps.transAxes)
    
    # Description
    desc_wrap = textwrap.fill(u['desc'], width=47)
    ax_usps.text(ux + 0.012, 0.56, desc_wrap, fontsize=7.2, color='#A3A3A3', va='top', transform=ax_usps.transAxes, linespacing=1.2)
    
    # Mini Diagram Flow at bottom of card
    flow_y = 0.17
    card_w = 0.300
    node_w = 0.078
    arrow_w = 0.020
    start_fx = ux + 0.012
    
    for f_i, f_step in enumerate(u['flow']):
        fx = start_fx + f_i * (node_w + arrow_w + 0.005)
        # Flow Node Box
        f_box = FancyBboxPatch((fx, flow_y - 0.05), node_w, 0.10, boxstyle="round,pad=0.004,rounding_size=0.01",
                               facecolor='#141414', edgecolor='#2A2A2A', linewidth=0.6, transform=ax_usps.transAxes)
        ax_usps.add_patch(f_box)
        ax_usps.text(fx + node_w/2, flow_y, f_step, ha='center', va='center', fontsize=6.3, fontweight='bold', color='#DDDDDD', transform=ax_usps.transAxes)
        
        # Arrow connector
        if f_i < len(u['flow']) - 1:
            ax_usps.text(fx + node_w + 0.012, flow_y, "→", ha='center', va='center', fontsize=7.5, color=u['color'], transform=ax_usps.transAxes)


# ==============================================================================
# 3. MIDDLE SECTION: COMPETITIVE MOAT vs REAL-WORLD IMPACT
# Left: Competitive Comparison Matrix (x: 0.04 to 0.525, y: 0.260 to 0.705)
# Right: Real-World Banking Impact (x: 0.545 to 0.96, y: 0.260 to 0.705)
# ==============================================================================

# ------------------------------------------------------------------------------
# MIDDLE-LEFT PANEL: COMPETITIVE COMPARISON MATRIX
# ------------------------------------------------------------------------------
ax_comp = fig.add_axes([0.04, 0.260, 0.490, 0.445], facecolor='#080808')
ax_comp.set_xticks([])
ax_comp.set_yticks([])
for spine in ax_comp.spines.values():
    spine.set_color('#1C1C1C')
    spine.set_linewidth(1.0)

ax_comp.text(0.04, 0.940, "COMPETITIVE MOAT: HOW AEGISFLOW BEATS ALTERNATIVE SYSTEMS", fontsize=10.2, fontweight='bold', color='#38BDF8', transform=ax_comp.transAxes)
ax_comp.text(0.04, 0.885, "Architectural feature-by-feature comparison against bank baselines & naive optimizers", fontsize=7.6, color='#777777', transform=ax_comp.transAxes)

# Table Header
c_head_y = 0.815
ax_comp.plot([0.04, 0.96], [c_head_y, c_head_y], color='#222222', linewidth=1.0, transform=ax_comp.transAxes)
ax_comp.text(0.04, c_head_y - 0.045, "APPROACH", fontsize=7.8, fontweight='bold', color='#777777', transform=ax_comp.transAxes)
ax_comp.text(0.24, c_head_y - 0.045, "ALLOCATION LOGIC", fontsize=7.8, fontweight='bold', color='#777777', transform=ax_comp.transAxes)
ax_comp.text(0.48, c_head_y - 0.045, "DEFICIT RESOLUTION", fontsize=7.8, fontweight='bold', color='#777777', transform=ax_comp.transAxes)
ax_comp.text(0.74, c_head_y - 0.045, "INSTITUTIONAL MOAT", fontsize=7.8, fontweight='bold', color='#777777', transform=ax_comp.transAxes)

comp_rows = [
    {
        "name": "Static Rules\n(20/30/30/20)",
        "logic": "Rigid fixed % pie\n(Mean-Variance / 60-40)",
        "deficit": "Forced liquidation of\n2Y bonds & equities",
        "tag": "FAILED",
        "tag_color": "#EF4444",
        "verdict": "Blind to structural drain;\nincurs massive haircut fees",
        "color": "#F59E0B"
    },
    {
        "name": "Greedy Chasers\n(Yield Maximizers)",
        "logic": "Sweeps cash into\n10% equities & repo",
        "deficit": "Cracks overnight repo;\nfire-sales equities",
        "tag": "CRITICAL",
        "tag_color": "#DC2626",
        "verdict": "71.2x penalty trap;\nwiped out in -36.6% crash",
        "color": "#EF4444"
    },
    {
        "name": "Deep Learning\n(LSTMs / Transformers)",
        "logic": "Latent sequence\nattention weights",
        "deficit": "Iterative interior-point\nLP solver (>50ms)",
        "tag": "FRAGILE",
        "tag_color": "#A78BFA",
        "verdict": "High GPU latency; model\nhallucinates in panic regimes",
        "color": "#C084FC"
    },
    {
        "name": "AegisFlow\n(Our Engine)",
        "logic": "Causal Quantile ML +\nNeed-Time Ladder",
        "deficit": "Closed-form Knapsack +\nTheorem 1 Overdraft",
        "tag": "SUPERIOR",
        "tag_color": "#10B981",
        "verdict": "100% Solvency; Zero GPU;\n+$264.8M Alpha Delivered",
        "color": "#2DD4BF"
    }
]

c_start_y = 0.690
c_spacing = 0.165
for i, cr in enumerate(comp_rows):
    cy = c_start_y - i * c_spacing
    ax_comp.plot([0.04, 0.96], [cy + 0.055, cy + 0.055], color='#141414', linewidth=0.8, transform=ax_comp.transAxes)
    ax_comp.text(0.04, cy, cr["name"], fontsize=8.0, fontweight='bold', color=cr["color"], va='center', transform=ax_comp.transAxes, linespacing=1.2)
    ax_comp.text(0.24, cy, cr["logic"], fontsize=7.5, color='#CCCCCC', va='center', transform=ax_comp.transAxes, linespacing=1.2)
    ax_comp.text(0.48, cy, cr["deficit"], fontsize=7.5, color='#D4D4D4', va='center', transform=ax_comp.transAxes, linespacing=1.2)
    
    # Tag Badge
    badge_box = FancyBboxPatch((0.74, cy + 0.015), 0.075, 0.042, boxstyle="round,pad=0.002,rounding_size=0.008",
                               facecolor=cr["tag_color"], edgecolor='none', transform=ax_comp.transAxes)
    ax_comp.add_patch(badge_box)
    ax_comp.text(0.7775, cy + 0.036, cr["tag"], ha='center', va='center', fontsize=6.2, fontweight='bold', color='#FFFFFF', transform=ax_comp.transAxes)
    
    ax_comp.text(0.74, cy - 0.030, cr["verdict"], fontsize=7.3, color='#E2E8F0', va='center', transform=ax_comp.transAxes, linespacing=1.15)


# ------------------------------------------------------------------------------
# MIDDLE-RIGHT PANEL: REAL-WORLD IMPACT & ECONOMIC BENEFITS
# ------------------------------------------------------------------------------
ax_impact = fig.add_axes([0.550, 0.260, 0.410, 0.445], facecolor='#080808')
ax_impact.set_xticks([])
ax_impact.set_yticks([])
for spine in ax_impact.spines.values():
    spine.set_color('#1C1C1C')
    spine.set_linewidth(1.0)

ax_impact.text(0.04, 0.940, "REAL-WORLD IMPACT & INSTITUTIONAL BENEFITS", fontsize=10.2, fontweight='bold', color='#10B981', transform=ax_impact.transAxes)
ax_impact.text(0.04, 0.885, "Measurable economic value unlocked across bank liquidity, solvency, and compliance", fontsize=7.6, color='#777777', transform=ax_impact.transAxes)

impacts = [
    {
        "badge": "IMPACT 01",
        "title": "WORKING CAPITAL & ROE MAXIMIZATION",
        "pill": "+$2.1M / yr Yield",
        "pill_color": "#10B981",
        "desc": "Operating with lean, causal P99 safety buffers frees $40M–$50M in trapped operational cash. Unlocks ~$2.1M/year in risk-free overnight yield on active deposits without increasing platform default risk.",
        "color": "#10B981"
    },
    {
        "badge": "IMPACT 02",
        "title": "INOCULATION AGAINST SYSTEMIC FIRE-SALES",
        "pill": "Zero Forced Haircuts",
        "pill_color": "#38BDF8",
        "desc": "During sudden liquidity panics (SVB-style deposit runs), naive banks dump sovereign bonds at steep discounts. AegisFlow's Overdraft Bridge absorbs acute intraday shocks cleanly, protecting secondary-market bond values.",
        "color": "#38BDF8"
    },
    {
        "badge": "IMPACT 03",
        "title": "BASEL III & REGULATORY ALIGNMENT",
        "pill": "30-Day LCR Compliant",
        "pill_color": "#A78BFA",
        "desc": "Preserves High-Quality Liquid Assets (HQLA) across Tier 0 and Tier 1 to maintain 30-day Liquidity Coverage Ratios. Generates cryptographic decision records with plain-language narratives for central-bank regulators.",
        "color": "#A78BFA"
    }
]

imp_start_y = 0.720
imp_spacing = 0.225
for idx, imp in enumerate(impacts):
    iy = imp_start_y - idx * imp_spacing
    ax_impact.text(0.04, iy + 0.075, f"{imp['badge']} · {imp['title']}", fontsize=8.2, fontweight='bold', color=imp['color'], transform=ax_impact.transAxes)
    
    # Value Pill Badge
    pill_box = FancyBboxPatch((0.71, iy + 0.055), 0.25, 0.045, boxstyle="round,pad=0.002,rounding_size=0.01",
                              facecolor='#141414', edgecolor=imp['pill_color'], linewidth=0.8, transform=ax_impact.transAxes)
    ax_impact.add_patch(pill_box)
    ax_impact.text(0.835, iy + 0.077, imp['pill'], ha='center', va='center', fontsize=7.2, fontweight='bold', color=imp['pill_color'], transform=ax_impact.transAxes)
    
    imp_wrap = textwrap.fill(imp['desc'], width=58)
    ax_impact.text(0.04, iy + 0.025, imp_wrap, fontsize=7.4, color='#A3A3A3', va='top', transform=ax_impact.transAxes, linespacing=1.25)
    
    if idx < len(impacts) - 1:
        ax_impact.plot([0.04, 0.96], [iy - 0.065, iy - 0.065], color='#141414', linewidth=0.8, transform=ax_impact.transAxes)


# ==============================================================================
# 4. BOTTOM SECTION: PRODUCTION FEASIBILITY & DEPLOYMENT VIABILITY
# Spanning across x in [0.04, 0.96], y in [0.045, 0.235]
# ==============================================================================
ax_feas = fig.add_axes([0.04, 0.045, 0.92, 0.190], facecolor='#080808')
ax_feas.set_xticks([])
ax_feas.set_yticks([])
for spine in ax_feas.spines.values():
    spine.set_color('#1C1C1C')
    spine.set_linewidth(1.0)

ax_feas.text(0.025, 0.880, "FEASIBILITY & PRODUCTION VIABILITY (ENTERPRISE READINESS)", fontsize=10.2, fontweight='bold', color='#F59E0B', transform=ax_feas.transAxes)
ax_feas.text(0.025, 0.770, "Production deployment architecture designed for tier-1 core banking integration", fontsize=7.6, color='#777777', transform=ax_feas.transAxes)

feas_pillars = [
    {
        "num": "01",
        "title": "ZERO GPU OVERHEAD",
        "sub": "Commodity x86 / ARM",
        "desc": "LightGBM quantile trees and closed-form knapsack run on standard CPU servers (<240MB RAM), avoiding costly GPU clusters.",
        "color": "#10B981"
    },
    {
        "num": "02",
        "title": "SUB-35ms TICK LATENCY",
        "sub": "FedNow & SWIFT Ready",
        "desc": "Zero-copy PyArrow vectorized batches guarantee sub-millisecond execution, fitting inside real-time gross settlement clearing windows.",
        "color": "#38BDF8"
    },
    {
        "num": "03",
        "title": "CRYPTOGRAPHIC ACCOUNTING",
        "sub": "$0.01 Audit Tolerance",
        "desc": "Strict cash-conservation identity reconciles across all 8,760 hours to within $0.01 tolerance with zero balance sheet leakage.",
        "color": "#F59E0B"
    },
    {
        "num": "04",
        "title": "HEADLESS ASGI ARCHITECTURE",
        "sub": "OpenAPI 3.1 & WebSockets",
        "desc": "Decoupled FastAPI service exposing validated REST endpoints and /ws/replay feeds directly into Google Stitch dashboards.",
        "color": "#A78BFA"
    }
]

f_w = 0.230
for f_idx, fp in enumerate(feas_pillars):
    fx = 0.025 + f_idx * 0.245
    ax_feas.text(fx, 0.58, f"{fp['num']} · {fp['title']}", fontsize=8.0, fontweight='bold', color=fp['color'], transform=ax_feas.transAxes)
    ax_feas.text(fx, 0.42, fp['sub'], fontsize=7.4, fontweight='bold', color='#E2E8F0', transform=ax_feas.transAxes)
    
    f_desc_wrap = textwrap.fill(fp['desc'], width=35)
    ax_feas.text(fx, 0.30, f_desc_wrap, fontsize=7.0, color='#8E8E8E', va='top', transform=ax_feas.transAxes, linespacing=1.2)
    
    if f_idx < len(feas_pillars) - 1:
        sep_fx = fx + 0.235
        ax_feas.plot([sep_fx, sep_fx], [0.08, 0.65], color='#1A1A1A', linewidth=0.8, transform=ax_feas.transAxes)
        # Flow arrow between pipeline stages
        ax_feas.text(sep_fx, 0.38, "▶", ha='center', va='center', fontsize=7.5, color='#2DD4BF', transform=ax_feas.transAxes)


# Save high-resolution slide
plt.savefig('assets/aegisflow_usps_impact_feasibility_slide.png', dpi=100, facecolor='#000000')
plt.close()

img = Image.open('assets/aegisflow_usps_impact_feasibility_slide.png')
img.convert('RGB').save('assets/aegisflow_usps_impact_feasibility_slide.jpg', quality=96)

# Copy to brain artifact directory
img.convert('RGB').save('/home/idioticspaceman/.gemini/antigravity-cli/brain/98d405f9-01a1-449c-91dc-21e4f690d2c7/aegisflow_usps_impact_feasibility_slide.jpg', quality=96)
print("Successfully generated assets/aegisflow_usps_impact_feasibility_slide.jpg!")
