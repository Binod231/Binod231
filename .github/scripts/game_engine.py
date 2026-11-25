#!/usr/bin/env python3
"""
Playable Turn-Based DevOps Terminal RPG Engine (Issue-Ops + SVG Renderer).
Reads move commands from GitHub Issues (via env vars), updates game_state.json,
renders assets/devops-game-board.svg, and optionally comments + closes the issue.
"""

import html
import json
import os
import random
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / ".github" / "state" / "game_state.json"
SVG_PATH = ROOT / "assets" / "devops-game-board.svg"

BOSSES = [
    {
        "id": "CVE-EXPLOIT",
        "name": "Zero-Day Scanner",
        "weakness": "WAF_BLOCK",
        "color": "#ef4444",
        "atk": (10, 18),
        "hint": "Weak to WAF_BLOCK",
    },
    {
        "id": "502-STORM",
        "name": "Bad Gateway Surge",
        "weakness": "SCALE_ECS",
        "color": "#f59e0b",
        "atk": (12, 20),
        "hint": "Weak to SCALE_ECS",
    },
    {
        "id": "LATENCY-SPIKE",
        "name": "OAuth2 Bottleneck",
        "weakness": "FLUSH_REDIS",
        "color": "#a855f7",
        "atk": (10, 16),
        "hint": "Weak to FLUSH_REDIS",
    },
    {
        "id": "OOM-KILLER",
        "name": "Memory Leak Daemon",
        "weakness": "SCALE_ECS",
        "color": "#ec4899",
        "atk": (14, 22),
        "hint": "Weak to SCALE_ECS",
    },
    {
        "id": "DDOS-FLOOD",
        "name": "SYN Flood Botnet",
        "weakness": "WAF_BLOCK",
        "color": "#f97316",
        "atk": (14, 24),
        "hint": "Weak to WAF_BLOCK",
    },
]

VALID_MOVES = {"WAF_BLOCK", "SCALE_ECS", "FLUSH_REDIS", "CANARY_DEPLOY", "RESET"}


def sanitize_user(username: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_-]", "", username or "visitor")
    return clean[:24] or "visitor"


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {
        "wave": 1,
        "score": 0,
        "cluster_hp": 100,
        "max_cluster_hp": 100,
        "boss_id": "CVE-EXPLOIT",
        "boss_hp": 100,
        "max_boss_hp": 100,
        "turns": 0,
        "defeated": 0,
        "last_player": "Binod231",
        "top_player": "Binod231",
        "top_score": 0,
        "logs": [
            "[BOOT] PROD_CLUSTER_DEFENDER v2.6 initialized.",
            "[ALERT] Wave 1 Threat: [CVE-EXPLOIT] probing ingress!",
            "[HINT] Click any terminal command below to play.",
        ],
    }


def get_boss(boss_id: str) -> dict:
    for b in BOSSES:
        if b["id"] == boss_id:
            return b
    return BOSSES[0]


def process_move(state: dict, move: str, player: str) -> str:
    player = sanitize_user(player)
    state["last_player"] = player

    if move == "RESET" or state["cluster_hp"] <= 0:
        boss = BOSSES[0]
        state.update(
            {
                "wave": 1,
                "score": 0,
                "cluster_hp": 100,
                "max_cluster_hp": 100,
                "boss_id": boss["id"],
                "boss_hp": 100,
                "max_boss_hp": 100,
                "turns": 0,
                "defeated": 0,
                "logs": [
                    f"[REBOOT] @{player} restarted cluster defense cluster!",
                    f"[ALERT] Wave 1 Threat Detected: [{boss['id']}]",
                    "[READY] Execute a DevOps countermeasure below.",
                ],
            }
        )
        return f"Cluster rebooted by @{player}! Wave 1 [{boss['id']}] spawned."

    boss = get_boss(state["boss_id"])
    state["turns"] += 1

    # Calculate player move effect
    dmg = 0
    heal = 0
    crit_tag = ""

    if move == "WAF_BLOCK":
        dmg = 48 if boss["weakness"] == "WAF_BLOCK" else 24
        crit_tag = " [SUPER EFFECTIVE!]" if boss["weakness"] == "WAF_BLOCK" else ""
        action_msg = f"@{player} ran ./waf_block.sh -> -{dmg} HP{crit_tag}"
    elif move == "SCALE_ECS":
        dmg = 48 if boss["weakness"] == "SCALE_ECS" else 26
        crit_tag = " [SUPER EFFECTIVE!]" if boss["weakness"] == "SCALE_ECS" else ""
        action_msg = f"@{player} ran ./scale_ecs.sh -> -{dmg} HP{crit_tag}"
    elif move == "FLUSH_REDIS":
        dmg = 44 if boss["weakness"] == "FLUSH_REDIS" else 18
        heal = 18
        state["cluster_hp"] = min(state["max_cluster_hp"], state["cluster_hp"] + heal)
        crit_tag = " [SUPER EFFECTIVE!]" if boss["weakness"] == "FLUSH_REDIS" else ""
        action_msg = f"@{player} ran ./flush_redis.sh -> -{dmg} HP, +{heal} SLA HP{crit_tag}"
    else:  # CANARY_DEPLOY
        is_crit = random.random() < 0.45
        dmg = 58 if is_crit else 30
        crit_tag = " [CRITICAL CANARY HIT!]" if is_crit else ""
        action_msg = f"@{player} ran ./canary_deploy.sh -> -{dmg} HP{crit_tag}"

    state["boss_hp"] = max(0, state["boss_hp"] - dmg)
    state["score"] += dmg * 10

    logs = list(state.get("logs", []))
    logs.append(f"[TURN {state['turns']}] {action_msg}")

    if state["boss_hp"] <= 0:
        state["defeated"] += 1
        bonus = state["wave"] * 250
        state["score"] += bonus
        state["wave"] += 1
        next_boss = BOSSES[(state["wave"] - 1) % len(BOSSES)]
        new_max = 100 + (state["wave"] - 1) * 20
        state["boss_id"] = next_boss["id"]
        state["boss_hp"] = new_max
        state["max_boss_hp"] = new_max
        state["cluster_hp"] = min(state["max_cluster_hp"], state["cluster_hp"] + 15)
        logs.append(f"[VICTORY] Threat neutralized! +{bonus} XP | +15 Cluster HP!")
        logs.append(f"[WAVE {state['wave']}] New Threat: [{next_boss['id']}] ({next_boss['hint']})")
        reply = (
            f"{action_msg}\n\n"
            f"Threat neutralized! +{bonus} XP bonus. Wave {state['wave']} [{next_boss['id']}] spawned!"
        )
    else:
        lo, hi = boss["atk"]
        enemy_dmg = random.randint(lo, hi)
        state["cluster_hp"] = max(0, state["cluster_hp"] - enemy_dmg)
        logs.append(f"[ATTACK] [{boss['id']}] hit prod cluster for -{enemy_dmg} HP!")
        if state["cluster_hp"] <= 0:
            logs.append("[DOWNTIME] Cluster hit 0 HP! Click ./reboot_game.sh to restart!")
            reply = f"{action_msg}\n[{boss['id']}] dealt -{enemy_dmg} HP. Cluster is down — click ./reboot_game.sh!"
        else:
            reply = f"{action_msg}\n[{boss['id']}] counter-attacked for -{enemy_dmg} HP. Cluster HP: {state['cluster_hp']}/100."

    if state["score"] >= state.get("top_score", 0):
        state["top_score"] = state["score"]
        state["top_player"] = player

    state["logs"] = logs[-3:]
    return reply


def render_svg(state: dict):
    boss = get_boss(state["boss_id"])
    cluster_hp = state["cluster_hp"]
    max_chp = max(1, state["max_cluster_hp"])
    boss_hp = state["boss_hp"]
    max_bhp = max(1, state["max_boss_hp"])

    chp_pct = max(0.0, min(1.0, cluster_hp / max_chp))
    bhp_pct = max(0.0, min(1.0, boss_hp / max_bhp))
    chp_w = int(340 * chp_pct)
    bhp_w = int(340 * bhp_pct)

    chp_color = "#10b981" if chp_pct > 0.5 else ("#f59e0b" if chp_pct > 0.25 else "#ef4444")
    sla_text = "99.9% SLA" if cluster_hp > 0 else "OUTAGE! REBOOT"

    logs = state.get("logs", [])
    while len(logs) < 3:
        logs.insert(0, "[READY] Awaiting operator command...")

    l1 = html.escape(logs[-3][:96])
    l2 = html.escape(logs[-2][:96])
    l3 = html.escape(logs[-1][:96])

    last_p = html.escape(state.get("last_player", "Binod231"))
    top_p = html.escape(state.get("top_player", "Binod231"))
    top_s = state.get("top_score", 0)
    boss_color = boss["color"]

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 360" width="100%" height="360">
  <defs>
    <linearGradient id="gameBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#04070e"/>
      <stop offset="100%" stop-color="#0b1222"/>
    </linearGradient>
    <pattern id="gGrid" width="28" height="28" patternUnits="userSpaceOnUse">
      <path d="M 28 0 L 0 0 0 28" fill="none" stroke="#132038" stroke-width="0.6"/>
    </pattern>
  </defs>
  <style>
    @keyframes hoverBoss {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-7px); }} }}
    @keyframes pulseLed {{ 0%, 100% {{ opacity: 0.45; }} 50% {{ opacity: 1; }} }}
    @keyframes beam {{ to {{ stroke-dashoffset: -36; }} }}
    .boss-hover {{ animation: hoverBoss 2.8s ease-in-out infinite; }}
    .led-pulse {{ animation: pulseLed 1.8s ease-in-out infinite; }}
    .laser-arc {{ stroke-dasharray: 6 6; animation: beam 1.2s linear infinite; }}
  </style>

  <!-- Terminal Frame -->
  <rect width="1120" height="360" rx="14" fill="url(#gameBg)" stroke="#1e293b" stroke-width="1.5"/>
  <rect width="1120" height="360" rx="14" fill="url(#gGrid)"/>

  <!-- Top HUD -->
  <rect x="20" y="16" width="1080" height="36" rx="8" fill="#09111f" stroke="#10b981" stroke-width="1"/>
  <text x="36" y="38" font-family="monospace" font-size="13" font-weight="bold" fill="#34d399">INCIDENT_RESPONDER // PLAYABLE_TERMINAL_RPG</text>
  <text x="455" y="38" font-family="monospace" font-size="12" fill="#38bdf8">WAVE: {state['wave']}</text>
  <text x="540" y="38" font-family="monospace" font-size="12" fill="#fbbf24">SCORE: {state['score']} XP</text>
  <text x="695" y="38" font-family="monospace" font-size="12" fill="#e2e8f0">LAST_CMD: @{last_p}</text>
  <text x="920" y="38" font-family="monospace" font-size="11.5" fill="#10b981">TOP: @{top_p} ({top_s})</text>

  <!-- LEFT PANEL: Production AWS/K8s Cluster -->
  <rect x="28" y="68" width="460" height="176" rx="10" fill="#070d19" stroke="#1e293b" stroke-width="1.2"/>
  <text x="48" y="92" font-family="monospace" font-size="12.5" font-weight="bold" fill="#38bdf8">[PROD_CLUSTER // AWS ECS + RDS]</text>
  <text x="375" y="92" font-family="monospace" font-size="11.5" font-weight="bold" fill="{chp_color}">{sla_text}</text>

  <!-- Cluster HP Bar -->
  <text x="48" y="120" font-family="monospace" font-size="11.5" fill="#94a3b8">CLUSTER_HP: {cluster_hp} / {max_chp}</text>
  <rect x="48" y="128" width="340" height="16" rx="4" fill="#0f172a" stroke="#334155"/>
  <rect x="48" y="128" width="{chp_w}" height="16" rx="4" fill="{chp_color}"/>

  <!-- 3D Isometric Server Nodes -->
  <g transform="translate(52, 165)">
    <rect x="0" y="0" width="84" height="58" rx="6" fill="#0b1526" stroke="#38bdf8" stroke-width="1"/>
    <circle cx="14" cy="14" r="3.5" fill="#10b981" class="led-pulse"/>
    <text x="24" y="18" font-family="monospace" font-size="10.5" font-weight="bold" fill="#e0f2fe">ECS-01</text>
    <text x="12" y="42" font-family="monospace" font-size="9.5" fill="#38bdf8">HEALTHY</text>

    <rect x="98" y="0" width="84" height="58" rx="6" fill="#0b1526" stroke="#38bdf8" stroke-width="1"/>
    <circle cx="112" cy="14" r="3.5" fill="#10b981" class="led-pulse"/>
    <text x="122" y="18" font-family="monospace" font-size="10.5" font-weight="bold" fill="#e0f2fe">RDS-AZ</text>
    <text x="110" y="42" font-family="monospace" font-size="9.5" fill="#34d399">SYNCED</text>

    <rect x="196" y="0" width="84" height="58" rx="6" fill="#0b1526" stroke="#a78bfa" stroke-width="1"/>
    <circle cx="210" cy="14" r="3.5" fill="#38bdf8" class="led-pulse"/>
    <text x="220" y="18" font-family="monospace" font-size="10.5" font-weight="bold" fill="#ede9fe">REDIS</text>
    <text x="208" y="42" font-family="monospace" font-size="9.5" fill="#a78bfa">CACHED</text>

    <rect x="294" y="0" width="84" height="58" rx="6" fill="#0b1526" stroke="#f59e0b" stroke-width="1"/>
    <circle cx="308" cy="14" r="3.5" fill="#f59e0b" class="led-pulse"/>
    <text x="318" y="18" font-family="monospace" font-size="10.5" font-weight="bold" fill="#fef3c7">AWS-WAF</text>
    <text x="306" y="42" font-family="monospace" font-size="9.5" fill="#fbbf24">ARMED</text>
  </g>

  <!-- Battle Line -->
  <line x1="496" y1="156" x2="624" y2="156" stroke="#38bdf8" stroke-width="2.5" class="laser-arc"/>
  <text x="560" y="144" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="#34d399">VS</text>

  <!-- RIGHT PANEL: Active Production Incident Boss -->
  <rect x="632" y="68" width="460" height="176" rx="10" fill="#070d19" stroke="{boss_color}" stroke-width="1.3"/>
  <text x="652" y="92" font-family="monospace" font-size="12.5" font-weight="bold" fill="{boss_color}">[THREAT // {html.escape(boss['id'])}]</text>
  <text x="915" y="92" font-family="monospace" font-size="11" fill="#94a3b8">{html.escape(boss['hint'])}</text>

  <!-- Boss HP Bar -->
  <text x="652" y="120" font-family="monospace" font-size="11.5" fill="#94a3b8">THREAT_HP: {boss_hp} / {max_bhp}</text>
  <rect x="652" y="128" width="340" height="16" rx="4" fill="#0f172a" stroke="#334155"/>
  <rect x="652" y="128" width="{bhp_w}" height="16" rx="4" fill="{boss_color}"/>

  <!-- 3D Boss Isometric Sprite -->
  <g transform="translate(800, 158)" class="boss-hover">
    <polygon points="56,0 108,24 56,48 4,24" fill="{boss_color}" opacity="0.9"/>
    <polygon points="4,24 56,48 56,74 4,50" fill="#1e1b4b" stroke="{boss_color}" stroke-width="1"/>
    <polygon points="108,24 56,48 56,74 108,50" fill="#090d16" stroke="{boss_color}" stroke-width="1"/>
    <text x="56" y="28" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="#ffffff">{html.escape(boss['id'])}</text>
  </g>
  <text x="652" y="190" font-family="monospace" font-size="12" fill="#e2e8f0" font-weight="bold">{html.escape(boss['name'])}</text>
  <text x="652" y="212" font-family="monospace" font-size="11" fill="#94a3b8">THREATS DEFEATED: {state['defeated']} | TURNS: {state['turns']}</text>

  <!-- BOTTOM PANEL: Live Combat Terminal Stdout -->
  <rect x="28" y="258" width="1064" height="86" rx="8" fill="#050912" stroke="#1e293b" stroke-width="1"/>
  <text x="44" y="280" font-family="monospace" font-size="11.5" fill="#64748b">&gt; {l1}</text>
  <text x="44" y="302" font-family="monospace" font-size="11.5" fill="#94a3b8">&gt; {l2}</text>
  <text x="44" y="324" font-family="monospace" font-size="12" font-weight="bold" fill="#34d399">&gt; {l3}</text>
</svg>
"""
    SVG_PATH.write_text(svg, encoding="utf-8")


def github_api_request(url: str, token: str, method: str = "POST", payload: dict | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Binod231-DevOps-GameBot",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def handle_issue_reply(reply: str):
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    issue_num = os.environ.get("ISSUE_NUMBER")
    if not (token and repo and issue_num):
        return

    comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_num}/comments"
    issue_url = f"https://api.github.com/repos/{repo}/issues/{issue_num}"
    try:
        github_api_request(
            comment_url,
            token,
            method="POST",
            payload={"body": f"```text\n{reply}\n```\n\nYour move is now live on https://github.com/{repo.split('/')[0]} !"},
        )
        github_api_request(issue_url, token, method="PATCH", payload={"state": "closed"})
    except Exception as exc:
        print(f"Warning: GitHub issue API update failed: {exc}")


def main():
    title = os.environ.get("ISSUE_TITLE", "").strip()
    player = os.environ.get("PLAYER_USER", "Binod231")

    state = load_state()

    if title.startswith("GAME:"):
        move = title.split("GAME:", 1)[1].strip().upper()
        if move not in VALID_MOVES:
            move = "CANARY_DEPLOY"
        reply = process_move(state, move, player)
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        render_svg(state)
        handle_issue_reply(reply)
        print(reply)
    else:
        # Render initial/current board cleanly without advancing turn
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        render_svg(state)
        print("Rendered game board SVG from current state.")


if __name__ == "__main__":
    main()
