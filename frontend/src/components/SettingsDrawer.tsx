import React, { useState } from 'react';
import {
  Sliders,
  Volume2,
  Clock,
  Music,
  Shuffle,
  Key,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';
import { VideoRenderConfig, VoiceOption } from '../types';

interface SettingsDrawerProps {
  config: VideoRenderConfig;
  voices: Record<string, VoiceOption[]>;
  onChange: (updated: Partial<VideoRenderConfig>) => void;
}

export const SettingsDrawer: React.FC<SettingsDrawerProps> = ({
  config,
  voices,
  onChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);

  const edgeVoices = voices['edge'] || [];
  const openaiVoices = voices['openai'] || [];

  return (
    <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 space-y-4">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between cursor-pointer select-none"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>Step 2: Video, Audio & Batch Mix Settings</span>
              {config.mix_mode ? (
                <span className="text-xs px-2.5 py-0.5 bg-gradient-to-r from-purple-500/30 to-pink-500/30 text-pink-300 border border-pink-400/40 rounded-full font-bold flex items-center gap-1">
                  <Shuffle className="w-3 h-3" />
                  <span>Mix & Match Mode Active</span>
                </span>
              ) : (
                <span className="text-xs px-2 py-0.5 bg-amber-400/20 text-amber-300 rounded font-normal">
                  Kids 3–5 Optimized
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-400">
              {config.mix_mode
                ? 'Rotating 4 mascots, 5 stock themes, and friendly voices across all batch shorts'
                : `Voice: ${config.tts_voice} • Countdown: ${config.countdown_duration}s • BGM: ${config.bgm_track}`}
            </p>
          </div>
        </div>

        <button
          type="button"
          className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-700/50 transition"
        >
          {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {/* Batch Mix Mode Highlight Banner */}
      <div className="p-3 bg-gradient-to-r from-purple-950/40 via-slate-900 to-pink-950/40 rounded-xl border border-purple-800/60 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-purple-500/20 text-purple-300 flex items-center justify-center shrink-0">
            <Shuffle className="w-4 h-4" />
          </div>
          <div>
            <p className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
              <span>🎲 Rotate & Mix Mascots, Themes & Voices Across Batch</span>
              <span className="text-[10px] px-1.5 py-0.5 bg-purple-400/20 text-purple-300 rounded">
                Recommended for Playlists
              </span>
            </p>
            <p className="text-[11px] text-slate-400">
              Every video in your batch will get a unique combination of Barnaby/Penny/Leo/Bella and Candy/Space/Safari/Ocean themes!
            </p>
          </div>
        </div>

        <label className="relative inline-flex items-center cursor-pointer shrink-0">
          <input
            type="checkbox"
            checked={config.mix_mode}
            onChange={(e) => onChange({ mix_mode: e.target.checked })}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
        </label>
      </div>

      {isOpen && (
        <div className="pt-4 border-t border-slate-700/60 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-xs">
          {/* 1. Voice & TTS Provider */}
          <div className="space-y-3">
            <label className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Volume2 className="w-4 h-4 text-amber-400" />
              <span>Voice / Narrator {config.mix_mode && '(Default fallback)'}</span>
            </label>

            <select
              value={config.tts_voice}
              disabled={config.mix_mode}
              onChange={(e) => {
                const val = e.target.value;
                const isOai = openaiVoices.some((v) => v.id === val);
                onChange({
                  tts_voice: val,
                  tts_provider: isOai ? 'openai' : 'edge',
                });
              }}
              className={`w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-400 transition ${
                config.mix_mode ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <optgroup label="Microsoft Edge Neural (Free & Recommended for Kids)">
                {edgeVoices.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </optgroup>
              {openaiVoices.length > 0 && (
                <optgroup label="OpenAI TTS (Requires API Key)">
                  {openaiVoices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>

            <div className="flex items-center justify-between text-slate-400">
              <span>Voice Speed:</span>
              <div className="flex gap-1.5">
                {['-10%', '+0%', '+10%'].map((rate) => (
                  <button
                    key={rate}
                    type="button"
                    onClick={() => onChange({ tts_speed: rate })}
                    className={`px-2 py-1 rounded-md text-[11px] font-medium transition ${
                      config.tts_speed === rate
                        ? 'bg-amber-500 text-slate-900 font-bold'
                        : 'bg-slate-900 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {rate}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between text-slate-400">
              <span>Voice Pitch:</span>
              <div className="flex gap-1.5">
                {['-20Hz', '+0Hz', '+20Hz'].map((pitch) => (
                  <button
                    key={pitch}
                    type="button"
                    onClick={() => onChange({ tts_pitch: pitch })}
                    className={`px-2 py-1 rounded-md text-[11px] font-medium transition ${
                      config.tts_pitch === pitch
                        ? 'bg-amber-500 text-slate-900 font-bold'
                        : 'bg-slate-900 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {pitch}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 2. Countdown & SFX */}
          <div className="space-y-3">
            <label className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-amber-400" />
              <span>Countdown & Sound Effects</span>
            </label>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Timer Duration:</span>
                <span className="font-bold text-amber-300">{config.countdown_duration}s</span>
              </div>
              <input
                type="range"
                min="2.0"
                max="5.0"
                step="0.5"
                value={config.countdown_duration}
                onChange={(e) => onChange({ countdown_duration: parseFloat(e.target.value) })}
                className="w-full accent-amber-400"
              />
            </div>

            <div className="space-y-1">
              <span className="text-slate-400">Countdown SFX:</span>
              <div className="grid grid-cols-3 gap-1.5 pt-1">
                {[
                  { id: 'tick_tock', label: '🪵 Tick-Tock' },
                  { id: 'beep', label: '🔔 Beeps' },
                  { id: 'mute', label: '🔇 Silent' },
                ].map((sfx) => (
                  <button
                    key={sfx.id}
                    type="button"
                    onClick={() => onChange({ countdown_sfx: sfx.id as any })}
                    className={`py-1.5 px-2 rounded-lg text-center font-medium transition text-[11px] ${
                      config.countdown_sfx === sfx.id
                        ? 'bg-amber-500 text-slate-900 font-bold'
                        : 'bg-slate-900 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {sfx.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 3. Background Music (BGM) */}
          <div className="space-y-3">
            <label className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Music className="w-4 h-4 text-amber-400" />
              <span>Background Nursery Music</span>
            </label>

            <select
              value={config.bgm_track}
              onChange={(e) => onChange({ bgm_track: e.target.value as any })}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-400 transition"
            >
              <option value="playful_nursery">🎶 Playful Ukulele & Xylophone</option>
              <option value="magical_story">✨ Dreamy Storybook Bells</option>
              <option value="none">🔇 No Background Music</option>
            </select>

            {config.bgm_track !== 'none' && (
              <div className="space-y-1.5 pt-1">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Music Volume:</span>
                  <span className="font-bold text-amber-300">{Math.round(config.bgm_volume * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.4"
                  step="0.05"
                  value={config.bgm_volume}
                  onChange={(e) => onChange({ bgm_volume: parseFloat(e.target.value) })}
                  className="w-full accent-amber-400"
                />
              </div>
            )}
          </div>

          {/* 4. Animation & Visual Effects */}
          <div className="col-span-full pt-3 border-t border-slate-700/40">
            <label className="font-semibold text-slate-200 flex items-center gap-1.5 mb-3">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>Animation & Visual Effects</span>
              <span className="text-[10px] px-1.5 py-0.5 bg-emerald-400/20 text-emerald-300 rounded font-normal">NEW</span>
            </label>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {/* Animation Style */}
              <div className="space-y-1.5">
                <span className="text-slate-400">Animation Style:</span>
                <div className="grid grid-cols-2 gap-1">
                  {[
                    { id: 'bounce', label: '🎾 Bounce' },
                    { id: 'slide', label: '📐 Slide' },
                    { id: 'pop', label: '💥 Pop' },
                    { id: 'none', label: '⛔ None' },
                  ].map((style) => (
                    <button
                      key={style.id}
                      type="button"
                      onClick={() => onChange({ animation_style: style.id as any })}
                      className={`py-1 px-1.5 rounded-lg text-center font-medium transition text-[10px] ${
                        config.animation_style === style.id
                          ? 'bg-amber-500 text-slate-900 font-bold'
                          : 'bg-slate-900 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {style.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Toggle Effects */}
              <div className="space-y-2">
                <span className="text-slate-400">Visual Effects:</span>
                {[
                  { key: 'confetti_enabled' as const, label: '🎊 Confetti Burst', icon: '🎉' },
                  { key: 'answer_flash' as const, label: '⚡ Answer Flash', icon: '💫' },
                  { key: 'background_zoom' as const, label: '🔍 Ken Burns Zoom', icon: '🎬' },
                ].map((toggle) => (
                  <label key={toggle.key} className="flex items-center justify-between gap-2 cursor-pointer group">
                    <span className="text-slate-300 group-hover:text-white transition text-[11px]">{toggle.label}</span>
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={config[toggle.key] as boolean}
                        onChange={(e) => onChange({ [toggle.key]: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-8 h-4 bg-slate-800 rounded-full peer peer-checked:bg-emerald-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:after:translate-x-4"></div>
                    </div>
                  </label>
                ))}
              </div>

              {/* Mascot & Dance */}
              <div className="space-y-2">
                <span className="text-slate-400">Mascot Animation:</span>
                <label className="flex items-center justify-between gap-2 cursor-pointer group">
                  <span className="text-slate-300 group-hover:text-white transition text-[11px]">🎤 Invite an answer</span>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={config.audience_prompt}
                      onChange={(e) => onChange({ audience_prompt: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-8 h-4 bg-slate-800 rounded-full peer peer-checked:bg-emerald-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:after:translate-x-4"></div>
                  </div>
                </label>
                <label className="flex items-center justify-between gap-2 cursor-pointer group">
                  <span className="text-slate-300 group-hover:text-white transition text-[11px]">💃 Dancing Mascot</span>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={config.mascot_dance}
                      onChange={(e) => onChange({ mascot_dance: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-8 h-4 bg-slate-800 rounded-full peer peer-checked:bg-emerald-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:after:translate-x-4"></div>
                  </div>
                </label>
                <label className="flex items-center justify-between gap-2 cursor-pointer group">
                  <span className="text-slate-300 group-hover:text-white transition text-[11px]">🔊 Audio Normalize</span>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={config.audio_normalize}
                      onChange={(e) => onChange({ audio_normalize: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-8 h-4 bg-slate-800 rounded-full peer peer-checked:bg-emerald-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:after:translate-x-4"></div>
                  </div>
                </label>
              </div>

              {/* SFX Volume */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-slate-400">
                  <span>SFX Volume:</span>
                  <span className="font-bold text-amber-300">{Math.round(config.sfx_volume * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1.0"
                  step="0.05"
                  value={config.sfx_volume}
                  onChange={(e) => onChange({ sfx_volume: parseFloat(e.target.value) })}
                  className="w-full accent-amber-400"
                />
              </div>
            </div>
          </div>

          {/* Optional API Key Section */}
          <div className="col-span-full pt-2">
            <button
              type="button"
              onClick={() => setShowApiKeyInput(!showApiKeyInput)}
              className="text-slate-400 hover:text-slate-300 flex items-center gap-1 text-[11px]"
            >
              <Key className="w-3.5 h-3.5" />
              <span>{showApiKeyInput ? 'Hide API Key Settings' : 'Configure Custom OpenAI API Key (Optional)'}</span>
            </button>

            {showApiKeyInput && (
              <div className="mt-2 p-3 bg-slate-900 rounded-xl border border-slate-700/60 space-y-2">
                <p className="text-[11px] text-slate-400">
                  By default, <strong>Edge-TTS</strong> runs without any API key or subscription. If you prefer OpenAI TTS:
                </p>
                <input
                  type="password"
                  placeholder="sk-..."
                  value={config.openai_api_key || ''}
                  onChange={(e) => onChange({ openai_api_key: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400"
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
