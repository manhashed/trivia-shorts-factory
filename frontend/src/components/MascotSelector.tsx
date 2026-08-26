import React from 'react';
import { Check, Volume2 } from 'lucide-react';
import { MascotInfo } from '../types';

interface MascotSelectorProps {
  mascots: MascotInfo[];
  selectedMascotId: string;
  onSelectMascot: (mascot: MascotInfo) => void;
}

export const MascotSelector: React.FC<MascotSelectorProps> = ({
  mascots,
  selectedMascotId,
  onSelectMascot,
}) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-bold text-white flex items-center gap-2">
          <span>Choose Your Interactive Host</span>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-300 font-semibold">
            4 Animated Mascots
          </span>
        </label>
        <span className="text-xs text-slate-400">
          Auto-pairs personality with optimal child-friendly voice
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {mascots.map((mascot) => {
          const isSelected = mascot.id === selectedMascotId;

          return (
            <div
              key={mascot.id}
              onClick={() => onSelectMascot(mascot)}
              className={`relative p-3.5 rounded-2xl border-2 transition-all cursor-pointer select-none flex flex-col items-center text-center group ${
                isSelected
                  ? 'bg-gradient-to-b from-amber-500/20 to-slate-900 border-amber-400 shadow-lg shadow-amber-500/10 scale-[1.02]'
                  : 'bg-slate-900/70 border-slate-700/80 hover:border-slate-500 hover:bg-slate-850'
              }`}
            >
              {/* Selected Checkmark Badge */}
              {isSelected && (
                <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-amber-400 text-slate-950 flex items-center justify-center shadow">
                  <Check className="w-3.5 h-3.5 stroke-[3]" />
                </div>
              )}

              {/* Mascot Avatar Emoji/Icon */}
              <div className="w-14 h-14 rounded-2xl bg-slate-800 border border-slate-700/80 flex items-center justify-center text-3xl mb-2 group-hover:scale-110 transition shadow-inner">
                {mascot.emoji}
              </div>

              <h4 className="font-bold text-slate-100 text-xs">{mascot.name}</h4>
              <p className="text-[10px] text-slate-400 line-clamp-1 mt-0.5">{mascot.tagline}</p>

              <div className="mt-2.5 flex items-center gap-1 text-[10px] text-amber-300 bg-amber-950/40 px-2 py-0.5 rounded-md border border-amber-800/40">
                <Volume2 className="w-3 h-3" />
                <span className="font-mono text-[9px]">{mascot.voice.split('-')[2] || mascot.voice}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
