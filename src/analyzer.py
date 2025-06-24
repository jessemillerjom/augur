import os
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv
import logging
import json

from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.schema import HumanMessage, AIMessage

# Load environment variables
load_dotenv()


class IncidentAnalyzer:
    """
    AI-powered incident analyzer that generates post-mortem reports
    from raw observability data using LangChain and Google's Gemini model.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the analyzer with Google API key."""
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("GOOGLE_API_KEY")
            
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError(
                "Please set your GOOGLE_API_KEY in the .env file or provide it as a parameter. "
                "Get your API key from https://makersuite.google.com/app/apikey"
            )
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=self.api_key,
            temperature=0.1,
            top_p=0.9
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(return_messages=True)
        self.conversation_initialized = False
    
    def _load_and_prepare_data(self, incident_path: str) -> Tuple[str, Optional[pd.DataFrame]]:
        """Load logs and metrics, returning combined text and a metrics DataFrame."""
        incident_path = Path(incident_path)
        if not incident_path.exists():
            raise FileNotFoundError(f"Incident path not found: {incident_path}")

        # Load logs into a single text block
        log_content = []
        logs_path = incident_path / "logs"
        if logs_path.exists():
            for log_file in logs_path.glob("*.log"):
                with open(log_file, 'r') as f:
                    log_content.append(f"=== Log: {log_file.name} ===\n{f.read()}")
        
        # Load metrics into a DataFrame and also get text representation
        metrics_df = None
        metrics_content = []
        metrics_path = incident_path / "metrics"
        if metrics_path.exists():
            csv_files = list(metrics_path.glob("*.csv"))
            if csv_files:
                # For now, we load the first CSV for charting
                try:
                    metrics_df = pd.read_csv(csv_files[0])
                    # Convert timestamp column if it exists
                    if 'timestamp' in metrics_df.columns:
                        metrics_df['timestamp'] = pd.to_datetime(metrics_df['timestamp'])
                        metrics_df = metrics_df.set_index('timestamp')
                except Exception as e:
                    print(f"Warning: Could not load CSV into DataFrame: {e}")

                for csv_file in csv_files:
                    with open(csv_file, 'r') as f:
                        metrics_content.append(f"=== Metrics: {csv_file.name} ===\n{f.read()}")

        if not log_content and not metrics_content:
            raise ValueError(f"No log or metrics files found in {incident_path}")
            
        full_context = "\n\n".join(log_content + metrics_content)
        return full_context, metrics_df

    def _extract_timeline(self, report_text: str) -> List[Dict[str, str]]:
        """
        Extracts the timeline from the report text using regex.
        Matches lines like:
        2024-01-15 16:30:00: Event...
        2024-01-15 16:30-17:15: Event...
        2024-01-15 16:30: Event...
        """
        # Find the Timeline of Events section (robust to whitespace and section header formatting)
        timeline_section_match = re.search(
            r"2\\. Timeline of Events:\s*\n(.*?)(?:\n\d+\.\s|$)",
            report_text, re.DOTALL)
        if not timeline_section_match:
            logging.warning("Timeline section not found in report text.")
            return []

        timeline_text = timeline_section_match.group(1)
        logging.info(f"Extracted timeline section:\n{timeline_text}")
        # Match lines starting with a date and time (with or without seconds), optional time range, then colon
        event_lines = re.findall(
            r"^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}(?::[0-9]{2})?(?:-[0-9]{2}:[0-9]{2}(?::[0-9]{2})?)?):\s*(.*)$",
            timeline_text, re.MULTILINE)

        events = []
        for start, desc in event_lines:
            events.append({"time": start, "event": desc.strip()})
        if not events:
            logging.warning(f"No timeline events matched in section:\n{timeline_text}")
        return events

    def generate_report(self, incident_path: str) -> Dict[str, Any]:
        """
        Generate a comprehensive post-mortem report from incident data.
        
        Returns:
            A dictionary with the report, timeline, and metrics DataFrame.
        """
        context, metrics_df = self._load_and_prepare_data(incident_path)
        
        prompt_template = """
You are a world-class Site Reliability Engineer. Your task is to write a detailed, data-driven post-mortem report based on the following context from an incident.

Context:
{context}

Based on the data, write a post-mortem report in Markdown. The report must include:
1. **Summary:** A brief overview of the incident.
2. **Timeline of Events:** A detailed, timestamped list of key events. Format each event as a bullet point: `- **YYYY-MM-DD HH:MM:SS:** Event description.`
3. **Root Cause Analysis:** A clear explanation of the root cause.
4. **Impact Analysis:** An assessment of services affected and business impact.
5. **Action Items:** A list of recommended actions to prevent this in the future.

IMPORTANT: Use the following section separators to clearly mark different parts of your output:

=== TIMELINE_JSON ===
At the end of your report, include the timeline as a JSON array in a code block, e.g.:
```json
[
  {{"time": "2024-01-15 16:30:00", "event": "Database connection timeouts begin."}},
  {{"time": "2024-01-15 16:33:00", "event": "Error rate spikes."}}
]
```
=== END_TIMELINE_JSON ===

=== MONITORING_CODE ===
Based on the root cause, act as a Staff SRE. If the incident could have been prevented with better monitoring, generate a code block for a datadog_monitor Terraform resource that would detect the issue. If not, state that no monitor could have prevented it.
=== END_MONITORING_CODE ===

=== REGRESSION_TEST ===
If the root cause was a software bug, also act as a Senior Software Engineer. Write a Python pytest test case that simulates the conditions of the failure and would fail if the bug were present. Add comments explaining what the test does.
=== END_REGRESSION_TEST ===

Report:
"""
        prompt = PromptTemplate(input_variables=["context"], template=prompt_template)
        
        try:
            response = self.llm.invoke(prompt.format(context=context))
            report_text = response.content
            
            # Extract timeline from JSON using the new separators
            timeline_events = []
            timeline_match = re.search(r"=== TIMELINE_JSON ===\s*(.*?)\s*=== END_TIMELINE_JSON ===", report_text, re.DOTALL)
            if timeline_match:
                try:
                    json_content = timeline_match.group(1).strip()
                    # Extract JSON from the code block
                    json_block = re.search(r"```json\s*(.*?)\s*```", json_content, re.DOTALL)
                    if json_block:
                        timeline_events = json.loads(json_block.group(1))
                except Exception as e:
                    timeline_events = []
            
            # Remove timeline section from main report
            report_text = re.sub(r"=== TIMELINE_JSON ===\s*.*?\s*=== END_TIMELINE_JSON ===", "", report_text, flags=re.DOTALL).strip()
            
            # Fallback to regex extraction if JSON not found
            if not timeline_events:
                timeline_events = self._extract_timeline(report_text)
            
            # Extract monitoring code using the new separators
            monitoring_code = ""
            monitoring_match = re.search(r"=== MONITORING_CODE ===\s*(.*?)\s*=== END_MONITORING_CODE ===", report_text, re.DOTALL)
            if monitoring_match:
                monitoring_code = monitoring_match.group(1).strip()
                # Remove monitoring section from main report
                report_text = re.sub(r"=== MONITORING_CODE ===\s*.*?\s*=== END_MONITORING_CODE ===", "", report_text, flags=re.DOTALL).strip()
            
            # Extract regression test using the new separators
            regression_test_code = ""
            regression_match = re.search(r"=== REGRESSION_TEST ===\s*(.*?)\s*=== END_REGRESSION_TEST ===", report_text, re.DOTALL)
            if regression_match:
                regression_test_code = regression_match.group(1).strip()
                # Remove regression test section from main report
                report_text = re.sub(r"=== REGRESSION_TEST ===\s*.*?\s*=== END_REGRESSION_TEST ===", "", report_text, flags=re.DOTALL).strip()
            
            return {
                "report_markdown": report_text,
                "timeline_events": timeline_events,
                "metrics_df": metrics_df,
                "monitoring_code": monitoring_code,
                "regression_test_code": regression_test_code
            }
        except Exception as e:
            raise RuntimeError(f"Failed to generate report: {str(e)}")
            
    def initialize_conversation(self, incident_context: str, report_markdown: str):
        """
        Initialize the conversation with the incident context and report.
        This sets up the conversation memory so we don't need to resend context with each question.
        """
        system_message = f"""You are an AI assistant helping with incident analysis. You have access to the following incident data and post-mortem report:

INCIDENT CONTEXT (raw data):
{incident_context}

POST-MORTEM REPORT:
{report_markdown}

IMPORTANT GUIDELINES:
1. ONLY answer questions that are directly related to this incident, its analysis, timeline, root cause, impact, or action items
2. If the question is NOT related to this specific incident or its analysis, politely redirect the conversation back to the incident
3. Be helpful but stay focused on the incident context
4. If you don't have enough information to answer the question, say so
5. Keep responses conversational but professional
6. You can reference both the raw incident data and the analyzed report to provide comprehensive answers

You are now ready to answer questions about this incident. What would you like to know?"""
        
        # Add the system message to memory
        self.memory.chat_memory.add_message(AIMessage(content=system_message))
        self.conversation_initialized = True
        
    def follow_up_question(self, question: str, incident_context: str = None, report_context: str = None) -> str:
        """
        Answer follow-up questions about the incident analysis using conversation memory.
        
        Args:
            question: The user's question
            incident_context: The raw incident data (only needed for first question if not initialized)
            report_context: The incident report (only needed for first question if not initialized)
        """
        # Initialize conversation if this is the first question
        if not self.conversation_initialized:
            if not incident_context or not report_context:
                return "I don't have access to the incident context. Please make sure you've analyzed an incident first."
            
            self.initialize_conversation(incident_context, report_context)
        
        # Add the user's question to memory
        self.memory.chat_memory.add_message(HumanMessage(content=question))
        
        # Get the conversation history
        messages = self.memory.chat_memory.messages
        
        try:
            # Send the full conversation to the LLM
            response = self.llm.invoke(messages)
            ai_response = response.content.strip()
            
            # Add the AI response to memory
            self.memory.chat_memory.add_message(AIMessage(content=ai_response))
            
            return ai_response
        except Exception as e:
            return f"I'm sorry, but I encountered an error while processing your question: {str(e)}"
    
    def clear_conversation(self):
        """Clear the conversation memory."""
        self.memory.clear()
        self.conversation_initialized = False 