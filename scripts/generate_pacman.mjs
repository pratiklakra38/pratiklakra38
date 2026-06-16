// generate_pacman.mjs
//
// Step 1: Use the real, proven snk engine (the same one that already worked
//         for your snake) to compute the exact eat-and-disappear animation.
// Step 2: Post-process the resulting SVG -- hide the trailing body segments
//         and restyle only the head segment (".s0") into a Pac-Man face
//         (yellow circle + animated chomping mouth). The motion/timing is
//         100% inherited from the original snake animation, since we reuse
//         its CSS keyframes untouched -- only the shape inside changes.

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

// 1. Hide every trailing body segment, keep only the head (.s0)
let pacmanSvg = svg.replace(
  /\.s\{([^}]*)\}/,
  `.s{$1}
   .s:not(.s0){ display:none; }`
);

// 2. Add chomping-mouth keyframes once
pacmanSvg = pacmanSvg.replace(
  "</style>",
  `.pac-mouth{ fill:#0d1117; transform-origin:8px 8px; animation: pacchomp 220ms linear infinite; }
   @keyframes pacchomp{
     0%   { d: path("M 8 8 L 16 2 A 8 8 0 1 1 16 14 Z"); }
     50%  { d: path("M 8 8 L 16 7.5 A 8 8 0 1 1 16 8.5 Z"); }
     100% { d: path("M 8 8 L 16 2 A 8 8 0 1 1 16 14 Z"); }
   }
   </style>`
);

// 3. Swap the head <rect class="s s0" .../> for a Pac-Man <g>, keeping the
//    same "s s0" class so it inherits the exact translate animation/path.
pacmanSvg = pacmanSvg.replace(
  /<rect class="s s0"[^/]*\/>/,
  `<g class="s s0">
     <circle cx="8" cy="8" r="8" fill="#FFD700"/>
     <path class="pac-mouth" d="M 8 8 L 16 2 A 8 8 0 1 1 16 14 Z"/>
     <circle cx="9.5" cy="4" r="1.3" fill="#0d1117"/>
   </g>`
);

mkdirSync("dist", { recursive: true });
writeFileSync("dist/pacman.svg", pacmanSvg);
console.log("pacman.svg generated successfully.");
