# logger_module.py

import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class QueryResponseLogger:
    """Logger for storing queries and responses in daily files for easy debugging."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.queries_dir = self.log_dir / "daily_queries"
        self.conversations_dir = self.log_dir / "daily_conversations"
        
        self.queries_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

    def _get_date_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _get_daily_query_file(self) -> Path:
        return self.queries_dir / f"queries_{self._get_date_str()}.txt"

    def _get_daily_conversation_file(self) -> Path:
        return self.conversations_dir / f"conversations_{self._get_date_str()}.txt"

    def log_query(self, rid: str, query: str, metadata: dict = None, response_id: str = None) -> str:
        filepath = self._get_daily_query_file()
        timestamp = self._get_timestamp()

        separator = "=" * 80
        entry = f"\n{separator}\n"
        entry += f"[{timestamp}] Request ID: {rid}\n"
        if response_id:
            entry += f"Response ID: {response_id}\n"
        entry += f"{separator}\nQUERY:\n{query}\n"

        if metadata:
            entry += "\nMETADATA:\n"
            for key, value in metadata.items():
                entry += f"  - {key}: {value}\n"

        entry += f"{separator}\n"

        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(entry)

        logger.info(f"[{rid}] Query logged to daily file: {filepath}")
        return str(filepath)

    def _clean_response(self, response: str) -> str:
        if not response:
            return ""

        if "data:" in response and "chat.completion.chunk" in response:
            clean_text = []
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('data:') and line != 'data: [DONE]':
                    try:
                        data = json.loads(line[5:].strip())
                        delta = data['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            clean_text.append(content)
                    except json.JSONDecodeError:
                        continue
            return ''.join(clean_text)
        return response

    def log_full_conversation(self, rid: str, query: str, response: str, metadata: dict = None, error: str = None, response_id: str = None) -> str:
        filepath = self._get_daily_conversation_file()
        timestamp = self._get_timestamp()
        clean_response = self._clean_response(response)

        separator = "=" * 80
        sub_separator = "-" * 80
        entry = (
            f"\n{separator}\n[{timestamp}] Request ID: {rid}\n"
        )
        
        if response_id:
            entry += f"Response ID: {response_id}\n"
        
        entry += f"{separator}\n\nQUERY:\n{sub_separator}\n{query}\n{sub_separator}\n\n"

        if metadata:
            entry += "METADATA:\n" + sub_separator + "\n"
            for key, value in metadata.items():
                entry += f"  - {key}: {value}\n"
            entry += f"{sub_separator}\n\n"

        entry += f"RESPONSE (Length: {len(clean_response)} chars):\n{sub_separator}\n{clean_response}\n{sub_separator}\n"

        if error:
            entry += f"\nERROR:\n{sub_separator}\n{error}\n{sub_separator}\n"

        entry += f"\n{separator}\n"

        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(entry)

        logger.info(f"[{rid}] Full conversation logged to daily file: {filepath}")
        return str(filepath)
