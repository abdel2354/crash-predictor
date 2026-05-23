"use client";

import { useEffect, useRef, useCallback, useReducer } from "react";

interface CrashGraphProps {
  targetMultiplier: number;
  isAnimating: boolean;
  onAnimationComplete: () => void;
}

interface GraphState {
  currentMultiplier: number;
  crashed: boolean;
  points: { x: number; y: number }[];
}

type GraphAction =
  | { type: "reset" }
  | { type: "update"; multiplier: number; points: { x: number; y: number }[] }
  | { type: "crash" };

function graphReducer(state: GraphState, action: GraphAction): GraphState {
  switch (action.type) {
    case "reset":
      return { currentMultiplier: 1.0, crashed: false, points: [] };
    case "update":
      return { ...state, currentMultiplier: action.multiplier, points: action.points };
    case "crash":
      return { ...state, crashed: true };
  }
}

export default function CrashGraph({
  targetMultiplier,
  isAnimating,
  onAnimationComplete,
}: CrashGraphProps) {
  const [state, dispatch] = useReducer(graphReducer, {
    currentMultiplier: 1.0,
    crashed: false,
    points: [],
  });
  const animRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onCompleteRef = useRef(onAnimationComplete);

  useEffect(() => {
    onCompleteRef.current = onAnimationComplete;
  }, [onAnimationComplete]);

  const startAnimation = useCallback((target: number) => {
    dispatch({ type: "reset" });

    const totalSteps = 100;
    const startTime = Date.now();
    const duration = 3000;

    animRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const step = Math.floor(progress * totalSteps);

      const mult = 1 + (target - 1) * Math.pow(progress, 0.7);

      const newPoints = [];
      for (let i = 0; i <= step; i++) {
        const p = i / totalSteps;
        const x = p * 280;
        const y =
          180 - Math.pow(p, 0.7) * (target - 1) * (180 / Math.max(target, 2));
        newPoints.push({ x: x + 30, y: Math.max(y, 10) });
      }

      dispatch({
        type: "update",
        multiplier: parseFloat(mult.toFixed(2)),
        points: newPoints,
      });

      if (progress >= 1) {
        if (animRef.current) clearInterval(animRef.current);
        dispatch({ type: "crash" });
        onCompleteRef.current();
      }
    }, 30);
  }, []);

  useEffect(() => {
    if (!isAnimating) return;
    startAnimation(targetMultiplier);

    return () => {
      if (animRef.current) clearInterval(animRef.current);
    };
  }, [isAnimating, targetMultiplier, startAnimation]);

  const { currentMultiplier, crashed, points } = state;

  const pathD =
    points.length > 1
      ? `M ${points.map((p) => `${p.x},${p.y}`).join(" L ")}`
      : "";

  const lastPoint = points[points.length - 1];

  return (
    <div className="relative w-full aspect-[16/10] bg-[#0d1117] rounded-xl border border-[#1e293b] overflow-hidden">
      {/* Grid lines */}
      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 320 200">
        {/* Horizontal grid lines */}
        {[40, 80, 120, 160].map((y) => (
          <line
            key={y}
            x1="30"
            y1={y}
            x2="310"
            y2={y}
            stroke="#1e293b"
            strokeWidth="0.5"
          />
        ))}
        {/* Vertical grid lines */}
        {[80, 130, 180, 230, 280].map((x) => (
          <line
            key={x}
            x1={x}
            y1="10"
            x2={x}
            y2="190"
            stroke="#1e293b"
            strokeWidth="0.5"
          />
        ))}

        {/* Crash line (graph) */}
        {pathD && (
          <>
            {/* Glow effect */}
            <path
              d={pathD}
              fill="none"
              stroke="#ff6b00"
              strokeWidth="4"
              opacity="0.3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {/* Main line */}
            <path
              d={pathD}
              fill="none"
              stroke={crashed ? "#ff3b3b" : "#ff6b00"}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {/* Area under curve */}
            {points.length > 1 && (
              <path
                d={`${pathD} L ${points[points.length - 1].x},190 L 30,190 Z`}
                fill="url(#areaGradient)"
                opacity="0.2"
              />
            )}
          </>
        )}

        {/* Plane icon at the tip */}
        {lastPoint && !crashed && (
          <g transform={`translate(${lastPoint.x - 12}, ${lastPoint.y - 12})`}>
            <text fontSize="20" className="select-none">
              ✈️
            </text>
          </g>
        )}

        {/* Crash explosion */}
        {crashed && lastPoint && (
          <g transform={`translate(${lastPoint.x}, ${lastPoint.y})`}>
            <circle r="15" fill="#ff3b3b" opacity="0.3">
              <animate
                attributeName="r"
                from="5"
                to="30"
                dur="0.5s"
                fill="freeze"
              />
              <animate
                attributeName="opacity"
                from="0.5"
                to="0"
                dur="0.5s"
                fill="freeze"
              />
            </circle>
            <text x="-8" y="5" fontSize="18" className="select-none">
              💥
            </text>
          </g>
        )}

        {/* Gradient definition */}
        <defs>
          <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ff6b00" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#ff6b00" stopOpacity="0" />
          </linearGradient>
        </defs>
      </svg>

      {/* Multiplier display */}
      <div className="absolute top-4 right-4 text-right">
        <p
          className={`text-4xl md:text-5xl font-black terminal-text transition-colors ${crashed ? "text-[#ff3b3b]" : "text-white"}`}
        >
          {currentMultiplier.toFixed(2)}x
        </p>
        {crashed && (
          <p className="text-[#ff3b3b] text-sm terminal-text mt-1 animate-fade-in-up">
            CRASHED
          </p>
        )}
      </div>

      {/* Idle state */}
      {!isAnimating && !crashed && points.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <p className="text-gray-500 terminal-text text-sm">
              Press PREDICT to generate forecast
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
