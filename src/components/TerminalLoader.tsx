"use client";

import { useEffect, useState } from "react";

interface TerminalLoaderProps {
  onComplete: () => void;
}

const TERMINAL_LINES = [
  { text: "$ Initializing CrashHack AI v2.0...", delay: 0, type: "command" },
  { text: "[OK] System boot sequence started", delay: 800, type: "success" },
  { text: "$ Connecting to prediction servers...", delay: 1500, type: "command" },
  { text: "[OK] Secure connection established (TLS 1.3)", delay: 2300, type: "success" },
  { text: "$ Loading neural network models...", delay: 3000, type: "command" },
  { text: "   ├── crash_pattern_v3.model [128MB]", delay: 3500, type: "info" },
  { text: "   ├── time_series_analyzer.model [64MB]", delay: 3900, type: "info" },
  { text: "   └── probability_engine.model [256MB]", delay: 4300, type: "info" },
  { text: "[OK] All models loaded successfully", delay: 4800, type: "success" },
  { text: "$ Decrypting historical crash data...", delay: 5500, type: "command" },
  { text: "   Processing 1,247,832 data points...", delay: 6000, type: "info" },
  { text: "[OK] Data decryption complete — AES-256", delay: 6800, type: "success" },
  { text: "$ Calibrating AI prediction engine...", delay: 7500, type: "command" },
  { text: "   Accuracy: 98.7% | Confidence: HIGH", delay: 8200, type: "info" },
  { text: "[OK] Engine calibrated and ready", delay: 8800, type: "success" },
  { text: "$ Running system diagnostics...", delay: 9400, type: "command" },
  { text: "[OK] All systems operational", delay: 10000, type: "success" },
  { text: "", delay: 10500, type: "blank" },
  { text: "★ CRASHHACK AI IS READY", delay: 11000, type: "final" },
  { text: "  Launching dashboard...", delay: 11500, type: "info" },
];

export default function TerminalLoader({ onComplete }: TerminalLoaderProps) {
  const [visibleLines, setVisibleLines] = useState<number>(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    TERMINAL_LINES.forEach((line, index) => {
      const timer = setTimeout(() => {
        setVisibleLines(index + 1);
        setProgress(((index + 1) / TERMINAL_LINES.length) * 100);
      }, line.delay);
      timers.push(timer);
    });

    const completeTimer = setTimeout(() => {
      onComplete();
    }, 12500);
    timers.push(completeTimer);

    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  const getLineColor = (type: string) => {
    switch (type) {
      case "command":
        return "text-[#ff6b00]";
      case "success":
        return "text-[#00ff88]";
      case "info":
        return "text-gray-400";
      case "final":
        return "text-[#ff6b00] font-bold text-lg";
      default:
        return "text-gray-500";
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Terminal window */}
        <div className="rounded-xl overflow-hidden border border-[#1e293b]">
          {/* Title bar */}
          <div className="bg-[#1a1f2e] px-4 py-2 flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#ff3b3b]" />
            <div className="w-3 h-3 rounded-full bg-[#ffbb00]" />
            <div className="w-3 h-3 rounded-full bg-[#00ff88]" />
            <span className="ml-3 text-gray-500 text-xs terminal-text">
              crashhack-ai — terminal
            </span>
          </div>

          {/* Terminal body */}
          <div className="bg-[#0d1117] p-4 md:p-6 min-h-[400px] max-h-[500px] overflow-y-auto">
            {TERMINAL_LINES.slice(0, visibleLines).map((line, index) => (
              <div
                key={index}
                className={`terminal-text text-sm md:text-base mb-1 animate-fade-in-up ${getLineColor(line.type)}`}
                style={{ animationDuration: "0.3s" }}
              >
                {line.text}
                {index === visibleLines - 1 && (
                  <span className="inline-block w-2 h-4 bg-[#ff6b00] ml-1 animate-blink" />
                )}
              </div>
            ))}
          </div>

          {/* Progress bar */}
          <div className="bg-[#1a1f2e] px-4 py-2">
            <div className="flex items-center gap-3">
              <div className="flex-1 h-1.5 bg-[#0d1117] rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-[#ff6b00] to-[#00ff88] rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-xs terminal-text text-gray-400 w-10 text-right">
                {Math.round(progress)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
