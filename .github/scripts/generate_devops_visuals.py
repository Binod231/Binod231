#!/usr/bin/env python3
"""
Generates three self-contained, animated SVGs for Binod231's GitHub Profile:
  1. assets/devops-3d-banner.svg        - Terminal HUD + 3D dot-matrix portrait + 3D isometric cluster
  2. assets/3d-isometric-contrib.svg   - 3D Isometric Contribution Skyline from live GitHub data
  3. assets/devops-arcade-game.svg     - Gamified DevOps Terminal Invaders over real contribution grid
"""

import html
import math
import os
import re
import urllib.request
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps

USERNAME = os.environ.get("GITHUB_USERNAME", "Binod231")
ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def fetch_contributions(username: str):
    """Fetch contribution grid (weeks x 7 days) and total count from GitHub."""
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; DevOpsProfileBot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="ignore")

    total_match = re.search(r"([\d,]+)\s+contributions\s+in the last year", body)
    total_str = total_match.group(1) if total_match else "1,250"

    # Extract tooltips: id -> count
    tooltip_counts = {}
    for m in re.finditer(
        r'for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]+)</tool-tip>',
        body,
    ):
        comp_id, text = m.group(1), m.group(2)
        num_m = re.search(r"(\d+)\s+contribution", text)
        tooltip_counts[comp_id] = int(num_m.group(1)) if num_m else 0

    # Extract cells
    grid = {}  # (col, row) -> (level, count, date)
    max_col = 0
    for m in re.finditer(
        r'<td[^>]*data-date="([^"]+)"[^>]*id="(contribution-day-component-(\d+)-(\d+))"[^>]*data-level="(\d)"',
        body,
    ):
        date_str = m.group(1)
        comp_id = m.group(2)
        row = int(m.group(3))
        col = int(m.group(4))
        level = int(m.group(5))
        count = tooltip_counts.get(comp_id, level * 3)
        grid[(col, row)] = (level, count, date_str)
        if col > max_col:
            max_col = col

    weeks = []
    for c in range(max_col + 1):
        week = []
        for r in range(7):
            week.append(grid.get((c, r), (0, 0, "")))
        weeks.append(week)

    return total_str, weeks


def build_dot_matrix_portrait(img_path: Path, cx: int, cy: int, radius: int = 86) -> str:
    """Convert profile photo into a glowing 3D cyber halftone dot-matrix portrait."""
    if not img_path.exists():
        return ""

    im = Image.open(img_path).convert("L")
    # Center-crop square focusing slightly toward top for face
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = max(0, int((h - side) * 0.2))
    im = im.crop((left, top, left + side, top + side))
    im = ImageOps.autocontrast(im, cutoff=2)
    im = ImageEnhance.Contrast(im).enhance(1.35)

    grid_n = 28
    im = im.resize((grid_n, grid_n), Image.Resampling.LANCZOS)
    px = im.load()

    dots = []
    step = (radius * 1.85) / grid_n
    start_x = cx - (grid_n - 1) * step / 2
    start_y = cy - (grid_n - 1) * step / 2

    for gy in range(grid_n):
        for gx in range(grid_n):
            dx = (gx - (grid_n - 1) / 2) / (grid_n / 2)
            dy = (gy - (grid_n - 1) / 2) / (grid_n / 2)
            dist = math.hypot(dx, dy)
            if dist > 0.96:
                continue

            val = px[gx, gy] / 255.0  # 0=dark, 1=bright
            # Subtle 3D spherical bulge near center
            sphere_boost = math.sqrt(max(0.0, 1.0 - dist * dist))
            r_dot = (0.55 + val * 2.15) * (0.78 + 0.25 * sphere_boost)
            if r_dot < 0.72:
                continue

            x = start_x + gx * step
            y = start_y + gy * step
            if val > 0.78:
                color = "#e0f2fe"
                opacity = f"{0.85 + 0.15 * sphere_boost:.2f}"
            elif val > 0.48:
                color = "#38bdf8"
                opacity = f"{0.65 + 0.25 * sphere_boost:.2f}"
            elif val > 0.25:
                color = "#0ea5e9"
                opacity = f"{0.45 + 0.25 * sphere_boost:.2f}"
            else:
                color = "#10b981"
                opacity = "0.32"

            dots.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_dot:.2f}" fill="{color}" opacity="{opacity}"/>'
            )

    return "\n      ".join(dots)


def generate_banner(total_str: str):
    portrait_dots = build_dot_matrix_portrait(ASSETS_DIR / "profile.jpeg", cx=150, cy=182, radius=88)

    # Orbital tech nodes around portrait
    orbit_labels = [
        (56, 128, "AWS", "#f59e0b"),
        (246, 128, "K8S", "#38bdf8"),
        (56, 236, "OPS", "#10b981"),
        (246, 236, "AI", "#a78bfa"),
    ]
    orbit_nodes = []
    for ox, oy, lbl, col in orbit_labels:
        orbit_nodes.append(
            f'<g class="pulse-slow">'
            f'<circle cx="{ox}" cy="{oy}" r="14" fill="#09111f" stroke="{col}" stroke-width="1.3"/>'
            f'<text x="{ox}" y="{oy+3.5}" text-anchor="middle" font-family="monospace" font-size="8.5" font-weight="bold" fill="{col}">{lbl}</text>'
            f"</g>"
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 340" width="100%" height="340">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#050811"/>
      <stop offset="50%" stop-color="#0b1324"/>
      <stop offset="100%" stop-color="#050811"/>
    </linearGradient>
    <linearGradient id="neonBar" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="50%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#8b5cf6"/>
    </linearGradient>
    <linearGradient id="awsTop" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fbbf24"/>
      <stop offset="100%" stop-color="#ea580c"/>
    </linearGradient>
    <linearGradient id="cyanTop" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#67e8f9"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
    <pattern id="cyberGrid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#162238" stroke-width="0.7"/>
    </pattern>
    <filter id="neonGlow" x="-25%" y="-25%" width="150%" height="150%">
      <feGaussianBlur stdDeviation="3.5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <style>
    @keyframes floatA {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-9px); }} }}
    @keyframes floatB {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(7px); }} }}
    @keyframes pulseSlow {{ 0%, 100% {{ opacity: 0.55; }} 50% {{ opacity: 1; }} }}
    @keyframes spinRing {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
    @keyframes spinRev {{ from {{ transform: rotate(360deg); }} to {{ transform: rotate(0deg); }} }}
    @keyframes dashFlow {{ to {{ stroke-dashoffset: -44; }} }}
    @keyframes scanY {{ 0% {{ transform: translateY(62px); opacity: 0.15; }} 50% {{ opacity: 0.45; }} 100% {{ transform: translateY(310px); opacity: 0.05; }} }}
    .float-a {{ animation: floatA 4.2s ease-in-out infinite; }}
    .float-b {{ animation: floatB 5.0s ease-in-out infinite; }}
    .pulse-slow {{ animation: pulseSlow 2.6s ease-in-out infinite; }}
    .spin-ring {{ transform-origin: 150px 182px; animation: spinRing 26s linear infinite; }}
    .spin-rev {{ transform-origin: 150px 182px; animation: spinRev 18s linear infinite; }}
    .data-line {{ stroke-dasharray: 6 5; animation: dashFlow 1.5s linear infinite; }}
    .scanline {{ animation: scanY 4.5s linear infinite; }}
  </style>

  <!-- Base Frame -->
  <rect width="1200" height="340" rx="14" fill="url(#bgGrad)" stroke="#1e293b" stroke-width="1.5"/>
  <rect width="1200" height="340" rx="14" fill="url(#cyberGrid)"/>

  <!-- Ambient Glows -->
  <circle cx="150" cy="182" r="120" fill="#0ea5e9" opacity="0.09"/>
  <circle cx="1010" cy="185" r="145" fill="#10b981" opacity="0.06"/>

  <!-- Animated Scanline -->
  <rect x="20" y="0" width="1160" height="2" fill="url(#neonBar)" opacity="0.25" class="scanline"/>

  <!-- Terminal Header Bar -->
  <rect x="20" y="16" width="1160" height="34" rx="8" fill="#09111f" stroke="#1e293b" stroke-width="1"/>
  <circle cx="40" cy="33" r="5.5" fill="#ef4444"/>
  <circle cx="58" cy="33" r="5.5" fill="#f59e0b"/>
  <circle cx="76" cy="33" r="5.5" fill="#10b981"/>
  <text x="98" y="37" font-family="monospace" font-size="12.5" fill="#34d399" font-weight="bold">root@binod-cloud:~#</text>
  <text x="248" y="37" font-family="monospace" font-size="12.5" fill="#cbd5e1">./boot_devops_hud.sh --profile=dot3d --gamify=on --sla=99.9</text>
  <rect x="978" y="23" width="190" height="20" rx="10" fill="#052e16" stroke="#10b981" stroke-width="0.9"/>
  <circle cx="992" cy="33" r="3.5" fill="#34d399" class="pulse-slow"/>
  <text x="1003" y="37" font-family="monospace" font-size="10.5" fill="#6ee7b7" font-weight="bold">99.9% SLA | {html.escape(total_str)} COMMITS</text>

  <!-- LEFT: 3D Holographic Dot-Matrix Portrait -->
  <g>
    <circle cx="150" cy="182" r="102" fill="none" stroke="#1e293b" stroke-width="1.2"/>
    <circle cx="150" cy="182" r="98" fill="none" stroke="#38bdf8" stroke-width="1.3" stroke-dasharray="14 8 4 8" class="spin-ring"/>
    <circle cx="150" cy="182" r="91" fill="none" stroke="#10b981" stroke-width="0.9" stroke-dasharray="6 10" class="spin-rev"/>
    <circle cx="150" cy="182" r="87" fill="#040812" opacity="0.85"/>
    <g filter="url(#neonGlow)">
      {portrait_dots}
    </g>
    {"".join(orbit_nodes)}
    <rect x="88" y="286" width="124" height="20" rx="5" fill="#09111f" stroke="#38bdf8" stroke-width="0.9"/>
    <text x="150" y="299.5" text-anchor="middle" font-family="monospace" font-size="10" fill="#38bdf8" font-weight="bold">HOLO_ID // BINOD231</text>
  </g>

  <!-- CENTER: Operator Identity & Telemetry -->
  <g transform="translate(292, 82)">
    <text x="0" y="16" font-family="monospace" font-size="12" fill="#10b981" font-weight="bold">[ SYSTEM AUTHENTICATED // DEVOPS_ARCHITECT_LV99 ]</text>
    <text x="0" y="58" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="40" font-weight="800" fill="#f8fafc" letter-spacing="-0.6">Binod Prasad Joshi</text>
    <rect x="0" y="70" width="440" height="3" rx="1.5" fill="url(#neonBar)"/>

    <text x="0" y="99" font-family="monospace" font-size="14" font-weight="bold" fill="#38bdf8">Cloud &amp; DevOps Consultant | 2x AWS Certified | AWS Community Builder</text>

    <text x="0" y="128" font-family="monospace" font-size="12.5" fill="#94a3b8">&gt; Multi-AZ AWS VPC, ECS Fargate &amp; Private Cloud Infrastructure</text>
    <text x="0" y="148" font-family="monospace" font-size="12.5" fill="#94a3b8">&gt; GitHub Actions CI/CD, Docker, FinOps Optimization &amp; DevSecOps</text>
    <text x="0" y="168" font-family="monospace" font-size="12.5" fill="#94a3b8">&gt; Enterprise ERP (Odoo), Prometheus/Grafana &amp; Bedrock RAG Ops</text>

    <!-- Terminal Stat Pills -->
    <g transform="translate(0, 192)">
      <rect x="0" y="0" width="158" height="32" rx="6" fill="#09111f" stroke="#38bdf8" stroke-width="1"/>
      <circle cx="14" cy="16" r="3.5" fill="#38bdf8" class="pulse-slow"/>
      <text x="25" y="20" font-family="monospace" font-size="11.5" fill="#e0f2fe" font-weight="bold">~50% FASTER CI/CD</text>

      <rect x="168" y="0" width="162" height="32" rx="6" fill="#09111f" stroke="#10b981" stroke-width="1"/>
      <circle cx="182" cy="16" r="3.5" fill="#10b981" class="pulse-slow"/>
      <text x="193" y="20" font-family="monospace" font-size="11.5" fill="#d1fae5" font-weight="bold">~30% FINOPS SAVED</text>

      <rect x="340" y="0" width="166" height="32" rx="6" fill="#09111f" stroke="#f59e0b" stroke-width="1"/>
      <circle cx="354" cy="16" r="3.5" fill="#f59e0b" class="pulse-slow"/>
      <text x="365" y="20" font-family="monospace" font-size="11.5" fill="#fef3c7" font-weight="bold">95% OAUTH2 SPEEDUP</text>
    </g>
  </g>

  <!-- RIGHT: 3D Isometric Cloud Mesh -->
  <g transform="translate(835, 76)">
    <!-- Isometric Platform -->
    <polygon points="175,215 335,135 175,55 15,135" fill="#08101e" stroke="#1e293b" stroke-width="1.5"/>
    <polygon points="175,200 305,135 175,70 45,135" fill="none" stroke="#38bdf8" stroke-width="0.7" opacity="0.4"/>

    <!-- Animated Data Streams -->
    <line x1="95" y1="145" x2="175" y2="108" stroke="#38bdf8" stroke-width="2" class="data-line"/>
    <line x1="175" y1="108" x2="255" y2="145" stroke="#a78bfa" stroke-width="2" class="data-line"/>
    <line x1="175" y1="108" x2="175" y2="175" stroke="#10b981" stroke-width="2" class="data-line"/>
    <line x1="95" y1="145" x2="175" y2="175" stroke="#f59e0b" stroke-width="1.4" class="data-line"/>
    <line x1="255" y1="145" x2="175" y2="175" stroke="#f59e0b" stroke-width="1.4" class="data-line"/>

    <!-- Center 3D Cube: AWS Core -->
    <g class="float-a" filter="url(#neonGlow)">
      <polygon points="175,52 218,73 175,94 132,73" fill="url(#awsTop)"/>
      <polygon points="132,73 175,94 175,138 132,117" fill="#c2410c"/>
      <polygon points="218,73 175,94 175,138 218,117" fill="#9a3412"/>
      <text x="175" y="77" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="#fff">AWS</text>
    </g>

    <!-- Left 3D Cube: ECS / Docker -->
    <g class="float-b">
      <polygon points="90,115 123,131 90,147 57,131" fill="url(#cyanTop)"/>
      <polygon points="57,131 90,147 90,181 57,165" fill="#0369a1"/>
      <polygon points="123,131 90,147 90,181 123,165" fill="#0c4a6e"/>
      <text x="90" y="135" text-anchor="middle" font-family="monospace" font-size="9.5" font-weight="bold" fill="#fff">ECS</text>
    </g>

    <!-- Right 3D Cube: CI/CD -->
    <g class="float-b">
      <polygon points="260,115 293,131 260,147 227,131" fill="#a78bfa"/>
      <polygon points="227,131 260,147 260,181 227,165" fill="#6d28d9"/>
      <polygon points="293,131 260,147 260,181 293,165" fill="#4c1d95"/>
      <text x="260" y="135" text-anchor="middle" font-family="monospace" font-size="9.5" font-weight="bold" fill="#fff">CI/CD</text>
    </g>

    <!-- Front 3D Cube: RAG / OPS -->
    <g class="float-a">
      <polygon points="175,162 206,177 175,192 144,177" fill="#34d399"/>
      <polygon points="144,177 175,192 175,222 144,207" fill="#059669"/>
      <polygon points="206,177 175,192 175,222 206,207" fill="#064e3b"/>
      <text x="175" y="180" text-anchor="middle" font-family="monospace" font-size="9" font-weight="bold" fill="#fff">OPS</text>
    </g>
  </g>
</svg>
"""
    (ASSETS_DIR / "devops-3d-banner.svg").write_text(svg, encoding="utf-8")


def generate_3d_isometric_contrib(total_str: str, weeks: list):
    """Render Binod's real contribution grid as a glowing 3D isometric skyline."""
    num_weeks = len(weeks)
    max_count = max(
        (day[1] for w in weeks for day in w),
        default=1,
    )
    max_count = max(max_count, 1)

    # Isometric projection parameters
    dx = 9.6
    dy = 4.9
    origin_x = 120
    origin_y = 225

    bars = []
    # Painter's algorithm: back-to-front (col + row ascending)
    cells = []
    for c in range(num_weeks):
        for r in range(7):
            level, count, date_str = weeks[c][r]
            cells.append((c + r, c, r, level, count, date_str))
    cells.sort(key=lambda item: (item[0], item[1]))

    palette = {
        0: ("#172033", "#0f172a", "#090f1d"),
        1: ("#0e7490", "#155e75", "#083344"),
        2: ("#06b6d4", "#0284c7", "#075985"),
        3: ("#34d399", "#059669", "#065f46"),
        4: ("#fbbf24", "#d97706", "#92400e"),
    }

    for _, c, r, level, count, _ in cells:
        # Isometric center base
        bx = origin_x + c * dx + r * dx * 1.15
        by = origin_y - c * dy * 0.48 + r * dy * 1.35

        if count == 0:
            h = 3.0
        else:
            # Smooth log-scaled height up to 88px
            h = 8.0 + 78.0 * (math.log1p(count) / math.log1p(max_count))

        top_c, left_c, right_c = palette.get(level, palette[1])
        w = 8.4
        d = 4.3

        # Top diamond shifted up by h
        p_top = f"{bx:.1f},{by-h-d:.1f} {bx+w:.1f},{by-h:.1f} {bx:.1f},{by-h+d:.1f} {bx-w:.1f},{by-h:.1f}"
        p_left = f"{bx-w:.1f},{by-h:.1f} {bx:.1f},{by-h+d:.1f} {bx:.1f},{by+d:.1f} {bx-w:.1f},{by:.1f}"
        p_right = f"{bx+w:.1f},{by-h:.1f} {bx:.1f},{by-h+d:.1f} {bx:.1f},{by+d:.1f} {bx+w:.1f},{by:.1f}"

        glow_cls = ' class="peak"' if level >= 4 else ""
        bars.append(
            f'<g{glow_cls}>'
            f'<polygon points="{p_left}" fill="{left_c}" stroke="#050811" stroke-width="0.35"/>'
            f'<polygon points="{p_right}" fill="{right_c}" stroke="#050811" stroke-width="0.35"/>'
            f'<polygon points="{p_top}" fill="{top_c}" stroke="#050811" stroke-width="0.35"/>'
            f"</g>"
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 400" width="100%" height="400">
  <defs>
    <linearGradient id="skyBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#050811"/>
      <stop offset="100%" stop-color="#0a1324"/>
    </linearGradient>
    <pattern id="isoGrid" width="28" height="28" patternUnits="userSpaceOnUse">
      <path d="M 28 0 L 0 0 0 28" fill="none" stroke="#132038" stroke-width="0.6"/>
    </pattern>
  </defs>
  <style>
    @keyframes peakPulse {{ 0%, 100% {{ opacity: 0.92; }} 50% {{ opacity: 1; }} }}
    .peak {{ animation: peakPulse 2.4s ease-in-out infinite; }}
  </style>

  <rect width="1120" height="400" rx="14" fill="url(#skyBg)" stroke="#1e293b" stroke-width="1.5"/>
  <rect width="1120" height="400" rx="14" fill="url(#isoGrid)"/>

  <!-- Terminal Header -->
  <rect x="20" y="16" width="1080" height="32" rx="8" fill="#09111f" stroke="#1e293b"/>
  <text x="36" y="36" font-family="monospace" font-size="12" fill="#38bdf8" font-weight="bold">3D_CONTRIB_SKYLINE // USER: {html.escape(USERNAME)} // 365D_TOTAL: {html.escape(total_str)} // PEAK_DAY: {max_count} COMMITS</text>

  <!-- Legend -->
  <g transform="translate(830, 24)">
    <rect x="0" y="2" width="12" height="12" rx="2" fill="#172033"/>
    <rect x="22" y="2" width="12" height="12" rx="2" fill="#0e7490"/>
    <rect x="44" y="2" width="12" height="12" rx="2" fill="#06b6d4"/>
    <rect x="66" y="2" width="12" height="12" rx="2" fill="#34d399"/>
    <rect x="88" y="2" width="12" height="12" rx="2" fill="#fbbf24"/>
    <text x="112" y="12" font-family="monospace" font-size="10.5" fill="#94a3b8">LOW -&gt; PEAK</text>
  </g>

  <!-- 3D Bars -->
  <g transform="translate(180, 62)">
    {"".join(bars)}
  </g>

  <text x="36" y="380" font-family="monospace" font-size="11" fill="#64748b">[RENDERED FROM LIVE GITHUB CONTRIBUTION MATRIX :: AUTO-SYNCED DAILY VIA GITHUB ACTIONS]</text>
</svg>
"""
    (ASSETS_DIR / "3d-isometric-contrib.svg").write_text(svg, encoding="utf-8")


def generate_arcade_game(total_str: str, weeks: list):
    """Render an animated DevOps Terminal Invaders game across the real contribution grid."""
    num_weeks = min(len(weeks), 53)
    cell_size = 15
    gap = 4
    step = cell_size + gap
    grid_x0 = 56
    grid_y0 = 86

    grid_rects = []
    level_colors = {
        0: "#111827",
        1: "#0e4429",
        2: "#006d32",
        3: "#26a641",
        4: "#39d353",
    }

    for c in range(num_weeks):
        for r in range(7):
            level, _, _ = weeks[c][r]
            x = grid_x0 + c * step
            y = grid_y0 + r * step
            col = level_colors.get(level, "#111827")
            grid_rects.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="3" fill="{col}" stroke="#0b1220" stroke-width="0.8"/>'
            )

    # Enemy bug nodes ("CVE", "502", "OOM", "LAG") targeted by laser beams
    targets = [
        (grid_x0 + 8 * step, grid_y0 + 1 * step, "CVE", "#ef4444", "0s"),
        (grid_x0 + 21 * step, grid_y0 + 2 * step, "502", "#f59e0b", "1.1s"),
        (grid_x0 + 34 * step, grid_y0 + 1 * step, "OOM", "#ec4899", "2.2s"),
        (grid_x0 + 46 * step, grid_y0 + 3 * step, "LAG", "#a855f7", "3.3s"),
    ]
    bug_elements = []
    for bx, by, tag, col, delay in targets:
        bug_elements.append(
            f'<g class="bug-pulse" style="animation-delay:{delay}">'
            f'<rect x="{bx-3}" y="{by-3}" width="21" height="21" rx="4" fill="#090d16" stroke="{col}" stroke-width="1.4"/>'
            f'<text x="{bx+7.5}" y="{by+10.5}" text-anchor="middle" font-family="monospace" font-size="7.5" font-weight="bold" fill="{col}">{tag}</text>'
            f"</g>"
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 330" width="100%" height="330">
  <defs>
    <linearGradient id="arcBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#04070e"/>
      <stop offset="100%" stop-color="#0a101d"/>
    </linearGradient>
  </defs>
  <style>
    @keyframes patrol {{
      0%   {{ transform: translateX(0px); }}
      25%  {{ transform: translateX(260px); }}
      50%  {{ transform: translateX(520px); }}
      75%  {{ transform: translateX(760px); }}
      100% {{ transform: translateX(0px); }}
    }}
    @keyframes fireLaser {{
      0%   {{ transform: translateY(0px); opacity: 1; }}
      80%  {{ transform: translateY(-138px); opacity: 0.95; }}
      100% {{ transform: translateY(-148px); opacity: 0; }}
    }}
    @keyframes bugPulse {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.45; }}
    }}
    .ship-patrol {{ animation: patrol 9s ease-in-out infinite; }}
    .laser-beam {{ animation: fireLaser 0.9s linear infinite; }}
    .bug-pulse {{ animation: bugPulse 1.8s ease-in-out infinite; }}
  </style>

  <!-- Terminal Arcade Cabinet -->
  <rect width="1120" height="330" rx="14" fill="url(#arcBg)" stroke="#1e293b" stroke-width="1.5"/>

  <!-- Top Arcade HUD -->
  <rect x="20" y="16" width="1080" height="36" rx="8" fill="#09111f" stroke="#10b981" stroke-width="1"/>
  <text x="36" y="38" font-family="monospace" font-size="13" font-weight="bold" fill="#34d399">DEVOPS_DEFENDER.SH</text>
  <text x="230" y="38" font-family="monospace" font-size="12" fill="#38bdf8">PLAYER: {html.escape(USERNAME)}</text>
  <text x="415" y="38" font-family="monospace" font-size="12" fill="#fbbf24">XP: {html.escape(total_str)}</text>
  <text x="550" y="38" font-family="monospace" font-size="12" fill="#e2e8f0">SHIELD: [||||||||||] 99.9% SLA</text>
  <text x="860" y="38" font-family="monospace" font-size="11.5" fill="#10b981">[LIVE_COMMIT_MATRIX]</text>

  <!-- Contribution Matrix Arena -->
  <rect x="38" y="68" width="1044" height="214" rx="10" fill="#050912" stroke="#1e293b"/>
  {"".join(grid_rects)}
  {"".join(bug_elements)}

  <!-- Animated DevOps Defender Ship & Laser -->
  <g transform="translate(135, 245)">
    <g class="ship-patrol">
      <!-- Laser -->
      <rect x="13" y="-22" width="4" height="16" rx="2" fill="#38bdf8" class="laser-beam"/>
      <!-- Cyber Defender Ship -->
      <polygon points="15,0 30,18 22,18 22,23 8,23 8,18 0,18" fill="#38bdf8"/>
      <polygon points="15,4 22,16 8,16" fill="#e0f2fe"/>
      <rect x="11" y="23" width="8" height="4" rx="1" fill="#10b981"/>
    </g>
  </g>

  <!-- Bottom Arcade Ticker -->
  <text x="40" y="308" font-family="monospace" font-size="11.5" fill="#94a3b8">&gt; [MISSION_LOG] Mitigated OAuth2 Latency (+95% Speed) | Pruned OpenSearch (-30% Cost) | Zero-Downtime ECS Rollouts [OK]</text>
</svg>
"""
    (ASSETS_DIR / "devops-arcade-game.svg").write_text(svg, encoding="utf-8")


def main():
    try:
        total_str, weeks = fetch_contributions(USERNAME)
    except Exception as exc:
        print(f"Warning: failed to fetch live contributions ({exc}); using fallback grid")
        total_str = "1,250"
        weeks = [[((c + r) % 5, ((c * 3 + r) % 12), "") for r in range(7)] for c in range(53)]

    generate_banner(total_str)
    generate_3d_isometric_contrib(total_str, weeks)
    generate_arcade_game(total_str, weeks)
    print(f"Generated SVGs for {USERNAME} ({total_str} contributions)")


if __name__ == "__main__":
    main()
