"use client";

import { useState } from "react";
import LandingPage from "@/components/LandingPage";
import PasswordPage from "@/components/PasswordPage";
import TerminalLoader from "@/components/TerminalLoader";
import Dashboard from "@/components/Dashboard";

type AppState = "landing" | "password" | "loading" | "dashboard";

export default function Home() {
  const [appState, setAppState] = useState<AppState>("landing");

  return (
    <main className="min-h-screen">
      {appState === "landing" && (
        <LandingPage onGetStarted={() => setAppState("password")} />
      )}
      {appState === "password" && (
        <PasswordPage onSuccess={() => setAppState("loading")} />
      )}
      {appState === "loading" && (
        <TerminalLoader onComplete={() => setAppState("dashboard")} />
      )}
      {appState === "dashboard" && <Dashboard />}
    </main>
  );
}
