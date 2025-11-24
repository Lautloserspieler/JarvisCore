"""Clarification plugin to handle ambiguous user requests."""

from __future__ import annotations

import hashlib
import random
from datetime import datetime
from typing import Dict, Any, Optional

from core.clarification_module import ClarificationModule
from plugins.conversation_plugin_base import ConversationPlugin
from utils.logger import Logger


class ClarificationPlugin(ConversationPlugin):
    """Triggers follow-up questions when a command is ambiguous."""

    plugin_name = "clarification"

    def __init__(self, logger: Optional[Logger] = None) -> None:
        super().__init__(self.plugin_name)
        self.logger = logger or Logger()
        self.module = ClarificationModule()
        self._pending_command_id: Optional[str] = None
        self._pending_command_text: Optional[str] = None
        self._suggestion_templates = [
            "Meinten Sie mit '{command}' vielleicht einen bestimmten Namen oder Ort?",
            "'{command}' klingt noch unklar - nennen Sie mir bitte das genaue Ziel.",
            "Ich habe '{command}' verstanden, aber was genau soll ich verwenden?",
        ]
        self._ack_templates = [
            "Alles klar, ich leite '{resolved}' ein.",
            "Verstanden - ich kuemmere mich um '{resolved}'.",
            "Danke fuer die Praezisierung. Ich erledige '{resolved}'.",
        ]
        self._action_keywords = {"oeffne", "schliesse", "starte", "beende", "suche", "berechne", "spiele"}

    def on_user_message(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        message = message.strip()
        if not message:
            return None

        command_id = self._command_id(message)
        history = context.get("conversation_history", [])

        if self._pending_command_id and command_id != self._pending_command_id:
            pending = self.module.get_pending_command(self._pending_command_id)
            original_command = self._pending_command_text or (pending.get("command") if pending else None)
            if pending and original_command:
                resolved = self._merge_clarification(original_command, message)
                context['override_command'] = resolved
                context['clarification_details'] = {
                    'original': original_command,
                    'clarification': message,
                    'resolved': resolved,
                }
                context['clarification_pending'] = False
                context['clarification_ack'] = random.choice(self._ack_templates).format(resolved=resolved)
                self.logger.debug("Klarstellung uebernommen: %s -> %s", original_command, resolved)
                self._pending_command_id = None
                self._pending_command_text = None
                return None
            self._pending_command_id = None
            self._pending_command_text = None

        needs_clarification, prompt = self.module.needs_clarification(command_id, message, history)
        if not needs_clarification:
            if self._pending_command_id and command_id == self._pending_command_id:
                self.module.clear_pending_command(self._pending_command_id)
                self._pending_command_id = None
                self._pending_command_text = None
            return None

        clarification_prompt = prompt or random.choice(self._suggestion_templates).format(command=message)
        self.module.store_pending_command(
            command_id,
            message,
            {
                "timestamp": datetime.now().isoformat(),
                "context": history[-3:] if history else [],
            },
        )
        context['clarification_pending'] = True
        context['clarification_details'] = {
            'original': message,
            'hint': clarification_prompt,
        }
        self._pending_command_id = command_id
        self._pending_command_text = message
        self.logger.debug("Rueckfrage ausgeloest fuer '%s'", message)
        return clarification_prompt

    def on_assistant_message(self, message: str, context: Dict[str, Any]) -> None:
        if not self._pending_command_id:
            return
        remaining = self.module.get_remaining_attempts(self._pending_command_id)
        if remaining <= 0:
            self.module.clear_pending_command(self._pending_command_id)
            self._pending_command_id = None
            self._pending_command_text = None
            context['clarification_pending'] = False

    def get_context(self) -> Dict[str, Any]:
        if not self._pending_command_id:
            return {}
        return {
            "clarification_pending": True,
            "remaining_attempts": self.module.get_remaining_attempts(self._pending_command_id),
        }

    def shutdown(self) -> None:  # pragma: no cover - best-effort cleanup
        if self._pending_command_id:
            self.module.clear_pending_command(self._pending_command_id)
        self._pending_command_id = None
        self._pending_command_text = None

    @staticmethod
    def _command_id(command: str) -> str:
        digest = hashlib.md5(command.encode("utf-8"))
        return digest.hexdigest()

    def _merge_clarification(self, original: str, clarification: str) -> str:
        clarification_lower = clarification.lower()
        if any(keyword in clarification_lower for keyword in self._action_keywords):
            return clarification
        trimmed_original = original.rstrip().rsplit(' ', 1)
        if trimmed_original and trimmed_original[-1].lower() in {"das", "es", "ihn", "sie", "ihm"}:
            base = ' '.join(trimmed_original[:-1]) or original
        else:
            base = original
        merged = f"{base} {clarification}".strip()
        return merged
