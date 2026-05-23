"use client";

import { useState, useEffect, useRef } from "react";

interface CrashEntry {
  id: number;
  multiplier: number;
  timestamp: string;
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

interface AIAnalysisProps {
  liveHistory: CrashRound[];
  liveStats: CrashStats | null;
  isConnected: boolean;
}

export default function AIAnalysis({
  liveHistory,
  liveStats,
  isConnected,
}: AIAnalysisProps) {
  const [history, setHistory] = useState<CrashEntry[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [stats, setStats] = useState({
    average: 0,
    median: 0,
    highest: 0,
    lowest: Infinity,
    above2x: 0,
    totalRounds: 0,
  });
  const [logLines, setLogLines] = useState<string[]>([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  const generateCrashPoint = (): number => {
    const rand = Math.random();
    if (rand < 0.33) return parseFloat((1 + Math.random() * 0.5).toFixed(2));
    if (rand < 0.55) return parseFloat((1.5 + Math.random() * 1).toFixed(2));
    if (rand < 0.75) return parseFloat((2.5 + Math.random() * 2).toFixed(2));
    if (rand < 0.9) return parseFloat((4.5 + Math.random() * 5).toFixed(2));
    return parseFloat((10 + Math.random() * 40).toFixed(2));
  };

  const addLogLine = (msg: string) => {
    setLogLines((prev) => [...prev.slice(-50), msg]);
  };

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logLines]);

  const startMonitoring = () => {
    setIsMonitoring(true);
    if (isConnected) {
      addLogLine("[AI] Connected to live 1xBet data stream...");
      addLogLine("[AI] Analyzing real crash patterns...");
    } else {
      addLogLine("[AI] Starting simulated crash monitoring...");
      addLogLine("[AI] Connect 1xBet for real data analysis...");
    }

    intervalRef.current = setInterval(() => {
      if (isConnected && liveHistory.length > 0) {
        return;
      }

      const crashPoint = generateCrashPoint();
      const now = new Date();
      const timestamp = now.toLocaleTimeString();

      const entry: CrashEntry = {
        id: Date.now(),
        multiplier: crashPoint,
        timestamp,
      };

      setHistory((prev) => {
        const updated = [entry, ...prev].slice(0, 100);

        const multipliers = updated.map((e) => e.multiplier);
        const sorted = [...multipliers].sort((a, b) => a - b);
        const avg =
          multipliers.reduce((a, b) => a + b, 0) / multipliers.length;
        const mid = Math.floor(sorted.length / 2);
        const median =
          sorted.length % 2 !== 0
            ? sorted[mid]
            : (sorted[mid - 1] + sorted[mid]) / 2;

        setStats({
          average: parseFloat(avg.toFixed(2)),
          median: parseFloat(median.toFixed(2)),
          highest: Math.max(...multipliers),
          lowest: Math.min(...multipliers),
          above2x: multipliers.filter((m) => m >= 2).length,
          totalRounds: updated.length,
        });

        return updated;
      });

      if (crashPoint < 1.5) {
        addLogLine(
          `[${timestamp}] Crash @ ${crashPoint}x — LOW — Quick crash detected`
        );
      } else if (crashPoint > 10) {
        addLogLine(
          `[${timestamp}] Crash @ ${crashPoint}x — HIGH — Moon round!`
        );
      } else {
        addLogLine(`[${timestamp}] Crash @ ${crashPoint}x — Recorded`);
      }
    }, 2500);
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
    if (intervalRef.current) clearInterval(intervalRef.current);
    addLogLine("[AI] Monitoring paused. Data preserved.");
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  // Log live data from 1xBet
  const prevLiveCountRef = useRef(0);
  useEffect(() => {
    if (isConnected && liveHistory.length > prevLiveCountRef.current) {
      const newEntries = liveHistory.slice(
        0,
        liveHistory.length - prevLiveCountRef.current
      );
      for (const entry of newEntries.reverse()) {
        const ts = new Date(entry.ts).toLocaleTimeString();
        if (entry.f < 1.5) {
          addLogLine(
            `[${ts}] LIVE Crash @ ${entry.f}x — LOW — Quick crash`
          );
        } else if (entry.f > 10) {
          addLogLine(`[${ts}] LIVE Crash @ ${entry.f}x — HIGH — Moon!`);
        } else {
          addLogLine(`[${ts}] LIVE Crash @ ${entry.f}x — Recorded`);
        }
      }
      prevLiveCountRef.current = liveHistory.length;
    }
  }, [liveHistory, isConnected]);

  const getMultiplierColor = (m: number) => {
    if (m < 1.5) return "text-[#ff3b3b]";
    if (m < 2) return "text-[#ffbb00]";
    if (m < 5) return "text-[#00ff88]";
    return "text-[#00ccff]";
  };

  const displayStats = isConnected && liveStats ? liveStats : stats;
  const displayHistory = isConnected
    ? liveHistory.map((r, i) => ({
        id: i,
        multiplier: r.f,
        timestamp: new Date(r.ts).toLocaleTimeString(),
      }))
    : history;

  return (
    <div className="space-y-6">
      {/* Live data banner */}
      {isConnected && (
        <div className="glass rounded-xl p-4 border border-[#00ff88]/30">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-[#00ff88] rounded-full animate-pulse" />
            <span className="text-[#00ff88] text-sm terminal-text font-bold">
              LIVE DATA FROM 1xBet
            </span>
            <span className="text-gray-500 text-xs terminal-text ml-auto">
              {liveHistory.length} rounds captured
            </span>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-4">
        {!isConnected && (
          <button
            onClick={isMonitoring ? stopMonitoring : startMonitoring}
            className={`px-6 py-3 font-bold rounded-lg transition-all duration-300 ${
              isMonitoring
                ? "bg-[#ff3b3b] hover:bg-[#ff5555] text-white"
                : "bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black hover:opacity-90"
            }`}
          >
            {isMonitoring
              ? "STOP MONITORING"
              : "START SIMULATED MONITORING"}
          </button>
        )}
        {(isMonitoring || isConnected) && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-[#00ff88] rounded-full animate-pulse" />
            <span className="text-[#00ff88] text-sm terminal-text">
              {isConnected ? "LIVE DATA" : "SIMULATED"} — Analyzing...
            </span>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      {displayStats.totalRounds > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="glass rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Average
            </p>
            <p className="text-xl font-bold text-[#ff6b00]">
              {displayStats.average}x
            </p>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Median
            </p>
            <p className="text-xl font-bold text-[#ffbb00]">
              {displayStats.median}x
            </p>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Highest
            </p>
            <p className="text-xl font-bold text-[#00ff88]">
              {displayStats.highest}x
            </p>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Lowest
            </p>
            <p className="text-xl font-bold text-[#ff3b3b]">
              {displayStats.lowest === Infinity ? "—" : displayStats.lowest}x
            </p>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Above 2x
            </p>
            <p className="text-xl font-bold text-white">
              {displayStats.totalRounds > 0
                ? (
                    (displayStats.above2x / displayStats.totalRounds) *
                    100
                  ).toFixed(0)
                : 0}
              %
            </p>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Rounds
            </p>
            <p className="text-xl font-bold text-white">
              {displayStats.totalRounds}
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* AI Log */}
        <div className="glass rounded-xl overflow-hidden">
          <div className="bg-[#1a1f2e] px-4 py-2 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#00ff88]" />
            <span className="text-gray-400 text-xs terminal-text">
              AI Analysis Log
            </span>
          </div>
          <div className="p-4 h-64 overflow-y-auto bg-[#0d1117]">
            {logLines.length === 0 ? (
              <p className="text-gray-600 terminal-text text-sm">
                {isConnected
                  ? "Live data streaming from 1xBet..."
                  : "Start monitoring to see AI analysis..."}
              </p>
            ) : (
              logLines.map((line, i) => (
                <p
                  key={i}
                  className={`text-xs terminal-text mb-0.5 ${line.includes("LIVE") ? "text-[#00ff88]" : "text-gray-400"}`}
                >
                  {line}
                </p>
              ))
            )}
            <div ref={logEndRef} />
          </div>
        </div>

        {/* History table */}
        <div className="glass rounded-xl overflow-hidden">
          <div className="bg-[#1a1f2e] px-4 py-2 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#ff6b00]" />
            <span className="text-gray-400 text-xs terminal-text">
              {isConnected ? "Live Crash History" : "Crash History"}
            </span>
          </div>
          <div className="h-64 overflow-y-auto">
            <table className="w-full">
              <thead className="sticky top-0 bg-[#1a1f2e]">
                <tr>
                  <th className="text-left text-xs text-gray-500 px-4 py-2 terminal-text">
                    TIME
                  </th>
                  <th className="text-right text-xs text-gray-500 px-4 py-2 terminal-text">
                    CRASH POINT
                  </th>
                </tr>
              </thead>
              <tbody>
                {displayHistory.length === 0 ? (
                  <tr>
                    <td
                      colSpan={2}
                      className="text-center text-gray-600 terminal-text text-sm py-8"
                    >
                      No data yet
                    </td>
                  </tr>
                ) : (
                  displayHistory.map((entry) => (
                    <tr
                      key={entry.id}
                      className="border-t border-[#1e293b] hover:bg-[#1a1f2e] transition-colors"
                    >
                      <td className="px-4 py-2 text-xs text-gray-400 terminal-text">
                        {entry.timestamp}
                      </td>
                      <td
                        className={`px-4 py-2 text-right font-bold terminal-text ${getMultiplierColor(entry.multiplier)}`}
                      >
                        {entry.multiplier}x
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
