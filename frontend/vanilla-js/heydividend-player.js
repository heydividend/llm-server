/**
 * HeyDividend Video Player - Vanilla JavaScript Version
 * No dependencies required (except YouTube IFrame API)
 * Works with any frontend: PHP, HTML, Vue, Angular, etc.
 * 
 * Usage:
 *   const player = new HeyDividendPlayer('container-id', videoMetadata, options);
 * 
 * @version 1.0.0
 */

class HeyDividendPlayer {
  constructor(containerId, videoMetadata, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`Container element with id "${containerId}" not found`);
      return;
    }

    this.video = videoMetadata;
    this.options = {
      variant: options.variant || 'expanded', // 'inline', 'expanded', 'modal'
      autoplay: options.autoplay || false,
      onVideoEnd: options.onVideoEnd || null,
      onVideoPlay: options.onVideoPlay || null,
      showControls: options.showControls !== false,
    };

    this.player = null;
    this.playerState = {
      isPlaying: false,
      currentTime: 0,
      duration: 0,
      volume: 100,
      isMuted: false,
      playbackSpeed: 1,
      showControls: false,
    };

    this.playerId = `heydividend-player-${Date.now()}`;
    this.updateInterval = null;

    this.init();
  }

  init() {
    this.loadYouTubeAPI();
    this.render();
    this.attachEventListeners();
  }

  loadYouTubeAPI() {
    if (window.YT && window.YT.Player) {
      this.onYouTubeAPIReady();
      return;
    }

    if (!window.onYouTubeIframeAPIReady) {
      window.onYouTubeIframeAPIReady = () => {
        this.onYouTubeAPIReady();
      };

      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    }
  }

  extractVideoId(url) {
    if (this.video.video_id) return this.video.video_id;

    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/,
      /youtube\.com\/embed\/([^&\n?#]+)/,
    ];

    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match && match[1]) return match[1];
    }

    return '';
  }

  render() {
    const videoId = this.extractVideoId(this.video.video_url || this.video.embed_url);
    const variantClass = `heydividend-player--${this.options.variant}`;

    this.container.innerHTML = `
      <div class="heydividend-player ${variantClass}">
        <!-- Brand Header -->
        <div class="heydividend-player__header">
          <div class="heydividend-player__brand">
            <div class="heydividend-player__logo">HD</div>
            <span class="heydividend-player__brand-name">HeyDividend</span>
          </div>
          <span class="heydividend-player__channel">${this.video.channel_name || '@heydividedtv'}</span>
        </div>

        <!-- Video Player -->
        <div class="heydividend-player__wrapper">
          <div id="${this.playerId}"></div>
          
          <!-- Custom Controls Overlay -->
          ${this.options.showControls ? this.renderControls() : ''}
        </div>

        <!-- Video Info -->
        <div class="heydividend-player__info">
          <h3 class="heydividend-player__title">${this.escapeHtml(this.video.title)}</h3>
          ${this.video.duration ? `<span class="heydividend-player__duration">${this.video.duration}</span>` : ''}
        </div>

        ${this.video.description ? `
          <p class="heydividend-player__description">${this.escapeHtml(this.video.description)}</p>
        ` : ''}

        <!-- CTA Button -->
        <div class="heydividend-player__cta">
          <a href="${this.video.video_url}" target="_blank" rel="noopener noreferrer" class="heydividend-player__cta-button">
            ${this.video.cta_copy || 'Watch on YouTube'} →
          </a>
        </div>
      </div>
    `;
  }

  renderControls() {
    return `
      <div class="heydividend-player__controls-overlay">
        <!-- Progress Bar -->
        <div class="heydividend-player__progress-bar">
          <div class="heydividend-player__progress-fill" style="width: 0%"></div>
        </div>

        <!-- Control Buttons -->
        <div class="heydividend-player__controls">
          <div class="heydividend-player__controls-left">
            <!-- Play/Pause -->
            <button class="heydividend-player__control-btn heydividend-player__play-btn" aria-label="Play">
              ${this.icons.play}
            </button>

            <!-- Volume -->
            <div class="heydividend-player__volume-control">
              <button class="heydividend-player__control-btn heydividend-player__mute-btn" aria-label="Mute">
                ${this.icons.volume}
              </button>
              <input type="range" min="0" max="100" value="100" class="heydividend-player__volume-slider" aria-label="Volume">
            </div>

            <!-- Time Display -->
            <div class="heydividend-player__time">0:00 / 0:00</div>
          </div>

          <div class="heydividend-player__controls-right">
            <!-- Playback Speed -->
            <div class="heydividend-player__speed-control">
              <button class="heydividend-player__control-btn heydividend-player__speed-btn" aria-label="Playback speed">
                ${this.icons.settings}
                <span class="heydividend-player__speed-label">1x</span>
              </button>
              <div class="heydividend-player__speed-menu" style="display: none;">
                ${[0.5, 0.75, 1, 1.25, 1.5, 2].map(speed => 
                  `<button class="heydividend-player__speed-option" data-speed="${speed}">${speed}x</button>`
                ).join('')}
              </div>
            </div>

            <!-- Fullscreen -->
            <button class="heydividend-player__control-btn heydividend-player__fullscreen-btn" aria-label="Fullscreen">
              ${this.icons.maximize}
            </button>

            <!-- External Link -->
            <a href="${this.video.video_url}" target="_blank" rel="noopener noreferrer" 
               class="heydividend-player__external-link" aria-label="Watch on YouTube">
              ${this.icons.externalLink}
            </a>
          </div>
        </div>
      </div>
    `;
  }

  onYouTubeAPIReady() {
    const videoId = this.extractVideoId(this.video.video_url || this.video.embed_url);

    this.player = new YT.Player(this.playerId, {
      height: this.options.variant === 'inline' ? '200' : '100%',
      width: '100%',
      videoId: videoId,
      playerVars: {
        autoplay: this.options.autoplay ? 1 : 0,
        modestbranding: 1,
        rel: 0,
        controls: 0,
        disablekb: 0,
        fs: 1,
        iv_load_policy: 3,
      },
      events: {
        onReady: (event) => this.onPlayerReady(event),
        onStateChange: (event) => this.onStateChange(event),
      },
    });
  }

  onPlayerReady(event) {
    this.playerState.duration = event.target.getDuration();
    this.updateTimeDisplay();
    this.startUpdateInterval();
  }

  onStateChange(event) {
    const isPlaying = event.data === YT.PlayerState.PLAYING;
    this.playerState.isPlaying = isPlaying;

    const playBtn = this.container.querySelector('.heydividend-player__play-btn');
    if (playBtn) {
      playBtn.innerHTML = isPlaying ? this.icons.pause : this.icons.play;
      playBtn.setAttribute('aria-label', isPlaying ? 'Pause' : 'Play');
    }

    if (event.data === YT.PlayerState.ENDED && this.options.onVideoEnd) {
      this.options.onVideoEnd();
    }

    if (isPlaying && this.options.onVideoPlay) {
      this.options.onVideoPlay();
    }
  }

  attachEventListeners() {
    // Play/Pause
    const playBtn = this.container.querySelector('.heydividend-player__play-btn');
    if (playBtn) {
      playBtn.addEventListener('click', () => this.togglePlayPause());
    }

    // Mute
    const muteBtn = this.container.querySelector('.heydividend-player__mute-btn');
    if (muteBtn) {
      muteBtn.addEventListener('click', () => this.toggleMute());
    }

    // Volume Slider
    const volumeSlider = this.container.querySelector('.heydividend-player__volume-slider');
    if (volumeSlider) {
      volumeSlider.addEventListener('input', (e) => this.changeVolume(e.target.value));
    }

    // Speed Button
    const speedBtn = this.container.querySelector('.heydividend-player__speed-btn');
    const speedMenu = this.container.querySelector('.heydividend-player__speed-menu');
    if (speedBtn && speedMenu) {
      speedBtn.addEventListener('click', () => {
        speedMenu.style.display = speedMenu.style.display === 'none' ? 'block' : 'none';
      });

      // Speed Options
      const speedOptions = this.container.querySelectorAll('.heydividend-player__speed-option');
      speedOptions.forEach(option => {
        option.addEventListener('click', () => {
          const speed = parseFloat(option.dataset.speed);
          this.changePlaybackSpeed(speed);
        });
      });
    }

    // Fullscreen
    const fullscreenBtn = this.container.querySelector('.heydividend-player__fullscreen-btn');
    if (fullscreenBtn) {
      fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
    }

    // Show/Hide controls on hover
    const wrapper = this.container.querySelector('.heydividend-player__wrapper');
    const controlsOverlay = this.container.querySelector('.heydividend-player__controls-overlay');
    if (wrapper && controlsOverlay) {
      wrapper.addEventListener('mouseenter', () => {
        controlsOverlay.classList.add('heydividend-player__controls-overlay--visible');
      });
      wrapper.addEventListener('mouseleave', () => {
        controlsOverlay.classList.remove('heydividend-player__controls-overlay--visible');
      });
    }
  }

  togglePlayPause() {
    if (!this.player) return;

    if (this.playerState.isPlaying) {
      this.player.pauseVideo();
    } else {
      this.player.playVideo();
    }
  }

  toggleMute() {
    if (!this.player) return;

    if (this.playerState.isMuted) {
      this.player.unMute();
      this.playerState.isMuted = false;
      this.updateMuteButton();
    } else {
      this.player.mute();
      this.playerState.isMuted = true;
      this.updateMuteButton();
    }
  }

  changeVolume(volume) {
    if (!this.player) return;

    this.player.setVolume(volume);
    this.playerState.volume = volume;
    this.playerState.isMuted = volume === 0;
    this.updateMuteButton();
  }

  changePlaybackSpeed(speed) {
    if (!this.player) return;

    this.player.setPlaybackRate(speed);
    this.playerState.playbackSpeed = speed;

    const speedLabel = this.container.querySelector('.heydividend-player__speed-label');
    if (speedLabel) {
      speedLabel.textContent = `${speed}x`;
    }

    const speedMenu = this.container.querySelector('.heydividend-player__speed-menu');
    if (speedMenu) {
      speedMenu.style.display = 'none';
    }

    // Update active state
    const speedOptions = this.container.querySelectorAll('.heydividend-player__speed-option');
    speedOptions.forEach(option => {
      if (parseFloat(option.dataset.speed) === speed) {
        option.classList.add('heydividend-player__speed-option--active');
      } else {
        option.classList.remove('heydividend-player__speed-option--active');
      }
    });
  }

  toggleFullscreen() {
    const wrapper = this.container.querySelector('.heydividend-player__wrapper');
    if (!wrapper) return;

    if (!document.fullscreenElement) {
      wrapper.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }

  updateMuteButton() {
    const muteBtn = this.container.querySelector('.heydividend-player__mute-btn');
    if (muteBtn) {
      muteBtn.innerHTML = this.playerState.isMuted ? this.icons.volumeX : this.icons.volume;
      muteBtn.setAttribute('aria-label', this.playerState.isMuted ? 'Unmute' : 'Mute');
    }
  }

  startUpdateInterval() {
    this.updateInterval = setInterval(() => {
      if (this.player && this.playerState.isPlaying) {
        this.playerState.currentTime = this.player.getCurrentTime();
        this.updateProgressBar();
        this.updateTimeDisplay();
      }
    }, 100);
  }

  updateProgressBar() {
    const progressFill = this.container.querySelector('.heydividend-player__progress-fill');
    if (progressFill && this.playerState.duration > 0) {
      const percentage = (this.playerState.currentTime / this.playerState.duration) * 100;
      progressFill.style.width = `${percentage}%`;
    }
  }

  updateTimeDisplay() {
    const timeDisplay = this.container.querySelector('.heydividend-player__time');
    if (timeDisplay) {
      const current = this.formatTime(this.playerState.currentTime);
      const duration = this.formatTime(this.playerState.duration);
      timeDisplay.textContent = `${current} / ${duration}`;
    }
  }

  formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  destroy() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
    if (this.player) {
      this.player.destroy();
    }
    this.container.innerHTML = '';
  }

  // SVG Icons
  get icons() {
    return {
      play: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>',
      pause: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>',
      volume: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>',
      volumeX: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>',
      maximize: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg>',
      externalLink: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>',
      settings: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M12 1v6m0 6v6m5.2-13.2l-3.4 3.4m-3.6 3.6l-3.4 3.4m13.2-5.2l-3.4-3.4m-3.6-3.6l-3.4-3.4"></path></svg>',
    };
  }
}

// Export for use in modules or make globally available
if (typeof module !== 'undefined' && module.exports) {
  module.exports = HeyDividendPlayer;
}
