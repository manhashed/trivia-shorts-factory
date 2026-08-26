import {
  PoemItem,
  PoemRenderConfig,
  PoemBatchJobState,
  MelodyOption,
} from '../types/poem';
import { CategoryInfo } from '../types';

const API_BASE = '/api';

export async function getPoemBank(category?: string): Promise<{ total: number; category: string; poems: PoemItem[] }> {
  const url = category && category !== 'all' ? `${API_BASE}/poems?category=${encodeURIComponent(category)}` : `${API_BASE}/poems`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch poem bank.');
  return res.json();
}

export async function getPoemCategories(): Promise<CategoryInfo[]> {
  const res = await fetch(`${API_BASE}/poems/categories`);
  if (!res.ok) throw new Error('Failed to fetch poem categories.');
  return res.json();
}

export async function getMelodies(): Promise<MelodyOption[]> {
  const res = await fetch(`${API_BASE}/melodies`);
  if (!res.ok) throw new Error('Failed to fetch melodies list.');
  return res.json();
}

export async function generatePoemPreview(
  poem: PoemItem,
  config: PoemRenderConfig
): Promise<{ preview_id: string; video_url: string }> {
  const formData = new FormData();
  formData.append('poem_json', JSON.stringify(poem));
  formData.append('config_json', JSON.stringify(config));

  const res = await fetch(`${API_BASE}/poems/preview`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to generate poem preview.');
  }

  return res.json();
}

export async function createPoemBatchJob(
  poems: PoemItem[],
  config: PoemRenderConfig
): Promise<{ job_id: string; total_items: number; status: string }> {
  const formData = new FormData();
  formData.append('poems_json', JSON.stringify(poems));
  formData.append('config_json', JSON.stringify(config));

  const res = await fetch(`${API_BASE}/poems/jobs/create`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to start poem batch rendering.');
  }

  return res.json();
}

export async function getPoemJobStatus(jobId: string): Promise<PoemBatchJobState> {
  const res = await fetch(`${API_BASE}/poems/jobs/${jobId}`);
  if (!res.ok) throw new Error('Failed to fetch poem job state.');
  return res.json();
}
