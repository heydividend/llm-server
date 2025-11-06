/**
 * Harvey Frontend API Integration Script
 * Complete configuration for connecting to Harvey API at port 8001
 * Supports both React/Next.js and Vanilla JS implementations
 */

// ============================================
// CONFIGURATION
// ============================================

const HARVEY_CONFIG = {
  baseURL: 'http://20.81.210.213:8001',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
};

// ============================================
// CORE API FUNCTIONS
// ============================================

/**
 * Test Harvey connection
 */
const testHarveyConnection = async () => {
  try {
    const response = await fetch(`${HARVEY_CONFIG.baseURL}/health`, {
      timeout: HARVEY_CONFIG.timeout
    });
    const data = await response.json();
    console.log('✅ Harvey is connected:', data);
    return true;
  } catch (error) {
    console.error('❌ Harvey connection failed:', error);
    return false;
  }
};

/**
 * Send chat message to Harvey
 */
const sendChatMessage = async (query, sessionId = null) => {
  try {
    const response = await fetch(`${HARVEY_CONFIG.baseURL}/api/chat`, {
      method: 'POST',
      headers: HARVEY_CONFIG.headers,
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

/**
 * Stream chat message (for streaming responses)
 */
const streamChatMessage = async (query, onChunk) => {
  const response = await fetch(`${HARVEY_CONFIG.baseURL}/api/chat/stream`, {
    method: 'POST',
    headers: HARVEY_CONFIG.headers,
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

/**
 * Get dividend analysis for a symbol
 */
const analyzeDividend = async (symbol) => {
  try {
    const response = await fetch(`${HARVEY_CONFIG.baseURL}/api/dividends/analyze?symbol=${symbol}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Dividend Analysis Error:', error);
    throw error;
  }
};

/**
 * Get portfolio projection
 */
const getPortfolioProjection = async (portfolioData) => {
  try {
    const response = await fetch(`${HARVEY_CONFIG.baseURL}/api/portfolio/projection`, {
      method: 'POST',
      headers: HARVEY_CONFIG.headers,
      body: JSON.stringify(portfolioData)
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Portfolio Projection Error:', error);
    throw error;
  }
};

// ============================================
// REACT/NEXT.JS MODULE EXPORTS
// ============================================

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    HARVEY_CONFIG,
    testHarveyConnection,
    sendChatMessage,
    streamChatMessage,
    analyzeDividend,
    getPortfolioProjection
  };
}

// ============================================
// ES6 MODULE EXPORTS
// ============================================

if (typeof exports !== 'undefined') {
  exports.HARVEY_CONFIG = HARVEY_CONFIG;
  exports.testHarveyConnection = testHarveyConnection;
  exports.sendChatMessage = sendChatMessage;
  exports.streamChatMessage = streamChatMessage;
  exports.analyzeDividend = analyzeDividend;
  exports.getPortfolioProjection = getPortfolioProjection;
}

// ============================================
// VANILLA JS / BROWSER IMPLEMENTATION
// ============================================

if (typeof window !== 'undefined') {
  // Make functions globally available in browser
  window.HarveyAPI = {
    config: HARVEY_CONFIG,
    testConnection: testHarveyConnection,
    sendMessage: sendChatMessage,
    streamMessage: streamChatMessage,
    analyzeDividend: analyzeDividend,
    getPortfolioProjection: getPortfolioProjection,
    
    // Initialize chat UI if DOM is ready
    initChatUI: function() {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', this._setupChatUI);
      } else {
        this._setupChatUI();
      }
    },
    
    _setupChatUI: function() {
      // Test connection on load
      testHarveyConnection();
      
      // Add event listener for Enter key
      const input = document.getElementById('query-input');
      if (input) {
        input.addEventListener('keypress', function(e) {
          if (e.key === 'Enter') {
            window.HarveyAPI.sendQuery();
          }
        });
      }
    },
    
    sendQuery: async function() {
      const input = document.getElementById('query-input');
      const query = input ? input.value : '';
      if (!query) return;
      
      // Show loading state
      const button = document.querySelector('button');
      if (button) {
        button.disabled = true;
        button.textContent = 'Sending...';
      }
      
      try {
        const data = await sendChatMessage(query, 'web-session');
        this.displayMessage(query, data.response, data.model_used);
        if (input) input.value = '';
      } catch (error) {
        console.error('Error:', error);
        alert('Failed to connect to Harvey. Please check if the service is running.');
      } finally {
        if (button) {
          button.disabled = false;
          button.textContent = 'Send';
        }
      }
    },
    
    displayMessage: function(query, response, modelUsed) {
      const messages = document.getElementById('messages');
      if (!messages) return;
      
      const messageHtml = `
        <div class="message user-message">
          <strong>You:</strong> ${query}
        </div>
        <div class="message harvey-message">
          <strong>Harvey${modelUsed ? ` (${modelUsed})` : ''}:</strong> 
          <div class="response-content">${response}</div>
        </div>
        <hr>
      `;
      
      messages.innerHTML += messageHtml;
      messages.scrollTop = messages.scrollHeight;
    }
  };
  
  // Auto-initialize if on a page with chat UI
  if (document.getElementById('chat-container')) {
    window.HarveyAPI.initChatUI();
  }
}

// ============================================
// EXAMPLE USAGE
// ============================================

/*
// React/Next.js Usage:
import { sendChatMessage, testHarveyConnection } from './harvey-frontend-api';

// In your component:
useEffect(() => {
  testHarveyConnection();
}, []);

const handleChat = async (query) => {
  const response = await sendChatMessage(query);
  console.log(response);
};

// Vanilla HTML Usage:
<script src="harvey-frontend-api.js"></script>
<script>
  // Use global HarveyAPI object
  HarveyAPI.testConnection();
  HarveyAPI.sendMessage('What are the top dividend stocks?').then(console.log);
</script>

// Or use the built-in UI handler:
<div id="chat-container">
  <div id="messages"></div>
  <input type="text" id="query-input" placeholder="Ask Harvey...">
  <button onclick="HarveyAPI.sendQuery()">Send</button>
</div>
*/

console.log('Harvey Frontend API loaded. Configuration:', HARVEY_CONFIG.baseURL);