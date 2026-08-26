import React from 'react';
import {
  CheckCircle2,
  Clock,
  Loader2,
  XCircle,
  RotateCw,
  Download,
} from 'lucide-react';
import { BatchJobState } from '../types';

interface BatchProgressProps {
  jobState: BatchJobState;
  onRetry: () => void;
}

const MASCOT_EMOJIS: Record<string, string> = {
  bear: '🐻',
  penguin: '🐧',
  lion: '🦁',
  bunny: '🐰',
};

const TEMPLATE_NAMES: Record<string, string> = {
  candy_clouds: '🍭 Candy',
  space_galaxy: '🚀 Space',
  safari_jungle: '🌿 Safari',
  ocean_bubbles: '🌊 Ocean',
  arcade_retro: '🎮 Arcade',
};

export const BatchProgress: React.FC<BatchProgressProps> = ({
  jobState,
  onRetry,
}) => {
  const isProcessing = jobState.status === 'processing' || jobState.status === 'pending';

  return (
    <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 space-y-6">
      {/* Header & Overall Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white">
              {isProcessing && 'Factory Generating Shorts...'}
              {jobState.status === 'completed' && '🎉 All Shorts Generated Successfully!'}
              {jobState.status === 'partial_failure' && '⚠️ Batch Completed with Partial Issues'}
              {jobState.status === 'failed' && '❌ Batch Generation Failed'}
            </h2>
            {isProcessing && (
              <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-400/20 text-amber-300 text-xs font-semibold animate-pulse">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Live Rendering</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Job ID: <strong className="text-slate-200">{jobState.job_id}</strong> • Concurrency: 3 workers
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          {jobState.failed_items > 0 && !isProcessing && (
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-300 hover:bg-amber-500/30 text-xs font-semibold transition"
            >
              <RotateCw className="w-3.5 h-3.5" />
              <span>Retry {jobState.failed_items} Failed Items</span>
            </button>
          )}

          {jobState.zip_url && (
            <a
              href={jobState.zip_url}
              download
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-yellow-400 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 hover:from-amber-400 hover:to-yellow-300 transition"
            >
              <Download className="w-4 h-4" />
              <span>Download Batch ZIP ({jobState.completed_items} Videos)</span>
            </a>
          )}
        </div>
      </div>

      {/* Progress Bar & Counters */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
          <span>
            Progress: {jobState.completed_items} of {jobState.total_items} Completed
          </span>
          <span className="text-amber-400">{jobState.overall_progress}%</span>
        </div>
        <div className="w-full h-3.5 bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-700/80">
          <div
            className="h-full bg-gradient-to-r from-amber-500 via-yellow-400 to-emerald-400 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(2, jobState.overall_progress))}%` }}
          />
        </div>
      </div>

      {/* Per-Item Live Status Grid */}
      <div className="space-y-2">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
          Individual Video Pipeline Status
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
          {jobState.items.map((item) => {
            const isItemDone = item.status === 'completed';
            const isItemRendering = item.status === 'rendering';
            const isItemTts = item.status === 'tts_processing';
            const isItemFailed = item.status === 'failed';

            const mascotEmoji = item.mascot_used ? MASCOT_EMOJIS[item.mascot_used] || '🐻' : '🐻';
            const themeLabel = item.template_used ? TEMPLATE_NAMES[item.template_used] || item.template_used : '';

            return (
              <div
                key={item.index}
                className={`p-3.5 rounded-xl border transition text-xs space-y-1.5 ${
                  isItemDone
                    ? 'bg-emerald-950/30 border-emerald-800/60'
                    : isItemFailed
                    ? 'bg-rose-950/30 border-rose-800/60'
                    : isItemRendering || isItemTts
                    ? 'bg-amber-950/30 border-amber-500/60 animate-pulse'
                    : 'bg-slate-900/60 border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-slate-200">
                      #{item.index + 1}
                    </span>
                    {item.mascot_used && (
                      <span className="text-xs">{mascotEmoji}</span>
                    )}
                    {themeLabel && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {themeLabel}
                      </span>
                    )}
                  </div>

                  {isItemDone && (
                    <span className="flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Ready ({item.duration?.toFixed(1)}s)</span>
                    </span>
                  )}
                  {isItemTts && (
                    <span className="flex items-center gap-1 text-amber-300 font-semibold text-[11px]">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Synthesizing TTS</span>
                    </span>
                  )}
                  {isItemRendering && (
                    <span className="flex items-center gap-1 text-amber-400 font-semibold text-[11px]">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>FFmpeg Rendering</span>
                    </span>
                  )}
                  {item.status === 'queued' && (
                    <span className="flex items-center gap-1 text-slate-500 text-[11px]">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Queued</span>
                    </span>
                  )}
                  {isItemFailed && (
                    <span className="flex items-center gap-1 text-rose-400 font-semibold text-[11px]">
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Failed</span>
                    </span>
                  )}
                </div>

                <p className="text-slate-300 font-medium line-clamp-1">{item.question}</p>
                <p className="text-emerald-400 font-medium text-[11px] line-clamp-1">
                  Answer: {item.answer}
                </p>

                {isItemFailed && item.error && (
                  <p className="text-[11px] text-rose-300 bg-rose-950/70 p-2 rounded border border-rose-800/80 mt-1">
                    <strong>Error:</strong> {item.error}
                  </p>
                )}

                {isItemDone && item.video_url && (
                  <div className="pt-1 flex items-center justify-between">
                    <span className="text-[10px] text-slate-400 font-mono">
                      {item.output_filename}
                    </span>
                    <a
                      href={item.video_url}
                      download={item.output_filename}
                      className="text-amber-400 hover:text-amber-300 font-semibold text-[11px] flex items-center gap-1"
                    >
                      <Download className="w-3 h-3" />
                      <span>Download MP4</span>
                    </a>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
