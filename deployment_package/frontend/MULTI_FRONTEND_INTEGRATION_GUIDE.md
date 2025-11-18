# Harvey API + HeyDividend Video Player - Multi-Frontend Integration Guide

## 🌐 Overview

This guide explains how **any frontend** (React, Vue, Angular, PHP, plain HTML, etc.) can integrate with Harvey's AI chat API and render HeyDividend-branded video players.

---

## 🎯 Quick Summary

### What Harvey Provides:
1. **Chat API**: Returns AI responses with structured JSON data
2. **Video Metadata**: Clean JSON objects for each recommended video
3. **Video Player Components**: React (TypeScript) + Vanilla JS versions

### What Your Frontend Does:
1. **Call Harvey API**: Send chat messages, receive responses
2. **Parse Video Metadata**: Extract `video_metadata` from API response
3. **Render Video Players**: Use provided components OR build your own

---

## 📡 Harvey Chat API

### Endpoint
```
POST /v1/chat
```

### Request Body

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Tell me about dividend stocks"
    }
  ],
  "stream": true,
  "enable_videos": true,
  "session_id": "optional-session-123",
  "user_id": "user-456"
}
```

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `messages` | `array` | **Required** | Array of message objects with `role` and `content` |
| `stream` | `boolean` | `true` | Enable Server-Sent Events (SSE) streaming |
| `enable_videos` | `boolean` | `true` | **NEW**: Include video recommendations in response |
| `session_id` | `string` | `null` | Optional session identifier for conversation tracking |
| `user_id` | `string` | `null` | Optional user identifier |
| `debug` | `boolean` | `false` | Enable debug logging |

### Response Format

#### Streaming Response (SSE)

Harvey's streaming API uses Server-Sent Events (SSE) to deliver real-time responses. Video metadata is emitted as a **separate SSE event** alongside the markdown text:

```
data: {"id":"req123","object":"chat.completion.chunk","choices":[{"delta":{"content":"Here's information about dividend stocks..."}}]}

data: {"id":"req123","object":"chat.completion.chunk","choices":[{"delta":{"content":"\n\n### 🎥 Related Videos from @heydividedtv\n\n..."}}]}

data: {"id":"req123","object":"chat.completion.chunk","video_metadata":[{"video_id":"abc123","title":"Understanding Dividend Investing",...}]}

data: [DONE]
```

**Key Points:**
- Video markdown text streams as regular `content` chunks
- Structured `video_metadata` emits as a separate event (look for `"video_metadata"` field)
- Metadata event **always** appears when videos are recommended (regardless of markdown)
- Extract metadata from SSE events that contain `video_metadata` field

**SSE Parsing Example:**
```javascript
const eventSource = new EventSource('/v1/chat');
eventSource.onmessage = (event) => {
  if (event.data === '[DONE]') return;
  
  const data = JSON.parse(event.data);
  
  // Handle content chunks
  if (data.choices?.[0]?.delta?.content) {
    appendToMessage(data.choices[0].delta.content);
  }
  
  // Handle video metadata event
  if (data.video_metadata) {
    renderVideoPlayers(data.video_metadata);
  }
};
```

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
      "video_id": "abc123",
      "title": "Understanding Dividend Investing",
      "description": "Learn the basics of dividend investing and passive income strategies.",
      "duration": "12:34",
      "thumbnail_url": "https://img.youtube.com/vi/abc123/maxresdefault.jpg",
      "video_url": "https://www.youtube.com/watch?v=abc123",
      "embed_url": "https://www.youtube.com/embed/abc123",
      "channel_name": "@heydividedtv",
      "published_at": "2024-01-15",
      "cta_copy": "Watch on YouTube"
    }
  ],
  "metadata": {
    "detected_tickers": ["AAPL", "MSFT"],
    "original_query": "Tell me about dividend stocks",
    "session_id": "session-123"
  }
}
```

**Video Metadata Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `video_id` | `string` | YouTube video ID (e.g., "abc123") |
| `title` | `string` | Video title |
| `description` | `string` | Video description/summary |
| `duration` | `string` | Formatted duration (e.g., "12:34") |
| `thumbnail_url` | `string` | High-resolution thumbnail URL |
| `video_url` | `string` | Full YouTube watch URL |
| `embed_url` | `string` | YouTube embed URL for iframes |
| `channel_name` | `string` | Channel name ("@heydividedtv") |
| `published_at` | `string` | Publication date (ISO format) |
| `cta_copy` | `string` | Call-to-action text ("Watch on YouTube") |

---

## 🎨 Video Player Integration Options

You have **3 options** for displaying videos:

### Option 1: React/Next.js Component (Recommended for React apps)
Use the fully-featured TypeScript components with HeyDividend branding.

**Location**: `frontend/components/video/`

**Installation**:
```bash
npm install react-youtube lucide-react
# Copy components to your project
cp -r frontend/components/video your-app/components/
cp -r frontend/types/video.ts your-app/types/
cp -r frontend/styles/components/*.module.css your-app/styles/components/
```

**Usage**:
```tsx
import { HeyDividendPlayer } from '@/components/video';

{message.video_metadata?.map(video => (
  <HeyDividendPlayer
    key={video.video_id}
    video={video}
    variant="expanded"
    autoplay={false}
  />
))}
```

**Documentation**: See `frontend/HEYDIVIDEND_VIDEO_PLAYER_GUIDE.md`

---

### Option 2: Vanilla JavaScript (Works with ANY framework)
Pure JavaScript implementation with no dependencies.

**Location**: `frontend/vanilla-js/`

**Installation**:
```html
<link rel="stylesheet" href="heydividend-player.css">
<script src="heydividend-player.js"></script>
```

**Usage**:
```javascript
const player = new HeyDividendPlayer('container-id', videoMetadata, {
  variant: 'expanded',
  autoplay: false
});
```

**Documentation**: See `frontend/vanilla-js/VANILLA_JS_INTEGRATION.md`

---

### Option 3: Build Your Own Player
Use the `video_metadata` JSON to create a custom player.

**Minimum Implementation**:
```html
<div class="video-container">
  <iframe 
    src="https://www.youtube.com/embed/VIDEO_ID"
    width="100%" 
    height="400"
    frameborder="0"
    allowfullscreen
  ></iframe>
  <h3>VIDEO_TITLE</h3>
  <a href="VIDEO_URL" target="_blank">Watch on YouTube</a>
</div>
```

---

## 🎛️ Controlling Video Recommendations

### Enable/Disable Videos

Use the `enable_videos` parameter to control whether Harvey includes video recommendations:

```json
{
  "messages": [...],
  "enable_videos": true  // true (default) or false
}
```

**When to disable videos:**
- API-only integrations without UI
- Text-only chat interfaces
- Performance-sensitive environments
- User preference toggles

**Example:**
```javascript
// Enable videos (default)
fetch('/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    messages: [{role: 'user', content: 'Tell me about dividend stocks'}],
    enable_videos: true
  })
});

// Disable videos
fetch('/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    messages: [{role: 'user', content: 'Tell me about dividend stocks'}],
    enable_videos: false  // No video_metadata in response
  })
});
```

**Response Comparison:**

With `enable_videos: true`:
```json
{
  "choices": [{...}],
  "video_metadata": [{...}]  // Videos included
}
```

With `enable_videos: false`:
```json
{
  "choices": [{...}]
  // No video_metadata field
}
```

---

## 🔧 Framework-Specific Examples

### React / Next.js

```tsx
'use client';

import { useState } from 'react';
import { HeyDividendPlayer } from '@/components/video';

export function ChatInterface() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState(null);

  const sendMessage = async () => {
    const res = await fetch('/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: message }],
        enable_videos: true
      })
    });

    const data = await res.json();
    setResponse(data);
  };

  return (
    <div>
      <input 
        value={message} 
        onChange={(e) => setMessage(e.target.value)}
      />
      <button onClick={sendMessage}>Send</button>

      {response && (
        <div>
          <div>{response.choices[0].message.content}</div>
          
          {response.video_metadata?.map(video => (
            <HeyDividendPlayer
              key={video.video_id}
              video={video}
              variant="expanded"
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

---

### Vue.js

```vue
<template>
  <div class="chat-interface">
    <input v-model="message" @keyup.enter="sendMessage" />
    <button @click="sendMessage">Send</button>

    <div v-if="response">
      <div v-html="response.choices[0].message.content"></div>
      
      <div
        v-for="(video, index) in response.video_metadata"
        :key="video.video_id"
        :id="`player-${index}`"
      ></div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      message: '',
      response: null
    };
  },
  methods: {
    async sendMessage() {
      const res = await fetch('/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [{ role: 'user', content: this.message }],
          enable_videos: true
        })
      });

      this.response = await res.json();

      // Render video players
      this.$nextTick(() => {
        this.response.video_metadata?.forEach((video, index) => {
          new HeyDividendPlayer(`player-${index}`, video, {
            variant: 'expanded'
          });
        });
      });
    }
  }
};
</script>
```

---

### Angular

```typescript
// chat.component.ts
import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

declare const HeyDividendPlayer: any;

@Component({
  selector: 'app-chat',
  template: `
    <div class="chat-interface">
      <input [(ngModel)]="message" (keyup.enter)="sendMessage()" />
      <button (click)="sendMessage()">Send</button>

      <div *ngIf="response">
        <div [innerHTML]="response.choices[0].message.content"></div>
        
        <div
          *ngFor="let video of response.video_metadata; let i = index"
          [id]="'player-' + i"
        ></div>
      </div>
    </div>
  `
})
export class ChatComponent {
  message = '';
  response: any = null;

  constructor(private http: HttpClient) {}

  sendMessage() {
    this.http.post('/v1/chat', {
      messages: [{ role: 'user', content: this.message }],
      enable_videos: true
    }).subscribe((data: any) => {
      this.response = data;

      // Render video players after DOM updates
      setTimeout(() => {
        this.response.video_metadata?.forEach((video: any, index: number) => {
          new HeyDividendPlayer(`player-${index}`, video, {
            variant: 'expanded'
          });
        });
      }, 0);
    });
  }
}
```

---

### PHP (Laravel / Pure PHP)

```php
<?php
// chat-controller.php

function getChatResponse($message) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, 'https://harvey-api.com/v1/chat');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'X-API-Key: your-api-key'
    ]);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
        'messages' => [
            ['role' => 'user', 'content' => $message]
        ],
        'enable_videos' => true,
        'stream' => false
    ]));

    $response = curl_exec($ch);
    curl_close($ch);

    return json_decode($response, true);
}

// View: chat.blade.php (Laravel) or chat.php
?>
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/heydividend-player.css">
</head>
<body>
    <div class="chat-interface">
        <?php
        $response = getChatResponse($_POST['message'] ?? '');
        if ($response): ?>
            <div class="message">
                <?php echo nl2br(htmlspecialchars($response['choices'][0]['message']['content'])); ?>
            </div>

            <?php if (!empty($response['video_metadata'])): ?>
                <?php foreach ($response['video_metadata'] as $index => $video): ?>
                    <div id="player-<?php echo $index; ?>"></div>
                    
                    <script>
                        const video<?php echo $index; ?> = <?php echo json_encode($video); ?>;
                        new HeyDividendPlayer('player-<?php echo $index; ?>', video<?php echo $index; ?>, {
                            variant: 'expanded',
                            autoplay: false
                        });
                    </script>
                <?php endforeach; ?>
            <?php endif; ?>
        <?php endif; ?>
    </div>

    <script src="/heydividend-player.js"></script>
</body>
</html>
```

---

### WordPress Plugin

```php
<?php
/**
 * Plugin Name: Harvey Chat Widget
 * Description: Integrates Harvey AI chat with HeyDividend videos
 */

// Enqueue scripts
function harvey_enqueue_scripts() {
    wp_enqueue_style('heydividend-player', plugins_url('assets/heydividend-player.css', __FILE__));
    wp_enqueue_script('heydividend-player', plugins_url('assets/heydividend-player.js', __FILE__), [], '1.0', true);
}
add_action('wp_enqueue_scripts', 'harvey_enqueue_scripts');

// Shortcode: [harvey_chat]
function harvey_chat_shortcode() {
    ob_start();
    ?>
    <div class="harvey-chat-widget">
        <form id="harvey-form">
            <input type="text" id="harvey-input" placeholder="Ask Harvey..." />
            <button type="submit">Send</button>
        </form>
        <div id="harvey-response"></div>
        <div id="harvey-videos"></div>
    </div>

    <script>
    document.getElementById('harvey-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = document.getElementById('harvey-input').value;

        const res = await fetch('https://harvey-api.com/v1/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: [{ role: 'user', content: message }],
                enable_videos: true,
                stream: false
            })
        });

        const data = await res.json();
        
        // Display response
        document.getElementById('harvey-response').innerHTML = data.choices[0].message.content;

        // Render videos
        const videosContainer = document.getElementById('harvey-videos');
        videosContainer.innerHTML = '';

        data.video_metadata?.forEach((video, index) => {
            const playerDiv = document.createElement('div');
            playerDiv.id = `video-player-${index}`;
            videosContainer.appendChild(playerDiv);

            new HeyDividendPlayer(`video-player-${index}`, video, {
                variant: 'inline'
            });
        });
    });
    </script>
    <?php
    return ob_get_clean();
}
add_shortcode('harvey_chat', 'harvey_chat_shortcode');
```

---

## 🎛️ Controlling Video Recommendations

### Enable/Disable Videos

You can control whether Harvey includes video recommendations using the `enable_videos` parameter:

```javascript
// WITH videos (default)
fetch('/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    messages: [...],
    enable_videos: true  // Videos included
  })
});

// WITHOUT videos
fetch('/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    messages: [...],
    enable_videos: false  // Videos excluded
  })
});
```

### Use Cases for Disabling Videos:

- **Mobile apps** with limited bandwidth
- **Voice-only** interfaces
- **Text-only** chat modes
- **Performance optimization** for low-end devices
- **Custom video handling** (you want raw metadata without formatted markdown)

---

## 🔐 Authentication

Harvey API uses API key authentication:

```javascript
fetch('/v1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-harvey-api-key'
  },
  body: JSON.stringify({...})
});
```

Contact Harvey team to obtain API keys.

---

## 📊 Video Metadata Schema

Complete TypeScript/JSON schema for video metadata:

```typescript
interface VideoMetadata {
  video_id: string;           // YouTube video ID (e.g., "abc123")
  title: string;              // Video title
  description: string;        // Video description
  duration: string;           // Duration in MM:SS format (e.g., "12:34")
  thumbnail_url: string;      // YouTube thumbnail URL
  video_url: string;          // Full YouTube watch URL
  embed_url: string;          // YouTube embed URL
  channel_name: string;       // "@heydividedtv"
  published_at?: string;      // ISO date string (optional)
  cta_copy?: string;          // CTA button text (optional)
}
```

---

## 🚀 Best Practices

### 1. **Always Check for Video Metadata**
```javascript
if (response.video_metadata && response.video_metadata.length > 0) {
  // Render videos
}
```

### 2. **Handle Streaming Responses Properly**
```javascript
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  // Process SSE chunk
}
```

### 3. **Lazy Load Video Players**
Don't render all videos immediately - use intersection observer:

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // Initialize player when visible
      const video = JSON.parse(entry.target.dataset.video);
      new HeyDividendPlayer(entry.target.id, video);
      observer.unobserve(entry.target);
    }
  });
});
```

### 4. **Destroy Players When Unmounting**
```javascript
// React
useEffect(() => {
  const player = new HeyDividendPlayer(...);
  return () => player.destroy();
}, []);

// Vue
beforeDestroy() {
  this.player.destroy();
}

// Angular
ngOnDestroy() {
  this.player.destroy();
}
```

---

## 🎨 Customization

### Brand Colors
Override HeyDividend colors in your CSS:

```css
.heydividend-player {
  --brand-navy: #1a1a2e;      /* Your navy */
  --brand-aqua: #16c172;      /* Your aqua */
}
```

### Player Sizes
```javascript
// Inline (compact)
new HeyDividendPlayer('container', video, { variant: 'inline' });

// Expanded (16:9)
new HeyDividendPlayer('container', video, { variant: 'expanded' });

// Modal (fullscreen)
new HeyDividendPlayer('container', video, { variant: 'modal' });
```

---

## 📱 Mobile Considerations

- Volume slider hidden on mobile (native controls used)
- Touch-friendly button sizes
- Always-visible controls on touchscreens
- Responsive text and layout

---

## 🐛 Troubleshooting

### Videos Not Showing

**Check 1**: Is `enable_videos` true?
```javascript
{ enable_videos: true }
```

**Check 2**: Does response contain `video_metadata`?
```javascript
console.log(response.video_metadata);
```

**Check 3**: Are scripts loaded?
```html
<script src="heydividend-player.js"></script>
```

### Player Not Rendering

**Issue**: Container doesn't exist  
**Solution**: Ensure DOM element exists before initializing

```javascript
// Good
document.addEventListener('DOMContentLoaded', () => {
  new HeyDividendPlayer('container', video);
});

// Bad
new HeyDividendPlayer('container', video);  // DOM might not be ready
```

### CORS Errors

**Issue**: Cross-origin request blocked  
**Solution**: Harvey API must allow your domain

Contact Harvey team to whitelist your domain.

---

## 📞 Support

For integration assistance:
1. Review this guide thoroughly
2. Check framework-specific examples
3. Review `frontend/HEYDIVIDEND_VIDEO_PLAYER_GUIDE.md` (React)
4. Review `frontend/vanilla-js/VANILLA_JS_INTEGRATION.md` (Vanilla JS)
5. Contact Harvey development team

---

## 🎯 Summary Checklist

- [ ] Obtained Harvey API key
- [ ] Chosen video player option (React, Vanilla JS, or custom)
- [ ] Installed dependencies (if using provided components)
- [ ] Implemented chat API integration
- [ ] Tested with `enable_videos: true`
- [ ] Tested with `enable_videos: false`
- [ ] Rendered video players correctly
- [ ] Tested on mobile devices
- [ ] Handled errors gracefully

---

**Version**: 1.0.0  
**Last Updated**: November 18, 2025  
**Maintained by**: Harvey AI Development Team

---

## 📚 Related Documentation

- [HeyDividend Video Player Guide (React)](./HEYDIVIDEND_VIDEO_PLAYER_GUIDE.md)
- [Vanilla JS Integration Guide](./vanilla-js/VANILLA_JS_INTEGRATION.md)
- [Harvey API Documentation](../API_DOCUMENTATION.md)
- [Video Player Demo](./vanilla-js/demo.html)
