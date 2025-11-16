# Harvey Chat + Video Integration Guide

## Overview

This guide explains how to integrate video recommendations into Harvey's chat responses.

## Architecture

```
User: "What is a dividend?"
    ↓
Harvey Chat Controller (ai_controller.chat_completions)
    ↓
Generate AI Response: "A dividend is a payment made by a corporation..."
    ↓
Video Enhancement (video_integration.py)
    ↓
Enhanced Response: AI answer + relevant videos
    ↓
Frontend displays: Answer + Videos
```

## Integration Methods

### Method 1: Automatic Enhancement (Recommended)

Automatically add videos to **every** chat response when relevant.

**Add to `app/controllers/ai_controller.py`:**

```python
from app.helpers.video_integration import enhance_response_with_videos

async def chat_completions(request: Request):
    # ... existing code to generate AI response ...
    
    user_query = request_data.get("messages", [])[-1].get("content", "")
    ai_response = generated_response  # Your generated response
    
    # Enhance with videos
    enhanced_response = enhance_response_with_videos(user_query, ai_response)
    
    # Return enhanced response
    return enhanced_response
```

### Method 2: Frontend-Triggered

Frontend explicitly requests videos when needed.

**Frontend calls both endpoints:**

```typescript
// 1. Get chat response
const chatResponse = await fetch('/v1/chat/completions', {
  method: 'POST',
  body: JSON.stringify({ messages: [...] })
});

// 2. Get videos separately
const videoResponse = await fetch('/api/videos/search', {
  method: 'POST',
  body: JSON.stringify({ 
    query: userMessage,
    max_results: 2 
  })
});

// Display both in UI
```

### Method 3: Contextual Trigger

Only add videos when certain keywords are detected.

```python
from app.helpers.video_integration import get_video_recommendations

TRIGGER_KEYWORDS = ["dividend", "reit", "aristocrat", "yield", "income", "portfolio"]

async def chat_completions(request: Request):
    user_query = request_data.get("messages", [])[-1].get("content", "").lower()
    
    # Generate AI response
    ai_response = generated_response
    
    # Check if query contains video-worthy keywords
    if any(keyword in user_query for keyword in TRIGGER_KEYWORDS):
        videos = get_video_recommendations(user_query)
        if videos:
            ai_response += videos
    
    return ai_response
```

## Example Integration (Streaming Responses)

For streaming chat responses, append videos at the end:

```python
async def chat_completions_streaming(request: Request):
    async def generate():
        # Stream AI response chunks
        async for chunk in ai_response_generator():
            yield chunk
        
        # After streaming complete, add videos
        user_query = get_user_query(request)
        videos = get_video_recommendations(user_query)
        if videos:
            yield f"\n\n{videos}"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Frontend Display Example

**React/Next.js:**

```typescript
function ChatMessage({ message }: { message: Message }) {
  // Parse videos from markdown response
  const hasVideos = message.content.includes('🎥 Related Videos');
  
  if (hasVideos) {
    const [answer, videosSection] = message.content.split('🎥 Related Videos');
    
    return (
      <div>
        <div className="answer">
          <ReactMarkdown>{answer}</ReactMarkdown>
        </div>
        <div className="videos">
          <h3>🎥 Related Videos from @heydividedtv</h3>
          <ReactMarkdown>{videosSection}</ReactMarkdown>
        </div>
      </div>
    );
  }
  
  return <ReactMarkdown>{message.content}</ReactMarkdown>;
}
```

## Configuration

**Control video enhancement behavior:**

```python
# In config.py or environment variables
VIDEO_ENHANCEMENT_ENABLED = os.getenv("VIDEO_ENHANCEMENT_ENABLED", "true") == "true"
VIDEO_MIN_RELEVANCE_SCORE = int(os.getenv("VIDEO_MIN_RELEVANCE_SCORE", "2"))
VIDEO_MAX_RESULTS = int(os.getenv("VIDEO_MAX_RESULTS", "2"))

# In video_integration.py
def enhance_response_with_videos(user_query, ai_response):
    if not VIDEO_ENHANCEMENT_ENABLED:
        return ai_response
    
    videos = video_service.search_videos(
        user_query, 
        max_results=VIDEO_MAX_RESULTS
    )
    
    if videos and videos[0].get("relevance_score", 0) >= VIDEO_MIN_RELEVANCE_SCORE:
        return ai_response + video_service.format_video_recommendations(videos)
    
    return ai_response
```

## Testing

**Test the integration:**

```bash
# Test video search
curl -X POST http://localhost:8001/api/videos/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a dividend?", "max_results": 2}'

# Test chat with video enhancement (after integration)
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is a dividend?"}
    ]
  }'
```

## Monitoring

Videos added to chat responses are automatically logged by the FeatureMonitoringMiddleware:

```
[VIDEO_SERVICE] endpoint=/api/videos/search status=200 duration=45ms
```

## Next Steps

1. Choose integration method (Automatic, Frontend-Triggered, or Contextual)
2. Add helper import to your chat controller
3. Enhance responses before returning to frontend
4. Test with questions like "What is a dividend?" or "REIT investing"
5. Monitor logs to see video recommendations in action

## FAQ

**Q: Will this slow down chat responses?**  
A: Video search adds ~50ms. Use async/await to minimize impact.

**Q: How often are videos recommended?**  
A: Only when relevance_score >= 2 (highly relevant matches)

**Q: Can I customize which videos appear?**  
A: Yes, edit `app/data/video_knowledge_base.json` to add/remove videos

**Q: What if no videos match?**  
A: The response is returned unchanged (no video section added)

---

**Last Updated:** November 16, 2025
