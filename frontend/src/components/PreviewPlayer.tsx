import React, { useState } from 'react';
import { Play, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { TriviaItem, VideoRenderConfig, VideoUploadResponse } from '../types';
import { generatePreview } from '../services/api';

interface PreviewPlayerProps {
  items: TriviaItem[];
  videoData: VideoUploadResponse | null;
  config: VideoRenderConfig;
}

export const PreviewPlayer: React.FC<PreviewPlayerProps> = ({
  items,
  videoData,
  config,
}) => {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [previewVideoUrl, setPreviewVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [timing, setTiming] = useState<Record<string, number> | null>(null);

  const canPreview = items.length > 0 && !!videoData;
  const currentItem = items[selectedIndex] || items[0];

  const handleGeneratePreview = async () => {
    if (!canPreview || !currentItem || !videoData) return;
    setIsLoading(true);
    setError(null);

    try {
      const res = await generatePreview(
        currentItem.q,
        currentItem.a,
        videoData.video_id,
        config,
        currentItem.options
      );
      setPreviewVideoUrl(res.video_url);
      setTiming(res.timing);
    } catch (err: any) {
      setError(err.message || 'Preview generation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>Step 3: Test Preview (Instant 5s Turnaround)</span>
            <span className="text-xs px-2 py-0.5 bg-emerald-400/20 text-emerald-300 rounded font-normal">
              Theme & Mascot Check
            </span>
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Test 1 question to verify your selected mascot, voice, template styling, and timing before running the full batch.
          </p>
        </div>

        {/* Question Selector & Preview Button */}
        <div className="flex items-center gap-3">
          {items.length > 1 && (
            <select
              value={selectedIndex}
              onChange={(e) => setSelectedIndex(parseInt(e.target.value))}
              disabled={isLoading || !canPreview}
              className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-400"
            >
              {items.map((it, idx) => (
                <option key={idx} value={idx}>
                  Question #{idx + 1}: {it.q.slice(0, 28)}...
                </option>
              ))}
            </select>
          )}

          <button
            type="button"
            onClick={handleGeneratePreview}
            disabled={!canPreview || isLoading}
            className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm shadow-md transition ${
              !canPreview || isLoading
                ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                : 'bg-gradient-to-r from-emerald-500 to-teal-400 text-slate-950 hover:from-emerald-400 hover:to-teal-300 shadow-emerald-500/20'
            }`}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-slate-900" />
                <span>Rendering Test Video (~4s)...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Generate Single Preview</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Preview Player Display */}
      {previewVideoUrl ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start bg-slate-900/60 p-6 rounded-2xl border border-slate-700/60">
          {/* Vertical 9:16 Video Frame */}
          <div className="flex justify-center lg:col-span-1">
            <div className="relative w-64 rounded-3xl overflow-hidden shadow-2xl border-4 border-slate-700 aspect-[9/16] bg-black">
              <video
                src={previewVideoUrl}
                controls
                autoPlay
                loop
                playsInline
                className="w-full h-full object-cover"
              />
            </div>
          </div>

          {/* Timing & Breakdown Details */}
          <div className="lg:col-span-2 space-y-4 text-xs">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
              <CheckCircle2 className="w-5 h-5" />
              <span>Preview Video Generated Successfully!</span>
            </div>

            <div className="p-4 bg-slate-800/80 rounded-xl border border-slate-700 space-y-2">
              <h4 className="font-bold text-slate-200">Active Test Item:</h4>
              <p className="text-amber-300 font-semibold text-sm">"{currentItem?.q}"</p>
              {currentItem?.options && currentItem.options.length > 0 && (
                <div className="flex gap-2 text-xs">
                  {currentItem.options.map((opt, oIdx) => (
                    <span key={oIdx} className="px-2 py-0.5 bg-slate-900 rounded border border-slate-700 text-slate-300">
                      {String.fromCharCode(65 + oIdx)}: {opt}
                    </span>
                  ))}
                </div>
              )}
              <p className="text-emerald-400 font-semibold">Answer: "{currentItem?.a}"</p>
            </div>

            {timing && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
                <div className="p-2.5 bg-slate-800 rounded-xl border border-slate-700 text-center">
                  <span className="text-slate-400 block text-[10px]">Question TTS</span>
                  <span className="font-bold text-slate-200 text-sm">{timing.q_duration}s</span>
                </div>
                <div className="p-2.5 bg-slate-800 rounded-xl border border-slate-700 text-center">
                  <span className="text-slate-400 block text-[10px]">Countdown</span>
                  <span className="font-bold text-amber-300 text-sm">{timing.countdown_duration}s</span>
                </div>
                <div className="p-2.5 bg-slate-800 rounded-xl border border-slate-700 text-center">
                  <span className="text-slate-400 block text-[10px]">Answer TTS</span>
                  <span className="font-bold text-emerald-400 text-sm">{timing.a_duration}s</span>
                </div>
                <div className="p-2.5 bg-slate-800 rounded-xl border border-slate-700 text-center">
                  <span className="text-slate-400 block text-[10px]">Total Short Duration</span>
                  <span className="font-bold text-purple-400 text-sm">{timing.total_duration}s</span>
                </div>
              </div>
            )}

            <p className="text-slate-400 pt-2">
              💡 <em>Looks great! If you're happy with the layout, voice, and animation, proceed to Step 4 below to generate the entire batch in one click.</em>
            </p>
          </div>
        </div>
      ) : (
        <div className="border border-slate-700/60 rounded-xl p-8 text-center text-slate-400 text-xs bg-slate-900/30">
          {!canPreview ? (
            <span>Load questions from the Question Bank or upload your JSON and video in Step 1 to enable preview.</span>
          ) : (
            <span>Click <strong>"Generate Single Preview"</strong> to render a 5-second test video before batch processing.</span>
          )}
        </div>
      )}
    </div>
  );
};
