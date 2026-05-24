import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const host = request.headers.get("host") || "crash-predictor-six.vercel.app";
  const protocol = host.includes("localhost") ? "http" : "https";
  const baseUrl = `${protocol}://${host}`;

  const script = `
// CrashHack AI — 1xBet Crash Data Capture Script
// Paste this in your browser console on the 1xBet Crash game page
(function() {
  const API_URL = "${baseUrl}/api/crash-data";
  let roundCount = 0;

  console.log("\\n%c CRASHHACK AI ", "background:#ff6b00;color:white;font-size:16px;padding:5px 20px;border-radius:5px;");
  console.log("%c Real-time crash data capture started...", "color:#00ff88;font-size:12px;");
  console.log("%c Waiting for crash events...\\n", "color:#888;font-size:11px;");

  // Method 1: Intercept WebSocket messages
  const OriginalWebSocket = window.WebSocket;
  window.WebSocket = function(...args) {
    const ws = new OriginalWebSocket(...args);

    ws.addEventListener("message", function(event) {
      try {
        let data = event.data;
        if (typeof data === "string" && data.includes('"OnCrash"')) {
          data = data.replace(/[^\\x20-\\x7E]/g, "");
          const parsed = JSON.parse(data);
          if (parsed.target === "OnCrash" && parsed.arguments && parsed.arguments[0]) {
            const crashData = parsed.arguments[0];
            roundCount++;

            const color = crashData.f < 2 ? "#ff3b3b" : crashData.f < 5 ? "#ffbb00" : "#00ff88";
            console.log(
              "%c[CRASH #" + roundCount + "] %c" + crashData.f + "x",
              "color:#888;font-size:11px;",
              "color:" + color + ";font-weight:bold;font-size:13px;"
            );

            // Get player/bet data from DOM
            const playerEl = document.querySelector('.crash-total__value--players');
            const betEl = document.querySelector('.crash-total__value--bets');
            const winEl = document.querySelector('.crash-total__value--prize');

            const payload = {
              f: crashData.f,
              l: crashData.l,
              ts: crashData.ts || new Date().toISOString(),
              totalPlayers: playerEl ? playerEl.innerText : undefined,
              totalBets: betEl ? betEl.innerText : undefined,
              totalPrize: winEl ? winEl.innerText : undefined,
            };

            fetch(API_URL, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            })
            .then(r => r.json())
            .then(res => {
              if (res.prediction) {
                const p = res.prediction;
                console.log(
                  "%c  AI: Range " + p.predictedRange.min + "x - " + p.predictedRange.max + "x | Safe exit: " + p.safeExit + "x | Strategy: " + p.strategy + " (" + p.confidence + "%)",
                  "color:#00ccff;font-size:10px;"
                );
              }
            })
            .catch(() => {});
          }
        }
      } catch(e) {}
    });

    return ws;
  };
  window.WebSocket.prototype = OriginalWebSocket.prototype;

  // Method 2: Also monitor DOM for crash values (fallback)
  let lastCrashValue = "";
  setInterval(() => {
    try {
      const frames = document.querySelectorAll("iframe");
      for (const frame of frames) {
        try {
          const frameDoc = frame.contentDocument || frame.contentWindow?.document;
          if (!frameDoc) continue;
          const crashEl = frameDoc.querySelector(".crash-multiplier, .crash-value, [class*='crash'][class*='value']");
          if (crashEl) {
            const val = crashEl.innerText;
            if (val !== lastCrashValue && val.includes("x")) {
              lastCrashValue = val;
            }
          }
        } catch(e) {}
      }
    } catch(e) {}
  }, 500);

  console.log("%c Script active! Keep this tab open while playing.", "color:#ff6b00;font-size:11px;");
  console.log("%c Data is being sent to CrashHack AI dashboard.\\n", "color:#888;font-size:10px;");
})();
`;

  return new NextResponse(script, {
    headers: {
      "Content-Type": "application/javascript",
      "Access-Control-Allow-Origin": "*",
    },
  });
}
