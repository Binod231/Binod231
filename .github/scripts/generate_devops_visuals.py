#!/usr/bin/env python3
"""
Generates live, self-contained visuals for Binod231's GitHub Profile:
  1. assets/avatar-circle.png          - Circular headshot with glowing cyber rings
  2. assets/ubuntu-terminal-profile.svg - Authentic Ubuntu GNOME Terminal outer window + live metrics + 3D dot portrait + 3D cubes
  3. assets/3d-isometric-contrib.svg   - 3D Isometric Contribution Skyline from live GitHub data
  4. assets/devops-racer-preview.svg   - AWS DevOps 3D Highway Racer preview inside Ubuntu terminal frame
"""

import datetime
import html
import json
import math
import os
import re
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

USERNAME = os.environ.get("GITHUB_USERNAME", "Binod231")
ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def fetch_github_stats(username: str):
    """Fetch public repo count, follower count, and contribution grid from GitHub."""
    repos, followers = 45, 3
    try:
        req = urllib.request.Request(
            f"https://api.github.com/users/{username}",
            headers={"User-Agent": "DevOpsProfileBot/2.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            repos = data.get("public_repos", repos)
            followers = data.get("followers", followers)
    except Exception as exc:
        print(f"Warning: user API fetch failed ({exc})")

    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; DevOpsProfileBot/2.0)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="ignore")

    total_match = re.search(r"([\d,]+)\s+contributions\s+in the last year", body)
    total_str = total_match.group(1) if total_match else "1,255"

    tooltip_counts = {}
    for m in re.finditer(
        r'for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]+)</tool-tip>',
        body,
    ):
        comp_id, text = m.group(1), m.group(2)
        num_m = re.search(r"(\d+)\s+contribution", text)
        tooltip_counts[comp_id] = int(num_m.group(1)) if num_m else 0

    grid = {}
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
        weeks.append([grid.get((c, r), (0, 0, "")) for r in range(7)])

    return repos, followers, total_str, weeks


def generate_circular_avatar(img_path: Path):
    """Create a transparent circular PNG avatar with Ubuntu/cyber rings."""
    if not img_path.exists():
        return
    size = 280
    im = Image.open(img_path).convert("RGBA")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = max(0, int((h - side) * 0.08))
    im = im.crop((left, top, left + side, top + side)).resize((size - 16, size - 16), Image.Resampling.LANCZOS)

    mask = Image.new("L", (size - 16, size - 16), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 17, size - 17), fill=255)
    im.putalpha(mask)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((2, 2, size - 3, size - 3), outline=(138, 226, 52, 220), width=3)
    draw.ellipse((6, 6, size - 7, size - 7), outline=(56, 189, 248, 200), width=2)
    canvas.paste(im, (8, 8), im)
    canvas.save(ASSETS_DIR / "avatar-circle.png", "PNG")


def build_dot_matrix_portrait(img_path: Path, cx: int, cy: int, radius: int = 66) -> str:
    """Convert studio headshot into a crisp 3D halftone dot-matrix portrait."""
    if not img_path.exists():
        return ""

    im = Image.open(img_path).convert("L")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = max(0, int((h - side) * 0.06))
    im = im.crop((left, top, left + side, top + side))

    grid_n = 28
    gray = im.resize((grid_n, grid_n), Image.Resampling.LANCZOS)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    px = gray.load()
    epx = edges.load()

    dots = []
    step = (radius * 1.82) / grid_n
    start_x = cx - (grid_n - 1) * step / 2
    start_y = cy - (grid_n - 1) * step / 2

    for gy in range(grid_n):
        for gx in range(grid_n):
            dx = (gx - (grid_n - 1) / 2) / (grid_n / 2)
            dy = (gy - (grid_n - 1) / 2) / (grid_n / 2)
            dist = math.hypot(dx, dy)
            if dist > 0.96:
                continue

            raw = px[gx, gy]
            edge = epx[gx, gy] / 255.0
            if raw > 218 and edge < 0.25:
                continue

            lum = raw / 255.0
            sphere = math.sqrt(max(0.0, 1.0 - dist * dist))
            intensity = min(1.0, max(0.18, (1.0 - lum) * 0.55 + edge * 0.85 + (0.35 if 0.28 < lum < 0.82 else 0.0)))
            r_dot = (0.85 + intensity * 2.15) * (0.82 + 0.22 * sphere)

            x = start_x + gx * step
            y = start_y + gy * step
            if edge > 0.35 or (0.42 < lum < 0.80):
                color = "#eeeeec" if edge > 0.45 else "#8ae234"
                opacity = f"{min(1.0, 0.65 + intensity * 0.35):.2f}"
            elif lum <= 0.42:
                color = "#38bdf8"
                opacity = "0.78"
            else:
                color = "#4e9a06"
                opacity = "0.55"

            dots.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_dot:.2f}" fill="{color}" opacity="{opacity}"/>'
            )

    return "\n      ".join(dots)


def generate_ubuntu_terminal(repos: int, followers: int, total_str: str, weeks: list):
    """Generate authentic Ubuntu GNOME Terminal outer window with live stats, inline graph, and fitted dot-matrix portrait."""
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y, %H:%M:%S UTC")
    portrait_dots = build_dot_matrix_portrait(ASSETS_DIR / "profile.jpeg", cx=980, cy=206, radius=106)

    # Build inline contribution intensity strip (last 20 weeks) like lowlighter metrics '#' blocks
    recent = weeks[-20:] if len(weeks) >= 20 else weeks
    hash_spans = []
    level_cols = {0: "#555753", 1: "#4e9a06", 2: "#73d216", 3: "#8ae234", 4: "#38bdf8"}
    for w in recent:
        peak = max(day[0] for day in w)
        col = level_cols.get(peak, "#555753")
        hash_spans.append(f'<tspan fill="{col}">#</tspan>')
    inline_graph = "".join(hash_spans)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 400" width="100%" height="400">
  <defs>
    <linearGradient id="ubuBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#300a24"/>
      <stop offset="100%" stop-color="#22071a"/>
    </linearGradient>
    <linearGradient id="titleBar" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#484642"/>
      <stop offset="100%" stop-color="#2c2b29"/>
    </linearGradient>
  </defs>
  <style>
    @keyframes blink {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
    .cursor {{ animation: blink 1.1s infinite; }}
  </style>

  <!-- Ubuntu Terminal Outer Window -->
  <rect width="1160" height="400" rx="10" fill="url(#ubuBg)" stroke="#4c4a46" stroke-width="1.5"/>

  <!-- GNOME Title Bar -->
  <path d="M 10,0 L 1150,0 Q 1160,0 1160,10 L 1160,34 L 0,34 L 0,10 Q 0,0 10,0 Z" fill="url(#titleBar)"/>
  <text x="580" y="21" text-anchor="middle" font-family="system-ui, -apple-system, 'Ubuntu', sans-serif" font-size="13" font-weight="600" fill="#eeeeec">binod@aws-cloud: ~</text>

  <!-- Top-Right Ubuntu Window Controls (-, square, orange X) -->
  <g transform="translate(1082, 17)">
    <circle cx="0" cy="0" r="8" fill="#3c3b37" stroke="#555753" stroke-width="0.8"/>
    <line x1="-3.5" y1="2" x2="3.5" y2="2" stroke="#eeeeec" stroke-width="1.4"/>
    <circle cx="24" cy="0" r="8" fill="#3c3b37" stroke="#555753" stroke-width="0.8"/>
    <rect x="20.5" y="-3.5" width="7" height="7" fill="none" stroke="#eeeeec" stroke-width="1.2"/>
    <circle cx="48" cy="0" r="8.5" fill="#e95420"/>
    <line x1="44.8" y1="-3.2" x2="51.2" y2="3.2" stroke="#ffffff" stroke-width="1.5"/>
    <line x1="51.2" y1="-3.2" x2="44.8" y2="3.2" stroke="#ffffff" stroke-width="1.5"/>
  </g>

  <!-- Left Terminal Text Session -->
  <g font-family="'Ubuntu Mono', 'JetBrains Mono', monospace" font-size="14.5">
    <text x="24" y="64" fill="#d3d7cf" opacity="0.88">Binod231 DevOps Terminal OS 2026.11 LTS (AWS / Private Cloud)</text>
    <text x="24" y="84" fill="#d3d7cf" opacity="0.88">Last synced: {html.escape(now_str)} | Live GitHub Telemetry</text>

    <!-- Prompt 1: whoami -->
    <text x="24" y="118">
      <tspan fill="#8ae234" font-weight="bold">binod@aws-cloud</tspan><tspan fill="#eeeeec">:</tspan><tspan fill="#729fcf" font-weight="bold">~</tspan><tspan fill="#eeeeec">$ whoami</tspan>
    </text>
    <text x="24" y="140" fill="#eeeeec">
      <tspan font-weight="bold" fill="#ffffff">Binod Prasad Joshi</tspan> role="Cloud &amp; DevOps Consultant", guild="Glovion Consulting"
    </text>
    <text x="42" y="160" fill="#eeeeec">
      contributed to <tspan font-weight="bold" fill="#8ae234">{repos}</tspan> repositories ({html.escape(total_str)} commits/yr) {inline_graph}
    </text>
    <text x="42" y="180" fill="#eeeeec">
      verified=[<tspan fill="#fbbf24">AWS SAA-C03</tspan>, <tspan fill="#38bdf8">AWS CLF-C02</tspan>, <tspan fill="#8ae234">AWS Community Builder 2026</tspan>] | followers=<tspan font-weight="bold">{followers}</tspan>
    </text>

    <!-- Prompt 2: metrics prod -->
    <text x="24" y="214">
      <tspan fill="#8ae234" font-weight="bold">binod@aws-cloud</tspan><tspan fill="#eeeeec">:</tspan><tspan fill="#729fcf" font-weight="bold">~</tspan><tspan fill="#eeeeec">$ ./metrics.sh --prod-impact</tspan>
    </text>
    <text x="42" y="236" fill="#d3d7cf">uptime_sla=<tspan fill="#8ae234" font-weight="bold">99.9%</tspan>  cicd_speedup=<tspan fill="#38bdf8" font-weight="bold">~50%</tspan>  finops_saved=<tspan fill="#fbbf24" font-weight="bold">-30%</tspan>  oauth2_latency=<tspan fill="#8ae234" font-weight="bold">-95%</tspan></text>

    <!-- Prompt 3: help -->
    <text x="24" y="270">
      <tspan fill="#8ae234" font-weight="bold">binod@aws-cloud</tspan><tspan fill="#eeeeec">:</tspan><tspan fill="#729fcf" font-weight="bold">~</tspan><tspan fill="#eeeeec">$ help</tspan>
    </text>
    <text x="42" y="292" fill="#d3d7cf">Commands below: <tspan fill="#8ae234">whoami</tspan> | <tspan fill="#8ae234">experience</tspan> | <tspan fill="#8ae234">projects</tspan> | <tspan fill="#8ae234">stack</tspan> | <tspan fill="#8ae234">certs</tspan> | <tspan fill="#8ae234">graphs</tspan> | <tspan fill="#e95420" font-weight="bold">play (AWS Racer)</tspan></text>

    <!-- Prompt 4: live cursor -->
    <text x="24" y="330">
      <tspan fill="#8ae234" font-weight="bold">binod@aws-cloud</tspan><tspan fill="#eeeeec">:</tspan><tspan fill="#729fcf" font-weight="bold">~</tspan><tspan fill="#eeeeec">$ ./run_all_modules.sh --interactive </tspan><tspan fill="#8ae234" class="cursor">&#9608;</tspan>
    </text>

    <text x="24" y="376" fill="#ad7fa8">Connection established with Binod231 (Kathmandu, Nepal / UTC+5:45)</text>
  </g>

  <!-- Right Rectangle inside Ubuntu Terminal: Fitted 3D Dot-Matrix Headshot -->
  <g>
    <rect x="822" y="52" width="316" height="328" rx="10" fill="#1e0617" stroke="#5c3566" stroke-width="1"/>
    <text x="980" y="76" text-anchor="middle" font-family="monospace" font-size="11.5" fill="#8ae234" font-weight="bold">[3D_HOLO_ID // BINOD231]</text>

    <circle cx="980" cy="206" r="115" fill="none" stroke="#8ae234" stroke-width="1.3" stroke-dasharray="10 6"/>
    <circle cx="980" cy="206" r="109" fill="none" stroke="#38bdf8" stroke-width="0.9" opacity="0.6"/>
    {portrait_dots}

    <text x="980" y="352" text-anchor="middle" font-family="monospace" font-size="11.5" fill="#eeeeec" font-weight="bold">Kathmandu, Nepal</text>
    <text x="980" y="368" text-anchor="middle" font-family="monospace" font-size="10.5" fill="#ad7fa8">UTC+5:45 | Remote-Ready</text>
  </g>
</svg>
"""
    (ASSETS_DIR / "ubuntu-terminal-profile.svg").write_text(svg, encoding="utf-8")


def generate_3d_isometric_contrib(total_str: str, weeks: list):
    """Render live contributions as a 3D Isometric Skyline framed inside an Ubuntu Terminal window."""
    num_weeks = len(weeks)
    max_count = max((day[1] for w in weeks for day in w), default=1)
    max_count = max(max_count, 1)

    dx = 9.5
    dy = 4.8
    origin_x = 120
    origin_y = 225

    cells = []
    for c in range(num_weeks):
        for r in range(7):
            level, count, date_str = weeks[c][r]
            cells.append((c + r, c, r, level, count, date_str))
    cells.sort(key=lambda item: (item[0], item[1]))

    palette = {
        0: ("#3d1430", "#290c20", "#1c0715"),
        1: ("#4e9a06", "#3d7a05", "#295203"),
        2: ("#73d216", "#58a310", "#3c700b"),
        3: ("#38bdf8", "#0284c7", "#075985"),
        4: ("#f59e0b", "#e95420", "#9a3412"),
    }

    bars = []
    for _, c, r, level, count, _ in cells:
        bx = origin_x + c * dx + r * dx * 1.15
        by = origin_y - c * dy * 0.48 + r * dy * 1.35
        h = 3.0 if count == 0 else (8.0 + 78.0 * (math.log1p(count) / math.log1p(max_count)))
        top_c, left_c, right_c = palette.get(level, palette[1])
        w, d = 8.4, 4.3
        p_top = f"{bx:.1f},{by-h-d:.1f} {bx+w:.1f},{by-h:.1f} {bx:.1f},{by-h+d:.1f} {bx-w:.1f},{by-h:.1f}"
        p_left = f"{bx-w:.1f},{by-h:.1f} {bx:.1f},{by-h+d:.1f} {bx:.1f},{by+d:.1f} {bx-w:.1f},{by:.1f}"
        p_right = f"{bx+w:.1f},{by-h:.1f} {bx:.1f},{by-h+d:.1f} {bx:.1f},{by+d:.1f} {bx+w:.1f},{by:.1f}"
        bars.append(
            f'<g><polygon points="{p_left}" fill="{left_c}" stroke="#1a0514" stroke-width="0.35"/>'
            f'<polygon points="{p_right}" fill="{right_c}" stroke="#1a0514" stroke-width="0.35"/>'
            f'<polygon points="{p_top}" fill="{top_c}" stroke="#1a0514" stroke-width="0.35"/></g>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 400" width="100%" height="400">
  <defs>
    <linearGradient id="skyBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#300a24"/>
      <stop offset="100%" stop-color="#1e0617"/>
    </linearGradient>
    <linearGradient id="tBar" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#484642"/>
      <stop offset="100%" stop-color="#2c2b29"/>
    </linearGradient>
  </defs>
  <rect width="1120" height="400" rx="10" fill="url(#skyBg)" stroke="#4c4a46" stroke-width="1.5"/>
  <path d="M 10,0 L 1110,0 Q 1120,0 1120,10 L 1120,32 L 0,32 L 0,10 Q 0,0 10,0 Z" fill="url(#tBar)"/>
  <text x="560" y="20" text-anchor="middle" font-family="system-ui, sans-serif" font-size="12.5" font-weight="600" fill="#eeeeec">binod@aws-cloud: ~/3d-contrib-skyline</text>
  <text x="24" y="56" font-family="monospace" font-size="12.5" fill="#8ae234" font-weight="bold">binod@aws-cloud:~# ./skyline_3d --total="{html.escape(total_str)}" --peak="{max_count}"</text>

  <g transform="translate(860, 44)">
    <rect x="0" y="2" width="12" height="12" rx="2" fill="#3d1430"/>
    <rect x="20" y="2" width="12" height="12" rx="2" fill="#4e9a06"/>
    <rect x="40" y="2" width="12" height="12" rx="2" fill="#73d216"/>
    <rect x="60" y="2" width="12" height="12" rx="2" fill="#38bdf8"/>
    <rect x="80" y="2" width="12" height="12" rx="2" fill="#f59e0b"/>
    <text x="102" y="12" font-family="monospace" font-size="10.5" fill="#d3d7cf">LOW -&gt; PEAK</text>
  </g>

  <g transform="translate(180, 68)">
    {"".join(bars)}
  </g>
</svg>
"""
    (ASSETS_DIR / "3d-isometric-contrib.svg").write_text(svg, encoding="utf-8")


def generate_racer_preview():
    """Generate an Ubuntu-framed 3D AWS DevOps Racing Game preview card."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 300" width="100%" height="300">
  <defs>
    <linearGradient id="rBg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#300a24"/>
      <stop offset="60%" stop-color="#190514"/>
      <stop offset="100%" stop-color="#0d1117"/>
    </linearGradient>
    <linearGradient id="tBar2" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#484642"/>
      <stop offset="100%" stop-color="#2c2b29"/>
    </linearGradient>
    <linearGradient id="roadGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#090d16"/>
    </linearGradient>
  </defs>
  <style>
    @keyframes laneScroll { from { stroke-dashoffset: 0; } to { stroke-dashoffset: -48; } }
    @keyframes carBob { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-3px); } }
    .lane-dash { stroke-dasharray: 18 14; animation: laneScroll 0.7s linear infinite; }
    .car-bob { animation: carBob 1.2s ease-in-out infinite; }
  </style>

  <rect width="1120" height="300" rx="10" fill="url(#rBg)" stroke="#4c4a46" stroke-width="1.5"/>
  <path d="M 10,0 L 1110,0 Q 1120,0 1120,10 L 1120,32 L 0,32 L 0,10 Q 0,0 10,0 Z" fill="url(#tBar2)"/>
  <text x="560" y="20" text-anchor="middle" font-family="system-ui, sans-serif" font-size="12.5" font-weight="600" fill="#eeeeec">binod@aws-cloud: ~/aws-devops-turbo-gp</text>

  <!-- Perspective Highway -->
  <polygon points="480,105 640,105 940,295 180,295" fill="url(#roadGrad)" stroke="#38bdf8" stroke-width="2"/>
  <line x1="533" y1="105" x2="430" y2="295" stroke="#8ae234" stroke-width="2" class="lane-dash"/>
  <line x1="587" y1="105" x2="690" y2="295" stroke="#8ae234" stroke-width="2" class="lane-dash"/>

  <!-- AWS Service Boosts on Road -->
  <rect x="445" y="148" width="64" height="24" rx="5" fill="#052e16" stroke="#8ae234" stroke-width="1.5"/>
  <text x="477" y="164" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="#8ae234">AWS ECS</text>

  <rect x="615" y="176" width="64" height="24" rx="5" fill="#1e1b4b" stroke="#38bdf8" stroke-width="1.5"/>
  <text x="647" y="192" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="#38bdf8">REDIS</text>

  <rect x="700" y="220" width="64" height="24" rx="5" fill="#450a0a" stroke="#ef4444" stroke-width="1.5"/>
  <text x="732" y="236" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="#ef4444">[502 ERR]</text>

  <!-- Cyber Racer Car -->
  <g transform="translate(518, 222)" class="car-bob">
    <polygon points="42,0 68,14 78,44 6,44 16,14" fill="#0284c7" stroke="#38bdf8" stroke-width="2"/>
    <polygon points="42,6 60,18 24,18" fill="#e0f2fe"/>
    <rect x="14" y="42" width="14" height="7" rx="2" fill="#e95420"/>
    <rect x="56" y="42" width="14" height="7" rx="2" fill="#e95420"/>
  </g>

  <!-- Left Overlay Callout -->
  <text x="36" y="76" font-family="monospace" font-size="14" font-weight="bold" fill="#8ae234">binod@aws-cloud:~$ ./play_aws_racer.sh</text>
  <text x="36" y="108" font-family="system-ui, sans-serif" font-size="26" font-weight="800" fill="#ffffff">AWS_TURBO_GP</text>
  <text x="36" y="134" font-family="monospace" font-size="12.5" fill="#d3d7cf">3D Highway Racer + Live Ubuntu Terminal</text>
  <text x="36" y="162" font-family="monospace" font-size="12" fill="#8ae234">&gt; Collect [ECS], [REDIS], [WAF], [LAMBDA]</text>
  <text x="36" y="182" font-family="monospace" font-size="12" fill="#f59e0b">&gt; Dodge [502], [OOM], [CVE], [DDOS]</text>
  <rect x="36" y="208" width="236" height="36" rx="8" fill="#e95420"/>
  <text x="154" y="230" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#ffffff">[ CLICK TO PLAY NOW ]</text>
</svg>
"""
    (ASSETS_DIR / "devops-racer-preview.svg").write_text(svg, encoding="utf-8")


def main():
    repos, followers, total_str, weeks = fetch_github_stats(USERNAME)
    generate_circular_avatar(ASSETS_DIR / "profile.jpeg")
    generate_ubuntu_terminal(repos, followers, total_str, weeks)
    generate_3d_isometric_contrib(total_str, weeks)
    generate_racer_preview()
    print(f"Generated Ubuntu Terminal + 3D Skyline + AWS Racer SVGs for {USERNAME} ({total_str} commits, {repos} repos)")


if __name__ == "__main__":
    main()
