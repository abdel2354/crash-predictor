---
name: testing-crashhack-ai
description: Test the CrashHack AI crash game prediction app end-to-end. Use when verifying UI, prediction flow, or AI analysis features.
---

# Testing CrashHack AI

## Setup

1. Install dependencies: `npm install`
2. Start dev server: `npm run dev -- -p 3000`
3. Open `http://localhost:3000` in Chrome

## App Flow

The app is a single-page application with state-driven transitions:

1. **Landing Page** (`/`) — Hero section with "GET STARTED" button
2. **Password Page** — Enter access key. Password is stored in `src/components/PasswordPage.tsx`
3. **Terminal Loader** — Auto-playing animation (~12s), then auto-transitions to dashboard
4. **Dashboard** — Two tabs:
   - **PREDICTION**: Click "PREDICT NEXT CRASH" to see animated graph with crash result
   - **AI ANALYSIS**: Click "START AI MONITORING" for live simulated data

## Key Test Scenarios

- **Wrong password**: Should show red "ACCESS DENIED — Invalid key" and clear input
- **Correct password**: Should transition to terminal loader
- **Terminal**: Should auto-transition to dashboard after ~12 seconds
- **Prediction**: Graph should animate with plane emoji, show multiplier, then crash with explosion
- **AI Monitoring**: Should populate stats grid, log panel, and history table with live data every 2.5s
- **Stop Monitoring**: Button should revert, data should persist, log should show "paused" message

## Build & Lint

- `npm run build` — production build
- `npm run lint` — ESLint check

## Tech Stack

- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS v4
- No backend — fully client-side

## Notes

- Predictions are randomly generated (no real AI backend)
- The terminal loader takes ~12 seconds — wait for it to auto-transition
- AI monitoring generates data every 2.5 seconds via `setInterval`
