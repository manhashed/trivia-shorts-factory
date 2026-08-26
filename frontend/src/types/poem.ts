export interface PoemItem {
  id?: string;
  title: string;
  lines: string[];
  category?: string;
  theme?: string;
  mascot?: string;
  melody?: string;
}

export interface MelodyOption {
  id: string;
  name: string;
  bpm: number;
}

export interface PoemRenderConfig {
  width: number;
  height: number;
  fps: number;
  mascot_id: string;
  template_id: string;
  melody_track: string;
  melody_volume: number;
  tts_provider: 'edge' | 'openai' | 'elevenlabs';
  tts_voice: string;
  tts_speed: string;
  dance_bpm: number;
  karaoke_style: 'bouncing_star' | 'glow_highlight' | 'clean_cards';
  mix_mode: boolean;
}

export interface PoemBatchItemStatus {
  index: number;
  id: string;
  title: string;
  lines: string[];
  category?: string;
  mascot_used?: string;
  template_used?: string;
  melody_used?: string;
  voice_used?: string;
  status: 'queued' | 'tts_processing' | 'rendering' | 'completed' | 'failed';
  progress: number;
  output_filename?: string;
  video_url?: string;
  duration?: number;
  error?: string;
}

export interface PoemBatchJobState {
  job_id: string;
  created_at: string;
  status: 'pending' | 'processing' | 'completed' | 'partial_failure' | 'failed';
  total_items: number;
  completed_items: number;
  failed_items: number;
  overall_progress: number;
  items: PoemBatchItemStatus[];
  zip_filename?: string;
  zip_url?: string;
  error?: string;
}
