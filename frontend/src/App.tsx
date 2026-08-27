import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  AlertCircle,
  Shuffle,
} from 'lucide-react';
import {
  TriviaItem,
  ValidationResponse,
  VideoUploadResponse,
  VoiceOption,
  VideoRenderConfig,
  BatchJobState,
  MascotInfo,
  TemplateInfo,
  HealthStatus,
} from './types';
import {
  checkHealth,
  getVoices,
  getMascots,
  getTemplates,
  createBatchJob,
  retryJobFailedItems,
  getJobStatus,
} from './services/api';

import { Header } from './components/Header';
import { StudioTabs } from './components/StudioTabs';
import { MascotSelector } from './components/MascotSelector';
import { TemplateSelector } from './components/TemplateSelector';
import { QuestionBankModal } from './components/QuestionBankModal';
import { UploadSection } from './components/UploadSection';
import { SettingsDrawer } from './components/SettingsDrawer';
import { PreviewPlayer } from './components/PreviewPlayer';
import { BatchProgress } from './components/BatchProgress';
import { MascotGuide } from './components/MascotGuide';
import { PoemStudio } from './components/PoemStudio';

export const App: React.FC = () => {
  const [activeStudio, setActiveStudio] = useState<'trivia' | 'poem'>('trivia');

  const [health, setHealth] = useState<HealthStatus | null>(null);

  const [voices, setVoices] = useState<Record<string, VoiceOption[]>>({});
  const [mascots, setMascots] = useState<MascotInfo[]>([]);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [isQuestionBankOpen, setIsQuestionBankOpen] = useState(false);

  const [validationData, setValidationData] = useState<ValidationResponse | null>(null);
  const [videoData, setVideoData] = useState<VideoUploadResponse | null>(null);
  const [activeJob, setActiveJob] = useState<BatchJobState | null>(null);
  const [isStartingBatch, setIsStartingBatch] = useState(false);
  const [batchError, setBatchError] = useState<string | null>(null);

  const [config, setConfig] = useState<VideoRenderConfig>({
    width: 1080,
    height: 1920,
    fps: 30,
    countdown_duration: 3.0,
    post_answer_pause: 1.0,
    mascot_id: 'bear',
    mascot_enabled: true,
    template_id: 'candy_clouds',
    countdown_style: 'pulse_badge',
    countdown_sfx: 'tick_tock',
    background_mode: 'crop_fill',
    mix_mode: false,
    bgm_track: 'playful_nursery',
    bgm_volume: 0.15,
    tts_provider: 'edge',
    tts_voice: 'en-US-AnaNeural',
    tts_speed: '+0%',
    tts_pitch: '+0Hz',
    animation_style: 'bounce',
    confetti_enabled: true,
    background_zoom: true,
    answer_flash: true,
    mascot_dance: true,
    audience_prompt: true,
    audio_normalize: true,
    sfx_volume: 0.6,
  });

  // Load initial health, voice, mascot, and template lists
  useEffect(() => {
    checkHealth()
      .then((status) => {
        setHealth(status);
        if (status.tts) {
          setConfig((prev) => ({
            ...prev,
            tts_provider: status.tts!.default_provider,
            tts_voice: status.tts!.default_voice,
          }));
        }
      })
      .catch((err) => console.error('Health check error:', err));

    getVoices()
      .then(setVoices)
      .catch((err) => console.error('Voices fetch error:', err));

    getMascots()
      .then(setMascots)
      .catch((err) => console.error('Mascots fetch error:', err));

    getTemplates()
      .then((tmplList) => {
        setTemplates(tmplList);
        if (tmplList.length > 0) {
          const firstTmpl = tmplList[0];
          setVideoData({
            video_id: firstTmpl.bg_video,
            filename: firstTmpl.bg_video,
            file_path: `storage/uploads/${firstTmpl.bg_video}`,
            duration: 6.0,
            width: 1080,
            height: 1920,
            fps: 30,
          });
        }
      })
      .catch((err) => console.error('Templates fetch error:', err));
  }, []);

  // SSE Stream Listener for Trivia Batch Progress
  useEffect(() => {
    if (!activeJob?.job_id) return;
    const isTerminal = ['completed', 'failed', 'partial_failure'].includes(activeJob.status);
    if (isTerminal) return;

    const eventSource = new EventSource(`/api/jobs/${activeJob.job_id}/stream`);

    eventSource.onmessage = (e) => {
      try {
        const updatedState: BatchJobState = JSON.parse(e.data);
        setActiveJob(updatedState);
        if (['completed', 'failed', 'partial_failure'].includes(updatedState.status)) {
          eventSource.close();
        }
      } catch (err) {
        console.error('Failed to parse SSE payload:', err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setTimeout(() => {
        getJobStatus(activeJob.job_id).then(setActiveJob).catch(console.error);
      }, 2000);
    };

    return () => {
      eventSource.close();
    };
  }, [activeJob?.job_id, activeJob?.status]);

  // Mascot selection handler
  const handleSelectMascot = (mascot: MascotInfo) => {
    setConfig((prev) => ({
      ...prev,
      mascot_id: mascot.id,
      tts_voice: mascot.voice,
    }));
  };

  // Template selection handler
  const handleSelectTemplate = (template: TemplateInfo) => {
    setConfig((prev) => ({
      ...prev,
      template_id: template.id,
    }));
    setVideoData({
      video_id: template.bg_video,
      filename: template.bg_video,
      file_path: `storage/uploads/${template.bg_video}`,
      duration: 6.0,
      width: 1080,
      height: 1920,
      fps: 30,
    });
  };

  // Handler when selecting questions from the Question Bank modal
  const handleSelectQuestionsFromBank = (selectedItems: TriviaItem[]) => {
    setValidationData({
      valid_count: selectedItems.length,
      error_count: 0,
      items: selectedItems,
      errors: [],
      is_valid: true,
    });
  };

  const handleStartBatch = async () => {
    if (!validationData?.items || !videoData) return;
    setIsStartingBatch(true);
    setBatchError(null);

    try {
      const res = await createBatchJob(validationData.items, videoData.video_id, config);
      const initialJob = await getJobStatus(res.job_id);
      setActiveJob(initialJob);
    } catch (err: any) {
      setBatchError(err.message || 'Failed to start batch generation.');
    } finally {
      setIsStartingBatch(false);
    }
  };

  const handleRetryFailed = async () => {
    if (!activeJob) return;
    try {
      await retryJobFailedItems(activeJob.job_id);
      const refreshed = await getJobStatus(activeJob.job_id);
      setActiveJob(refreshed);
    } catch (err: any) {
      alert(err.message || 'Retry failed.');
    }
  };

  const canStartBatch = validationData?.is_valid && !!videoData;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header health={health} />
      <StudioTabs activeTab={activeStudio} onSelectTab={setActiveStudio} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
        {activeStudio === 'poem' ? (
          /* 🎵 SINGING & DANCING POEM STUDIO */
          <PoemStudio mascots={mascots} templates={templates} ttsStatus={health?.tts} />
        ) : (
          /* 🧠 TRIVIA & QUIZ STUDIO */
          <>
            <MascotGuide />

            {/* Mascot Selector */}
            {mascots.length > 0 && (
              <MascotSelector
                mascots={mascots}
                selectedMascotId={config.mascot_id}
                onSelectMascot={handleSelectMascot}
              />
            )}

            {/* Stock Template & Background Selector */}
            {templates.length > 0 && (
              <TemplateSelector
                templates={templates}
                selectedTemplateId={config.template_id}
                onSelectTemplate={handleSelectTemplate}
              />
            )}

            {/* Step 1: Upload Assets / Question Bank Explorer */}
            <UploadSection
              validationData={validationData}
              videoData={videoData}
              onValidationSuccess={setValidationData}
              onVideoSuccess={setVideoData}
              onOpenQuestionBank={() => setIsQuestionBankOpen(true)}
              isLoading={isStartingBatch}
            />

            {/* Step 2: Configure Render, Audio & BGM Settings */}
            <SettingsDrawer
              config={config}
              voices={voices}
              ttsStatus={health?.tts}
              onChange={(updated) => setConfig((prev) => ({ ...prev, ...updated }))}
            />

            {/* Step 3: Single-Item Test Preview Player */}
            <PreviewPlayer
              items={validationData?.items || []}
              videoData={videoData}
              config={config}
            />

            {/* Step 4: Start Full Batch Generation Call-To-Action */}
            <div className="bg-gradient-to-r from-amber-500/10 via-yellow-500/10 to-amber-500/10 border-2 border-amber-500/40 rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-xl shadow-amber-500/5">
              <div className="space-y-1 text-center sm:text-left">
                <h3 className="text-lg font-bold text-white flex items-center gap-2 justify-center sm:justify-start">
                  <span>Step 4: Launch Full Batch Generation</span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-400 text-slate-950 font-extrabold">
                    {validationData?.valid_count || 0} Shorts Ready
                  </span>
                </h3>
                <p className="text-xs text-slate-400 flex items-center gap-1.5 justify-center sm:justify-start">
                  {config.mix_mode ? (
                    <span className="text-pink-300 font-semibold flex items-center gap-1">
                      <Shuffle className="w-3.5 h-3.5" />
                      <span>Variety Playlist Active: Rotating 4 mascots, 5 stock themes & voices</span>
                    </span>
                  ) : (
                    <span>
                      Host: <strong className="text-amber-300">{mascots.find(m => m.id === config.mascot_id)?.name || 'Barnaby Bear'}</strong> • Theme: <strong className="text-sky-300">{templates.find(t => t.id === config.template_id)?.name || 'Rainbow Candy'}</strong>
                    </span>
                  )}
                </p>
              </div>

              <button
                type="button"
                onClick={handleStartBatch}
                disabled={!canStartBatch || isStartingBatch}
                className={`px-8 py-4 rounded-2xl font-extrabold text-base shadow-xl flex items-center gap-3 transition transform active:scale-95 ${
                  !canStartBatch || isStartingBatch
                    ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                    : 'bg-gradient-to-r from-amber-400 via-amber-500 to-yellow-400 text-slate-950 hover:brightness-110 shadow-amber-500/30'
                }`}
              >
                <Sparkles className="w-5 h-5 fill-current" />
                <span>
                  {isStartingBatch
                    ? 'Starting Factory...'
                    : `Generate All ${validationData?.valid_count || 0} Shorts`}
                </span>
              </button>
            </div>

            {batchError && (
              <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
                <span>{batchError}</span>
              </div>
            )}

            {/* Live Batch Progress & Results Hub */}
            {activeJob && (
              <BatchProgress
                jobState={activeJob}
                onRetry={handleRetryFailed}
              />
            )}
          </>
        )}
      </main>

      {/* 100+ Question Bank Modal */}
      <QuestionBankModal
        isOpen={isQuestionBankOpen}
        onClose={() => setIsQuestionBankOpen(false)}
        onSelectQuestions={handleSelectQuestionsFromBank}
      />

      <footer className="border-t border-slate-800 bg-slate-900/60 py-6 text-center text-xs text-slate-500">
        <p>
          AI Kids Shorts Factory • 🧠 Trivia & Quiz Studio • 🎵 Singing & Dancing Mascot Poem Studio
        </p>
      </footer>
    </div>
  );
};
