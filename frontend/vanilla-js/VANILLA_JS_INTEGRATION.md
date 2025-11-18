# HeyDividend Video Player - Vanilla JavaScript Integration Guide

## 🎯 Overview

A drop-in, dependency-free video player with HeyDividend branding that works with **any web framework** or plain HTML. No React, no build tools, no npm packages required.

### ✨ Perfect For:
- ✅ PHP applications
- ✅ WordPress sites
- ✅ Vue.js apps
- ✅ Angular apps
- ✅ Plain HTML/JavaScript sites
- ✅ Any web frontend that can't use React

---

## 📦 What's Included

```
vanilla-js/
├── heydividend-player.js       # Main player class (18KB)
├── heydividend-player.css      # Standalone styles (12KB)
├── demo.html                   # Complete demo
└── VANILLA_JS_INTEGRATION.md   # This file
```

**Total Size:** ~30KB (uncompressed)  
**Dependencies:** None (YouTube IFrame API loads automatically)

---

## 🚀 Quick Start (3 Steps)

### Step 1: Include Files

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="heydividend-player.css">
</head>
<body>
  <!-- Your content -->
  <script src="heydividend-player.js"></script>
</body>
</html>
```

### Step 2: Create Container

```html
<div id="my-video-player"></div>
```

### Step 3: Initialize Player

```javascript
const videoMetadata = {
  video_id: "dQw4w9WgXcQ",
  title: "Understanding Dividend Investing",
  description: "Learn the basics of dividend investing...",
  duration: "12:34",
  thumbnail_url: "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  video_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  embed_url: "https://www.youtube.com/embed/dQw4w9WgXcQ",
  channel_name: "@heydividedtv",
  cta_copy: "Watch on YouTube"
};

const player = new HeyDividendPlayer('my-video-player', videoMetadata, {
  variant: 'expanded',
  autoplay: false
});
```

**Done!** 🎉

---

## 📖 Complete API Reference

### Constructor

```javascript
new HeyDividendPlayer(containerId, videoMetadata, options)
```

### Parameters

#### `containerId` (required)
- Type: `string`
- Description: ID of the HTML element to render the player in

#### `videoMetadata` (required)
- Type: `object`
- Description: Video information from Harvey API

```javascript
{
  video_id: "abc123",              // YouTube video ID
  title: "Video Title",            // Display title
  description: "Description...",   // Video description
  duration: "12:34",               // Duration string
  thumbnail_url: "https://...",    // Thumbnail image URL
  video_url: "https://...",        // Full YouTube URL
  embed_url: "https://...",        // Embed URL
  channel_name: "@heydividedtv",   // Channel name
  cta_copy: "Watch on YouTube"     // CTA button text
}
```

#### `options` (optional)
- Type: `object`
- Description: Configuration options

```javascript
{
  variant: 'expanded',           // 'inline', 'expanded', 'modal'
  autoplay: false,               // Auto-start playback
  showControls: true,            // Show custom controls
  onVideoEnd: () => {},          // Callback when video ends
  onVideoPlay: () => {}          // Callback when video starts
}
```

### Methods

```javascript
// Destroy player and clean up
player.destroy();

// Programmatically control playback
player.togglePlayPause();
player.toggleMute();
player.changeVolume(50);           // 0-100
player.changePlaybackSpeed(1.5);   // 0.5, 0.75, 1, 1.25, 1.5, 2
```

---

## 🔌 Integration Examples

### Example 1: PHP Application

```php
<!-- chat-message.php -->
<div class="chat-message">
  <div class="message-text">
    <?php echo htmlspecialchars($message['text']); ?>
  </div>

  <?php if (!empty($message['video_metadata'])): ?>
    <div id="video-<?php echo $message['id']; ?>"></div>
    
    <script>
      const videoData = <?php echo json_encode($message['video_metadata'][0]); ?>;
      new HeyDividendPlayer('video-<?php echo $message['id']; ?>', videoData, {
        variant: 'inline'
      });
    </script>
  <?php endif; ?>
</div>
```

### Example 2: Vue.js Component

```vue
<template>
  <div>
    <div :id="playerId" class="video-container"></div>
  </div>
</template>

<script>
export default {
  props: ['videoMetadata'],
  data() {
    return {
      playerId: `player-${Date.now()}`,
      player: null
    };
  },
  mounted() {
    this.player = new HeyDividendPlayer(this.playerId, this.videoMetadata, {
      variant: 'expanded',
      autoplay: false
    });
  },
  beforeDestroy() {
    if (this.player) {
      this.player.destroy();
    }
  }
};
</script>
```

### Example 3: Angular Component

```typescript
// video-player.component.ts
import { Component, Input, OnInit, OnDestroy, AfterViewInit } from '@angular/core';

declare const HeyDividendPlayer: any;

@Component({
  selector: 'app-video-player',
  template: '<div [id]="playerId"></div>'
})
export class VideoPlayerComponent implements OnInit, AfterViewInit, OnDestroy {
  @Input() videoMetadata: any;
  @Input() variant: string = 'expanded';
  
  playerId: string;
  player: any;

  ngOnInit() {
    this.playerId = `player-${Date.now()}`;
  }

  ngAfterViewInit() {
    this.player = new HeyDividendPlayer(this.playerId, this.videoMetadata, {
      variant: this.variant,
      autoplay: false
    });
  }

  ngOnDestroy() {
    if (this.player) {
      this.player.destroy();
    }
  }
}
```

### Example 4: WordPress Plugin

```php
// heydividend-video-player.php
function render_heydividend_player($video_data) {
  $player_id = 'player-' . uniqid();
  
  ob_start();
  ?>
  <div id="<?php echo $player_id; ?>"></div>
  <script>
    (function() {
      const videoData = <?php echo json_encode($video_data); ?>;
      new HeyDividendPlayer('<?php echo $player_id; ?>', videoData, {
        variant: 'expanded',
        autoplay: false
      });
    })();
  </script>
  <?php
  return ob_get_clean();
}

// Shortcode: [heydividend_video id="abc123"]
add_shortcode('heydividend_video', function($atts) {
  $video_data = get_video_metadata($atts['id']);
  return render_heydividend_player($video_data);
});
```

---

## 🎨 Variants

### 1. Inline (Compact)

Perfect for chat messages and sidebars.

```javascript
new HeyDividendPlayer('container', videoMetadata, {
  variant: 'inline'  // 200px height, compact design
});
```

### 2. Expanded (16:9)

Full-width responsive player.

```javascript
new HeyDividendPlayer('container', videoMetadata, {
  variant: 'expanded'  // 16:9 aspect ratio, full-width
});
```

### 3. Modal (Fullscreen)

Overlay player (requires custom backdrop).

```javascript
new HeyDividendPlayer('container', videoMetadata, {
  variant: 'modal'  // Fixed position, fullscreen
});
```

---

## 🔗 Integration with Harvey API

### Automatic Rendering

```javascript
// Fetch chat response from Harvey
fetch('https://your-harvey-instance.com/v1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key'
  },
  body: JSON.stringify({
    message: 'Tell me about dividend stocks',
    user_id: 'user123'
  })
})
.then(res => res.json())
.then(data => {
  // Display message text
  document.getElementById('message').innerHTML = data.enhanced_response;

  // Render videos if available
  if (data.video_metadata && data.video_metadata.length > 0) {
    data.video_metadata.forEach((video, index) => {
      // Create container dynamically
      const container = document.createElement('div');
      container.id = `video-${index}`;
      document.getElementById('videos').appendChild(container);

      // Initialize player
      new HeyDividendPlayer(`video-${index}`, video, {
        variant: 'expanded',
        autoplay: false
      });
    });
  }
});
```

### With Video Queue

```javascript
const videos = data.video_metadata;
let currentIndex = 0;

function renderVideoPlayer() {
  const player = new HeyDividendPlayer('main-player', videos[currentIndex], {
    variant: 'expanded',
    autoplay: true,
    onVideoEnd: () => {
      // Auto-play next video
      if (currentIndex < videos.length - 1) {
        currentIndex++;
        player.destroy();
        renderVideoPlayer();
      }
    }
  });
}

renderVideoPlayer();
```

---

## 🎛️ Customization

### Custom Branding Colors

Override CSS variables in your stylesheet:

```css
.heydividend-player {
  /* Override brand colors */
  background: linear-gradient(135deg, #1a1a2e 0%, #2d3a5a 100%);
}

.heydividend-player__logo {
  background: linear-gradient(135deg, #16c172 0%, #12a05c 100%);
}

.heydividend-player__progress-fill {
  background: linear-gradient(90deg, #16c172 0%, #12a05c 100%);
}
```

### Custom Player Size

```css
#my-custom-player .heydividend-player {
  max-width: 800px;
  margin: 0 auto;
}
```

---

## ♿ Accessibility

The player includes:
- ✅ Keyboard navigation
- ✅ ARIA labels
- ✅ Focus indicators
- ✅ Screen reader support

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `M` | Mute/Unmute |
| `F` | Fullscreen |
| `←` | Seek backward (YouTube default) |
| `→` | Seek forward (YouTube default) |

---

## 📱 Mobile Responsiveness

The player automatically adapts to mobile devices:
- Volume slider hidden on mobile (native controls used)
- Always-visible controls on touchscreens
- Optimized button sizes for touch
- Responsive text scaling

---

## 🐛 Troubleshooting

### Player Not Showing

**Problem**: Container is empty  
**Solution**: Ensure container exists before initializing player

```javascript
// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
  new HeyDividendPlayer('my-player', videoData);
});
```

### YouTube API Not Loading

**Problem**: YouTube IFrame API fails to load  
**Solution**: Check console for errors, ensure internet connection

```javascript
// Manual API loading check
if (!window.YT) {
  console.error('YouTube API failed to load');
}
```

### Styles Not Applying

**Problem**: CSS not loaded or conflicting styles  
**Solution**: Ensure CSS file is loaded and check for conflicts

```html
<!-- Check network tab to ensure CSS loaded -->
<link rel="stylesheet" href="heydividend-player.css">
```

### Multiple Players on Same Page

**Problem**: Players interfere with each other  
**Solution**: Use unique container IDs

```javascript
// Good: Unique IDs
new HeyDividendPlayer('player-1', video1);
new HeyDividendPlayer('player-2', video2);

// Bad: Same ID
new HeyDividendPlayer('player', video1);
new HeyDividendPlayer('player', video2);  // ❌ Overwrites first
```

---

## ⚡ Performance Tips

### 1. Lazy Loading

Only initialize players when they're visible:

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const playerId = entry.target.id;
      const videoData = JSON.parse(entry.target.dataset.video);
      new HeyDividendPlayer(playerId, videoData);
      observer.unobserve(entry.target);
    }
  });
});

document.querySelectorAll('.lazy-video').forEach(el => observer.observe(el));
```

### 2. Destroy Players When Not Needed

```javascript
// Clean up when navigating away
window.addEventListener('beforeunload', () => {
  if (player) {
    player.destroy();
  }
});
```

### 3. Limit Concurrent Players

Only show one video at a time or limit to 2-3 max on a page.

---

## 📊 Browser Support

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | 90+ | ✅ Full support |
| Firefox | 88+ | ✅ Full support |
| Safari | 14+ | ✅ Full support |
| Edge | 90+ | ✅ Full support |
| Mobile Safari | iOS 14+ | ✅ Full support |
| Chrome Mobile | 90+ | ✅ Full support |

---

## 🔒 Security

- ✅ All HTML is escaped to prevent XSS
- ✅ External links use `rel="noopener noreferrer"`
- ✅ YouTube embeds use secure HTTPS
- ✅ No eval() or inline scripts

---

## 📝 Complete Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Harvey Chat with Videos</title>
  <link rel="stylesheet" href="heydividend-player.css">
  <style>
    .chat-container { max-width: 800px; margin: 0 auto; padding: 20px; }
    .message { margin-bottom: 20px; }
  </style>
</head>
<body>
  <div class="chat-container">
    <div class="message">
      <p id="response-text">Loading...</p>
      <div id="videos"></div>
    </div>
  </div>

  <script src="heydividend-player.js"></script>
  <script>
    // Fetch from Harvey API
    fetch('/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'dividend stocks' })
    })
    .then(r => r.json())
    .then(data => {
      // Show response
      document.getElementById('response-text').textContent = data.enhanced_response;

      // Render videos
      if (data.video_metadata) {
        data.video_metadata.forEach((video, i) => {
          const div = document.createElement('div');
          div.id = `player-${i}`;
          document.getElementById('videos').appendChild(div);

          new HeyDividendPlayer(`player-${i}`, video, {
            variant: 'expanded',
            autoplay: false
          });
        });
      }
    });
  </script>
</body>
</html>
```

---

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review `demo.html` for working examples
3. Check browser console for errors
4. Contact Harvey development team

---

**Version:** 1.0.0  
**Last Updated:** November 18, 2025  
**License:** Part of Harvey AI project
