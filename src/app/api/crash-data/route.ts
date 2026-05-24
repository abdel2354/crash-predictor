import { NextRequest, NextResponse } from "next/server";

interface CrashRound {
  f: number;
  l: number;
  ts: string;
  totalPlayers?: string;
  totalBets?: string;
  totalPrize?: string;
}

const crashHistory: CrashRound[] = [];
const MAX_HISTORY = 500;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const rounds = Array.isArray(body) ? body : [body];

    for (const round of rounds) {
      if (round.f !== undefined) {
        crashHistory.unshift({
          f: Number(round.f),
          l: Number(round.l || 0),
          ts: round.ts || new Date().toISOString(),
          totalPlayers: round.totalPlayers,
          totalBets: round.totalBets,
          totalPrize: round.totalPrize,
        });
      }
    }

    while (crashHistory.length > MAX_HISTORY) {
      crashHistory.pop();
    }

    const prediction = generatePrediction(crashHistory);

    return NextResponse.json({
      success: true,
      totalRounds: crashHistory.length,
      prediction,
    });
  } catch {
    return NextResponse.json({ success: false }, { status: 400 });
  }
}

export async function GET() {
  const prediction = generatePrediction(crashHistory);

  const stats = computeStats(crashHistory);

  return NextResponse.json({
    history: crashHistory.slice(0, 100),
    totalRounds: crashHistory.length,
    prediction,
    stats,
  });
}

function computeStats(history: CrashRound[]) {
  if (history.length === 0) {
    return {
      average: 0,
      median: 0,
      highest: 0,
      lowest: 0,
      above2x: 0,
      above5x: 0,
      above10x: 0,
      totalRounds: 0,
      recentTrend: "neutral" as const,
      streakInfo: "",
    };
  }

  const multipliers = history.map((r) => r.f);
  const sorted = [...multipliers].sort((a, b) => a - b);
  const avg = multipliers.reduce((a, b) => a + b, 0) / multipliers.length;
  const mid = Math.floor(sorted.length / 2);
  const median =
    sorted.length % 2 !== 0
      ? sorted[mid]
      : (sorted[mid - 1] + sorted[mid]) / 2;

  const above2x = multipliers.filter((m) => m >= 2).length;
  const above5x = multipliers.filter((m) => m >= 5).length;
  const above10x = multipliers.filter((m) => m >= 10).length;

  const recent10 = multipliers.slice(0, Math.min(10, multipliers.length));
  const recent10Avg =
    recent10.reduce((a, b) => a + b, 0) / recent10.length;
  const recentTrend: "up" | "down" | "neutral" =
    recent10Avg > avg * 1.2 ? "up" : recent10Avg < avg * 0.8 ? "down" : "neutral";

  let currentStreak = 0;
  let streakType = "";
  if (multipliers.length > 0) {
    const threshold = 2;
    const firstAbove = multipliers[0] >= threshold;
    streakType = firstAbove ? "above 2x" : "below 2x";
    for (const m of multipliers) {
      if ((m >= threshold) === firstAbove) {
        currentStreak++;
      } else {
        break;
      }
    }
  }

  return {
    average: parseFloat(avg.toFixed(2)),
    median: parseFloat(median.toFixed(2)),
    highest: Math.max(...multipliers),
    lowest: Math.min(...multipliers),
    above2x,
    above5x,
    above10x,
    totalRounds: history.length,
    recentTrend,
    streakInfo: `${currentStreak} rounds ${streakType}`,
  };
}

function generatePrediction(history: CrashRound[]) {
  if (history.length < 3) {
    return {
      predictedRange: { min: 1.2, max: 3.5 },
      confidence: 30,
      signals: ["Not enough data — need at least 10 rounds for analysis"],
      strategy: "WAIT",
      safeExit: 1.5,
    };
  }

  const multipliers = history.map((r) => r.f);
  const recent = multipliers.slice(0, Math.min(20, multipliers.length));
  const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
  const sortedRecent = [...recent].sort((a, b) => a - b);
  const midIdx = Math.floor(sortedRecent.length / 2);
  const median =
    sortedRecent.length % 2 !== 0
      ? sortedRecent[midIdx]
      : (sortedRecent[midIdx - 1] + sortedRecent[midIdx]) / 2;

  const signals: string[] = [];
  let confidence = 50;

  // Streak analysis
  let lowStreak = 0;
  for (const m of recent) {
    if (m < 2) lowStreak++;
    else break;
  }

  let highStreak = 0;
  for (const m of recent) {
    if (m >= 3) highStreak++;
    else break;
  }

  if (lowStreak >= 3) {
    signals.push(
      `${lowStreak} consecutive rounds below 2x — higher crash likely`
    );
    confidence += lowStreak * 5;
  }

  if (highStreak >= 3) {
    signals.push(
      `${highStreak} consecutive high rounds — low crash risk increasing`
    );
    confidence -= highStreak * 3;
  }

  // Moving average comparison
  const ma5 =
    recent.slice(0, 5).reduce((a, b) => a + b, 0) /
    Math.min(5, recent.length);
  const ma10 =
    recent.slice(0, 10).reduce((a, b) => a + b, 0) /
    Math.min(10, recent.length);

  if (ma5 > ma10 * 1.3) {
    signals.push("Short-term trend UP — momentum is bullish");
    confidence += 8;
  } else if (ma5 < ma10 * 0.7) {
    signals.push("Short-term trend DOWN — caution advised");
    confidence -= 5;
  }

  // Volatility analysis
  const variance =
    recent.reduce((sum, m) => sum + Math.pow(m - recentAvg, 2), 0) /
    recent.length;
  const stdDev = Math.sqrt(variance);

  if (stdDev > recentAvg * 0.8) {
    signals.push("HIGH volatility — unpredictable rounds");
    confidence -= 10;
  } else if (stdDev < recentAvg * 0.3) {
    signals.push("LOW volatility — stable pattern detected");
    confidence += 10;
  }

  // 60% payout rule analysis (if bet data available)
  const lastWithBets = history.find((r) => r.totalBets);
  if (lastWithBets?.totalBets && lastWithBets?.totalPrize) {
    const bets = parseInt(lastWithBets.totalBets.replace(/[^\d]/g, ""), 10);
    const prize = parseInt(lastWithBets.totalPrize.replace(/[^\d]/g, ""), 10);
    if (bets > 0) {
      const payoutRatio = prize / bets;
      if (payoutRatio < 0.4) {
        signals.push(
          `Payout ratio ${(payoutRatio * 100).toFixed(0)}% — platform may allow higher crash`
        );
        confidence += 12;
      } else if (payoutRatio > 0.7) {
        signals.push(
          `Payout ratio ${(payoutRatio * 100).toFixed(0)}% — quick crash likely to recover margin`
        );
        confidence -= 8;
      }
    }
  }

  // Last value pattern
  const last = multipliers[0];
  if (last < 1.3) {
    signals.push("Last round was instant crash — recovery bounce possible");
    confidence += 7;
  } else if (last > 15) {
    signals.push("Last round was moon — regression to mean expected");
    confidence -= 5;
  }

  confidence = Math.max(20, Math.min(95, confidence));

  // Predicted range calculation
  const predictedCenter = recentAvg * (lowStreak >= 3 ? 1.4 : highStreak >= 3 ? 0.7 : 1.0);
  const range = {
    min: parseFloat(Math.max(1.01, predictedCenter - stdDev * 0.5).toFixed(2)),
    max: parseFloat((predictedCenter + stdDev * 1.2).toFixed(2)),
  };

  // Safe exit recommendation
  const safeExit = parseFloat(
    Math.max(1.2, Math.min(recentAvg * 0.6, median * 0.8)).toFixed(2)
  );

  const strategy: string =
    lowStreak >= 4
      ? "AGGRESSIVE"
      : highStreak >= 3
        ? "CONSERVATIVE"
        : confidence > 70
          ? "MODERATE"
          : "WAIT";

  if (signals.length === 0) {
    signals.push("Pattern analysis active — collecting more data");
  }

  return {
    predictedRange: range,
    confidence,
    signals,
    strategy,
    safeExit,
  };
}
