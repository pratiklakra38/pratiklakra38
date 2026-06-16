import requests, os, re

USERNAME = "pratiklakra38"

# Fetch GitHub's own contribution graph SVG (public, no auth needed)
url = f"https://github.com/users/{USERNAME}/contributions"
res = requests.get(url)
svg_text = res.text

# Parse each contribution day rect: <rect ... data-date="2025-01-01" data-level="2" .../>
# GitHub's markup uses data-date and data-level (0-4) attributes on <td> or <rect>
pattern = re.compile(r'data-date="([\d-]+)"[^>]*data-level="(\d)"')
matches = pattern.findall(svg_text)

if not matches:
    # fallback older markup: class="ContributionCalendar-day" data-date data-count
    pattern2 = re.compile(r'data-date="([\d-]+)"[^>]*data-count="(\d+)"')
    matches2 = pattern2.findall(svg_text)
    days = [(d, int(c)) for d, c in matches2]
else:
    days = [(d, int(lvl)) for d, lvl in matches]

print(f"Parsed {len(days)} contribution days")

if not days:
    print("ERROR: Could not parse contribution data from GitHub page")
    exit(1)

# Map level -> color (GitHub's standard green scale)
LEVEL_COLORS = {
    0: "#161b22",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
}

# Group days into weeks (7 per week), in chronological order
weeks = [days[i:i+7] for i in range(0, len(days), 7)]

CELL = 12
GAP = 3
STEP = CELL + GAP
COLS = len(weeks)
ROWS = 7
PAD = 20

W = PAD * 2 + COLS * STEP
H = PAD * 2 + ROWS * STEP + 60

dots = []
cells = []
for ci, week in enumerate(weeks):
    for ri, (date, level) in enumerate(week):
        x = PAD + ci * STEP + CELL // 2
        y = PAD + 40 + ri * STEP + CELL // 2
        color = LEVEL_COLORS.get(level, "#161b22")
        cells.append((x - CELL//2, y - CELL//2, color))
        if level > 0:
            dots.append((x, y))

print(f"{len(dots)} active contribution dots out of {len(cells)} total cells")

total_dur = 12
pac_size = 9

# Build a path that sweeps row by row, like the original snake
path_parts = []
for ri in range(ROWS):
    y = PAD + 40 + ri * STEP + CELL // 2
    if ri == 0:
        path_parts.append(f"M {PAD + CELL//2} {y}")
    if ri % 2 == 0:
        path_parts.append(f"L {PAD + (COLS-1)*STEP + CELL//2} {y}")
    else:
        path_parts.append(f"L {PAD + CELL//2} {y}")
    if ri < ROWS - 1:
        next_y = PAD + 40 + (ri+1) * STEP + CELL // 2
        x_pos = PAD + (COLS-1)*STEP + CELL//2 if ri % 2 == 0 else PAD + CELL//2
        path_parts.append(f"L {x_pos} {next_y}")

path_d = " ".join(path_parts)

svg_parts = []
svg_parts.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">')
svg_parts.append(f'<rect width="{W}" height="{H}" fill="#0d1117" rx="8"/>')
svg_parts.append(f'<text x="{W//2}" y="24" fill="#FFD700" font-size="13" font-family="monospace" text-anchor="middle" font-weight="bold">PAC-MAN eating my contributions</text>')

# draw all grid cells first (the actual contribution graph, just like before)
for (cx, cy, color) in cells:
    svg_parts.append(f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" fill="{color}" rx="2"/>')

# small yellow dots overlay on top of active cells, which fade as pac-man passes
for (dx, dy) in dots:
    svg_parts.append(
        f'<circle cx="{dx}" cy="{dy}" r="2.2" fill="#FFD700">'
        f'<animate attributeName="opacity" values="1;0" dur="{total_dur}s" '
        f'repeatCount="indefinite" calcMode="discrete" keyTimes="0;0.98"/></circle>'
    )

# Pac-Man (pure SVG shapes, not emoji)
svg_parts.append(f'''
<g>
  <animateMotion dur="{total_dur}s" repeatCount="indefinite" rotate="auto">
    <mpath href="#pacpath"/>
  </animateMotion>
  <circle r="{pac_size}" fill="#FFD700"/>
  <path fill="#0d1117">
    <animate attributeName="d"
      values="M0,0 L{pac_size},-4 A{pac_size},{pac_size} 0 1,0 {pac_size},4 Z;M0,0 L{pac_size},0 A{pac_size},{pac_size} 0 1,0 {pac_size},0.1 Z;M0,0 L{pac_size},-4 A{pac_size},{pac_size} 0 1,0 {pac_size},4 Z"
      dur="0.25s" repeatCount="indefinite"/>
  </path>
  <circle cx="2" cy="-5" r="1.5" fill="#0d1117"/>
</g>
<path id="pacpath" d="{path_d}" fill="none"/>
''')

svg_parts.append('</svg>')

os.makedirs("dist", exist_ok=True)
with open("dist/pacman.svg", "w") as f:
    f.write("\n".join(svg_parts))

print(f"Done! Generated pacman.svg ({W}x{H}) with {len(dots)} dots.")
