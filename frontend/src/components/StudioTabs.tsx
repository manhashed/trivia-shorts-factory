import React from 'react';
import { HelpCircle, Music2, Sparkles } from 'lucide-react';

interface StudioTabsProps {
  activeTab: 'trivia' | 'poem';
  onSelectTab: (tab: 'trivia' | 'poem') => void;
}

export const StudioTabs: React.FC<StudioTabsProps> = ({
  activeTab,
  onSelectTab,
}) => {
  return (
    <div className="bg-slate-900 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between">
        <div className="flex items-center gap-2 py-3 overflow-x-auto custom-scrollbar">
          {/* Tab 1: Trivia & Quiz Studio */}
          <button
            type="button"
            onClick={() => onSelectTab('trivia')}
            className={`flex items-center gap-2.5 px-5 py-2.5 rounded-2xl font-bold text-xs transition select-none ${
              activeTab === 'trivia'
                ? 'bg-gradient-to-r from-amber-500 to-yellow-400 text-slate-950 shadow-lg shadow-amber-500/20'
                : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <HelpCircle className="w-4 h-4 stroke-[2.5]" />
            <span>🧠 Trivia & Quiz Factory</span>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-extrabold ${
                activeTab === 'trivia' ? 'bg-slate-950/20 text-slate-950' : 'bg-slate-700 text-slate-300'
              }`}
            >
              100+ Bank
            </span>
          </button>

          {/* Tab 2: Singing & Dancing Poem Studio */}
          <button
            type="button"
            onClick={() => onSelectTab('poem')}
            className={`flex items-center gap-2.5 px-5 py-2.5 rounded-2xl font-bold text-xs transition select-none ${
              activeTab === 'poem'
                ? 'bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white shadow-lg shadow-purple-500/20'
                : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Music2 className="w-4 h-4 stroke-[2.5]" />
            <span>🎵 Singing & Dancing Poem Studio</span>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-extrabold ${
                activeTab === 'poem' ? 'bg-white/20 text-white' : 'bg-pink-950 text-pink-300 border border-pink-700/50'
              }`}
            >
              ✨ NEW (120 BPM)
            </span>
          </button>
        </div>

        <div className="hidden md:flex items-center gap-2 text-[11px] text-slate-400 font-medium">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Multi-Format Kids 5–8 Content Engine</span>
        </div>
      </div>
    </div>
  );
};
