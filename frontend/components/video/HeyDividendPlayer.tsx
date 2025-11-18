'use client';

import React, { useState, useRef, useEffect } from 'react';
import YouTube, { YouTubeProps, YouTubePlayer } from 'react-youtube';
import { VideoMetadata, VideoPlayerProps, PlayerState } from '@/types/video';
import styles from '@/styles/components/HeyDividendPlayer.module.css';
import { Play, Pause, Volume2, VolumeX, Maximize, ExternalLink, Settings } from 'lucide-react';

/**
 * HeyDividend Branded Video Player Component
 * 
 * A custom-styled YouTube player with HeyDividend branding
 * Supports three variants: inline, expanded, and modal
 * 
 * @example
 * ```tsx
 * <HeyDividendPlayer 
 *   video={videoMetadata}
 *   variant="expanded"
 *   autoplay={false}
 * />
 * ```
 */
export const HeyDividendPlayer: React.FC<VideoPlayerProps> = ({
  video,
  variant = 'inline',
  autoplay = false,
  onVideoEnd,
  onVideoPlay,
  className = '',
}) => {
  const playerRef = useRef<YouTubePlayer | null>(null);
  const [playerState, setPlayerState] = useState<PlayerState>({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    volume: 100,
    isMuted: false,
    isFullscreen: false,
    playbackSpeed: 1,
    showControls: false,
  });

  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const [isReady, setIsReady] = useState(false);

  // Extract video ID from various YouTube URL formats
  const extractVideoId = (url: string): string => {
    if (video.video_id) return video.video_id;
    
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/,
      /youtube\.com\/embed\/([^&\n?#]+)/,
    ];

    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match && match[1]) return match[1];
    }

    return '';
  };

  const videoId = extractVideoId(video.video_url || video.embed_url);

  const opts: YouTubeProps['opts'] = {
    height: variant === 'inline' ? '200' : '100%',
    width: '100%',
    playerVars: {
      autoplay: autoplay ? 1 : 0,
      modestbranding: 1,
      rel: 0,
      controls: 0, // Hide default YouTube controls
      disablekb: 0,
      fs: 1,
      iv_load_policy: 3,
    },
  };

  const onPlayerReady = (event: { target: YouTubePlayer }) => {
    playerRef.current = event.target;
    setIsReady(true);
    const duration = event.target.getDuration();
    setPlayerState(prev => ({ ...prev, duration }));
  };

  const onStateChange = (event: { data: number }) => {
    const isPlaying = event.data === 1;
    setPlayerState(prev => ({ ...prev, isPlaying }));

    if (event.data === 0 && onVideoEnd) {
      onVideoEnd();
    }

    if (isPlaying && onVideoPlay) {
      onVideoPlay();
    }
  };

  const togglePlayPause = () => {
    if (!playerRef.current) return;

    if (playerState.isPlaying) {
      playerRef.current.pauseVideo();
    } else {
      playerRef.current.playVideo();
    }
  };

  const toggleMute = () => {
    if (!playerRef.current) return;

    if (playerState.isMuted) {
      playerRef.current.unMute();
      setPlayerState(prev => ({ ...prev, isMuted: false }));
    } else {
      playerRef.current.mute();
      setPlayerState(prev => ({ ...prev, isMuted: true }));
    }
  };

  const changeVolume = (newVolume: number) => {
    if (!playerRef.current) return;

    playerRef.current.setVolume(newVolume);
    setPlayerState(prev => ({ ...prev, volume: newVolume, isMuted: newVolume === 0 }));
  };

  const changePlaybackSpeed = (speed: number) => {
    if (!playerRef.current) return;

    playerRef.current.setPlaybackRate(speed);
    setPlayerState(prev => ({ ...prev, playbackSpeed: speed }));
    setShowSpeedMenu(false);
  };

  const toggleFullscreen = () => {
    const iframe = document.querySelector(`.${styles.playerWrapper} iframe`);
    if (!iframe) return;

    if (!document.fullscreenElement) {
      iframe.requestFullscreen?.();
      setPlayerState(prev => ({ ...prev, isFullscreen: true }));
    } else {
      document.exitFullscreen?.();
      setPlayerState(prev => ({ ...prev, isFullscreen: false }));
    }
  };

  // Update current time periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (playerRef.current && playerState.isPlaying) {
        const currentTime = playerRef.current.getCurrentTime();
        setPlayerState(prev => ({ ...prev, currentTime }));
      }
    }, 100);

    return () => clearInterval(interval);
  }, [playerState.isPlaying]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progressPercentage = playerState.duration > 0
    ? (playerState.currentTime / playerState.duration) * 100
    : 0;

  return (
    <div 
      className={`${styles.container} ${styles[variant]} ${className}`}
      onMouseEnter={() => setPlayerState(prev => ({ ...prev, showControls: true }))}
      onMouseLeave={() => setPlayerState(prev => ({ ...prev, showControls: false }))}
    >
      {/* HeyDividend Branding Header */}
      <div className={styles.brandHeader}>
        <div className={styles.brandLogo}>
          <div className={styles.logoIcon}>HD</div>
          <span className={styles.brandName}>HeyDividend</span>
        </div>
        <span className={styles.channelBadge}>{video.channel_name}</span>
      </div>

      {/* Video Player */}
      <div className={styles.playerWrapper}>
        <YouTube
          videoId={videoId}
          opts={opts}
          onReady={onPlayerReady}
          onStateChange={onStateChange}
          className={styles.youtubePlayer}
        />

        {/* Custom Controls Overlay */}
        {isReady && (
          <div className={`${styles.controlsOverlay} ${playerState.showControls ? styles.visible : ''}`}>
            {/* Progress Bar */}
            <div className={styles.progressBar}>
              <div 
                className={styles.progressFill} 
                style={{ width: `${progressPercentage}%` }}
              />
            </div>

            {/* Control Buttons */}
            <div className={styles.controls}>
              <div className={styles.controlsLeft}>
                {/* Play/Pause */}
                <button 
                  onClick={togglePlayPause} 
                  className={styles.controlButton}
                  aria-label={playerState.isPlaying ? 'Pause' : 'Play'}
                >
                  {playerState.isPlaying ? <Pause size={20} /> : <Play size={20} />}
                </button>

                {/* Volume */}
                <div className={styles.volumeControl}>
                  <button 
                    onClick={toggleMute} 
                    className={styles.controlButton}
                    aria-label={playerState.isMuted ? 'Unmute' : 'Mute'}
                  >
                    {playerState.isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
                  </button>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={playerState.volume}
                    onChange={(e) => changeVolume(Number(e.target.value))}
                    className={styles.volumeSlider}
                    aria-label="Volume"
                  />
                </div>

                {/* Time Display */}
                <div className={styles.timeDisplay}>
                  {formatTime(playerState.currentTime)} / {formatTime(playerState.duration)}
                </div>
              </div>

              <div className={styles.controlsRight}>
                {/* Playback Speed */}
                <div className={styles.speedControl}>
                  <button 
                    onClick={() => setShowSpeedMenu(!showSpeedMenu)}
                    className={styles.controlButton}
                    aria-label="Playback speed"
                  >
                    <Settings size={20} />
                    <span className={styles.speedLabel}>{playerState.playbackSpeed}x</span>
                  </button>

                  {showSpeedMenu && (
                    <div className={styles.speedMenu}>
                      {[0.5, 0.75, 1, 1.25, 1.5, 2].map(speed => (
                        <button
                          key={speed}
                          onClick={() => changePlaybackSpeed(speed)}
                          className={`${styles.speedOption} ${playerState.playbackSpeed === speed ? styles.active : ''}`}
                        >
                          {speed}x
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Fullscreen */}
                <button 
                  onClick={toggleFullscreen} 
                  className={styles.controlButton}
                  aria-label="Fullscreen"
                >
                  <Maximize size={20} />
                </button>

                {/* Watch on YouTube */}
                <a 
                  href={video.video_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className={styles.externalLink}
                  aria-label="Watch on YouTube"
                >
                  <ExternalLink size={20} />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Video Info */}
      <div className={styles.videoInfo}>
        <h3 className={styles.videoTitle}>{video.title}</h3>
        {video.duration && (
          <span className={styles.duration}>{video.duration}</span>
        )}
      </div>

      {video.description && (
        <p className={styles.videoDescription}>{video.description}</p>
      )}

      {/* CTA Button */}
      <div className={styles.ctaSection}>
        <a 
          href={video.video_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className={styles.ctaButton}
        >
          {video.cta_copy || 'Watch on YouTube'} →
        </a>
      </div>
    </div>
  );
};

export default HeyDividendPlayer;
