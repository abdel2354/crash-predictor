"use client";

import { useMemo, useSyncExternalStore } from "react";

interface LandingPageProps {
  onGetStarted: () => void;
}

function useIsMounted() {
  return useSyncExternalStore(
    (cb) => {
      cb();
      return () => {};
    },
    () => true,
    () => false
  );
}

export default function LandingPage({ onGetStarted }: LandingPageProps) {
  const mounted = useIsMounted();

  const particles = useMemo(
    () =>
      Array.from({ length: 20 }).map((_, i) => ({
        id: i,
        left: `${((i * 37 + 13) % 100)}%`,
        top: `${((i * 53 + 7) % 100)}%`,
        duration: `${3 + (i % 5)}s`,
        delay: `${(i % 4) * 0.5}s`,
      })),
    []
  );

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background grid */}
      <div className="absolute inset-0 opacity-5">
        <div
          className="w-full h-full"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,107,0,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(255,107,0,0.3) 1px, transparent 1px)",
            backgroundSize: "50px 50px",
          }}
        />
      </div>

      {/* Floating particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {mounted &&
          particles.map((p) => (
            <div
              key={p.id}
              className="absolute w-1 h-1 bg-[#ff6b00] rounded-full opacity-30"
              style={{
                left: p.left,
                top: p.top,
                animation: `float ${p.duration} ease-in-out infinite`,
                animationDelay: p.delay,
              }}
            />
          ))}
      </div>

      {/* Main content */}
      <div
        className={`text-center z-10 transition-all duration-1000 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"}`}
      >
        {/* Logo / Icon */}
        <div className="mb-8">
          <div className="inline-block relative">
            <svg
              width="120"
              height="120"
              viewBox="0 0 120 120"
              className="animate-float"
            >
              {/* Plane body */}
              <g transform="translate(60,60) rotate(-20)">
                <ellipse
                  cx="0"
                  cy="0"
                  rx="35"
                  ry="10"
                  fill="#ff6b00"
                  opacity="0.9"
                />
                <polygon
                  points="-15,-10 -5,-25 5,-10"
                  fill="#ff6b00"
                  opacity="0.8"
                />
                <polygon
                  points="20,-5 35,-15 35,0"
                  fill="#ff8c33"
                  opacity="0.7"
                />
                <ellipse cx="-30" cy="3" rx="8" ry="3" fill="#ff3b3b" opacity="0.6" />
              </g>
              {/* Trail */}
              <line
                x1="15"
                y1="85"
                x2="40"
                y2="70"
                stroke="#ff6b00"
                strokeWidth="2"
                opacity="0.4"
              />
              <line
                x1="10"
                y1="90"
                x2="35"
                y2="75"
                stroke="#ff6b00"
                strokeWidth="1.5"
                opacity="0.3"
              />
            </svg>
          </div>
        </div>

        <h1 className="text-6xl md:text-8xl font-black mb-4 tracking-tight">
          <span className="gradient-text">CRASH</span>
          <span className="text-white">HACK</span>
        </h1>

        <div className="flex items-center justify-center gap-2 mb-6">
          <div className="w-2 h-2 bg-[#00ff88] rounded-full animate-pulse" />
          <p className="text-[#00ff88] terminal-text text-sm tracking-widest uppercase">
            AI Prediction System v2.0
          </p>
          <div className="w-2 h-2 bg-[#00ff88] rounded-full animate-pulse" />
        </div>

        <p className="text-gray-400 text-lg md:text-xl mb-12 max-w-lg mx-auto px-4">
          Advanced AI-powered crash game analysis & prediction engine
        </p>

        {/* Get Started Button */}
        <button
          onClick={onGetStarted}
          className="group relative px-12 py-4 bg-gradient-to-r from-[#ff6b00] to-[#ff3b3b] text-white font-bold text-lg rounded-xl
                     hover:from-[#ff8c33] hover:to-[#ff5555] transition-all duration-300
                     animate-pulse-glow hover:scale-105 active:scale-95"
        >
          <span className="relative z-10 flex items-center gap-3">
            GET STARTED
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              className="group-hover:translate-x-1 transition-transform"
            >
              <path
                d="M4 10H16M16 10L10 4M16 10L10 16"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
        </button>

        {/* Stats */}
        <div className="mt-16 flex gap-8 md:gap-16 justify-center text-center">
          <div className="animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
            <p className="text-2xl md:text-3xl font-bold text-[#ff6b00]">98.7%</p>
            <p className="text-xs text-gray-500 uppercase tracking-wider mt-1">
              Accuracy Rate
            </p>
          </div>
          <div className="animate-fade-in-up" style={{ animationDelay: "0.4s" }}>
            <p className="text-2xl md:text-3xl font-bold text-[#ff6b00]">50K+</p>
            <p className="text-xs text-gray-500 uppercase tracking-wider mt-1">
              Predictions
            </p>
          </div>
          <div className="animate-fade-in-up" style={{ animationDelay: "0.6s" }}>
            <p className="text-2xl md:text-3xl font-bold text-[#00ff88]">LIVE</p>
            <p className="text-xs text-gray-500 uppercase tracking-wider mt-1">
              AI Status
            </p>
          </div>
        </div>
      </div>

      {/* Bottom gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#0a0e1a] to-transparent" />
    </div>
  );
}
