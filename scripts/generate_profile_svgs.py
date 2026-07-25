#!/usr/bin/env python3
"""Regenerate assets/skill-dna.svg and assets/tech-stack.svg from data/*.json.

Percentages, domain labels, and the tool list are self-reported inputs edited
by hand in data/skill-dna.json and data/tech-stack.json (there is no GitHub
metric for "career focus by domain" or "which enterprise tools I use"). This
script only automates the mechanical part: turning that data into correctly
laid-out SVG markup, so bar widths and card heights never drift out of sync
with the numbers/labels the way they could when the SVGs were hand-edited.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets"

CARD_WIDTH = 640
CARD_LEFT = 32
CARD_RIGHT = 608  # right edge of the skill-dna progress track


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_skill_dna(data: dict) -> str:
    domains = data["domains"]
    total = sum(d["percent"] for d in domains)
    if total != 100:
        raise ValueError(f"data/skill-dna.json percentages sum to {total}, expected 100")

    row_height = 76
    first_cy = 110
    track_width = CARD_RIGHT - CARD_LEFT
    height = 196 + row_height * (len(domains) - 1)

    gradients = []
    rows = []
    for i, d in enumerate(domains):
        cy = first_cy + row_height * i
        text_y = cy + 6
        track_y = cy + 18
        bar_width = round(track_width * d["percent"] / 100)
        gid = f"skillBar{i}"
        gradients.append(
            f'<linearGradient id="{gid}" x1="0%" y1="0%" x2="100%" y2="0%">'
            f'<stop offset="0%" stop-color="{d["color"]}"/>'
            f'<stop offset="100%" stop-color="{d["colorLight"]}"/></linearGradient>'
        )
        rows.append(f'''
  <!-- {esc(d["label"])} {d["percent"]}% -->
  <circle cx="48" cy="{cy}" r="6" fill="{d["color"]}"/>
  <text x="68" y="{text_y}" class="label3">{esc(d["label"])}</text>
  <text x="{CARD_RIGHT}" y="{text_y}" class="pct3" text-anchor="end">{d["percent"]}%</text>
  <rect class="track" x="{CARD_LEFT}" y="{track_y}" width="{track_width}" height="18"/>
  <rect x="{CARD_LEFT}" y="{track_y}" width="{bar_width}" height="18" rx="9" fill="url(#{gid})"/>''')

    return f'''<svg width="{CARD_WIDTH}" height="{height}" viewBox="0 0 {CARD_WIDTH} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="borderGrad3" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#A9FEF7"/>
      <stop offset="50%" stop-color="#A78BFA"/>
      <stop offset="100%" stop-color="#F472B6"/>
    </linearGradient>
    <linearGradient id="titleGrad3" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#A9FEF7"/>
      <stop offset="100%" stop-color="#A78BFA"/>
    </linearGradient>
    {"".join(gradients)}
    <pattern id="diagLinesSkill" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="14" stroke="#A9FEF7" stroke-opacity="0.035" stroke-width="1"/>
    </pattern>
    <style>
      .bg3 {{ fill: #0d1117; }}
      .title3 {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 28px; font-weight: 700; fill: url(#titleGrad3); }}
      .sub3 {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; fill: #6e7681; }}
      .label3 {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 20px; font-weight: 700; fill: #c9d1d9; }}
      .pct3 {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 22px; font-weight: 700; fill: #A78BFA; }}
      .track {{ fill: #161b22; rx: 9; }}
    </style>
  </defs>

  <rect class="bg3" width="{CARD_WIDTH}" height="{height}" rx="20"/>
  <rect width="{CARD_WIDTH}" height="{height}" rx="20" fill="url(#diagLinesSkill)"/>
  <rect x="6" y="6" width="{CARD_WIDTH - 12}" height="{height - 12}" rx="16" fill="none" stroke="url(#borderGrad3)" stroke-width="1.5"/>

  <text x="32" y="46" class="title3">\U0001f9ec Skill DNA</text>
  <text x="32" y="68" class="sub3">{esc(data.get("subtitle", "Portfolio focus by domain"))}</text>
  {"".join(rows)}

  <defs>
    <clipPath id="cardClipSkill">
      <rect x="6" y="6" width="{CARD_WIDTH - 12}" height="{height - 12}" rx="16"/>
    </clipPath>
    <linearGradient id="glowBarSkill" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#3FB950" stop-opacity="0"/>
      <stop offset="50%" stop-color="#3FB950" stop-opacity="0.04"/>
      <stop offset="100%" stop-color="#3FB950" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="6" y="-60" width="{CARD_WIDTH - 12}" height="60" fill="url(#glowBarSkill)" clip-path="url(#cardClipSkill)">
    <animate attributeName="y" values="-60;{height}" dur="7s" repeatCount="indefinite"/>
  </rect>
</svg>
'''


def badge_width(text: str) -> int:
    """Estimate a badge width from label length, rounded to the nearest 10px.

    Calibrated against the hand-picked widths in the original tech-stack.svg
    (e.g. "Azure" -> 110, "Microsoft Sentinel" -> 220), so generated badges
    stay close in size to the ones they replace.
    """
    raw = 8.6 * len(text) + 66
    return max(90, round(raw / 10) * 10)


ROW_HEIGHT = 44
BADGE_HEIGHT = 36
BADGE_GAP = 10
GROUP_GAP = 36
HEADER_TO_BADGES = 12
MAX_RIGHT_TECH = 616


def layout_group(tools, top_y, color):
    rows = [[]]
    cursor_x = CARD_LEFT
    for tool in tools:
        w = badge_width(tool)
        if rows[-1] and cursor_x + w > MAX_RIGHT_TECH:
            rows.append([])
            cursor_x = CARD_LEFT
        rows[-1].append((tool, cursor_x, w))
        cursor_x += w + BADGE_GAP

    markup = []
    for r, row in enumerate(rows):
        y = top_y + r * ROW_HEIGHT
        for tool, x, w in row:
            cx, cy = x + 18, y + 18
            tx, ty = x + 32, y + 23
            markup.append(
                f'<rect class="badge" x="{x}" y="{y}" width="{w}" height="{BADGE_HEIGHT}"/>'
                f'<circle cx="{cx}" cy="{cy}" r="5" fill="{color}"/>'
                f'<text x="{tx}" y="{ty}" class="badgetext">{esc(tool)}</text>'
            )
    bottom = top_y + (len(rows) - 1) * ROW_HEIGHT + BADGE_HEIGHT
    return markup, bottom


def generate_tech_stack(data: dict) -> str:
    y_cursor = 84
    sections = []
    for g in data["groups"]:
        header_y = y_cursor
        badges_top = header_y + HEADER_TO_BADGES
        markup, bottom = layout_group(g["tools"], badges_top, g["color"])
        badges = "\n    ".join(markup)
        sections.append(
            f'\n  <text x="{CARD_LEFT}" y="{header_y}" class="group">{esc(g["name"].upper())}</text>\n'
            f'  <g>\n    {badges}\n  </g>'
        )
        y_cursor = bottom + GROUP_GAP

    content_bottom = y_cursor - GROUP_GAP
    height = content_bottom + 42

    return f'''<svg width="{CARD_WIDTH}" height="{height}" viewBox="0 0 {CARD_WIDTH} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="borderGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#A9FEF7"/>
      <stop offset="50%" stop-color="#A78BFA"/>
      <stop offset="100%" stop-color="#F472B6"/>
    </linearGradient>
    <linearGradient id="titleGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#A9FEF7"/>
      <stop offset="100%" stop-color="#A78BFA"/>
    </linearGradient>
    <pattern id="diagLinesTech" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="14" stroke="#A9FEF7" stroke-opacity="0.035" stroke-width="1"/>
    </pattern>
    <style>
      .bg2 {{ fill: #0d1117; }}
      .title2 {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 28px; font-weight: 700; fill: url(#titleGrad2); }}
      .group {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 18px; font-weight: 700; fill: #8b949e; letter-spacing: 1.5px; }}
      .badge {{ fill: #161b22; stroke: #30363d; stroke-width: 1; rx: 8; }}
      .badgetext {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 16px; fill: #c9d1d9; }}
    </style>
  </defs>

  <rect class="bg2" width="{CARD_WIDTH}" height="{height}" rx="20"/>
  <rect width="{CARD_WIDTH}" height="{height}" rx="20" fill="url(#diagLinesTech)"/>
  <rect x="6" y="6" width="{CARD_WIDTH - 12}" height="{height - 12}" rx="16" fill="none" stroke="url(#borderGrad2)" stroke-width="1.5"/>

  <text x="32" y="48" class="title2">\U0001f6e0️ Tech Stack</text>
  {"".join(sections)}

  <defs>
    <clipPath id="cardClipTech">
      <rect x="6" y="6" width="{CARD_WIDTH - 12}" height="{height - 12}" rx="16"/>
    </clipPath>
    <linearGradient id="glowBarTech" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#A9FEF7" stop-opacity="0"/>
      <stop offset="50%" stop-color="#A9FEF7" stop-opacity="0.04"/>
      <stop offset="100%" stop-color="#A9FEF7" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="6" y="-60" width="{CARD_WIDTH - 12}" height="60" fill="url(#glowBarTech)" clip-path="url(#cardClipTech)">
    <animate attributeName="y" values="-60;{height}" dur="7s" repeatCount="indefinite"/>
  </rect>
</svg>
'''


def main():
    skill_data = json.loads((DATA_DIR / "skill-dna.json").read_text())
    tech_data = json.loads((DATA_DIR / "tech-stack.json").read_text())

    (ASSETS_DIR / "skill-dna.svg").write_text(generate_skill_dna(skill_data))
    (ASSETS_DIR / "tech-stack.svg").write_text(generate_tech_stack(tech_data))
    print("Generated assets/skill-dna.svg and assets/tech-stack.svg")


if __name__ == "__main__":
    main()
