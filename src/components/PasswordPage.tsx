"use client";

import { useState, useRef, useEffect } from "react";

interface PasswordPageProps {
  onSuccess: () => void;
}

const CORRECT_PASSWORD = "HATIM200707";

export default function PasswordPage({ onSuccess }: PasswordPageProps) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const [shake, setShake] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === CORRECT_PASSWORD) {
      setError(false);
      onSuccess();
    } else {
      setError(true);
      setShake(true);
      setTimeout(() => setShake(false), 500);
      setPassword("");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Background scanline effect */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none">
        <div
          className="w-full h-full"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,107,0,0.1) 2px, rgba(255,107,0,0.1) 4px)",
          }}
        />
      </div>

      <div
        className={`glass rounded-2xl p-8 md:p-12 w-full max-w-md mx-4 text-center transition-transform ${shake ? "animate-crash-shake" : ""}`}
      >
        {/* Lock icon */}
        <div className="mb-6">
          <div className="w-20 h-20 mx-auto rounded-full border-2 border-[#ff6b00] flex items-center justify-center">
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#ff6b00"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>
        </div>

        <h2 className="text-2xl font-bold text-white mb-2">ACCESS REQUIRED</h2>
        <p className="text-gray-400 text-sm mb-8 terminal-text">
          Enter authorization key to continue
        </p>

        <form onSubmit={handleSubmit}>
          <div className="relative mb-4">
            <input
              ref={inputRef}
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError(false);
              }}
              placeholder="Enter access key..."
              className="w-full px-4 py-3 bg-[#0a0e1a] border border-[#1e293b] rounded-lg text-white
                         placeholder-gray-600 focus:outline-none focus:border-[#ff6b00] transition-colors
                         terminal-text text-center tracking-widest"
            />
            {error && (
              <div className="absolute -bottom-6 left-0 right-0">
                <p className="text-[#ff3b3b] text-xs terminal-text flex items-center justify-center gap-1">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="15" y1="9" x2="9" y2="15" />
                    <line x1="9" y1="9" x2="15" y2="15" />
                  </svg>
                  ACCESS DENIED — Invalid key
                </p>
              </div>
            )}
          </div>

          <button
            type="submit"
            className="w-full mt-6 px-6 py-3 bg-gradient-to-r from-[#ff6b00] to-[#ff3b3b] text-white font-bold rounded-lg
                       hover:from-[#ff8c33] hover:to-[#ff5555] transition-all duration-300
                       hover:scale-[1.02] active:scale-[0.98]"
          >
            AUTHENTICATE
          </button>
        </form>

        <div className="mt-8 flex items-center justify-center gap-2">
          <div className="w-1.5 h-1.5 bg-[#ff6b00] rounded-full animate-pulse" />
          <p className="text-gray-600 text-xs terminal-text">
            CRASHHACK AI v2.0 — Secured Connection
          </p>
        </div>
      </div>
    </div>
  );
}
