'use client';

import React from 'react';
import { VideoMetadata, VideoQueueProps } from '@/types/video';
import styles from '@/styles/components/VideoQueue.module.css';
import { Play, Clock } from 'lucide-react';

/**
 * Video Queue Component
 * Displays a list of recommended videos that can be selected
 * 
 * @example
 * ```tsx
 * <VideoQueue
 *   videos={videoMetadataArray}
 *   currentIndex={0}
 *   onVideoSelect={(index) => setCurrentVideo(index)}
 * />
 * ```
 */
export const VideoQueue: React.FC<VideoQueueProps> = ({
  videos,
  currentIndex,
  onVideoSelect,
}) => {
  if (videos.length === 0) return null;

  return (
    <div className={styles.container}>
      <h4 className={styles.title}>
        Up Next ({videos.length} video{videos.length !== 1 ? 's' : ''})
      </h4>

      <div className={styles.queue}>
        {videos.map((video, index) => (
          <button
            key={video.video_id || index}
            onClick={() => onVideoSelect(index)}
            className={`${styles.videoCard} ${index === currentIndex ? styles.active : ''}`}
            aria-label={`Play ${video.title}`}
          >
            {/* Thumbnail */}
            <div className={styles.thumbnail}>
              <img
                src={video.thumbnail_url}
                alt={video.title}
                className={styles.thumbnailImage}
              />
              <div className={styles.thumbnailOverlay}>
                {index === currentIndex ? (
                  <div className={styles.nowPlaying}>Now Playing</div>
                ) : (
                  <Play size={24} className={styles.playIcon} />
                )}
              </div>
              {video.duration && (
                <div className={styles.durationBadge}>
                  <Clock size={12} />
                  <span>{video.duration}</span>
                </div>
              )}
            </div>

            {/* Video Info */}
            <div className={styles.videoInfo}>
              <h5 className={styles.videoTitle}>{video.title}</h5>
              {video.description && (
                <p className={styles.videoDescription}>
                  {video.description.slice(0, 80)}
                  {video.description.length > 80 ? '...' : ''}
                </p>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default VideoQueue;
