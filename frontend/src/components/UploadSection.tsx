import React, { useRef, useState } from 'react';
import {
  FileText,
  Video,
  CheckCircle2,
  AlertTriangle,
  Eye,
  BookOpen,
} from 'lucide-react';
import { ValidationResponse, VideoUploadResponse } from '../types';
import { validateTriviaFile, uploadBackgroundVideo } from '../services/api';

interface UploadSectionProps {
  validationData: ValidationResponse | null;
  videoData: VideoUploadResponse | null;
  onValidationSuccess: (data: ValidationResponse) => void;
  onVideoSuccess: (data: VideoUploadResponse) => void;
  onOpenQuestionBank: () => void;
  isLoading: boolean;
}

export const UploadSection: React.FC<UploadSectionProps> = ({
  validationData,
  videoData,
  onValidationSuccess,
  onVideoSuccess,
  onOpenQuestionBank,
  isLoading,
}) => {
  const jsonInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [isUploadingJson, setIsUploadingJson] = useState(false);
  const [isUploadingVideo, setIsUploadingVideo] = useState(false);
  const [showQuestionsPreview, setShowQuestionsPreview] = useState(false);

  const handleJsonChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setJsonError(null);
    setIsUploadingJson(true);
    try {
      const res = await validateTriviaFile(file);
      onValidationSuccess(res);
    } catch (err: any) {
      setJsonError(err.message || 'JSON validation failed.');
    } finally {
      setIsUploadingJson(false);
    }
  };

  const handleVideoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setVideoError(null);
    setIsUploadingVideo(true);
    try {
      const res = await uploadBackgroundVideo(file);
      onVideoSuccess(res);
    } catch (err: any) {
      setVideoError(err.message || 'Video upload failed.');
    } finally {
      setIsUploadingVideo(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>Step 1: Questions & Video</span>
            <span className="text-xs px-2 py-0.5 bg-slate-800 text-slate-400 rounded-md border border-slate-700 font-normal">
              Library or Custom Upload
            </span>
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Load curated preschool questions or upload your own custom JSON & background video.
          </p>
        </div>

        {/* Question Bank Explorer Button */}
        <button
          type="button"
          onClick={onOpenQuestionBank}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500/20 to-yellow-500/20 border border-amber-400/50 text-amber-300 hover:from-amber-500/30 hover:to-yellow-500/30 font-bold text-sm transition shadow-md shadow-amber-500/10"
        >
          <BookOpen className="w-4 h-4 text-amber-400" />
          <span>Browse 100+ Question Bank (10 Categories)</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 1. Trivia JSON Card */}
        <div
          onClick={() => jsonInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-2xl p-6 transition cursor-pointer flex flex-col items-center justify-center text-center group ${
            validationData?.is_valid
              ? 'border-emerald-500/50 bg-emerald-500/5'
              : jsonError
              ? 'border-rose-500/50 bg-rose-500/5'
              : 'border-slate-700 bg-slate-800/40 hover:border-amber-400/50 hover:bg-slate-800/70'
          }`}
        >
          <input
            ref={jsonInputRef}
            type="file"
            accept=".json,application/json"
            className="hidden"
            onChange={handleJsonChange}
          />

          <div className="w-14 h-14 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mb-3 group-hover:scale-110 transition">
            <FileText className="w-7 h-7" />
          </div>

          <h3 className="text-base font-semibold text-white">
            {validationData?.is_valid ? 'Questions Loaded' : 'Upload Custom Trivia JSON'}
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-xs">
            {validationData?.is_valid
              ? `${validationData.valid_count} questions ready for production`
              : 'Click or drop a JSON file or use the 100+ Question Bank'}
          </p>

          {isUploadingJson && (
            <div className="mt-3 text-xs text-amber-300 animate-pulse font-medium">
              Validating questions & answers...
            </div>
          )}

          {validationData?.is_valid && (
            <div className="mt-3 flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-800/80 px-3 py-1 rounded-full">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{validationData.valid_count} Questions Active</span>
            </div>
          )}

          {jsonError && (
            <div className="mt-3 text-xs text-rose-400 bg-rose-950/60 border border-rose-800 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{jsonError}</span>
            </div>
          )}
        </div>

        {/* 2. Background Video Card */}
        <div
          onClick={() => videoInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-2xl p-6 transition cursor-pointer flex flex-col items-center justify-center text-center group ${
            videoData
              ? 'border-emerald-500/50 bg-emerald-500/5'
              : videoError
              ? 'border-rose-500/50 bg-rose-500/5'
              : 'border-slate-700 bg-slate-800/40 hover:border-sky-400/50 hover:bg-slate-800/70'
          }`}
        >
          <input
            ref={videoInputRef}
            type="file"
            accept="video/mp4,video/quicktime,video/webm"
            className="hidden"
            onChange={handleVideoChange}
          />

          <div className="w-14 h-14 rounded-2xl bg-sky-500/10 text-sky-400 flex items-center justify-center mb-3 group-hover:scale-110 transition">
            <Video className="w-7 h-7" />
          </div>

          <h3 className="text-base font-semibold text-white">
            {videoData ? 'Background Video Selected' : 'Upload Custom MP4 Video'}
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-xs">
            {videoData
              ? `${videoData.filename} (${videoData.duration.toFixed(1)}s, ${videoData.width}x${videoData.height})`
              : 'Or select any stock template above (Rainbow, Space, Safari, Ocean, Arcade)'}
          </p>

          {isUploadingVideo && (
            <div className="mt-3 text-xs text-sky-300 animate-pulse font-medium">
              Uploading & inspecting video streams with FFmpeg...
            </div>
          )}

          {videoData && (
            <div className="mt-3 flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-800/80 px-3 py-1 rounded-full">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>9:16 Adaptive Framing & Looping Ready</span>
            </div>
          )}

          {videoError && (
            <div className="mt-3 text-xs text-rose-400 bg-rose-950/60 border border-rose-800 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{videoError}</span>
            </div>
          )}
        </div>
      </div>

      {/* Questions Preview Drawer */}
      {validationData && validationData.items.length > 0 && (
        <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
              <span>Current Batch Questions</span>
              <span className="text-xs px-2 py-0.5 bg-amber-400/20 text-amber-300 rounded-full font-bold">
                {validationData.items.length} Items Loaded
              </span>
            </div>
            <button
              type="button"
              onClick={() => setShowQuestionsPreview(!showQuestionsPreview)}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-medium transition"
            >
              <Eye className="w-3.5 h-3.5" />
              <span>{showQuestionsPreview ? 'Hide List' : 'View Question Cards'}</span>
            </button>
          </div>

          {showQuestionsPreview && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
              {validationData.items.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-slate-900/70 border border-slate-700/60 rounded-xl text-xs space-y-1"
                >
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-bold text-amber-400">Question #{idx + 1}</span>
                    {item.category && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-slate-800 rounded text-slate-300">
                        {item.category}
                      </span>
                    )}
                  </div>
                  <p className="text-slate-100 font-medium">{item.q}</p>
                  {item.options && item.options.length > 0 && (
                    <div className="flex gap-1 text-[10px] text-slate-400 pt-0.5">
                      {item.options.map((opt, oIdx) => (
                        <span key={oIdx} className="bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">
                          {String.fromCharCode(65 + oIdx)}: {opt}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="text-emerald-400 font-semibold pt-0.5">Answer: {item.a}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
