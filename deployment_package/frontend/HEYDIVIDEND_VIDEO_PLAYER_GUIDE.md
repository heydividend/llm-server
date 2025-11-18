# HeyDividend Video Player - Integration Guide

## Overview

Custom-branded video player system for Harvey AI's video answer service. Includes React/TypeScript components and vanilla JavaScript versions for multi-framework support. Integrates with Harvey's chat API to render @heydividedtv YouTube content with professional HeyDividend branding.

### Architecture

**Backend (VideoAnswerService):**
- Semantic search across 500+ dividend investing videos
- Returns clean `video_metadata` array (no HTML, pure JSON)
- Uses `video_suffix` approach for reliable streaming SSE delivery
- Supports `enable_videos` toggle (defaults to true)

**Frontend (Multi-Framework Support):**
- React/TypeScript components (HeyDividendPlayer, VideoQueue, VideoModal)
- Vanilla JavaScript class for non-React frameworks
- Parses structured metadata from Harvey API responses
- Handles both streaming SSE and non-streaming JSON formats

## Features

✅ **Custom HeyDividend Branding**
- Navy (#0B1E39) and aqua (#00d9ff) color scheme
- Custom logo and branded overlay
- Professional gradient design

✅ **Three Display Variants**
- **Inline**: Compact player for chat width (200px height)
- **Expanded**: Full-width 16:9 player
- **Modal**: Fullscreen overlay with backdrop

✅ **Advanced Controls**
- Play/Pause with keyboard shortcuts
- Custom volume slider
- Playback speed menu (0.5x to 2x)
- Progress bar with seek
- Fullscreen support
- "Watch on YouTube" CTA

✅ **Accessibility**
- Keyboard navigation
- ARIA labels
- Focus indicators
- Screen reader support

✅ **Responsive Design**
- Mobile-optimized controls
- Touch-friendly interface
- Adaptive layouts

---

## Installation

### 1. Install Dependencies

```bash
npm install react-youtube lucide-react
# or
yarn add react-youtube lucide-react
# or
pnpm add react-youtube lucide-react
```

### 2. Copy Component Files

Copy these files to your Next.js project:

```
frontend/
├── components/video/
│   ├── HeyDividendPlayer.tsx
│   ├── VideoQueue.tsx
│   ├── VideoModal.tsx
│   └── index.ts
├── styles/components/
│   ├── HeyDividendPlayer.module.css
│   ├── VideoQueue.module.css
│   └── VideoModal.module.css
└── types/
    └── video.ts
```

### 3. Update tsconfig.json

Add path aliases if not already configured:

```json
{
  "compilerOptions": {
    "paths": {
      "@/components/*": ["./components/*"],
      "@/styles/*": ["./styles/*"],
      "@/types/*": ["./types/*"]
    }
  }
}
```

---

## Usage

### Basic Usage (Inline Variant)

```tsx
import { HeyDividendPlayer } from '@/components/video';
import type { VideoMetadata } from '@/types/video';

export function ChatMessage({ videoMetadata }: { videoMetadata: VideoMetadata }) {
  return (
    <HeyDividendPlayer
      video={videoMetadata}
      variant="inline"
      autoplay={false}
    />
  );
}
```

### Expanded Player

```tsx
<HeyDividendPlayer
  video={videoMetadata}
  variant="expanded"
  autoplay={false}
  onVideoEnd={() => console.log('Video ended')}
  onVideoPlay={() => console.log('Video started')}
/>
```

### Modal Player with Queue

```tsx
'use client';

import { useState } from 'react';
import { VideoModal } from '@/components/video';
import type { VideoMetadata } from '@/types/video';

export function VideoPlayer({ videos }: { videos: VideoMetadata[] }) {
  const [showModal, setShowModal] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  return (
    <>
      <button onClick={() => setShowModal(true)}>
        Open Video Player
      </button>

      {showModal && (
        <VideoModal
          videos={videos}
          currentIndex={currentIndex}
          onClose={() => setShowModal(false)}
          onVideoChange={(index) => setCurrentIndex(index)}
        />
      )}
    </>
  );
}
```

---

## Integration with Harvey Backend

### API Response Formats

Harvey's VideoAnswerService returns structured video metadata through the chat API. The backend uses a `video_suffix` approach to reliably deliver video content in both streaming and non-streaming modes.

#### Non-Streaming Response

For non-streaming requests (`stream: false`), video metadata appears in the root-level `video_metadata` field:

```json
{
  "id": "req123",
  "object": "chat.completion",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Here's information about dividend stocks...\n\n### 🎥 Related Videos from @heydividedtv\n\n..."
    }
  }],
  "video_metadata": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "Understanding Dividend Investing",
      "description": "Learn the basics of dividend investing and passive income strategies.",
      "duration": "12:34",
      "thumbnail_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
      "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "embed_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
      "channel_name": "@heydividedtv",
      "published_at": "2024-01-15",
      "cta_copy": "Watch on YouTube"
    }
  ]
}
```

#### Streaming Response (SSE)

For streaming requests (`stream: true`), Harvey emits video metadata as a **separate SSE event**:

```
data: {"id":"req123","object":"chat.completion.chunk","choices":[{"delta":{"content":"Here's information..."}}]}

data: {"id":"req123","object":"chat.completion.chunk","choices":[{"delta":{"content":"\n\n### 🎥 Related Videos from @heydividedtv\n\n..."}}]}

data: {"id":"req123","object":"chat.completion.chunk","video_metadata":[{...}]}

data: [DONE]
```

**Key Points:**
- Video markdown text streams as regular content chunks
- Structured metadata emits as a separate event with `video_metadata` field
- Metadata event **always** appears when videos are found
- Parse SSE events to extract both text and metadata

**SSE Parsing Example:**
```typescript
const processSSEEvent = (data: string) => {
  if (data === '[DONE]') return;
  
  const parsed = JSON.parse(data);
  
  // Handle content chunks
  if (parsed.choices?.[0]?.delta?.content) {
    appendMessageText(parsed.choices[0].delta.content);
  }
  
  // Handle video metadata event
  if (parsed.video_metadata) {
    setVideoMetadata(parsed.video_metadata);
  }
};
```

### Controlling Video Recommendations

Use the `enable_videos` API parameter to control whether videos are included:

```typescript
// Enable videos (default)
fetch('/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    messages: [{role: 'user', content: 'Tell me about dividends'}],
    enable_videos: true  // Videos will be included
  })
});

// Disable videos
fetch('/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    messages: [{role: 'user', content: 'Tell me about dividends'}],
    enable_videos: false  // No video_metadata in response
  })
});
```

### Frontend Integration

In your chat message renderer:

```tsx
import { HeyDividendPlayer } from '@/components/video';

interface ChatMessageProps {
  message: {
    text: string;
    video_metadata?: VideoMetadata[];
  };
}

export function ChatMessage({ message }: ChatMessageProps) {
  return (
    <div className="chat-message">
      {/* Markdown message content */}
      <div className="message-text">
        {message.text}
      </div>

      {/* Render video players if available */}
      {message.video_metadata && message.video_metadata.length > 0 && (
        <div className="video-section">
          {message.video_metadata.map((video, index) => (
            <HeyDividendPlayer
              key={video.video_id}
              video={video}
              variant="expanded"
              autoplay={false}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Advanced Usage

### With Video Queue

```tsx
'use client';

import { useState } from 'react';
import { HeyDividendPlayer, VideoQueue } from '@/components/video';

export function VideoWithQueue({ videos }: { videos: VideoMetadata[] }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  return (
    <div>
      <HeyDividendPlayer
        video={videos[currentIndex]}
        variant="expanded"
        onVideoEnd={() => {
          if (currentIndex < videos.length - 1) {
            setCurrentIndex(currentIndex + 1);
          }
        }}
      />

      <VideoQueue
        videos={videos}
        currentIndex={currentIndex}
        onVideoSelect={(index) => setCurrentIndex(index)}
      />
    </div>
  );
}
```

### Custom Event Handlers

```tsx
<HeyDividendPlayer
  video={videoMetadata}
  variant="expanded"
  onVideoPlay={() => {
    // Track analytics
    analytics.track('video_play', {
      video_id: videoMetadata.video_id,
      title: videoMetadata.title,
    });
  }}
  onVideoEnd={() => {
    // Show next video or recommendations
    showRecommendations();
  }}
/>
```

---

## Styling Customization

### Override Default Colors

Create a custom CSS module to override brand colors:

```css
/* custom-player.module.css */
.container {
  --brand-navy: #0B1E39;
  --brand-aqua: #00d9ff;
  --brand-aqua-dark: #00a8cc;
}

/* Change to your custom colors */
.container {
  --brand-navy: #1a1a2e;
  --brand-aqua: #16c172;
  --brand-aqua-dark: #12a05c;
}
```

### Customize Player Size

```tsx
<HeyDividendPlayer
  video={videoMetadata}
  variant="expanded"
  className="custom-player-size"
/>
```

```css
/* your-styles.module.css */
.customPlayerSize {
  max-width: 800px;
  margin: 0 auto;
}
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `M` | Mute/Unmute |
| `F` | Fullscreen |
| `←` | Seek backward |
| `→` | Seek forward |
| `Escape` | Exit fullscreen/modal |

---

## TypeScript Interface Reference

```typescript
interface VideoMetadata {
  video_id: string;
  title: string;
  description: string;
  duration: string;              // e.g., "12:34"
  thumbnail_url: string;          // YouTube thumbnail
  video_url: string;              // Watch URL
  embed_url: string;              // Embed URL
  channel_name: string;           // "@heydividedtv"
  published_at?: string;          // ISO date string
  cta_copy?: string;              // "Watch on YouTube"
}

interface VideoPlayerProps {
  video: VideoMetadata;
  variant?: 'inline' | 'expanded' | 'modal';
  autoplay?: boolean;
  onVideoEnd?: () => void;
  onVideoPlay?: () => void;
  className?: string;
}
```

---

## Best Practices

### 1. **Always Use Structured Metadata**
- Never pass raw YouTube URLs as strings
- Always use the `VideoMetadata` interface
- Backend provides normalized data

### 2. **Choose the Right Variant**
- **Inline**: For chat messages (compact, unobtrusive)
- **Expanded**: For dedicated video sections (full-width, immersive)
- **Modal**: For focused viewing (fullscreen, distraction-free)

### 3. **Handle Analytics**
```tsx
<HeyDividendPlayer
  video={video}
  onVideoPlay={() => trackEvent('video_play', video.video_id)}
  onVideoEnd={() => trackEvent('video_complete', video.video_id)}
/>
```

### 4. **Lazy Loading**
Only render videos when they're visible:

```tsx
import { Suspense, lazy } from 'react';

const HeyDividendPlayer = lazy(() => import('@/components/video/HeyDividendPlayer'));

export function ChatMessage({ video }) {
  return (
    <Suspense fallback={<div>Loading player...</div>}>
      <HeyDividendPlayer video={video} variant="inline" />
    </Suspense>
  );
}
```

---

## Troubleshooting

### Player Not Loading

**Issue**: YouTube player doesn't load  
**Solution**: Ensure `react-youtube` is installed and video_id is valid

```bash
npm install react-youtube
```

### Styling Issues

**Issue**: Styles not applying  
**Solution**: Check CSS module imports and ensure Next.js CSS modules are configured

```json
// next.config.js
module.exports = {
  // ... other config
};
```

### TypeScript Errors

**Issue**: Type errors on VideoMetadata  
**Solution**: Ensure types are properly exported and imported

```tsx
import type { VideoMetadata } from '@/types/video';
```

---

## Performance Optimization

### 1. **Lazy Load YouTube IFrame API**

The component automatically lazy-loads the YouTube API only when needed.

### 2. **Thumbnail Preview**

Show thumbnail before player loads:

```tsx
{!isPlayerReady ? (
  <img src={video.thumbnail_url} alt={video.title} />
) : (
  <HeyDividendPlayer video={video} />
)}
```

### 3. **Limit Concurrent Players**

Avoid rendering multiple players simultaneously:

```tsx
// Only render one player at a time in modal
<VideoModal videos={videos} currentIndex={currentIndex} />
```

---

## Examples

### Example 1: Chat Integration

```tsx
// features/chat/components/MessageContent.tsx
import { HeyDividendPlayer } from '@/components/video';

export function MessageContent({ message }) {
  return (
    <div>
      <div dangerouslySetInnerHTML={{ __html: sanitize(message.html) }} />

      {message.video_metadata?.map(video => (
        <HeyDividendPlayer
          key={video.video_id}
          video={video}
          variant="inline"
        />
      ))}
    </div>
  );
}
```

### Example 2: Video Library Page

```tsx
// app/videos/page.tsx
'use client';

import { useState } from 'react';
import { VideoModal, VideoQueue } from '@/components/video';

export default function VideosPage({ videos }) {
  const [showModal, setShowModal] = useState(false);
  const [currentVideo, setCurrentVideo] = useState(0);

  return (
    <div>
      <h1>HeyDividend Video Library</h1>

      <VideoQueue
        videos={videos}
        currentIndex={currentVideo}
        onVideoSelect={(index) => {
          setCurrentVideo(index);
          setShowModal(true);
        }}
      />

      {showModal && (
        <VideoModal
          videos={videos}
          currentIndex={currentVideo}
          onClose={() => setShowModal(false)}
          onVideoChange={setCurrentVideo}
        />
      )}
    </div>
  );
}
```

---

## API Documentation Updates

The Harvey backend `/v1/chat` endpoint now includes `video_metadata` in responses when videos are recommended.

See `docs/API_NEW_FEATURES.md` for complete API documentation.

---

## Support

For issues or questions:
1. Check this documentation
2. Review TypeScript interfaces in `types/video.ts`
3. Inspect CSS modules for styling issues
4. Contact Harvey development team

---

**Version**: 1.0.0  
**Last Updated**: November 17, 2025  
**Maintained by**: Harvey AI Development Team
