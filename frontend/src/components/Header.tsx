import React from 'react';
import { Sparkles, CheckCircle, AlertCircle } from 'lucide-react';
import { HealthStatus } from '../types';

interface HeaderProps {
  health: HealthStatus | null;
}

function ttsBadgeLabel(health: HealthStatus | null): string {
  const tts = health?.tts;
  if (!tts) return 'Edge Neural TTS (Free)';
  const provider = tts.providers[tts.default_provider];
  if (tts.default_provider === 'edge' || !provider?.configured) {
    return 'Edge Neural TTS (Free)';
  }
  return `${provider.label} (from .env)`;
}

export const Header: React.FC<HeaderProps> = ({ health }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand & Mascot */}
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500 to-yellow-300 flex items-center justify-center shadow-lg shadow-amber-500/20 text-2xl animate-bounce-short">
            🐻
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5 font-sans">
                Trivia Shorts Factory
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-400/20 text-amber-300 border border-amber-400/30 font-medium">
                  Kids 5–8 Edition
                </span>
              </h1>
            </div>
            <p className="text-xs text-slate-400">
              Host: <strong className="text-amber-300">Barnaby Bear</strong> • High-Retention 9:16 Video Automation
            </p>
          </div>
        </div>

        {/* System Health / Engine Status */}
        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 text-xs">
            <span className="text-slate-400">Engine:</span>
            {health?.ffmpeg_installed ? (
              <span className="flex items-center text-emerald-400 font-medium">
                <CheckCircle className="w-3.5 h-3.5 mr-1" /> FFmpeg 7.1 Active
              </span>
            ) : (
              <span className="flex items-center text-rose-400 font-medium">
                <AlertCircle className="w-3.5 h-3.5 mr-1" /> Initializing Engine
              </span>
            )}
          </div>

          <div className="flex items-center space-x-1 text-xs text-slate-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-xl text-amber-300">
            <Sparkles className="w-3.5 h-3.5" />
            <span>{ttsBadgeLabel(health)}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
