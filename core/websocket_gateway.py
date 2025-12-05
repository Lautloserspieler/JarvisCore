"""
WebSocket-Gateway fuer die Fernsteuerung von J.A.R.V.I.S.

Erlaubt Web-Clients, Textbefehle zu senden und Status-Updates zu abonnieren.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import threading
import time
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Any, Dict, Optional, Set

import requests
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from websockets.server import WebSocketServerProtocol, serve


class GatewayServiceClient:
    """HTTP-Client fuer den Go-basierten gatewayd-Server."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        *,
        logger: Optional[Any] = None,
        timeout: float = 5.0,
    ) -> None:
        self.logger = logger
        env_disable = os.getenv("JARVIS_GATEWAYD_ENABLED")
        disable_flag = env_disable is not None and env_disable.strip().lower() in {"0", "false", "no"}
        chosen_url = base_url or os.getenv("JARVIS_GATEWAYD_URL") or "http://127.0.0.1:7081"
        if disable_flag:
            chosen_url = ""
        self.base_url = chosen_url.rstrip("/") if chosen_url else ""
        self.token = token or os.getenv("JARVIS_GATEWAYD_TOKEN") or os.getenv("GATEWAYD_TOKEN")
        self.timeout = timeout
        self.enabled = bool(self.base_url)
        self.session = requests.Session()

    @classmethod
    def from_settings(cls, settings: Dict[str, Any] | None, logger: Optional[Any] = None) -> "GatewayServiceClient":
        settings = settings or {}
        gateway_cfg = settings.get("gatewayd") or settings.get("go_services") or {}
        if isinstance(gateway_cfg, dict) and "gatewayd" in gateway_cfg:
            gateway_cfg = gateway_cfg.get("gatewayd") or {}
        url = gateway_cfg.get("base_url") or gateway_cfg.get("url")
        token = gateway_cfg.get("token") or gateway_cfg.get("api_key")
        timeout = float(gateway_cfg.get("timeout_seconds", 5.0)) if isinstance(gateway_cfg, dict) else 5.0
        return cls(base_url=url, token=token, timeout=timeout, logger=logger)

    def broadcast(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        if not self.enabled:
            return False
        url = f"{self.base_url}/api/events"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-API-Key"] = self.token
        body = {
            "type": event_type,
            "timestamp": time.time(),
            "payload": payload or {},
        }
        try:
            resp = self.session.post(url, json=body, headers=headers, timeout=self.timeout)
            if resp.status_code >= 400:
                if self.logger:
                    self.logger.debug(f"gatewayd Broadcast fehlgeschlagen: {resp.status_code} {resp.text}")
                return False
            return True
        except Exception as exc:
            if self.logger:
                self.logger.debug(f"gatewayd Broadcast nicht erreichbar: {exc}")
            return False


class RemoteCommandGateway:
    """Asynchrones WebSocket-Gateway fuer Jarvis."""

    def __init__(self, jarvis: Any, config: Dict[str, Any], *, logger: Any) -> None:
        self.jarvis = jarvis
        self.logger = logger
        self.config = config or {}
        self.enabled = bool(self.config.get("enabled", False))
        self.host = str(self.config.get("host") or "127.0.0.1")
        self.port = int(self.config.get("port") or 8765)
        raw_token = self.config.get("token")
        token_str = str(raw_token).strip() if raw_token is not None else ""
        self.token = token_str or None
        self.broadcast_conversation = bool(self.config.get("broadcast_conversation", True))
        self.allow_status_queries = bool(self.config.get("allow_status_queries", True))
        timeout = self.config.get("command_timeout_seconds", 45.0)
        self.command_timeout = float(timeout if timeout is not None else 45.0)
        self.gateway_client = GatewayServiceClient.from_settings(self.config, logger=self.logger)
        forward_only_env = os.getenv("JARVIS_GATEWAYD_ONLY", "").strip().lower()
        self.forward_only_gatewayd = forward_only_env in {"1", "true", "yes"} or bool(self.config.get("gatewayd_only", False))

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.server: Optional[asyncio.base_events.Server] = None
        self.thread: Optional[threading.Thread] = None
        self._clients: Set[WebSocketServerProtocol] = set()
        self._authorized: Set[WebSocketServerProtocol] = set()
        self._ready_event = threading.Event()

    # -- Lifecycle -----------------------------------------------------
    def start(self) -> None:
        # Wenn Go-gatewayd genutzt werden soll, muss der Python-Server nicht laufen
        if not self.enabled:
            return
        if self.forward_only_gatewayd and self.gateway_client and self.gateway_client.enabled:
            # Nur Forwarding an gatewayd, kein lokaler WS-Server
            return
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run_loop, name="JarvisRemoteGateway", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self._ready_event.clear()
        loop = self.loop
        if not loop:
            return
        try:
            asyncio.run_coroutine_threadsafe(self._close_clients(), loop).result(timeout=2)
        except Exception:
            pass
        if self.server:
            self.server.close()
            with contextlib.suppress(Exception):
                asyncio.run_coroutine_threadsafe(self.server.wait_closed(), loop).result(timeout=2)
        loop.call_soon_threadsafe(loop.stop)
        if self.thread:
            self.thread.join(timeout=2)
        self.thread = None
        self.loop = None
        self.server = None
        self._clients.clear()
        self._authorized.clear()

    def mark_ready(self) -> None:
        if self.enabled:
            self._ready_event.set()

    def mark_not_ready(self) -> None:
        self._ready_event.clear()

    def publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Sendet Ereignisse an verbundene Clients."""
        # Zuerst optional an gatewayd weiterleiten (Go-Service)
        forwarded = False
        try:
            if self.gateway_client and self.gateway_client.enabled:
                forwarded = self.gateway_client.broadcast(event_type, payload)
        except Exception:
            forwarded = False

        if not self.enabled or not self.loop or not self._ready_event.is_set():
            if self.forward_only_gatewayd and forwarded:
                return
            return
        if event_type in ("user_message", "assistant_message") and not self.broadcast_conversation:
            return
        targets = self._get_targets()
        if not targets:
            return
        message = {
            "type": event_type,
            "timestamp": time.time(),
            "payload": payload or {},
        }
        try:
            data = json.dumps(message, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as exc:
            self.logger.debug("Remote-Event konnte nicht serialisiert werden: %s", exc)
            return
        try:
            asyncio.run_coroutine_threadsafe(self._broadcast(data, targets), self.loop)
        except RuntimeError:
            self.logger.debug("Remote-Event konnte nicht gesendet werden (Loop gestoppt).")

    # -- Internals -----------------------------------------------------
    def _run_loop(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            ws_server = serve(self._handle_connection, self.host, self.port, ping_interval=30, ping_timeout=20)
            self.server = self.loop.run_until_complete(ws_server)
            self.logger.info("Remote-WebSocket laeuft auf ws://%s:%s", self.host, self.port)
            self.loop.run_forever()
        except Exception as exc:
            self.logger.error("WebSocket-Gateway konnte nicht gestartet werden: %s", exc)
        finally:
            with contextlib.suppress(Exception):
                self.loop.run_until_complete(self._close_clients())
            if self.server:
                self.server.close()
                with contextlib.suppress(Exception):
                    self.loop.run_until_complete(self.server.wait_closed())
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            with contextlib.suppress(Exception):
                self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self.loop.close()
            self.loop = None
            self.server = None

    async def _close_clients(self) -> None:
        if not self._clients:
            return
        await asyncio.gather(*(self._safe_close(ws) for ws in list(self._clients)), return_exceptions=True)
        self._clients.clear()
        self._authorized.clear()

    async def _safe_close(self, websocket: WebSocketServerProtocol) -> None:
        with contextlib.suppress(Exception):
            await websocket.close()

    async def _broadcast(self, data: str, targets: Set[WebSocketServerProtocol]) -> None:
        if not targets:
            return
        await asyncio.gather(*(self._safe_send(ws, data) for ws in list(targets)), return_exceptions=True)

    async def _safe_send(self, websocket: WebSocketServerProtocol, data: str) -> None:
        try:
            await websocket.send(data)
        except Exception:
            self._clients.discard(websocket)
            self._authorized.discard(websocket)

    def _get_targets(self) -> Set[WebSocketServerProtocol]:
        if not self.token:
            return set(self._clients)
        return {ws for ws in self._clients if ws in self._authorized}

    # -- Connection Handling ------------------------------------------
    async def _handle_connection(self, websocket: WebSocketServerProtocol, _path: str) -> None:
        client_label = self._format_client(websocket)
        self.logger.info("Remote-Client verbunden: %s", client_label)
        self._clients.add(websocket)
        await self._send_json(
            websocket,
            {
                "type": "welcome",
                "ready": self._ready_event.is_set(),
                "requires_auth": bool(self.token),
                "timestamp": time.time(),
            },
        )
        try:
            async for raw in websocket:
                reply = await self._handle_message(websocket, raw)
                if reply:
                    await self._send_json(websocket, reply)
        except (ConnectionClosedOK, ConnectionClosedError):
            self.logger.info("Remote-Client getrennt: %s", client_label)
        finally:
            self._clients.discard(websocket)
            self._authorized.discard(websocket)

    async def _handle_message(self, websocket: WebSocketServerProtocol, raw: str) -> Dict[str, Any]:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return {"type": "error", "error": "invalid_json", "message": "Payload muss JSON sein."}

        msg_type = str(payload.get("type") or "").lower()

        if self.token and websocket not in self._authorized:
            if msg_type != "auth":
                return {"type": "error", "error": "unauthorized", "message": "Token erforderlich."}

        if msg_type == "auth":
            if not self.token:
                return {"type": "auth", "status": "not_required"}
            provided = payload.get("token")
            if provided == self.token:
                self._authorized.add(websocket)
                return {"type": "auth", "status": "ok"}
            return {"type": "auth", "status": "failed", "message": "Token falsch."}

        if msg_type == "ping":
            return {"type": "pong", "timestamp": time.time(), "ready": self._ready_event.is_set()}
        if msg_type == "status":
            if not self.allow_status_queries:
                return {"type": "error", "error": "forbidden", "message": "Statusabfragen deaktiviert."}
            status = dict(self.jarvis.get_runtime_status())
            status['ready'] = self._ready_event.is_set()
            return {"type": "status", "status": status}

        if not self._ready_event.is_set():
            return {"type": "error", "error": "not_ready", "message": "System initialisiert noch."}
        if msg_type == "command":
            command_text = payload.get("command") or payload.get("text")
            metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            loop = asyncio.get_running_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    self._execute_command_blocking,
                    command_text,
                    metadata,
                )
            except FuturesTimeout:
                return {"type": "command_result", "status": "timeout", "message": "Ausfuehrung zu langsam."}
            except Exception as exc:
                self.logger.error("Remote-Befehl fehlgeschlagen: %s", exc)
                return {"type": "command_result", "status": "error", "message": str(exc)}
            return {"type": "command_result", "status": "ok", "response": response}

        return {"type": "error", "error": "unknown_type", "message": f"Unbekannter Typ: {msg_type}"}

    async def _send_json(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any]) -> None:
        await websocket.send(json.dumps(payload, ensure_ascii=False))

    def _execute_command_blocking(self, command_text: Optional[str], metadata: Dict[str, Any]) -> str:
        cleaned = (command_text or "").strip()
        if not cleaned:
            raise ValueError("Leerer Befehl.")
        return self.jarvis.execute_remote_command(cleaned, metadata=metadata, timeout=self.command_timeout)

    @staticmethod
    def _format_client(websocket: WebSocketServerProtocol) -> str:
        host, port = websocket.remote_address or ("?", "?")
        return f"{host}:{port}"


