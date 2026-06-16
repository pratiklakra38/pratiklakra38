import requests, os, datetime

USERNAME = "pratiklakra38"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Use REST API to get contribution data via events (no GraphQL needed)
# Build a contribution map using commit activity
today = datetime.date.today()
one_year_ago = today - datetime.timedelta(days=365)

# Get all dates in the last year arranged as contribution grid (53 weeks x 7 days)
all_days = []
# Start from the Sunday before one_year_ago
start = one_year_ago - datetime.timedelta(days=one_year_ago.weekday() + 1)
if start.weekday() != 6:  # not Sunday
    days_since_sunday = (start.weekday() + 1) % 7
    start = start - datetime.timedelta(days=days_since_sunday)

# Fetch repos to get commit counts per day
contrib_map = {}

# Use the GitHub contributions API via SVG scraping as fallback
# Actually use the stats endpoint - get repos and their commit activity
res = requests.get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=pushed", headers=headers)
repos = res.json() if res.status_code == 200 else []

print(f"Found {len(repos)} repos")

# For each repo get weekly commit stats
for repo in repos[:20]:  # limit to 20 repos
    name = repo.get("name", "")
    r = requests.get(f"https://api.github.com/repos/{USERNAME}/{name}/stats/commit_activity", headers=headers)
    if r.status_code == 200:
        weeks_data = r.json()
        if isinstance(weeks_data, list):
            for week in weeks_data:
                week_ts = week.get("week", 0)
                days = week.get("days", [0]*7)
                for di, count in enumerate(days):
                    date = datetime.date.fromtimestamp(week_ts) + datetime.timedelta(days=di)
                    date_str = date.isoformat()
                    contrib_map[date_str] = contrib_map.get(date_str, 0) + count

print(f"Got contribution data for {len(contrib_map)} days")

# Build 53 weeks x 7 days grid
weeks = []
cur = start
for w in range(53):
    week = []
    for d in range(7):
        date_str = cur.isoformat()
        count = contrib_map.get(date_str, 0)
        # Color based on count
        if count == 0:
            color = "#161b22"
        elif count < 3:
            color = "#0e4429"
        elif count < 6:
            color = "#006d32"
        elif count < 10:
            color = "#26a641"
        else:
            color = "#39d353"
        week.append({"count": count, "color": color, "date": date_str})
        cur += datetime.timedelta(days=1)
    weeks.append(week)

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
    for ri, day in enumerate(week):
        x = PAD + ci * STEP + CELL // 2
        y = PAD + 40 + ri * STEP + CELL // 2
        cells.append((x - CELL//2, y - CELL//2, day["color"]))
        if day["count"] > 0:
            dots.append((x, y))

total_dur = 10
pac_size = 9

# Build snake path for pac-man
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

for (cx, cy, color) in cells:
    svg_parts.append(f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" fill="{color}" rx="2"/>')

for (dx, dy) in dots:
    svg_parts.append(f'<circle cx="{dx}" cy="{dy}" r="2.5" fill="#FFD700"><animate attributeName="opacity" values="1;0" dur="{total_dur}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;0.99"/></circle>')

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

ghost_colors = ["#FF0000", "#FFB8FF", "#00FFFF", "#FFB852"]
for i, gc in enumerate(ghost_colors):
    delay = i * 1.8
    svg_parts.append(f'''
<g opacity="0.9">
  <animateMotion dur="{total_dur}s" begin="{delay}s" repeatCount="indefinite" rotate="auto">
    <mpath href="#pacpath"/>
  </animateMotion>
  <circle cx="0" cy="-5" r="9" fill="{gc}"/>
  <rect x="-9" y="-5" width="18" height="9" fill="{gc}"/>
  <polygon points="-9,4 -6,8 -3,4 0,8 3,4 6,8 9,4" fill="{gc}"/>
  <circle cx="-3" cy="-5" r="2.5" fill="white"/>
  <circle cx="3" cy="-5" r="2.5" fill="white"/>
  <circle cx="-3" cy="-5" r="1.2" fill="#222"/>
  <circle cx="3" cy="-5" r="1.2" fill="#222"/>
</g>
''')

svg_parts.append('</svg>')

os.makedirs("dist", exist_ok=True)
with open("dist/pacman.svg", "w") as f:
    f.write("\n".join(svg_parts))

print(f"Done! Generated pacman.svg with {len(dots)} dots.")
