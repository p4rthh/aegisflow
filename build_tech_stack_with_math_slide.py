import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from PIL import Image
import numpy as np

# Setup typography and base canvas (1920x1080, Pure OLED Black)
fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor='#000000')

# Top Header Bar
fig.text(0.035, 0.952, "AEGISFLOW", fontsize=16.5, fontweight='bold', color='#2DD4BF')
fig.text(0.122, 0.952, "/", fontsize=17, color='#444444')
fig.text(0.136, 0.952, "TECHNICAL APPROACH: ALGORITHM, TECH STACK & FORMULATIONS", fontsize=15.5, fontweight='bold', color='#FFFFFF')
fig.text(0.965, 0.952, "Autonomous Liquidity & Quantitative Treasury Optimization", fontsize=11.5, color='#888888', ha='right')

# Header underline
fig.add_artist(plt.Line2D([0.035, 0.965], [0.932, 0.932], color='#222222', linewidth=1.0))

# Sidebar Header Title
fig.text(0.040, 0.908, "TECH STACK ARCHITECTURE", fontsize=12, fontweight='bold', color='#FFFFFF')

# ------------------------------------------------------------------------------
# DEDICATED SECTION: "CORE QUANTITATIVE THEOREMS & ALGORITHMIC HEURISTICS"
# y in [0.228, 0.408]
# ------------------------------------------------------------------------------
ax_math = fig.add_axes([0.245, 0.228, 0.720, 0.175], facecolor='#080808')
ax_math.set_xticks([])
ax_math.set_yticks([])
for spine in ax_math.spines.values():
    spine.set_color('#222222')
    spine.set_linewidth(1.0)

ax_math.text(0.02, 0.905, "CORE QUANTITATIVE THEOREMS & ALGORITHMIC HEURISTICS", fontsize=10.2, fontweight='bold', color='#F59E0B', transform=ax_math.transAxes)
ax_math.text(0.98, 0.905, "Closed-form mathematical proofs governing liquidity gates & capital inventory", fontsize=8.2, color='#888888', ha='right', transform=ax_math.transAxes)

# 4 Cards inside Math Section
m_w = 0.235
m_h = 0.72
m_y = 0.08

# Card 1: Theorem 1 (Overdraft Arbitrage)
c1 = FancyBboxPatch((0.015, m_y), m_w, m_h, boxstyle="round,pad=0.01", facecolor='#0D1814', edgecolor='#10B981', linewidth=1.1, transform=ax_math.transAxes)
ax_math.add_patch(c1)
ax_math.text(0.028, m_y + 0.54, "THEOREM 1 · OVERDRAFT ARBITRAGE", fontsize=8.2, color='#10B981', fontweight='bold', transform=ax_math.transAxes)
ax_math.text(0.028, m_y + 0.32, r"$c_{OD} = \frac{15}{8760} r_{OD} \ll h_{repo} \; (24.4\times)$", fontsize=10.0, color='#FFFFFF', transform=ax_math.transAxes)
ax_math.text(0.028, m_y + 0.09, "15h discount loan (0.02%) is 24.4x\ncheaper than 100bps early repo break.", fontsize=7.5, color='#A3A3A3', transform=ax_math.transAxes, linespacing=1.28)

# Card 2: Theorem 2 (0% Equity Blacklist)
c2 = FancyBboxPatch((0.260, m_y), m_w, m_h, boxstyle="round,pad=0.01", facecolor='#1C140A', edgecolor='#F59E0B', linewidth=1.1, transform=ax_math.transAxes)
ax_math.add_patch(c2)
ax_math.text(0.273, m_y + 0.54, "THEOREM 2 · 0% EQUITY BLACKLIST", fontsize=8.2, color='#F59E0B', fontweight='bold', transform=ax_math.transAxes)
ax_math.text(0.273, m_y + 0.32, r"$\tau_e = \frac{h_3 - h_2}{\mu_3 - y_2} = \frac{13\%}{5.25\%} = 2.48\mathrm{y} > 1\mathrm{y}$", fontsize=10.0, color='#FFFFFF', transform=ax_math.transAxes)
ax_math.text(0.273, m_y + 0.09, "Equities require 2.48y to beat bonds;\nliquidated at 15% loss in draining float.", fontsize=7.5, color='#A3A3A3', transform=ax_math.transAxes, linespacing=1.28)

# Card 3: Pinball Loss (Asymmetric Tail Quantile Loss)
c3 = FancyBboxPatch((0.505, m_y), m_w, m_h, boxstyle="round,pad=0.01", facecolor='#0B171C', edgecolor='#2DD4BF', linewidth=1.1, transform=ax_math.transAxes)
ax_math.add_patch(c3)
ax_math.text(0.518, m_y + 0.54, "PINBALL LOSS OBJECTIVE", fontsize=8.2, color='#2DD4BF', fontweight='bold', transform=ax_math.transAxes)
ax_math.text(0.518, m_y + 0.32, r"$\mathcal{L}_q = \max(q \cdot e, (q - 1) \cdot e)$", fontsize=10.2, color='#FFFFFF', transform=ax_math.transAxes)
ax_math.text(0.518, m_y + 0.09, r"Penalizes cash shortfalls 99x more" + "\n" + r"than surpluses ($q \in \{0.50, 0.90, 0.99\}$).", fontsize=7.5, color='#A3A3A3', transform=ax_math.transAxes, linespacing=1.28)

# Card 4: Need-Time Ladder (Bond Holding Horizon)
c4 = FancyBboxPatch((0.750, m_y), m_w, m_h, boxstyle="round,pad=0.01", facecolor='#121320', edgecolor='#818CF8', linewidth=1.1, transform=ax_math.transAxes)
ax_math.add_patch(c4)
ax_math.text(0.763, m_y + 0.54, "NEED-TIME INVENTORY LADDER", fontsize=8.2, color='#818CF8', fontweight='bold', transform=ax_math.transAxes)
ax_math.text(0.763, m_y + 0.32, r"$\tau_b = \frac{h_2}{y_2 - y_1} \approx 7,900\mathrm{h} \quad (t_{need} > \tau_b)$", fontsize=10.0, color='#FFFFFF', transform=ax_math.transAxes)
ax_math.text(0.763, m_y + 0.09, "Allocates dollars to 2Y bonds only if\ncapital survival time exceeds 7,900h.", fontsize=7.5, color='#A3A3A3', transform=ax_math.transAxes, linespacing=1.28)


# ------------------------------------------------------------------------------
# BOTTOM SECTION: "WHY CAUSAL QUANTILE ML OVER DEEP LEARNING / LSTMs?"
# y in [0.032, 0.207]
# ------------------------------------------------------------------------------
ax_bot = fig.add_axes([0.245, 0.032, 0.720, 0.175], facecolor='#080808')
ax_bot.set_xticks([])
ax_bot.set_yticks([])
for spine in ax_bot.spines.values():
    spine.set_color('#222222')
    spine.set_linewidth(1.0)

ax_bot.text(0.02, 0.905, "WHY CAUSAL QUANTILE ML OVER DEEP LEARNING / LSTMs?", fontsize=10.2, fontweight='bold', color='#FFFFFF', transform=ax_bot.transAxes)

b_w = 0.315
b_h = 0.72
b_y = 0.08

# Sub-card 1
ax_bot.add_patch(FancyBboxPatch((0.015, b_y), b_w, b_h, boxstyle="round,pad=0.01", facecolor='#111111', edgecolor='#2A2A2A', linewidth=1.0, transform=ax_bot.transAxes))
ax_bot.text(0.028, b_y + 0.54, "P99 Tail-Risk Direct Optimization", fontsize=8.5, color='#FFFFFF', fontweight='bold', transform=ax_bot.transAxes)
ax_bot.text(0.028, b_y + 0.34, r"$\text{Loss: } \mathcal{L}_{0.99} = \max(0.99 e, -0.01 e)$", fontsize=8.8, color='#2DD4BF', transform=ax_bot.transAxes)
ax_bot.text(0.028, b_y + 0.09, "Pinball loss directly optimizes solvency tail;\nstandard MSE averages away tail-risk.", fontsize=7.6, color='#A3A3A3', linespacing=1.28, transform=ax_bot.transAxes)

# Sub-card 2
ax_bot.add_patch(FancyBboxPatch((0.342, b_y), b_w, b_h, boxstyle="round,pad=0.01", facecolor='#111111', edgecolor='#2A2A2A', linewidth=1.0, transform=ax_bot.transAxes))
ax_bot.text(0.355, b_y + 0.54, "<1.5ms Ultra-Low Latency", fontsize=8.5, color='#FFFFFF', fontweight='bold', transform=ax_bot.transAxes)
ax_bot.text(0.355, b_y + 0.34, r"$\text{Inference: } \mathcal{O}(D \cdot K) < 1.5\mathrm{ms} \text{ (CPU)}$", fontsize=8.8, color='#38BDF8', transform=ax_bot.transAxes)
ax_bot.text(0.355, b_y + 0.09, "Lightweight decision trees run on CPU cores\nwithout GPU overhead or inference jitter.", fontsize=7.6, color='#A3A3A3', linespacing=1.28, transform=ax_bot.transAxes)

# Sub-card 3
ax_bot.add_patch(FancyBboxPatch((0.670, b_y), b_w, b_h, boxstyle="round,pad=0.01", facecolor='#111111', edgecolor='#2A2A2A', linewidth=1.0, transform=ax_bot.transAxes))
ax_bot.text(0.683, b_y + 0.54, "Non-Stationary Regime Robustness", fontsize=8.5, color='#FFFFFF', fontweight='bold', transform=ax_bot.transAxes)
ax_bot.text(0.683, b_y + 0.34, r"$\text{Heuristic: } \hat{d}_t = \alpha f_t + (1-\alpha)\hat{d}_{t-1}$", fontsize=8.8, color='#F59E0B', transform=ax_bot.transAxes)
ax_bot.text(0.683, b_y + 0.09, "Adaptive EWMA and causal filters prevent\nhallucination during macro rate shocks.", fontsize=7.6, color='#A3A3A3', linespacing=1.28, transform=ax_bot.transAxes)


# Save template
plt.savefig('assets/tech_slide_base.png', dpi=100, facecolor='#000000')
plt.close()

# Composite with PIL:
canvas = Image.open('assets/tech_slide_base.png').convert('RGBA')

# Source image with authentic logos
orig = Image.open('assets/aegisflow_technical_approach_pure_black.jpg').convert('RGBA')

# 1. Crop sidebar tiles:
sidebar = orig.crop((18, 135, 292, 750))
sidebar_resized = sidebar.resize((375, 840), Image.Resampling.LANCZOS)
canvas.paste(sidebar_resized, (50, 115))

# 2. Crop 4-stage pipeline including full top and bottom loop arrows:
# Exactly y=112 to y=600 to capture both loop lines completely
pipeline = orig.crop((305, 112, 1355, 600))
pipeline_resized = pipeline.resize((1380, 485), Image.Resampling.LANCZOS)
canvas.paste(pipeline_resized, (470, 75))

# Save finalized pure black 1920x1080 slide
canvas_rgb = canvas.convert('RGB')
canvas_rgb.save('assets/aegisflow_technical_approach_with_math.jpg', quality=96)
canvas_rgb.save('assets/aegisflow_technical_approach_with_math.png')

# Also copy to brain artifact directory
canvas_rgb.save('/home/idioticspaceman/.gemini/antigravity-cli/brain/98d405f9-01a1-449c-91dc-21e4f690d2c7/aegisflow_technical_approach_with_math.jpg', quality=96)

print("Successfully regenerated assets/aegisflow_technical_approach_with_math.jpg with perfected layout!")
