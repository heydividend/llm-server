# Context-Aware Status Messages - Harvey AI

## Overview

Harvey AI now displays intelligent, context-aware status messages during streaming responses. These messages help users understand what Harvey is processing based on their query.

## Feature Details

### Status Message Flow

```
User Query → Status Detection → Status Message → AI Response → Videos → Done
```

**Example:**
1. User asks: "What are the top dividend aristocrats?"
2. Harvey shows: "*Finding dividend aristocrats...*"
3. Harvey streams the AI response
4. Harvey appends relevant videos
5. Response complete

### Supported Keywords & Status Messages

#### Dividend-Related Queries
- `dividend` → "Calculating dividends..."
- `yield` → "Checking yields..."
- `distribution` → "Analyzing distributions..."
- `aristocrat` → "Finding dividend aristocrats..."
- `king` → "Finding dividend kings..."
- `champion` → "Finding dividend champions..."
- `ex-dividend` → "Finding ex-dividend dates..."
- `payout` → "Evaluating payout ratios..."
- `drip` → "Analyzing dividend reinvestment..."
- `payment` → "Checking payment schedules..."

#### Portfolio & Strategy
- `portfolio` → "Scanning portfolios..."
- `allocation` → "Optimizing allocations..."
- `rebalance` → "Balancing portfolio..."
- `diversif` → "Assessing diversification..."
- `watchlist` → "Analyzing watchlist..."
- `position` → "Reviewing positions..."

#### Market Analysis
- `market` → "Analyzing markets..."
- `sector` → "Scanning sectors..."
- `industry` → "Reviewing industries..."
- `stock` → "Analyzing stocks..."
- `etf` → "Reviewing ETFs..."
- `reit` → "Analyzing REITs..."

#### ML/AI Features
- `predict` → "Running ML models..."
- `forecast` → "Generating forecasts..."
- `backtest` → "Running backtests..."
- `optimize` → "Optimizing strategy..."
- `score` → "Calculating scores..."
- `rating` → "Generating ratings..."

#### Income & Tax
- `income` → "Calculating income projections..."
- `tax` → "Analyzing tax implications..."
- `qualified` → "Checking dividend qualifications..."

#### Company Analysis
- `fundamental` → "Analyzing fundamentals..."
- `financial` → "Reviewing financials..."
- `earnings` → "Checking earnings..."
- `revenue` → "Analyzing revenue..."

#### Lists & Categories
- `list` → "Building dividend lists..."
- `category` → "Finding categories..."
- `top` → "Finding top performers..."
- `best` → "Finding best options..."

#### Ticker-Specific
- `$AAPL` or `#AAPL` → "Analyzing AAPL fundamentals..."
- Any ticker pattern → "Analyzing {TICKER} fundamentals..."

#### Default Fallback
- No keywords matched → "Harvey is thinking..."

## Technical Implementation

### SSE Streaming Format

Status messages are sent as SSE chunks at the beginning of the response:

```
data: {"id":"status-msg","object":"chat.completion.chunk","choices":[{"delta":{"content":"*Finding dividend aristocrats...*\n\n"}}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"Here"}}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":" are"}}]}

... (AI response chunks) ...

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"### 🎥 Related Videos..."}}]}

data: [DONE]
```

### Files Modified

1. **app/helpers/status_message_detector.py** (NEW)
   - `detect_status_message(query)` - Detects appropriate status message
   - `get_status_sse_chunk(status_message, request_id)` - Formats as SSE chunk

2. **app/controllers/ai_controller.py**
   - Imported status message helpers
   - Modified both `stream_and_log()` functions to send status messages first
   - Added video integration to JSON streaming path (previously missing)

### Code Example

```python
from app.helpers.status_message_detector import detect_status_message, get_status_sse_chunk

# In streaming function
async def stream_and_log():
    # 1. Send status message first
    status_msg = detect_status_message(user_query)
    status_chunk = get_status_sse_chunk(status_msg, request_id)
    yield status_chunk
    
    # 2. Stream AI response
    for chunk in ai_response_generator:
        yield chunk
    
    # 3. Append videos (before [DONE])
    videos = get_video_recommendations(user_query)
    if videos:
        yield format_video_sse(videos)
    
    # 4. Send [DONE]
    yield b'data: [DONE]\n\n'
```

## Frontend Integration

### React/Next.js Example

```typescript
const streamResponse = async (userQuery: string) => {
  const response = await fetch('/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: [{ role: 'user', content: userQuery }],
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ') && line !== 'data: [DONE]') {
        const data = JSON.parse(line.slice(6));
        const content = data.choices[0]?.delta?.content;
        
        if (content) {
          // Check if it's a status message (starts with *)
          if (content.startsWith('*') && content.includes('...*')) {
            displayStatusMessage(content); // Show in UI with special styling
          } else {
            appendToResponse(content); // Regular AI response
          }
        }
      }
    }
  }
};
```

### Styling Recommendation

Status messages are wrapped in `*asterisks*` for markdown italic formatting:

```css
/* Status message styling */
.status-message {
  font-style: italic;
  color: #6b7280; /* Gray-500 */
  font-size: 0.875rem;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}
```

## Benefits

1. **Better UX** - Users see immediate feedback that Harvey is working
2. **Context Awareness** - Status messages match the query type
3. **Professional Feel** - Similar to ChatGPT, Claude, etc.
4. **Transparency** - Users understand what processing is happening
5. **Reduced Perceived Latency** - Shows progress immediately

## Testing

### Test Queries

```bash
# Dividend query
"What are the top dividend aristocrats?"
→ Status: "Finding dividend aristocrats..."

# Ticker query
"Analyze $AAPL dividend history"
→ Status: "Analyzing AAPL fundamentals..."

# Portfolio query
"Show me my portfolio allocation"
→ Status: "Scanning portfolios..."

# ML query
"Predict dividend growth for JNJ"
→ Status: "Running ML models..."

# Default
"Hello"
→ Status: "Harvey is thinking..."
```

### cURL Test

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What are the best dividend aristocrats?"}
    ],
    "stream": true
  }'
```

Expected output:
```
data: {"id":"status-msg","object":"chat.completion.chunk","choices":[{"delta":{"content":"*Finding dividend aristocrats...*\n\n"}}]}

data: {"id":"chatcmpl-...","object":"chat.completion.chunk","choices":[{"delta":{"content":"Based"}}]}
... (continues)
```

## Deployment

The feature is automatically active in both streaming paths:
- Form-data path (`/v1/chat/completions` with multipart/form-data)
- JSON path (`/v1/chat/completions` with application/json)

### Deploy to Azure VM

```bash
# On Azure VM (20.81.210.213)
cd /home/azureuser/llm/server
git pull origin main
sudo systemctl restart harvey-ml
sudo systemctl status harvey-ml
```

## Future Enhancements

1. **Dynamic Status Updates** - Show multiple status messages as processing progresses
2. **Estimated Time** - Add time estimates for complex queries
3. **Progress Bars** - Show percentage completion for multi-step operations
4. **Custom Status** - Allow frontends to request specific status types

---

**Last Updated:** November 16, 2025  
**Author:** Harvey AI Development Team
