"""
Clarification Module for J.A.R.V.I.S.

Handles ambiguous user queries by asking clarifying questions
and managing the clarification dialog flow.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import time

logger = logging.getLogger(__name__)


@dataclass
class ClarificationQuestion:
    """Represents a clarification question to ask the user."""
    
    question: str
    context: str = ""
    options: List[str] = field(default_factory=list)
    expected_type: str = "text"  # text, choice, yes_no, number
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "context": self.context,
            "options": self.options,
            "expected_type": self.expected_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class ClarificationContext:
    """Holds the state of an ongoing clarification dialog."""
    
    original_query: str
    intent: Optional[str] = None
    pending_questions: List[ClarificationQuestion] = field(default_factory=list)
    answered_questions: List[tuple[ClarificationQuestion, str]] = field(default_factory=list)
    collected_data: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None
    started_at: float = field(default_factory=time.time)
    
    @property
    def is_complete(self) -> bool:
        """Check if all questions have been answered."""
        return len(self.pending_questions) == 0
    
    @property
    def current_question(self) -> Optional[ClarificationQuestion]:
        """Get the current pending question."""
        return self.pending_questions[0] if self.pending_questions else None


class ClarificationModule:
    """
    Manages clarification dialogs for ambiguous or incomplete queries.
    
    Handles:
    - Detecting when clarification is needed
    - Generating appropriate questions
    - Managing multi-step clarification flows
    - Collecting and validating answers
    """

    def __init__(self):
        """Initialize ClarificationModule."""
        self.active_context: Optional[ClarificationContext] = None
        self._question_templates: Dict[str, str] = self._load_templates()
        logger.info("ClarificationModule initialized")

    def _load_templates(self) -> Dict[str, str]:
        """Load question templates for common clarification scenarios."""
        return {
            "missing_parameter": "Für '{action}' benötige ich noch: {parameter}. Bitte geben Sie dies an.",
            "ambiguous_entity": "Ich habe mehrere Ergebnisse für '{entity}' gefunden: {options}. Welches meinen Sie?",
            "confirm_action": "Möchten Sie wirklich '{action}' ausführen?",
            "specify_time": "Zu welcher Zeit soll '{action}' ausgeführt werden?",
            "specify_location": "An welchem Ort soll '{action}' stattfinden?",
            "choose_option": "Bitte wählen Sie eine Option: {options}",
            "yes_no": "{question} (Ja/Nein)",
        }

    def needs_clarification(
        self,
        query: str,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> bool:
        """
        Determine if a query needs clarification.
        
        Args:
            query: The user's query
            intent: Detected intent if available
            entities: Extracted entities
            confidence: Confidence score of intent detection
            
        Returns:
            True if clarification is needed
        """
        # Low confidence intent
        if confidence < 0.6:
            logger.debug(f"Low confidence ({confidence}), clarification needed")
            return True
        
        # No clear intent
        if not intent or intent == "unknown":
            logger.debug("No clear intent, clarification needed")
            return True
        
        # Check for required parameters based on intent
        if intent and entities is not None:
            required_params = self._get_required_params(intent)
            missing = [p for p in required_params if p not in entities]
            if missing:
                logger.debug(f"Missing required parameters: {missing}")
                return True
        
        return False

    def start_clarification(
        self,
        query: str,
        *,
        intent: Optional[str] = None,
        questions: Optional[List[ClarificationQuestion]] = None,
        callback: Optional[Callable] = None,
    ) -> ClarificationQuestion:
        """
        Start a new clarification dialog.
        
        Args:
            query: Original user query
            intent: Detected intent
            questions: Pre-defined questions to ask
            callback: Function to call when clarification is complete
            
        Returns:
            First question to ask
        """
        if self.active_context:
            logger.warning("Abandoning previous clarification context")
        
        # Generate questions if not provided
        if questions is None:
            questions = self._generate_questions(query, intent)
        
        self.active_context = ClarificationContext(
            original_query=query,
            intent=intent,
            pending_questions=questions,
            callback=callback,
        )
        
        logger.info(f"Started clarification for: '{query}' ({len(questions)} questions)")
        
        current = self.active_context.current_question
        if not current:
            raise RuntimeError("No questions to ask")
        
        return current

    def process_answer(
        self,
        answer: str,
    ) -> tuple[Optional[ClarificationQuestion], bool]:
        """
        Process an answer to the current question.
        
        Args:
            answer: User's answer
            
        Returns:
            Tuple of (next_question, is_complete)
        """
        if not self.active_context:
            raise RuntimeError("No active clarification context")
        
        current = self.active_context.current_question
        if not current:
            raise RuntimeError("No current question")
        
        # Validate and process answer
        validated_answer = self._validate_answer(answer, current)
        
        # Store answer
        self.active_context.answered_questions.append((current, validated_answer))
        self.active_context.pending_questions.pop(0)
        
        # Store in collected data if metadata specifies a key
        if "data_key" in current.metadata:
            key = current.metadata["data_key"]
            self.active_context.collected_data[key] = validated_answer
        
        logger.debug(f"Answer recorded: {validated_answer}")
        
        # Check if complete
        if self.active_context.is_complete:
            logger.info("Clarification complete")
            if self.active_context.callback:
                try:
                    self.active_context.callback(self.active_context.collected_data)
                except Exception as e:
                    logger.error(f"Callback failed: {e}")
            return None, True
        
        # Return next question
        return self.active_context.current_question, False

    def cancel(self) -> None:
        """Cancel the current clarification dialog."""
        if self.active_context:
            logger.info(f"Cancelled clarification for: '{self.active_context.original_query}'")
            self.active_context = None

    def get_collected_data(self) -> Dict[str, Any]:
        """
        Get all data collected so far.
        
        Returns:
            Dictionary of collected data
        """
        if not self.active_context:
            return {}
        return dict(self.active_context.collected_data)

    def is_active(self) -> bool:
        """Check if clarification is currently active."""
        return self.active_context is not None

    def _generate_questions(
        self,
        query: str,
        intent: Optional[str],
    ) -> List[ClarificationQuestion]:
        """
        Generate clarification questions based on query and intent.
        
        Args:
            query: User query
            intent: Detected intent
            
        Returns:
            List of questions to ask
        """
        questions: List[ClarificationQuestion] = []
        
        # Generic unclear intent question
        if not intent or intent == "unknown":
            questions.append(
                ClarificationQuestion(
                    question="Was möchten Sie tun?",
                    context=f"Ihre Anfrage: '{query}'",
                    expected_type="text",
                    metadata={"data_key": "clarified_intent"},
                )
            )
        
        # Intent-specific questions
        elif intent:
            required_params = self._get_required_params(intent)
            for param in required_params:
                questions.append(
                    ClarificationQuestion(
                        question=f"Bitte geben Sie {param} an:",
                        context=f"Für '{intent}'",
                        expected_type="text",
                        metadata={"data_key": param},
                    )
                )
        
        return questions

    def _validate_answer(
        self,
        answer: str,
        question: ClarificationQuestion,
    ) -> str:
        """
        Validate answer based on expected type.
        
        Args:
            answer: User's answer
            question: The question that was asked
            
        Returns:
            Validated/normalized answer
        """
        answer = answer.strip()
        
        if question.expected_type == "yes_no":
            answer_lower = answer.lower()
            if answer_lower in ("ja", "yes", "y", "j"):
                return "yes"
            elif answer_lower in ("nein", "no", "n"):
                return "no"
            else:
                # Keep original if unclear
                logger.warning(f"Ambiguous yes/no answer: {answer}")
                return answer
        
        elif question.expected_type == "choice" and question.options:
            # Try to match to one of the options
            answer_lower = answer.lower()
            for option in question.options:
                if answer_lower == option.lower() or answer_lower in option.lower():
                    return option
            logger.warning(f"Answer '{answer}' not in options: {question.options}")
        
        elif question.expected_type == "number":
            try:
                # Try to extract number
                import re
                numbers = re.findall(r'\d+', answer)
                if numbers:
                    return numbers[0]
            except Exception:
                pass
        
        return answer

    def _get_required_params(self, intent: str) -> List[str]:
        """
        Get required parameters for a given intent.
        
        Args:
            intent: The intent
            
        Returns:
            List of required parameter names
        """
        # This would typically come from a configuration file
        # For now, return common parameters based on intent
        param_map: Dict[str, List[str]] = {
            "send_email": ["recipient", "subject", "body"],
            "set_reminder": ["time", "message"],
            "create_event": ["title", "time", "location"],
            "search": ["query"],
            "play_music": ["song"],
            "weather": ["location"],
        }
        
        return param_map.get(intent, [])


__all__ = ["ClarificationModule", "ClarificationQuestion", "ClarificationContext"]
