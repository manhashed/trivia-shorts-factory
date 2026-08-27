import {
  ValidationResponse,
  VideoUploadResponse,
  VoiceOption,
  VideoRenderConfig,
  BatchJobState,
  TriviaItem,
  MascotInfo,
  TemplateInfo,
  CategoryInfo,
} from '../types';

const API_BASE = '/api';

export async function checkHealth(): Promise<{
  status: string;
  ffmpeg_installed: boolean;
  ffmpeg_path: string | null;
  app_version: string;
  error: string | null;
}> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Failed to reach backend server.');
  return res.json();
}

export async function getVoices(): Promise<Record<string, VoiceOption[]>> {
  const res = await fetch(`${API_BASE}/voices`);
  if (!res.ok) throw new Error('Failed to fetch voices list.');
  return res.json();
}

export async function getMascots(): Promise<MascotInfo[]> {
  const res = await fetch(`${API_BASE}/mascots`);
  if (!res.ok) throw new Error('Failed to fetch mascots list.');
  return res.json();
}

export async function getTemplates(): Promise<TemplateInfo[]> {
  const res = await fetch(`${API_BASE}/templates`);
  if (!res.ok) throw new Error('Failed to fetch templates list.');
  return res.json();
}

export async function getQuestionBank(category?: string): Promise<{ total: number; category: string; questions: TriviaItem[] }> {
  const url = category && category !== 'all' ? `${API_BASE}/question-bank?category=${encodeURIComponent(category)}` : `${API_BASE}/question-bank`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch question bank.');
  return res.json();
}

export async function getQuestionBankCategories(): Promise<CategoryInfo[]> {
  const res = await fetch(`${API_BASE}/question-bank/categories`);
  if (!res.ok) throw new Error('Failed to fetch question bank categories.');
  return res.json();
}

export async function validateTriviaFile(file: File): Promise<ValidationResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/validate`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Validation failed.');
  }

  return res.json();
}

export async function uploadBackgroundVideo(file: File): Promise<VideoUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/upload/video`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Video upload failed.');
  }

  return res.json();
}

export async function generatePreview(
  question: string,
  answer: string,
  videoId: string,
  config: VideoRenderConfig,
  options?: string[],
  correctIndex?: number
): Promise<{ preview_id: string; video_url: string; timing: Record<string, number> }> {
  const formData = new FormData();
  formData.append('question', question);
  formData.append('answer', answer);
  formData.append('video_id', videoId);
  formData.append('config_json', JSON.stringify(config));
  if (options && options.length > 0) {
    formData.append('options_json', JSON.stringify(options));
    formData.append('correct_index', String(correctIndex ?? 0));
  }

  const res = await fetch(`${API_BASE}/preview`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to generate preview short.');
  }

  return res.json();
}

export async function createBatchJob(
  items: TriviaItem[],
  videoId: string,
  config: VideoRenderConfig
): Promise<{ job_id: string; total_items: number; status: string }> {
  const formData = new FormData();
  formData.append('items_json', JSON.stringify(items));
  formData.append('video_id', videoId);
  formData.append('config_json', JSON.stringify(config));

  const res = await fetch(`${API_BASE}/jobs/create`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to start batch rendering job.');
  }

  return res.json();
}

export async function getJobStatus(jobId: string): Promise<BatchJobState> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error('Failed to fetch job state.');
  return res.json();
}

export async function retryJobFailedItems(jobId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/retry`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to trigger retry for failed items.');
}
