# Frontend Update Guide for Harvey Port 8001

## For React/Next.js Frontend

### 1. Update API Configuration

In your frontend project, update the API base URL:

```javascript
// src/config/api.js or .env file
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://20.81.210.213:8001';

// Or in .env file:
REACT_APP_API_URL=http://20.81.210.213:8001
NEXT_PUBLIC_API_URL=http://20.81.210.213:8001
```

### 2. Update API Service

```javascript
// src/services/api.js
const API_CONFIG = {
  baseURL: 'http://20.81.210.213:8001',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
};

// Example chat function
export const sendChatMessage = async (query, sessionId = null) => {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/api/chat`, {
      method: 'POST',
      headers: API_CONFIG.headers,
      body: JSON.stringify({
        query,
        session_id: sessionId || `session-${Date.now()}`
      })
    });
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Chat API Error:', error);
    throw error;
  }
};
```

### 3. Test the Connection

```javascript
// src/utils/testConnection.js
export const testHarveyConnection = async () => {
  try {
    const response = await fetch('http://20.81.210.213:8001/health');
    const data = await response.json();
    console.log('✅ Harvey is connected:', data);
    return true;
  } catch (error) {
    console.error('❌ Harvey connection failed:', error);
    return false;
  }
};

// Call this on app load
testHarveyConnection();
```

### 4. Handle Streaming Responses

If using streaming for chat responses:

```javascript
export const streamChatMessage = async (query, onChunk) => {
  const response = await fetch(`${API_CONFIG.baseURL}/api/chat/stream`, {
    method: 'POST',
    headers: API_CONFIG.headers,
    body: JSON.stringify({ query })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    onChunk(chunk);
  }
};
```

## For HTML/Vanilla JS Frontend

```html
<!DOCTYPE html>
<html>
<head>
    <title>Harvey Chat</title>
</head>
<body>
    <div id="chat-container">
        <div id="messages"></div>
        <input type="text" id="query-input" placeholder="Ask Harvey...">
        <button onclick="sendQuery()">Send</button>
    </div>

    <script>
        const API_URL = 'http://20.81.210.213:8001';
        
        async function sendQuery() {
            const input = document.getElementById('query-input');
            const query = input.value;
            if (!query) return;
            
            try {
                const response = await fetch(`${API_URL}/api/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        session_id: 'web-session'
                    })
                });
                
                const data = await response.json();
                displayMessage(query, data.response);
                input.value = '';
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to connect to Harvey');
            }
        }
        
        function displayMessage(query, response) {
            const messages = document.getElementById('messages');
            messages.innerHTML += `
                <div><strong>You:</strong> ${query}</div>
                <div><strong>Harvey:</strong> ${response}</div>
                <hr>
            `;
        }
        
        // Test connection on load
        fetch(`${API_URL}/health`)
            .then(r => r.json())
            .then(d => console.log('Harvey connected:', d))
            .catch(e => console.error('Harvey not accessible:', e));
    </script>
</body>
</html>
```

## Testing the Frontend

After updating your frontend:

1. **Clear browser cache**: Ctrl+F5 or Cmd+Shift+R
2. **Check browser console** for connection logs
3. **Test a simple query** to verify the connection
4. **Check CORS**: If you get CORS errors, Harvey backend may need CORS headers enabled

## Troubleshooting

### CORS Issues
If you see CORS errors, add these headers to Harvey's FastAPI backend:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Connection Timeouts
- Increase timeout in fetch requests
- Check Azure NSG rules for port 8001
- Verify Harvey is running: `sudo systemctl status harvey-backend`