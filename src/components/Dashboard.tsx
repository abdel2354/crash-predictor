"use client";

import { useState, useCallback } from "react";
import CrashGraph from "./CrashGraph";
import AIAnalysis from "./AIAnalysis";

type Tab = "predict" | "analysis";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>("predict");
  const [isAnimating, setIsAnimating] = useState(false);
  const [predictedValue, setPredictedValue] = useState<number | null>(null);
  const [confidence, setConfidence] = useState<number>(0);
  const [predictionHistory, setPredictionHistory] = useState<
    { value: number; confidence: number; time: string }[]
  >([]);

  const generatePrediction = (): number => {
    const rand = Math.random();
    if (rand < 0.3) return parseFloat((1.1 + Math.random() * 0.8).toFixed(2));
    if (rand < 0.55) return parseFloat((1.9 + Math.random() * 1.5).toFixed(2));
    if (rand < 0.75) return parseFloat((3.4 + Math.random() * 3).toFixed(2));
    if (rand < 0.9) return parseFloat((6.4 + Math.random() * 6).toFixed(2));
    return parseFloat((12.4 + Math.random() * 30).toFixed(2));
  };

  const handlePredict = () => {
    if (isAnimating) return;
    const value = generatePrediction();
    const conf = Math.floor(60 + Math.random() * 35);
    setPredictedValue(value);
    setConfidence(conf);
    setIsAnimating(true);
  };

  const handleAnimationComplete = useCallback(() => {
    setIsAnimating(false);
    if (predictedValue !== null) {
      setPredictionHistory((prev) => [
        {
          value: predictedValue,
          confidence,
          time: new Date().toLocaleTimeString(),
        },
        ...prev,
      ].slice(0, 20));
    }
  }, [predictedValue, confidence]);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top bar */}
      <header className="glass border-b border-[#1e293b] px-4 md:px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-black">
            <span className="gradient-text">CRASH</span>
            <span className="text-white">HACK</span>
          </h1>
          <div className="hidden md:flex items-center gap-1.5 ml-4">
            <div className="w-1.5 h-1.5 bg-[#00ff88] rounded-full animate-pulse" />
            <span className="text-[#00ff88] text-xs terminal-text">
              AI ONLINE
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500 terminal-text">
          <span className="hidden md:inline">crashhack.online</span>
          <div className="w-1.5 h-1.5 bg-[#ff6b00] rounded-full" />
        </div>
      </header>

      {/* Tab buttons */}
      <div className="px-4 md:px-6 pt-4">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab("predict")}
            className={`px-6 py-2.5 rounded-lg font-bold text-sm transition-all duration-300 ${
              activeTab === "predict"
                ? "bg-gradient-to-r from-[#ff6b00] to-[#ff3b3b] text-white"
                : "bg-[#111827] text-gray-400 hover:text-white border border-[#1e293b]"
            }`}
          >
            🎯 PREDICTION
          </button>
          <button
            onClick={() => setActiveTab("analysis")}
            className={`px-6 py-2.5 rounded-lg font-bold text-sm transition-all duration-300 ${
              activeTab === "analysis"
                ? "bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black"
                : "bg-[#111827] text-gray-400 hover:text-white border border-[#1e293b]"
            }`}
          >
            🧠 AI ANALYSIS
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-4 md:p-6">
        {activeTab === "predict" && (
          <div className="space-y-6">
            {/* Graph */}
            <CrashGraph
              targetMultiplier={predictedValue ?? 1}
              isAnimating={isAnimating}
              onAnimationComplete={handleAnimationComplete}
            />

            {/* Prediction result */}
            {predictedValue !== null && !isAnimating && (
              <div className="glass rounded-xl p-6 text-center animate-fade-in-up">
                <p className="text-gray-400 text-sm mb-2 terminal-text">
                  AI PREDICTION RESULT
                </p>
                <p className="text-5xl font-black text-[#ff6b00] mb-2">
                  {predictedValue}x
                </p>
                <div className="flex items-center justify-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full ${confidence > 80 ? "bg-[#00ff88]" : confidence > 60 ? "bg-[#ffbb00]" : "bg-[#ff3b3b]"}`}
                  />
                  <p className="text-sm terminal-text text-gray-400">
                    Confidence:{" "}
                    <span
                      className={
                        confidence > 80
                          ? "text-[#00ff88]"
                          : confidence > 60
                            ? "text-[#ffbb00]"
                            : "text-[#ff3b3b]"
                      }
                    >
                      {confidence}%
                    </span>
                  </p>
                </div>
              </div>
            )}

            {/* Predict button */}
            <div className="text-center">
              <button
                onClick={handlePredict}
                disabled={isAnimating}
                className={`px-12 py-4 font-bold text-lg rounded-xl transition-all duration-300
                  ${
                    isAnimating
                      ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                      : "bg-gradient-to-r from-[#ff6b00] to-[#ff3b3b] text-white hover:from-[#ff8c33] hover:to-[#ff5555] hover:scale-105 active:scale-95 animate-pulse-glow"
                  }`}
              >
                {isAnimating ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    ANALYZING...
                  </span>
                ) : (
                  "🎯 PREDICT NEXT CRASH"
                )}
              </button>
            </div>

            {/* Prediction history */}
            {predictionHistory.length > 0 && (
              <div className="glass rounded-xl overflow-hidden">
                <div className="bg-[#1a1f2e] px-4 py-2 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#ff6b00]" />
                  <span className="text-gray-400 text-xs terminal-text">
                    Prediction History
                  </span>
                </div>
                <div className="p-4 max-h-48 overflow-y-auto">
                  <div className="grid grid-cols-3 gap-2 text-xs terminal-text text-gray-500 mb-2 px-2">
                    <span>TIME</span>
                    <span className="text-center">PREDICTION</span>
                    <span className="text-right">CONFIDENCE</span>
                  </div>
                  {predictionHistory.map((entry, i) => (
                    <div
                      key={i}
                      className="grid grid-cols-3 gap-2 text-sm terminal-text py-1.5 px-2 rounded hover:bg-[#1a1f2e] transition-colors"
                    >
                      <span className="text-gray-400">{entry.time}</span>
                      <span
                        className={`text-center font-bold ${
                          entry.value < 2
                            ? "text-[#ff3b3b]"
                            : entry.value < 5
                              ? "text-[#ffbb00]"
                              : "text-[#00ff88]"
                        }`}
                      >
                        {entry.value}x
                      </span>
                      <span
                        className={`text-right ${
                          entry.confidence > 80
                            ? "text-[#00ff88]"
                            : entry.confidence > 60
                              ? "text-[#ffbb00]"
                              : "text-[#ff3b3b]"
                        }`}
                      >
                        {entry.confidence}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "analysis" && <AIAnalysis />}
      </div>

      {/* Footer */}
      <footer className="glass border-t border-[#1e293b] px-4 py-3 text-center">
        <p className="text-gray-600 text-xs terminal-text">
          CrashHack AI v2.0 — For educational & analysis purposes only —
          crashhack.online
        </p>
      </footer>
    </div>
  );
}
