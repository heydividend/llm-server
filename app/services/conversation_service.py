"""
Conversational Memory Service for Harvey AI Financial Advisor

Manages conversation sessions, threads, and message history with token budgeting.
Stores every user-assistant interaction in the database for context-aware responses.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy import text
import tiktoken

from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("conversation_service")

DEFAULT_MODEL = "gpt-4"
DEFAULT_MAX_TOKENS = 4000
TOKEN_BUFFER = 500


def count_tokens(text: str, model: str = DEFAULT_MODEL) -> int:
    """
    Count tokens in a text string using tiktoken.
    
    Args:
        text: The text to count tokens for
        model: The model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
    
    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Token counting failed, using estimate: {e}")
        return len(text) // 4


def create_session(user_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a new user session.
    
    Args:
        user_data: Optional dict with user info (email, name, preferences)
    
    Returns:
        session_id (UUID string)
    """
    session_id = str(uuid.uuid4())
    user_data_json = json.dumps(user_data) if user_data else None
    
    try:
        query = text("""
            INSERT INTO dbo.user_sessions (session_id, user_data, created_at, last_active)
            VALUES (:session_id, :user_data, GETDATE(), GETDATE());
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {
                "session_id": session_id,
                "user_data": user_data_json
            })
        
        logger.info(f"Created new session: {session_id}")
        return session_id
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise


def update_session_activity(session_id: str) -> None:
    """
    Update the last_active timestamp for a session.
    
    Args:
        session_id: The session ID to update
    """
    try:
        query = text("""
            UPDATE dbo.user_sessions
            SET last_active = GETDATE()
            WHERE session_id = :session_id;
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {"session_id": session_id})
            
    except Exception as e:
        logger.warning(f"Failed to update session activity: {e}")


def create_conversation(session_id: str, title: Optional[str] = None) -> str:
    """
    Create a new conversation thread.
    
    Args:
        session_id: The session ID this conversation belongs to
        title: Optional conversation title (auto-generated if not provided)
    
    Returns:
        conversation_id (UUID string)
    """
    conversation_id = str(uuid.uuid4())
    
    if not title:
        title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    try:
        query = text("""
            INSERT INTO dbo.conversations 
            (conversation_id, session_id, title, created_at, updated_at, total_tokens, message_count)
            VALUES (:conversation_id, :session_id, :title, GETDATE(), GETDATE(), 0, 0);
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {
                "conversation_id": conversation_id,
                "session_id": session_id,
                "title": title
            })
        
        logger.info(f"Created conversation {conversation_id} for session {session_id}")
        return conversation_id
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise


def add_message(
    conversation_id: str,
    role: str,
    content: str,
    tokens: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Add a message to a conversation.
    
    Args:
        conversation_id: The conversation ID
        role: Message role ('user' or 'assistant')
        content: Message content
        tokens: Token count (auto-calculated if not provided)
        metadata: Optional metadata (query_type, tickers, ml_predictions, etc)
    
    Returns:
        message_id (UUID string)
    """
    message_id = str(uuid.uuid4())
    
    if tokens is None:
        tokens = count_tokens(content)
    
    metadata_json = json.dumps(metadata) if metadata else None
    
    try:
        insert_query = text("""
            INSERT INTO dbo.conversation_messages 
            (message_id, conversation_id, role, content, tokens, created_at, metadata)
            VALUES (:message_id, :conversation_id, :role, :content, :tokens, GETDATE(), :metadata);
        """)
        
        update_query = text("""
            UPDATE dbo.conversations
            SET total_tokens = total_tokens + :tokens,
                message_count = message_count + 1,
                updated_at = GETDATE()
            WHERE conversation_id = :conversation_id;
        """)
        
        with engine.begin() as conn:
            conn.execute(insert_query, {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "tokens": tokens,
                "metadata": metadata_json
            })
            
            conn.execute(update_query, {
                "conversation_id": conversation_id,
                "tokens": tokens
            })
        
        logger.info(f"Added {role} message to conversation {conversation_id} ({tokens} tokens)")
        return message_id
        
    except Exception as e:
        logger.error(f"Failed to add message: {e}")
        raise


def get_conversation_history(
    conversation_id: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    include_system: bool = False
) -> List[Dict[str, str]]:
    """
    Retrieve conversation history formatted for OpenAI API.
    
    Implements token budgeting to stay within limits:
    1. Loads messages from newest to oldest
    2. Stops when token limit is reached
    3. Returns messages in chronological order
    
    Args:
        conversation_id: The conversation ID
        max_tokens: Maximum tokens to include in history
        include_system: Whether to include system messages
    
    Returns:
        List of message dicts with 'role' and 'content' keys
    """
    try:
        query = text("""
            SELECT role, content, tokens, created_at
            FROM dbo.conversation_messages
            WHERE conversation_id = :conversation_id
            ORDER BY created_at DESC;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"conversation_id": conversation_id})
            rows = result.fetchall()
        
        if not rows:
            return []
        
        messages = []
        total_tokens = 0
        
        for row in rows:
            role, content, tokens, created_at = row
            
            if total_tokens + tokens > max_tokens - TOKEN_BUFFER:
                logger.info(
                    f"Token limit reached for conversation {conversation_id}. "
                    f"Loaded {len(messages)} messages ({total_tokens} tokens)"
                )
                break
            
            messages.append({
                "role": role,
                "content": content
            })
            total_tokens += tokens
        
        messages.reverse()
        
        logger.info(
            f"Retrieved {len(messages)} messages for conversation {conversation_id} "
            f"({total_tokens} tokens)"
        )
        
        return messages
        
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        return []


def get_recent_conversations(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent conversations for a session.
    
    Args:
        session_id: The session ID
        limit: Maximum number of conversations to return
    
    Returns:
        List of conversation dicts with metadata
    """
    try:
        query = text("""
            SELECT TOP (:limit)
                conversation_id,
                title,
                created_at,
                updated_at,
                total_tokens,
                message_count
            FROM dbo.conversations
            WHERE session_id = :session_id
            ORDER BY updated_at DESC;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {
                "session_id": session_id,
                "limit": limit
            })
            rows = result.fetchall()
        
        conversations = []
        for row in rows:
            conversations.append({
                "conversation_id": row[0],
                "title": row[1],
                "created_at": row[2].isoformat() if row[2] else None,
                "updated_at": row[3].isoformat() if row[3] else None,
                "total_tokens": row[4],
                "message_count": row[5]
            })
        
        logger.info(f"Retrieved {len(conversations)} conversations for session {session_id}")
        return conversations
        
    except Exception as e:
        logger.error(f"Failed to get recent conversations: {e}")
        return []


def get_conversation_stats(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Get statistics for a conversation.
    
    Args:
        conversation_id: The conversation ID
    
    Returns:
        Dict with conversation stats or None if not found
    """
    try:
        query = text("""
            SELECT 
                conversation_id,
                session_id,
                title,
                created_at,
                updated_at,
                total_tokens,
                message_count,
                metadata
            FROM dbo.conversations
            WHERE conversation_id = :conversation_id;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"conversation_id": conversation_id})
            row = result.fetchone()
        
        if not row:
            return None
        
        return {
            "conversation_id": row[0],
            "session_id": row[1],
            "title": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
            "updated_at": row[4].isoformat() if row[4] else None,
            "total_tokens": row[5],
            "message_count": row[6],
            "metadata": json.loads(row[7]) if row[7] else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation stats: {e}")
        return None


def summarize_old_conversations(conversation_id: str) -> None:
    """
    Summarize old messages in a conversation to reduce token usage.
    
    This is a placeholder for future implementation that would:
    1. Identify old messages beyond a threshold
    2. Generate summaries using LLM
    3. Replace old messages with summaries
    4. Keep recent messages intact
    
    Args:
        conversation_id: The conversation ID to summarize
    """
    logger.info(f"Summarization not yet implemented for conversation {conversation_id}")
    pass


def delete_conversation(conversation_id: str) -> bool:
    """
    Delete a conversation and all its messages.
    
    Args:
        conversation_id: The conversation ID to delete
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        query = text("""
            DELETE FROM dbo.conversations
            WHERE conversation_id = :conversation_id;
        """)
        
        with engine.begin() as conn:
            result = conn.execute(query, {"conversation_id": conversation_id})
        
        logger.info(f"Deleted conversation {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        return False


def session_exists(session_id: str) -> bool:
    """
    Check if a session exists.
    
    Args:
        session_id: The session ID to check
    
    Returns:
        True if session exists, False otherwise
    """
    try:
        query = text("""
            SELECT 1 FROM dbo.user_sessions
            WHERE session_id = :session_id;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"session_id": session_id})
            return result.fetchone() is not None
            
    except Exception as e:
        logger.error(f"Failed to check session existence: {e}")
        return False


def conversation_exists(conversation_id: str) -> bool:
    """
    Check if a conversation exists.
    
    Args:
        conversation_id: The conversation ID to check
    
    Returns:
        True if conversation exists, False otherwise
    """
    try:
        query = text("""
            SELECT 1 FROM dbo.conversations
            WHERE conversation_id = :conversation_id;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"conversation_id": conversation_id})
            return result.fetchone() is not None
            
    except Exception as e:
        logger.error(f"Failed to check conversation existence: {e}")
        return False
