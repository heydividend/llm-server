# Harvey Video Answer Service - System Summary

## Overview

Complete video recommendation system that enhances Harvey AI responses with relevant @heydividedtv YouTube content.

---

## 🏗️ System Architecture

### Backend (Python/FastAPI)

**VideoAnswerService** (`app/services/video_answer_service.py`)
- Semantic search across 500+ dividend investing videos
- Returns structured `video_metadata` array (pure JSON, no HTML)
- Uses `video_suffix` field for reliable streaming delivery
- Integrates with Harvey's chat completions endpoint

**Key Features:**
- ✅ Semantic video search with relevance scoring
- ✅ Ticker-aware video matching
- ✅ Structured metadata extraction
- ✅ Enable/disable toggle via `enable_videos` parameter (defaults to true)

**Response Format:**
```python
{
    "enhanced_response": str,      # Original response + video markdown
    "video_suffix": str,           # Exact video section for streaming
    "video_metadata": [...],       # Structured JSON metadata
    "videos_added": int
}
```

---

### API Integration (`app/controllers/ai_controller.py`)

#### Non-Streaming Response

```json
{
  "choices": [{
    "message": {
      "content": "AI response text + video markdown"
    }
  }],
  "video_metadata": [
    {
      "video_id": "abc123",
      "title": "Video Title",
      "duration": "12:34",
      "thumbnail_url": "https://...",
      "video_url": "https://youtube.com/watch?v=...",
      "embed_url": "https://youtube.com/embed/...",
      "channel_name": "@heydividedtv",
      "published_at": "2024-01-15",
      "cta_copy": "Watch on YouTube"
    }
  ]
}
```

#### Streaming Response (SSE)

```
data: {"choices":[{"delta":{"content":"AI response text..."}}]}
data: {"choices":[{"delta":{"content":"### 🎥 Related Videos..."}}]}
data: {"video_metadata":[{...}]}  ← Separate event with structured data
data: [DONE]
```

**Key Implementation Details:**
- `video_suffix` field ensures exact video section extraction (no string manipulation errors)
- `video_metadata` always emitted when videos are found (regardless of markdown)
- Works in both streaming and non-streaming modes
- Frontend can parse SSE events to extract structured metadata

---

### Frontend Components

#### React/TypeScript Components

**Location:** `frontend/components/video/`

**Components:**
- `HeyDividendPlayer.tsx` - Main video player with 3 variants
- `VideoQueue.tsx` - Video playlist component
- `VideoModal.tsx` - Fullscreen modal player

**Variants:**
1. **Inline** - Compact 200px player for chat width
2. **Expanded** - Full-width 16:9 player
3. **Modal** - Fullscreen overlay with backdrop

**Features:**
- Custom HeyDividend branding (Navy #0B1E39, aqua accents)
- YouTube IFrame API integration
- Custom controls (play/pause, volume, speed, seek)
- Keyboard shortcuts and accessibility
- Event callbacks (onVideoPlay, onVideoEnd)

**Installation:**
```bash
npm install react-youtube lucide-react
```

**Usage:**
```tsx
import { HeyDividendPlayer } from '@/components/video';

<HeyDividendPlayer
  video={videoMetadata}
  variant="expanded"
  autoplay={false}
/>
```

---

#### Vanilla JavaScript Version

**Location:** `frontend/vanilla-js/`

**Features:**
- Zero dependencies
- Works with any framework (Vue, Angular, PHP, WordPress, plain HTML)
- Same HeyDividend branding as React version
- YouTube IFrame API integration

**Installation:**
```html
<link rel="stylesheet" href="heydividend-player.css">
<script src="heydividend-player.js"></script>
```

**Usage:**
```javascript
const player = new HeyDividendPlayer('container-id', videoMetadata, {
  variant: 'expanded',
  autoplay: false
});
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `replit.md` | Main project documentation with video service overview |
| `MULTI_FRONTEND_INTEGRATION_GUIDE.md` | Complete API + player integration for all frameworks |
| `HEYDIVIDEND_VIDEO_PLAYER_GUIDE.md` | React component usage and API integration |
| `vanilla-js/VANILLA_JS_INTEGRATION.md` | Vanilla JS player integration guide |
| `VIDEO_SYSTEM_SUMMARY.md` | This file - quick system overview |

---

## 🎯 Quick Start Guide

### 1. Backend Setup (Already Configured)

The VideoAnswerService is integrated into Harvey's chat API:

```python
# app/controllers/ai_controller.py
from app.services.video_answer_service import VideoAnswerService

video_service = VideoAnswerService()
result = video_service.enhance_response_with_videos(query, response)
```

### 2. Frontend Integration

**Option A: React/Next.js**
```tsx
import { HeyDividendPlayer } from '@/components/video';

{message.video_metadata?.map(video => (
  <HeyDividendPlayer key={video.video_id} video={video} variant="expanded" />
))}
```

**Option B: Vanilla JavaScript**
```javascript
const player = new HeyDividendPlayer('container', videoMetadata);
```

**Option C: Custom Implementation**
```javascript
// Parse video_metadata from API response
const { video_metadata } = await response.json();

// Render your own player
video_metadata.forEach(video => {
  renderCustomPlayer(video.embed_url, video.title);
});
```

### 3. API Usage

**Enable Videos (default):**
```json
{
  "messages": [{...}],
  "enable_videos": true
}
```

**Disable Videos:**
```json
{
  "messages": [{...}],
  "enable_videos": false
}
```

---

## 🔑 Key Technical Details

### Why `video_suffix` Approach?

**Problem:** String manipulation in streaming can fail when:
- AI response contains repeated text
- VideoService normalizes whitespace
- Content has inline annotations

**Solution:** Backend returns exact video section:
```python
{
    "enhanced_response": original + video_section,
    "video_suffix": video_section  # Exact appended section
}
```

**Benefits:**
- ✅ No string slicing in controller
- ✅ Works regardless of text normalization
- ✅ Reliable streaming SSE delivery
- ✅ No content duplication or truncation

### Streaming SSE Architecture

**Markdown Text:**
```
data: {"choices":[{"delta":{"content":"### 🎥 Related Videos..."}}]}
```

**Structured Metadata (Separate Event):**
```
data: {"video_metadata":[{video_id, title, ...}]}
```

**Frontend Parsing:**
```typescript
if (event.choices?.[0]?.delta?.content) {
  // Handle markdown text
}
if (event.video_metadata) {
  // Handle structured metadata
}
```

---

## 🎨 HeyDividend Brand Guidelines

**Colors:**
- Primary Navy: `#0B1E39`
- Aqua Accent: `#00d9ff`
- Background Gradient: Navy to darker navy
- Text: White on dark backgrounds

**Typography:**
- Channel name: "@heydividedtv"
- CTA: "Watch on YouTube"

**Logo/Branding:**
- Custom branded overlay on player
- HeyDividend logo in controls
- Professional financial-grade styling

---

## 📊 Video Metadata Schema

```typescript
interface VideoMetadata {
  video_id: string;           // YouTube video ID
  title: string;              // Video title
  description: string;        // Video description
  duration: string;           // Formatted (e.g., "12:34")
  thumbnail_url: string;      // High-res thumbnail
  video_url: string;          // Full YouTube URL
  embed_url: string;          // Embed URL for iframes
  channel_name: string;       // "@heydividedtv"
  published_at: string;       // ISO date
  cta_copy: string;          // "Watch on YouTube"
}
```

---

## ✅ Production Readiness Checklist

- [x] Backend VideoAnswerService implemented
- [x] Structured metadata delivery (video_metadata array)
- [x] Reliable streaming SSE with video_suffix
- [x] Enable/disable toggle (enable_videos parameter)
- [x] React/TypeScript components
- [x] Vanilla JavaScript version
- [x] Multi-framework integration guides
- [x] API documentation complete
- [x] Architect-approved implementation
- [x] Server running without errors

---

## 🚀 Deployment

**Development (Replit):**
- Server running on `python main.py`
- API: `http://localhost:5000/v1/chat`

**Production (Azure VM):**
- Path: `/home/azureuser/harvey`
- Deploy updated files to Azure VM
- Restart Harvey service
- Nginx reverse proxy handles routing

**Deploy Command:**
```bash
# From local/Replit
scp -r app/ azureuser@20.81.210.213:/home/azureuser/harvey/
ssh azureuser@20.81.210.213 'sudo systemctl restart harvey'
```

---

## 📝 Notes

- Video recommendations use semantic search with relevance scoring (threshold: 2+)
- Max 3 videos per response (configurable)
- Videos only included if relevance score meets threshold
- Backend handles all video logic; frontend just renders metadata
- Works with both streaming and non-streaming API modes
- No breaking changes to existing chat API

---

**Last Updated:** November 18, 2025  
**Status:** Production Ready ✅
