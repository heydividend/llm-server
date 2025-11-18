# HeyDividend Video Player - Frontend Components

## 🎥 Custom-Branded YouTube Player for Harvey AI

A professional, fully-branded video player component for Harvey's Next.js frontend, featuring HeyDividend branding, custom controls, and seamless YouTube integration.

---

## ✨ Features

- **🎨 HeyDividend Branding**: Navy (#0B1E39) and aqua (#00d9ff) color scheme
- **📱 3 Display Variants**: Inline, Expanded, and Modal
- **🎮 Custom Controls**: Play/pause, volume, speed, progress bar, fullscreen
- **♿ Accessible**: Keyboard navigation, ARIA labels, screen reader support
- **📱 Responsive**: Mobile-optimized with touch-friendly controls
- **⚡ Performance**: Lazy loading, efficient rendering
- **🔌 Easy Integration**: Drop-in component for Harvey chat interface

---

## 📂 File Structure

```
frontend/
├── components/video/
│   ├── HeyDividendPlayer.tsx      # Main video player component
│   ├── VideoQueue.tsx              # Video queue/playlist component
│   ├── VideoModal.tsx              # Fullscreen modal player
│   └── index.ts                    # Component exports
├── styles/components/
│   ├── HeyDividendPlayer.module.css    # Player styles
│   ├── VideoQueue.module.css           # Queue styles
│   └── VideoModal.module.css           # Modal styles
├── types/
│   └── video.ts                    # TypeScript interfaces
├── package.json                     # Dependencies
├── README.md                        # This file
└── HEYDIVIDEND_VIDEO_PLAYER_GUIDE.md   # Complete integration guide
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install react-youtube lucide-react
```

### 2. Copy Files to Your Next.js Project

Copy the entire `frontend/` directory contents to your Next.js project:

```bash
cp -r frontend/components/video your-nextjs-project/components/
cp -r frontend/styles/components/* your-nextjs-project/styles/components/
cp -r frontend/types your-nextjs-project/
```

### 3. Use in Your Components

```tsx
import { HeyDividendPlayer } from '@/components/video';

export function ChatMessage({ videoMetadata }) {
  return (
    <HeyDividendPlayer
      video={videoMetadata}
      variant="expanded"
      autoplay={false}
    />
  );
}
```

---

## 📖 Complete Documentation

See **[HEYDIVIDEND_VIDEO_PLAYER_GUIDE.md](./HEYDIVIDEND_VIDEO_PLAYER_GUIDE.md)** for:
- Detailed installation instructions
- Complete API reference
- Integration examples
- Customization guide
- Troubleshooting
- Best practices

---

## 🎯 Component Variants

### Inline Player (Compact)
```tsx
<HeyDividendPlayer video={video} variant="inline" />
```
- Height: 200px
- Perfect for chat messages
- Compact, unobtrusive design

### Expanded Player (Full-Width)
```tsx
<HeyDividendPlayer video={video} variant="expanded" />
```
- 16:9 aspect ratio
- Full-width responsive
- Immersive viewing experience

### Modal Player (Fullscreen)
```tsx
<VideoModal 
  videos={videos} 
  currentIndex={0}
  onClose={() => setShowModal(false)}
  onVideoChange={(index) => setCurrentIndex(index)}
/>
```
- Fullscreen overlay
- Video queue support
- Distraction-free viewing

---

## 🔌 Backend Integration

Harvey's backend (`video_answer_service.py`) now returns structured video metadata:

```json
{
  "video_metadata": [
    {
      "video_id": "abc123",
      "title": "Dividend Investing 101",
      "description": "Learn the basics...",
      "duration": "12:34",
      "thumbnail_url": "https://...",
      "video_url": "https://youtube.com/watch?v=abc123",
      "embed_url": "https://youtube.com/embed/abc123",
      "channel_name": "@heydividedtv",
      "cta_copy": "Watch on YouTube"
    }
  ]
}
```

The frontend automatically renders these with the HeyDividendPlayer component.

---

## 🎨 Brand Colors

```css
--brand-navy: #0B1E39;        /* Primary background */
--brand-aqua: #00d9ff;        /* Accent color */
--brand-aqua-dark: #00a8cc;   /* Darker accent */
```

---

## 🛠️ Technology Stack

- **React 18**: Component library
- **Next.js 14**: Framework
- **TypeScript**: Type safety
- **react-youtube**: YouTube IFrame API wrapper
- **lucide-react**: Icon library
- **CSS Modules**: Scoped styling

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `M` | Mute/Unmute |
| `F` | Fullscreen |
| `←` | Seek backward |
| `→` | Seek forward |
| `Escape` | Exit modal |

---

## 📱 Responsive Design

- **Desktop**: Full controls, volume slider, speed menu
- **Tablet**: Compact controls, touch-optimized
- **Mobile**: Simplified UI, always-visible controls

---

## ♿ Accessibility

- ✅ Keyboard navigation
- ✅ ARIA labels
- ✅ Focus indicators
- ✅ Screen reader support
- ✅ Semantic HTML

---

## 🎬 Usage Examples

### Chat Integration
```tsx
import { HeyDividendPlayer } from '@/components/video';

export function ChatMessage({ message }) {
  return (
    <div className="chat-message">
      <div>{message.text}</div>
      
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

### With Video Queue
```tsx
import { HeyDividendPlayer, VideoQueue } from '@/components/video';

export function VideoSection({ videos }) {
  const [current, setCurrent] = useState(0);

  return (
    <>
      <HeyDividendPlayer 
        video={videos[current]} 
        variant="expanded"
        onVideoEnd={() => setCurrent(c => c + 1)}
      />
      <VideoQueue 
        videos={videos} 
        currentIndex={current}
        onVideoSelect={setCurrent}
      />
    </>
  );
}
```

---

## 🐛 Troubleshooting

**Player not loading?**
- Check that `react-youtube` is installed
- Verify video_id is valid
- Ensure YouTube API is accessible

**Styles not applying?**
- Confirm CSS modules are configured in Next.js
- Check import paths match your project structure

**TypeScript errors?**
- Ensure `types/video.ts` is in the correct location
- Verify tsconfig.json path aliases are configured

---

## 📦 What's Included

- ✅ 3 React components (Player, Queue, Modal)
- ✅ Complete TypeScript interfaces
- ✅ Responsive CSS modules
- ✅ Comprehensive documentation
- ✅ Usage examples
- ✅ Best practices guide

---

## 🔄 Updates

**Version 1.0.0** (November 17, 2025)
- Initial release
- HeyDividendPlayer component
- VideoQueue component
- VideoModal component
- Complete styling system
- Full documentation

---

## 📄 License

Part of Harvey AI project.

---

## 📞 Support

For questions or issues:
1. Check the complete guide: `HEYDIVIDEND_VIDEO_PLAYER_GUIDE.md`
2. Review TypeScript interfaces in `types/video.ts`
3. Contact Harvey AI development team

---

**Built with ❤️ for HeyDividend by the Harvey AI Team**
