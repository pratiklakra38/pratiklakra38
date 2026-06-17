// generate_pacman.mjs
//
// Step 1: Use the real, proven snk engine (the same one that already worked
//         for your snake) to compute the exact eat-and-disappear animation.
// Step 2: Post-process the resulting SVG:
//   - hide the trailing body segments, keep only the head (".s0")
//   - restyle the head into a Pac-Man face (yellow circle + chomping mouth)
//   - read the head's own movement keyframes and derive a pure-CSS flip
//     animation, so Pac-Man visibly faces left when moving backwards/left
//     and right when moving forwards/right (no <script>, since GitHub
//     strips <script> tags from SVGs served through an <img> tag).

import { generateSnakeAnimation } from "generate-snake-animation";
import { writeFileSync, mkdirSync } from "fs";

const USERNAME = process.env.GH_USERNAME || "pratiklakra38";
const TOKEN = process.env.GITHUB_TOKEN || "";

const outputs = [
  {
    format: "svg",
    drawOptions: {
      colorDots: {
        0: "#161b22",
        1: "#0e4429",
        2: "#006d32",
        3: "#26a641",
        4: "#39d353",
      },
      colorEmpty: "#161b22",
      colorDotBorder: "#1b1f230a",
      colorSnake: "#FFD700",
      sizeCell: 16,
      sizeDot: 12,
      sizeDotBorderRadius: 2,
    },
    animationOptions: { stepDurationMs: 110, frameByStep: 1 },
  },
];

const [svg] = await generateSnakeAnimation(
  { platform: "github", username: USERNAME, githubToken: TOKEN },
  outputs
);

if (!svg || typeof svg !== "string") {
  console.error("Failed to generate base snake SVG");
  process.exit(1);
}

let pacmanSvg = svg;

// 1. Hide every trailing body segment, keep only the head (.s0)
pacmanSvg = pacmanSvg.replace(
  /\.s\{([^}]*)\}/,
  `.s{$1}
   .s:not(.s0){ display:none; }`
);

// 2. Read the head's own movement keyframes (@keyframes s0{...}) so we can
//    derive a left/right facing flip purely from real per-step x deltas.
const overallDurMatch = pacmanSvg.match(
  /\.s\{[^}]*animation: none linear (\d+)ms infinite[^}]*\}/
);
const totalDurationMs = overallDurMatch ? parseInt(overallDurMatch[1], 10) : 5000;

const kfMatch = pacmanSvg.match(/@keyframes s0\{([\s\S]*?)\}\s*\.s\.s0/);
let flipKeyframesCss = "";
if (kfMatch) {
  const body = kfMatch[1];
  const frameRe = /([\d.]+)%\{transform:translate\(([-\d.]+)px,[-\d.]+px\)\}/g;
  let frame;
  const frames = [];
  while ((frame = frameRe.exec(body))) {
    frames.push({ t: parseFloat(frame[1]), x: parseFloat(frame[2]) });
  }
  let facing = 1; // 1 = right, -1 = left
  const flipFrames = frames.map((f, i) => {
    if (i > 0) {
      const dx = f.x - frames[i - 1].x;
      if (dx < -0.01) facing = -1;
      else if (dx > 0.01) facing = 1;
    }
    return `${f.t}%{transform:scaleX(${facing})}`;
  });
  flipKeyframesCss = `@keyframes pacflip{${flipFrames.join("")}}`;
}

// 3. Add the chomping-mouth animation + the flip animation (reusing the
//    exact same total duration as the snake's own movement, so the flip
//    timing always matches the head's real position frame-for-frame).
pacmanSvg = pacmanSvg.replace(
  "</style>",
  `.pac-mouth{ fill:#0d1117; transform-origin:8px 8px; animation: pacchomp 220ms linear infinite; }
   @keyframes pacchomp{
     0%   { d: path("M 8 8 L 16 2 A 8 8 0 1 1 16 14 Z"); }
     50%  { d: path("M 8 8 L 16 7.5 A 8 8 0 1 1 16 8.5 Z"); }
     100% { d: path("M 8 8 L 16 2 A 8 8 0 1 1 16 14 Z"); }
   }
   ${flipKeyframesCss}
   .pac-flip{ transform-origin:8px 8px; animation: pacflip ${totalDurationMs}ms linear infinite; }
   </style>`
);

// 4. Swap the head <rect class="s s0" .../> for a Pac-Man <g>, keeping the
//    same "s s0" class so it inherits the exact translate animation/path.
//    No stray eye/dot -- just the body circle and the mouth wedge, wrapped
//    in .pac-flip so it mirrors correctly when moving left/backwards.
pacmanSvg = pacmanSvg.replace(
  /<rect class="s s0"[^/]*\/>/,
  `<g class="s s0">
     <g class="pac-flip">
       <circle cx="8" cy="8" r="8" fill="#FFD700"/>
       <path class="pac-mouth" d="M 8 8 L 16 2 A 8 8 0 1 1 16 14 Z"/>
     </g>
   </g>`
);

mkdirSync("dist", { recursive: true });
writeFileSync("dist/pacman.svg", pacmanSvg);
console.log("pacman.svg generated successfully.");
