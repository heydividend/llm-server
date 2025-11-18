'use client';

import React, { useEffect } from 'react';
import { VideoMetadata } from '@/types/video';
import { HeyDividendPlayer } from './HeyDividendPlayer';
import { VideoQueue } from './VideoQueue';
import styles from '@/styles/components/VideoModal.module.css';
import { X } from 'lucide-react';

interface VideoModalProps {
  videos: VideoMetadata[];
  currentIndex: number;
  onClose: () => void;
  onVideoChange: (index: number) => void;
}

/**
 * Video Modal Component
 * Fullscreen modal overlay for immersive video viewing
 * 
 * @example
 * ```tsx
 * <VideoModal
 *   videos={videoMetadataArray}
 *   currentIndex={0}
 *   onClose={() => setShowModal(false)}
 *   onVideoChange={(index) => setCurrentIndex(index)}
 * />
 * ```
 */
export const VideoModal: React.FC<VideoModalProps> = ({
  videos,
  currentIndex,
  onClose,
  onVideoChange,
}) => {
  const currentVideo = videos[currentIndex];

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  const handleNext = () => {
    if (currentIndex < videos.length - 1) {
      onVideoChange(currentIndex + 1);
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div className={styles.backdrop} onClick={onClose} />

      {/* Modal Content */}
      <div className={styles.modal}>
        {/* Close Button */}
        <button 
          onClick={onClose} 
          className={styles.closeButton}
          aria-label="Close video player"
        >
          <X size={24} />
        </button>

        {/* Main Video Player */}
        <div className={styles.playerSection}>
          <HeyDividendPlayer
            video={currentVideo}
            variant="modal"
            onVideoEnd={handleNext}
            autoplay={true}
          />
        </div>

        {/* Video Queue (if multiple videos) */}
        {videos.length > 1 && (
          <div className={styles.queueSection}>
            <VideoQueue
              videos={videos}
              currentIndex={currentIndex}
              onVideoSelect={onVideoChange}
            />
          </div>
        )}
      </div>
    </>
  );
};

export default VideoModal;
