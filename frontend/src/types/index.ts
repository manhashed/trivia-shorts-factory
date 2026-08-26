export interface TriviaItem {
  id?: string;
  q: string;
  a: string;
  category?: string;
  options?: string[];
  correct_index?: number;
}

export interface ValidationErrorItem {
  index: number;
  reason: string;
}

export interface ValidationResponse {
  valid_count: number;
  error_count: number;
  items: TriviaItem[];
  errors: ValidationErrorItem[];
  is_valid: boolean;
}

export interface VideoUploadResponse {
  video_id: string;
  filename: string;
  file_path: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
}

export interface VoiceOption {
  id: string;
  name: string;
  gender: string;
  locale: string;
  tags?: string[];
}

export interface MascotInfo {
  id: string;
  name: string;
  emoji: string;
  tagline: string;
  voice: string;
  theme: string;
}

export interface TemplateInfo {
  id: string;
  name: string;
  emoji: string;
  bg_video: string;
  accent_color: string;
  description: string;
}

export interface CategoryInfo {
  name: string;
  count: number;
}

export interface VideoRenderConfig {
  width: number;
  height: number;
  fps: number;
  countdown_duration: number;
  post_answer_pause: number;
  mascot_id: string;
  mascot_enabled: boolean;
  template_id: string;
  countdown_style: 'pulse_badge' | 'radial_ring' | 'clean_bar';
  countdown_sfx: 'tick_tock' | 'beep' | 'mute';
  background_mode: 'crop_fill' | 'blur_fill';
  mix_mode: boolean;
  bgm_track: 'playful_nursery' | 'magical_story' | 'none';
  bgm_volume: number;
  // Animation & Visual Effects
  animation_style: 'bounce' | 'slide' | 'pop' | 'none';
  confetti_enabled: boolean;
  background_zoom: boolean;
  answer_flash: boolean;
  mascot_dance: boolean;
  audience_prompt: boolean;
  audio_normalize: boolean;
  sfx_volume: number;
  tts_provider: 'edge' | 'openai' | 'elevenlabs';
  tts_voice: string;
  tts_speed: string;
  tts_pitch: string;
  openai_api_key?: string;
  elevenlabs_api_key?: string;
}

export interface BatchItemStatus {
  index: number;
  id: string;
  question: string;
  answer: string;
  category?: string;
  options?: string[];
  mascot_used?: string;
  template_used?: string;
  voice_used?: string;
  status: 'queued' | 'tts_processing' | 'rendering' | 'completed' | 'failed';
  progress: number;
  output_filename?: string;
  video_url?: string;
  duration?: number;
  error?: string;
  action_suggestion?: string;
}

export interface BatchJobState {
  job_id: string;
  created_at: string;
  status: 'pending' | 'processing' | 'completed' | 'partial_failure' | 'failed';
  total_items: number;
  completed_items: number;
  failed_items: number;
  overall_progress: number;
  items: BatchItemStatus[];
  zip_filename?: string;
  zip_url?: string;
  error?: string;
}
