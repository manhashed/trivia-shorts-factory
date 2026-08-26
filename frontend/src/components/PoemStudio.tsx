import React, { useState, useEffect } from 'react';
import {
  Music2,
  Sparkles,
  BookOpen,
  Play,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Download,
  Shuffle,
  Volume2,
  Check,
  Film,
  Plus,
  X,
  Search,
} from 'lucide-react';
import { PoemItem, PoemRenderConfig, PoemBatchJobState, MelodyOption } from '../types/poem';
import { MascotInfo, TemplateInfo, CategoryInfo } from '../types';
import {
  getPoemBank,
  getPoemCategories,
  getMelodies,
  generatePoemPreview,
  createPoemBatchJob,
  getPoemJobStatus,
} from '../services/poem_api';

interface PoemStudioProps {
  mascots: MascotInfo[];
  templates: TemplateInfo[];
}

export const PoemStudio: React.FC<PoemStudioProps> = ({
  mascots,
  templates,
}) => {
  const [poems, setPoems] = useState<PoemItem[]>([]);
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [melodies, setMelodies] = useState<MelodyOption[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isPoemBankModalOpen, setIsPoemBankModalOpen] = useState(false);

  // Active workspace poems (loaded for batch / preview)
  const [workspacePoems, setWorkspacePoems] = useState<PoemItem[]>([]);
  const [selectedPoemIndex, setSelectedPoemIndex] = useState<number>(0);

  // Configuration
  const [config, setConfig] = useState<PoemRenderConfig>({
    width: 1080,
    height: 1920,
    fps: 30,
    mascot_id: 'bear',
    template_id: 'candy_clouds',
    melody_track: 'twinkle_star',
    melody_volume: 0.20,
    tts_provider: 'edge',
    tts_voice: 'en-US-AnaNeural',
    tts_speed: '+0%',
    dance_bpm: 120,
    karaoke_style: 'bouncing_star',
    mix_mode: false,
  });

  // Preview State
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  // Batch Job State
  const [activeJob, setActiveJob] = useState<PoemBatchJobState | null>(null);
  const [isStartingBatch, setIsStartingBatch] = useState(false);
  const [batchError, setBatchError] = useState<string | null>(null);

  // Load initial bank and melodies
  useEffect(() => {
    getPoemBank().then((res) => {
      setPoems(res.poems);
      // Pre-load first 5 poems by default
      if (res.poems.length > 0) {
        setWorkspacePoems(res.poems.slice(0, 5));
      }
    }).catch(console.error);

    getPoemCategories().then(setCategories).catch(console.error);
    getMelodies().then(setMelodies).catch(console.error);
  }, []);

  // SSE Stream Listener for Poem Batch Progress
  useEffect(() => {
    if (!activeJob?.job_id) return;
    const isTerminal = ['completed', 'failed', 'partial_failure'].includes(activeJob.status);
    if (isTerminal) return;

    const eventSource = new EventSource(`/api/poems/jobs/${activeJob.job_id}/stream`);

    eventSource.onmessage = (e) => {
      try {
        const updatedState: PoemBatchJobState = JSON.parse(e.data);
        setActiveJob(updatedState);
        if (['completed', 'failed', 'partial_failure'].includes(updatedState.status)) {
          eventSource.close();
        }
      } catch (err) {
        console.error('Failed to parse poem SSE payload:', err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setTimeout(() => {
        getPoemJobStatus(activeJob.job_id).then(setActiveJob).catch(console.error);
      }, 2000);
    };

    return () => {
      eventSource.close();
    };
  }, [activeJob?.job_id, activeJob?.status]);

  const activePoem = workspacePoems[selectedPoemIndex] || workspacePoems[0];

  const handleSelectMascot = (m: MascotInfo) => {
    setConfig((prev) => ({
      ...prev,
      mascot_id: m.id,
      tts_voice: m.voice,
    }));
  };

  const handleGeneratePreview = async () => {
    if (!activePoem) return;
    setIsPreviewLoading(true);
    setPreviewError(null);

    try {
      const res = await generatePoemPreview(activePoem, config);
      setPreviewUrl(res.video_url);
    } catch (err: any) {
      setPreviewError(err.message || 'Failed to render poem preview.');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleStartBatch = async () => {
    if (workspacePoems.length === 0) return;
    setIsStartingBatch(true);
    setBatchError(null);

    try {
      const res = await createPoemBatchJob(workspacePoems, config);
      const initialJob = await getPoemJobStatus(res.job_id);
      setActiveJob(initialJob);
    } catch (err: any) {
      setBatchError(err.message || 'Failed to start poem batch job.');
    } finally {
      setIsStartingBatch(false);
    }
  };

  const filteredBankPoems = poems.filter((p) => {
    const term = searchQuery.toLowerCase();
    const matchCat = selectedCategory === 'all' || (p.category && p.category.toLowerCase() === selectedCategory.toLowerCase());
    const matchSearch = !searchQuery || p.title.toLowerCase().includes(term) || p.lines.some((l) => l.toLowerCase().includes(term));
    return matchCat && matchSearch;
  });

  return (
    <div className="space-y-8">
      {/* Hero Welcome Banner */}
      <div className="bg-gradient-to-r from-purple-900/40 via-pink-900/30 to-indigo-900/40 border border-purple-500/40 rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xl">
        <div className="space-y-2 text-center md:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-pink-500/20 text-pink-300 border border-pink-500/40 text-xs font-bold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>120 BPM Beat-Synced Dancing & Singing Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white">
            Singing & Dancing Mascot Poem Studio
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
            Turn classic nursery rhymes and sweet rhyming poems into dancing, singing 9:16 vertical shorts.
            Mascots step, sway, sing, and jump in lockstep with the nursery music!
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsPoemBankModalOpen(true)}
          className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white font-extrabold text-xs shadow-xl shadow-purple-500/25 hover:brightness-110 transition flex items-center gap-2 shrink-0"
        >
          <BookOpen className="w-4 h-4" />
          <span>Browse 25+ Poem Bank ({poems.length} Ready)</span>
        </button>
      </div>

      {/* 1. Mascot Dancing Host Picker */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-bold text-white flex items-center gap-2">
            <span>1. Choose Dancing & Singing Host</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-purple-400/20 text-purple-300 font-semibold">
              4 Animated Dancers
            </span>
          </label>
          <span className="text-xs text-slate-400">
            Step Left • Sing Mouth • Step Right • Airborne Jump
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {mascots.map((m) => {
            const isSelected = m.id === config.mascot_id;
            return (
              <div
                key={m.id}
                onClick={() => handleSelectMascot(m)}
                className={`relative p-3.5 rounded-2xl border-2 transition cursor-pointer select-none flex flex-col items-center text-center group ${
                  isSelected
                    ? 'bg-gradient-to-b from-purple-500/20 to-slate-900 border-purple-400 shadow-lg shadow-purple-500/10 scale-[1.02]'
                    : 'bg-slate-900/70 border-slate-700/80 hover:border-slate-500 hover:bg-slate-850'
                }`}
              >
                {isSelected && (
                  <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-purple-400 text-slate-950 flex items-center justify-center shadow">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </div>
                )}
                <div className="w-14 h-14 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center text-3xl mb-2 group-hover:scale-110 transition shadow-inner">
                  {m.emoji}
                </div>
                <h4 className="font-bold text-slate-100 text-xs">{m.name}</h4>
                <p className="text-[10px] text-slate-400 line-clamp-1 mt-0.5">{m.tagline}</p>
                <div className="mt-2 flex items-center gap-1 text-[9px] text-purple-300 bg-purple-950/50 px-2 py-0.5 rounded border border-purple-800/40">
                  <Volume2 className="w-3 h-3" />
                  <span>{m.voice.split('-')[2] || m.voice}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. Visual Theme & Nursery Melody Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Template Selector */}
        <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 space-y-3">
          <label className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Film className="w-4 h-4 text-sky-400" />
            <span>2. Visual Motion Background</span>
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {templates.map((tmpl) => {
              const isSelected = tmpl.id === config.template_id;
              return (
                <div
                  key={tmpl.id}
                  onClick={() => setConfig((p) => ({ ...p, template_id: tmpl.id }))}
                  className={`p-2.5 rounded-xl border transition cursor-pointer text-center select-none ${
                    isSelected
                      ? 'bg-sky-500/20 border-sky-400 text-white'
                      : 'bg-slate-900/80 border-slate-700 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <div className="text-xl mb-1">{tmpl.emoji}</div>
                  <div className="text-[11px] font-bold truncate">{tmpl.name}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Nursery Melody Selector */}
        <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 space-y-3">
          <label className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Music2 className="w-4 h-4 text-pink-400" />
            <span>3. Nursery Accompaniment Melody</span>
          </label>
          <div className="space-y-2">
            <select
              value={config.melody_track}
              onChange={(e) => setConfig((p) => ({ ...p, melody_track: e.target.value }))}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-pink-400"
            >
              {melodies.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.bpm} BPM)
                </option>
              ))}
            </select>

            {config.melody_track !== 'none' && (
              <div className="space-y-1 pt-1 text-xs">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Music Ducking Volume:</span>
                  <span className="font-bold text-pink-300">{Math.round(config.melody_volume * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.40"
                  step="0.05"
                  value={config.melody_volume}
                  onChange={(e) => setConfig((p) => ({ ...p, melody_volume: parseFloat(e.target.value) }))}
                  className="w-full accent-pink-400"
                />
              </div>
            )}
          </div>

          {/* Mix Mode Toggle */}
          <div className="pt-2 border-t border-slate-700/60 flex items-center justify-between">
            <div className="text-xs">
              <span className="font-bold text-slate-200 flex items-center gap-1">
                <Shuffle className="w-3.5 h-3.5 text-purple-400" />
                <span>Mix Mascots & Themes in Batch</span>
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={config.mix_mode}
                onChange={(e) => setConfig((p) => ({ ...p, mix_mode: e.target.checked }))}
                className="sr-only peer"
              />
              <div className="w-10 h-5 bg-slate-900 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* 3. Loaded Poems Workspace */}
      <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>Active Batch Poems</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-pink-400/20 text-pink-300 font-extrabold">
                {workspacePoems.length} Poems Loaded
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Select an item to preview or generate the entire batch of singing shorts.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setIsPoemBankModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800 text-xs font-semibold transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4 text-pink-400" />
            <span>Add / Replace from 25+ Bank</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {workspacePoems.map((p, idx) => {
            const isSelected = idx === selectedPoemIndex;
            return (
              <div
                key={p.id || idx}
                onClick={() => setSelectedPoemIndex(idx)}
                className={`p-3.5 rounded-2xl border transition cursor-pointer text-xs space-y-1.5 ${
                  isSelected
                    ? 'bg-gradient-to-b from-pink-500/20 to-slate-900 border-pink-400 shadow-md shadow-pink-500/10'
                    : 'bg-slate-900/70 border-slate-700/70 hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-pink-300">
                    Poem #{idx + 1} • {p.title}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                    {p.lines.length} lines
                  </span>
                </div>
                <p className="text-slate-200 font-medium line-clamp-2 leading-relaxed">
                  "{p.lines[0]}"
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Single-Poem Test Preview Player */}
      <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span>Test Preview (Singing & Dancing Mascot)</span>
              <span className="text-xs px-2 py-0.5 bg-pink-400/20 text-pink-300 rounded font-normal">
                4s Turnaround
              </span>
            </h2>
            <p className="text-sm text-slate-400 mt-0.5">
              Testing active item: <strong className="text-pink-300">{activePoem?.title}</strong>
            </p>
          </div>

          <button
            type="button"
            onClick={handleGeneratePreview}
            disabled={!activePoem || isPreviewLoading}
            className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm shadow-md transition ${
              !activePoem || isPreviewLoading
                ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                : 'bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white hover:brightness-110 shadow-purple-500/20'
            }`}
          >
            {isPreviewLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Rendering Dancing Mascot Short...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Generate Test Preview</span>
              </>
            )}
          </button>
        </div>

        {previewError && (
          <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{previewError}</span>
          </div>
        )}

        {previewUrl ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start bg-slate-900/60 p-6 rounded-2xl border border-slate-700/60">
            <div className="flex justify-center lg:col-span-1">
              <div className="relative w-64 rounded-3xl overflow-hidden shadow-2xl border-4 border-slate-700 aspect-[9/16] bg-black">
                <video
                  src={previewUrl}
                  controls
                  autoPlay
                  loop
                  playsInline
                  className="w-full h-full object-cover"
                />
              </div>
            </div>

            <div className="lg:col-span-2 space-y-4 text-xs">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                <CheckCircle2 className="w-5 h-5" />
                <span>Poem Video Rendered with 120 BPM Mascot Dancing!</span>
              </div>

              <div className="p-4 bg-slate-800/80 rounded-xl border border-slate-700 space-y-2">
                <h4 className="font-bold text-slate-200">🎵 {activePoem?.title}</h4>
                <div className="space-y-1 pt-1 text-slate-300">
                  {activePoem?.lines.map((l, lIdx) => (
                    <p key={lIdx} className="font-medium text-xs">
                      {l}
                    </p>
                  ))}
                </div>
              </div>

              <p className="text-slate-400">
                💡 <em>The mascot dances in rhythm with the nursery melody while singing the lyrics. Proceed below to generate all {workspacePoems.length} shorts!</em>
              </p>
            </div>
          </div>
        ) : (
          <div className="border border-slate-700/60 rounded-xl p-8 text-center text-slate-400 text-xs bg-slate-900/30">
            Click <strong>"Generate Test Preview"</strong> to watch the mascot dance and sing!
          </div>
        )}
      </div>

      {/* 5. Launch Full Batch */}
      <div className="bg-gradient-to-r from-pink-500/10 via-purple-500/10 to-indigo-500/10 border-2 border-purple-500/40 rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-xl shadow-purple-500/5">
        <div className="space-y-1 text-center sm:text-left">
          <h3 className="text-lg font-bold text-white flex items-center gap-2 justify-center sm:justify-start">
            <span>Launch Batch Poem Shorts Production</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-pink-400 text-slate-950 font-extrabold">
              {workspacePoems.length} Videos Ready
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            {config.mix_mode
              ? 'Rotating 4 mascots, 5 stock themes, and melodies across each poem short'
              : `Host: ${mascots.find(m => m.id === config.mascot_id)?.name || 'Barnaby Bear'} • Theme: ${templates.find(t => t.id === config.template_id)?.name || 'Rainbow Candy'}`}
          </p>
        </div>

        <button
          type="button"
          onClick={handleStartBatch}
          disabled={workspacePoems.length === 0 || isStartingBatch}
          className={`px-8 py-4 rounded-2xl font-extrabold text-base shadow-xl flex items-center gap-3 transition transform active:scale-95 ${
            workspacePoems.length === 0 || isStartingBatch
              ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
              : 'bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white hover:brightness-110 shadow-purple-500/30'
          }`}
        >
          <Sparkles className="w-5 h-5 fill-current" />
          <span>
            {isStartingBatch
              ? 'Starting Poem Factory...'
              : `Generate All ${workspacePoems.length} Dancing Shorts`}
          </span>
        </button>
      </div>

      {batchError && (
        <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{batchError}</span>
        </div>
      )}

      {/* Batch Progress */}
      {activeJob && (
        <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white">
                  {activeJob.status === 'processing' && 'Rendering Poem Shorts...'}
                  {activeJob.status === 'completed' && '🎉 All Dancing Poem Shorts Completed!'}
                  {activeJob.status === 'partial_failure' && '⚠️ Batch Completed with Partial Issues'}
                </h2>
                {activeJob.status === 'processing' && (
                  <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-pink-400/20 text-pink-300 text-xs font-semibold animate-pulse">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Live 120 BPM Rendering</span>
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Job ID: <strong className="text-slate-200">{activeJob.job_id}</strong>
              </p>
            </div>

            {activeJob.zip_url && (
              <a
                href={activeJob.zip_url}
                download
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white font-bold text-sm shadow-lg shadow-purple-500/20 hover:brightness-110 transition"
              >
                <Download className="w-4 h-4" />
                <span>Download Poem Shorts ZIP ({activeJob.completed_items} Videos)</span>
              </a>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
              <span>
                Progress: {activeJob.completed_items} of {activeJob.total_items} Completed
              </span>
              <span className="text-pink-400">{activeJob.overall_progress}%</span>
            </div>
            <div className="w-full h-3.5 bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-700/80">
              <div
                className="h-full bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(2, activeJob.overall_progress))}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
            {activeJob.items.map((item) => (
              <div
                key={item.index}
                className={`p-3.5 rounded-xl border text-xs space-y-1.5 ${
                  item.status === 'completed'
                    ? 'bg-emerald-950/30 border-emerald-800/60'
                    : item.status === 'failed'
                    ? 'bg-rose-950/30 border-rose-800/60'
                    : 'bg-slate-900/60 border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200">
                    #{item.index + 1} • {item.title}
                  </span>
                  {item.status === 'completed' && (
                    <span className="flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Ready ({item.duration?.toFixed(1)}s)</span>
                    </span>
                  )}
                  {item.status === 'rendering' && (
                    <span className="flex items-center gap-1 text-pink-400 font-semibold text-[11px]">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Compositing</span>
                    </span>
                  )}
                </div>

                <p className="text-slate-300 text-[11px] line-clamp-1">"{item.lines[0]}"</p>

                {item.status === 'completed' && item.video_url && (
                  <div className="pt-1 flex items-center justify-between">
                    <span className="text-[10px] text-slate-400 font-mono">
                      {item.output_filename}
                    </span>
                    <a
                      href={item.video_url}
                      download={item.output_filename}
                      className="text-pink-400 hover:text-pink-300 font-semibold text-[11px] flex items-center gap-1"
                    >
                      <Download className="w-3 h-3" />
                      <span>Download MP4</span>
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 25+ Curated Poem Bank Modal */}
      {isPoemBankModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 w-full max-w-4xl rounded-3xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-pink-500/20 text-pink-300 flex items-center justify-center">
                  <Music2 className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>25+ Preschool Nursery Rhymes & Poem Bank</span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full bg-pink-500 text-white font-bold">
                      {poems.length} Rhymes
                    </span>
                  </h2>
                  <p className="text-xs text-slate-400">
                    Classic melodies, counting songs, lullabies, and healthy habit rhymes.
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsPoemBankModalOpen(false)}
                className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Filter Pills & Search */}
            <div className="px-6 py-3 border-b border-slate-800 bg-slate-950/60 space-y-3">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search nursery rhymes, titles, lyrics..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-pink-400"
                />
              </div>

              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 custom-scrollbar text-xs">
                <button
                  type="button"
                  onClick={() => setSelectedCategory('all')}
                  className={`px-3 py-1.5 rounded-xl font-semibold whitespace-nowrap transition text-xs ${
                    selectedCategory === 'all'
                      ? 'bg-pink-500 text-white shadow'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  All Rhymes ({poems.length})
                </button>
                {categories.map((cat) => (
                  <button
                    key={cat.name}
                    type="button"
                    onClick={() => setSelectedCategory(cat.name)}
                    className={`px-3 py-1.5 rounded-xl font-medium whitespace-nowrap transition text-xs ${
                      selectedCategory === cat.name
                        ? 'bg-pink-500 text-white font-bold shadow'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {cat.name} ({cat.count})
                  </button>
                ))}
              </div>
            </div>

            {/* List Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-3 custom-scrollbar bg-slate-950/30">
              {filteredBankPoems.map((p, idx) => (
                <div
                  key={p.id || idx}
                  className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-pink-400 text-sm">
                      #{idx + 1} • {p.title}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {p.category}
                    </span>
                  </div>
                  <div className="space-y-1 text-slate-200">
                    {p.lines.map((l, lIdx) => (
                      <p key={lIdx} className="italic">
                        {l}
                      </p>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="px-6 py-4 border-t border-slate-800 bg-slate-900 flex items-center justify-between">
              <span className="text-xs text-slate-400">
                Showing {filteredBankPoems.length} of {poems.length} rhymes
              </span>
              <button
                type="button"
                onClick={() => {
                  setWorkspacePoems(filteredBankPoems);
                  setIsPoemBankModalOpen(false);
                }}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white font-extrabold text-xs shadow-lg shadow-purple-500/20 hover:brightness-110 transition"
              >
                Load These {filteredBankPoems.length} Poems into Workspace
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
