/**
 * HeyDividend Video Player - TypeScript Interfaces
 * Data contract between Harvey backend and frontend video player
 */

export interface VideoMetadata {
  video_id: string;
  title: string;
  description: string;
  duration: string;
  thumbnail_url: string;
  video_url: string;
  embed_url: string;
  channel_name: string;
  published_at?: string;
  cta_copy?: string;
}

export interface VideoPlayerProps {
  video: VideoMetadata;
  variant?: 'inline' | 'expanded' | 'modal';
  autoplay?: boolean;
  onVideoEnd?: () => void;
  onVideoPlay?: () => void;
  className?: string;
}

export interface PlayerState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  isFullscreen: boolean;
  playbackSpeed: number;
  showControls: boolean;
}

export interface VideoQueueProps {
  videos: VideoMetadata[];
  currentIndex: number;
  onVideoSelect: (index: number) => void;
}
