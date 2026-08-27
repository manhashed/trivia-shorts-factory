import React from 'react';
import { Star } from 'lucide-react';

export const MascotGuide: React.FC = () => {
  return (
    <div className="bg-gradient-to-br from-amber-500/10 via-yellow-500/5 to-slate-900 border border-amber-500/30 rounded-2xl p-5 relative overflow-hidden">
      <div className="flex items-start gap-4">
        {/* Mascot Avatar Icon */}
        <div className="w-14 h-14 rounded-2xl bg-amber-400/20 border border-amber-400/40 flex items-center justify-center text-3xl shadow-inner shrink-0 animate-bounce-short">
          🐻
        </div>

        <div className="space-y-2 text-xs text-slate-300">
          <div className="flex items-center gap-2">
            <h4 className="font-bold text-amber-300 text-sm flex items-center gap-1.5">
              <span>Barnaby Bear's Attention Hook Playbook</span>
              <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
            </h4>
          </div>

          <p className="text-slate-300 leading-relaxed">
            For <strong>5–8 year olds (early elementary)</strong>, curious minds thrive on:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
            <div className="p-2.5 bg-slate-900/80 rounded-xl border border-slate-700/60">
              <span className="font-bold text-amber-400 block mb-0.5">⏱️ 3s Rhythmic Countdown</span>
              <span className="text-[11px] text-slate-400">
                Gives kids a beat to shout the answer before the reveal.
              </span>
            </div>

            <div className="p-2.5 bg-slate-900/80 rounded-xl border border-slate-700/60">
              <span className="font-bold text-emerald-400 block mb-0.5">✨ Magic Fanfare Reveal</span>
              <span className="text-[11px] text-slate-400">
                Celebratory chime + excited Barnaby Bear triggers positive reinforcement.
              </span>
            </div>

            <div className="p-2.5 bg-slate-900/80 rounded-xl border border-slate-700/60">
              <span className="font-bold text-sky-400 block mb-0.5">🗣️ Ana Child Voice</span>
              <span className="text-[11px] text-slate-400">
                Natural peer-to-peer tone increases child comprehension and watch time.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
