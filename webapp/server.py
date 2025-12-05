"""
HTTP + Websocket Webinterface fuer J.A.R.V.I.S.

Stellt ein modernes Web-Dashboard bereit, inkl. Chat-Steuerung.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import threading
import time
import base64
from collections import deque
from io import BytesIO
from pathlib import Path
from typing import Any, Deque, Dict, Optional, Set

from aiohttp import WSMsgType, web
from aiohttp.client_exceptions import ClientConnectionResetError

try:
    import qrcode
except ImportError:  # pragma: no cover - defensive fallback
    qrcode = None


class WebInterfaceServer:
    """AIOHTTP-basierter Server fuer die Weboberflaeche."""

    def __init__(self, jarvis: Any, config: Dict[str, Any], *, logger: Any) -> None:
        self.jarvis = jarvis
        self.logger = logger
        self.config = config or {}
        self.enabled = bool(self.config.get("enabled", False))
        self.host = str(self.config.get("host") or "127.0.0.1")
        self.port = int(self.config.get("port") or 8080)
        raw_token = self.config.get("token")
        # Token immer als String behandeln, damit auch numerische Tokens funktionieren
        if raw_token is None:
            self.token = None
        else:
            try:
                self.token = str(raw_token).strip() or None
            except Exception:
                self.token = None
        self.allow_guest_commands = bool(self.config.get("allow_guest_commands", False))
        timeout = self.config.get("command_timeout_seconds", 45.0)
        self.command_timeout = float(timeout if timeout is not None else 45.0)
        whitelist = self.config.get("allowed_ips") or []
        self.allowed_ips: Set[str] = {str(entry).strip() for entry in whitelist if str(entry).strip()}
        self._rate_limit_window = int(self.config.get("rate_limit_window_seconds", 60) or 60)
        if self._rate_limit_window <= 0:
            self._rate_limit_window = 60
        self._rate_limit_max_requests = int(self.config.get("rate_limit_max_requests", 0) or 0)
        self._rate_limit_buckets: Dict[str, Deque[float]] = {}

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.thread: Optional[threading.Thread] = None
        self._clients: Set[web.WebSocketResponse] = set()
        self._telemetry_task: Optional[asyncio.Task] = None
        self._ready_event = threading.Event()
        self._static_root = Path(__file__).resolve().parent / "static"
        if self.enabled and not self.token:
            self.logger.error("Web-Interface deaktiviert: Zugriffstoken fehlt in der Konfiguration.")
            self.enabled = False

    # Lifecycle ---------------------------------------------------------
    def start(self) -> None:
        if not self.enabled:
            return
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run_loop, name="JarvisWebUI", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self._ready_event.clear()
        loop = self.loop
        if not loop:
            return

        async def _shutdown() -> None:
            await self._close_clients()
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()

        try:
            asyncio.run_coroutine_threadsafe(_shutdown(), loop).result(timeout=3)
        except Exception:
            pass
        loop.call_soon_threadsafe(loop.stop)
        if self.thread:
            self.thread.join(timeout=3)
        self.thread = None
        self.loop = None
        self.runner = None
        self.site = None
        self._clients.clear()

    def mark_ready(self) -> None:
        if self.enabled:
            self._ready_event.set()
            self.publish("status", {"state": "ready"})

    def mark_not_ready(self) -> None:
        self._ready_event.clear()

    def wait_until_ready(self, timeout: Optional[float] = None) -> bool:
        if not self.enabled:
            return False
        return self._ready_event.wait(timeout)

    def publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled or not self.loop:
            return
        message = {
            "type": event_type,
            "timestamp": time.time(),
            "payload": payload or {},
        }
        try:
            asyncio.run_coroutine_threadsafe(self._broadcast(message), self.loop)
        except RuntimeError:
            self.logger.debug("Web-Event konnte nicht gesendet werden (Loop gestoppt).")

    # Internal operations ----------------------------------------------
    def _run_loop(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.app = self._build_app()
            self.runner = web.AppRunner(self.app)
            self.loop.run_until_complete(self.runner.setup())
            self.site = web.TCPSite(self.runner, host=self.host, port=self.port)
            self.loop.run_until_complete(self.site.start())
            self._telemetry_task = self.loop.create_task(self._telemetry_loop())
            self.logger.info("Web-UI erreichbar unter http://%s:%s", self.host, self.port)
            self.loop.run_forever()
        except Exception as exc:
            self.logger.error("Web-UI konnte nicht gestartet werden: %s", exc)
        finally:
            if self._telemetry_task:
                self._telemetry_task.cancel()
                with contextlib.suppress(Exception):
                    self.loop.run_until_complete(self._telemetry_task)
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            with contextlib.suppress(Exception):
                self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self.loop.close()
            self.loop = None

    def _build_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/", self._handle_index)
        app.router.add_get("/static/{path:.*}", self._handle_static)
        app.router.add_get("/events", self._handle_events)
        app.router.add_get("/api/status", self._handle_status)
        app.router.add_get("/api/context", self._handle_context)
        app.router.add_get("/api/logs", self._handle_logs)
        app.router.add_post("/api/command", self._handle_command)
        app.router.add_get("/api/system/metrics", self._handle_system_metrics)
        app.router.add_post("/api/system/speedtest", self._handle_speedtest)
        app.router.add_get("/api/system/speedtest", self._handle_speedtest)
        app.router.add_get("/api/models", self._handle_models)
        app.router.add_post("/api/models", self._handle_model_action)
        app.router.add_get("/api/training", self._handle_training_status)
        app.router.add_post("/api/training/run", self._handle_training_run)
        app.router.add_get("/api/chat/history", self._handle_chat_history)
        app.router.add_get("/api/tts/settings", self._handle_tts_settings_get)
        app.router.add_post("/api/tts/settings", self._handle_tts_settings_post)
        app.router.add_get("/api/settings", self._handle_settings_snapshot)
        app.router.add_post("/api/settings", self._handle_settings_update)
        app.router.add_get("/api/audio/devices", self._handle_audio_devices)
        app.router.add_post("/api/audio/devices", self._handle_audio_set)
        app.router.add_post("/api/audio/measure", self._handle_audio_measure)
        app.router.add_get("/api/speech/status", self._handle_speech_status)
        app.router.add_post("/api/speech/control", self._handle_speech_control)
        app.router.add_get("/api/knowledge/stats", self._handle_knowledge_stats)
        app.router.add_get("/api/crawler/status", self._handle_crawler_status)
        app.router.add_post("/api/crawler/jobs", self._handle_crawler_job_create)
        app.router.add_post("/api/crawler/sync", self._handle_crawler_sync)
        app.router.add_post("/api/crawler/control", self._handle_crawler_control)
        app.router.add_get("/api/crawler/documents", self._handle_crawler_documents)
        app.router.add_get("/api/crawler/config", self._handle_crawler_config)
        app.router.add_post("/api/crawler/config", self._handle_crawler_config_update)
        app.router.add_post("/api/crawler/security", self._handle_crawler_security)
        app.router.add_get("/api/plugins", self._handle_plugins_overview)
        app.router.add_post("/api/plugins", self._handle_plugins_update)
        app.router.add_get("/api/commands", self._handle_commands_list)
        app.router.add_post("/api/commands", self._handle_commands_create)
        app.router.add_get("/api/memory", self._handle_memory_snapshot)
        app.router.add_post("/api/logs/clear", self._handle_logs_clear)
        app.router.add_get("/api/security/status", self._handle_security_status)
        app.router.add_post("/api/security/role", self._handle_security_role)
        app.router.add_post("/api/security/safe-mode", self._handle_security_safe_mode)
        app.router.add_get("/api/security/authenticator/qr", self._handle_authenticator_qr)
        app.router.add_post("/api/security/authenticator/init", self._handle_authenticator_init)
        app.router.add_post("/api/security/authenticator/confirm", self._handle_authenticator_confirm)
        app.router.add_post("/api/security/authenticator/verify", self._handle_authenticator_verify)
        app.router.add_post("/api/security/voice/enroll", self._handle_voice_enroll)
        app.router.add_post("/api/feedback", self._handle_feedback)
        return app

    async def _broadcast(self, message: Dict[str, Any]) -> None:
        if not self._clients:
            return
        try:
            data = json.dumps(message, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as exc:
            self.logger.debug("Web-Event konnte nicht serialisiert werden: %s", exc)
            return
        await asyncio.gather(
            *(self._safe_ws_send(client, data) for client in list(self._clients)),
            return_exceptions=True,
        )

    async def _safe_ws_send(self, ws: web.WebSocketResponse, data: str) -> None:
        if ws.closed:
            self._clients.discard(ws)
            return
        try:
            await ws.send_str(data)
        except Exception:
            self._clients.discard(ws)

    async def _close_clients(self) -> None:
        if not self._clients:
            return
        await asyncio.gather(*(client.close() for client in list(self._clients)), return_exceptions=True)
        self._clients.clear()

    # Request handlers --------------------------------------------------
    async def _handle_index(self, request: web.Request) -> web.StreamResponse:
        index_path = self._static_root / "index.html"
        if index_path.exists():
            return web.FileResponse(index_path)
        return web.Response(text="Web-Interface wurde nicht gefunden.", content_type="text/plain")

    async def _handle_static(self, request: web.Request) -> web.StreamResponse:
        rel_path = request.match_info.get("path", "")
        safe_path = (self._static_root / rel_path).resolve()
        if self._static_root not in safe_path.parents and safe_path != self._static_root:
            raise web.HTTPNotFound()
        if not safe_path.exists() or not safe_path.is_file():
            raise web.HTTPNotFound()
        return web.FileResponse(safe_path)

    async def _handle_events(self, request: web.Request) -> web.StreamResponse:
        if not self._authorize_read(request):
            raise web.HTTPUnauthorized()
        ws = web.WebSocketResponse(heartbeat=30)
        try:
            await ws.prepare(request)
        except ClientConnectionResetError:
            # Browser hat die Verbindung unmittelbar geschlossen; still ignore
            return web.Response(status=499, text="Client closed connection")
        except ConnectionResetError:
            return web.Response(status=499, text="Connection reset by peer")
        except Exception as exc:
            self.logger.debug("Websocket konnte nicht vorbereitet werden: %s", exc)
            return web.Response(status=500, text="Websocket init failed")
        self._clients.add(ws)
        await ws.send_json({"type": "welcome", "ready": self._ready_event.is_set()})
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT and msg.data == "ping":
                    await ws.send_json({"type": "pong", "timestamp": time.time()})
                elif msg.type == WSMsgType.ERROR:
                    break
        finally:
            self._clients.discard(ws)
        return ws

    async def _handle_status(self, request: web.Request) -> web.Response:
        if not self._check_network_guards(request):
            return self._unauthorized()
        requires_token = not self.jarvis.requires_authenticator_setup()
        if requires_token and not (self._verify_token(request) or self._allow_guest(request)):
            return self._unauthorized()
        payload = self._collect_status_payload()
        return web.json_response({"status": "ok", "data": payload})

    async def _handle_context(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        context = self.jarvis.get_context_snapshot()
        history = self.jarvis.get_conversation_history(limit=50)
        ready = self._ready_event.is_set()
        return web.json_response(
            {
                "status": "ok",
                "context": context,
                "history": history,
                "ready": ready,
            }
        )

    async def _handle_logs(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        lines = max(10, min(500, int(request.query.get("lines", 150))))
        needle = (request.query.get("q") or "").strip().lower()
        log_path = Path("logs/jarvis.log")
        if not log_path.exists():
            return web.json_response({"status": "ok", "logs": []})
        try:
            content = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            if needle:
                filtered = [line for line in content if needle in line.lower()]
                data = filtered[-lines:]
            else:
                data = content[-lines:]
        except Exception as exc:
            self.logger.debug("Logdatei konnte nicht gelesen werden: %s", exc)
            data = []
        return web.json_response({"status": "ok", "logs": data})

    async def _handle_command(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        if self.jarvis.requires_authenticator_setup():
            return web.json_response(
                {
                    "status": "error",
                    "message": "Authenticator muss zuerst eingerichtet werden.",
                    "security": self.jarvis.get_security_status(),
                },
                status=428,
            )
        if self.jarvis.requires_voice_enrollment():
            return web.json_response(
                {
                    "status": "error",
                    "message": "Stimmmuster fehlt. Bitte erst in der Web-UI anlegen.",
                    "security": self.jarvis.get_security_status(),
                },
                status=428,
            )
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        command_text = (data.get("command") or data.get("text") or "").strip()
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        if not command_text:
            return web.json_response({"status": "error", "message": "Kein Befehl uebermittelt."}, status=400)
        loop = asyncio.get_running_loop()
        try:
            response = await loop.run_in_executor(
                None,
                self._execute_command_sync,
                command_text,
                metadata,
            )
        except Exception as exc:
            self.logger.error("Web-Befehl fehlgeschlagen: %s", exc)
            return web.json_response({"status": "error", "message": str(exc)}, status=500)
        return web.json_response({"status": "ok", "response": response})

    async def _handle_system_metrics(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        include_details = request.query.get("details", "false").lower() in ("1", "true", "yes", "on")
        metrics = self.jarvis.get_system_metrics(include_details=include_details)
        runtime = self.jarvis.get_runtime_status()
        runtime["ready"] = self._ready_event.is_set()
        return web.json_response({"status": "ok", "metrics": metrics, "runtime": runtime})

    async def _handle_speedtest(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        monitor = getattr(self.jarvis, "system_monitor", None)
        if not monitor:
            return web.json_response({"status": "error", "message": "Systemmonitor nicht verfuegbar."}, status=500)
        result = monitor.get_speedtest()
        return web.json_response({"status": "ok", "result": result})

    async def _handle_models(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        return web.json_response({"status": "ok", "models": self.jarvis.get_llm_status()})

    async def _handle_model_action(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        action = payload.get("action")
        model_key = payload.get("model")
        try:
            if action == "download":
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, self.jarvis.control_llm_model, action, model_key
                )
            else:
                result = self.jarvis.control_llm_model(action, model_key=model_key)
        except Exception as exc:
            return web.json_response({"status": "error", "message": str(exc)}, status=400)
        return web.json_response({"status": "ok", "result": result})

    async def _handle_training_status(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        return web.json_response({"status": "ok", "training": self.jarvis.get_training_snapshot()})

    async def _handle_training_run(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        result = self.jarvis.run_training_cycle()
        return web.json_response({"status": "ok", "result": result})

    async def _handle_feedback(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        score = float(payload.get("score", 0.0) or 0.0)
        message = payload.get("message") or self.jarvis.get_last_assistant_message() or ""
        correction = payload.get("correction")
        intent = payload.get("intent")
        if not message:
            return web.json_response({"status": "error", "message": "Kein Nachrichteninhalt"}, status=400)
        entry = self.jarvis.record_feedback(score, message, correction=correction, intent=intent)
        return web.json_response({"status": "ok", "feedback": entry})

    async def _handle_chat_history(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        try:
            limit = int(request.query.get("limit", "25") or 25)
        except ValueError:
            limit = 25
        limit = max(1, min(200, limit))
        history = self.jarvis.get_conversation_history(limit=limit)
        return web.json_response({"status": "ok", "history": history})

    async def _handle_tts_settings_get(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        settings = self.jarvis.get_tts_settings()
        return web.json_response({"status": "ok", "settings": settings})

    async def _handle_tts_settings_post(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        if not isinstance(payload, dict) or "stream_enabled" not in payload:
            return web.json_response({"status": "error", "message": "stream_enabled wird benoetigt."}, status=400)
        state = self.jarvis.set_tts_stream_enabled(bool(payload.get("stream_enabled")))
        return web.json_response({"status": "ok", "settings": {"stream_enabled": state}})

    async def _handle_settings_snapshot(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        return web.json_response({"status": "ok", "settings": self.jarvis.get_settings_snapshot()})

    async def _handle_settings_update(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        updated = self.jarvis.apply_settings_from_payload(payload or {})
        return web.json_response({"status": "ok", "updated": bool(updated)})

    async def _handle_audio_devices(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        return web.json_response({"status": "ok", **self.jarvis.list_audio_devices()})

    async def _handle_audio_set(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        name = payload.get("name")
        index = payload.get("index")
        success = self.jarvis.set_audio_device(name=name, index=index)
        return web.json_response({"status": "ok", "success": success})

    async def _handle_audio_measure(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        duration = float(payload.get("duration", 1.5))
        level = self.jarvis.sample_audio_level(duration=duration)
        if level is None:
            return web.json_response({"status": "error", "message": "Pegel konnte nicht gemessen werden."}, status=500)
        return web.json_response({"status": "ok", "level": level})

    async def _handle_speech_status(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        status = self.jarvis.get_speech_status()
        return web.json_response({"status": "ok", "speech": status})

    async def _handle_speech_control(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        action = str(payload.get("action") or "").strip().lower()
        if action not in {"start", "stop", "wake_word"}:
            return web.json_response({"status": "error", "message": "Unbekannte Aktion."}, status=400)
        try:
            if action == "start":
                success = bool(self.jarvis.start_listening())
            elif action == "stop":
                success = bool(self.jarvis.stop_listening())
            else:
                enabled = bool(payload.get("enabled", False))
                success = bool(self.jarvis.set_wake_word_enabled(enabled))
        except Exception as exc:
            self.logger.error("Sprachsteuerung fehlgeschlagen (%s): %s", action, exc)
            return web.json_response({"status": "error", "message": "Sprachsteuerung fehlgeschlagen."}, status=500)
        speech_status = self.jarvis.get_speech_status()
        try:
            self.jarvis._publish_remote_event("status", self.jarvis.get_runtime_status())
        except Exception:
            pass
        return web.json_response({"status": "ok", "success": success, "speech": speech_status})

    async def _handle_knowledge_stats(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        stats = self.jarvis.get_knowledge_statistics()
        return web.json_response({"status": "ok", "stats": stats or {}})

    async def _handle_crawler_status(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        try:
            crawler_status = self.jarvis.get_crawler_status()
        except Exception as exc:
            self.logger.warning("Crawlerstatus nicht verfuegbar: %s", exc)
            return web.json_response({"status": "error", "message": "Crawlerstatus nicht verfuegbar."}, status=500)
        return web.json_response({"status": "ok", "crawler": crawler_status})

    async def _handle_crawler_job_create(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        topic = str(payload.get("topic") or "").strip()
        start_urls = payload.get("start_urls")
        if not isinstance(start_urls, list):
            start_urls = []
        cleaned_urls = [str(url).strip() for url in start_urls if str(url).strip()]
        try:
            max_pages = int(payload.get("max_pages") or 50)
            max_depth = int(payload.get("max_depth") or 1)
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltige Limits."}, status=400)
        if not topic or not cleaned_urls:
            return web.json_response({"status": "error", "message": "Topic und Start-URLs sind erforderlich."}, status=400)
        job_id = self.jarvis.start_crawler_job(topic, cleaned_urls, max_pages=max_pages, max_depth=max_depth)
        if not job_id:
            return web.json_response({"status": "error", "message": "Crawler-Service nicht aktiviert."}, status=503)
        return web.json_response({"status": "ok", "job_id": job_id})

    async def _handle_crawler_sync(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        result = self.jarvis.run_crawler_sync_now()
        return web.json_response({"status": "ok", "result": result})

    async def _handle_crawler_control(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        action = str(payload.get("action") or "").strip().lower()
        if action not in {"pause", "resume"}:
            return web.json_response({"status": "error", "message": "Ungueltige Aktion."}, status=400)
        success = self.jarvis.control_crawler(action)
        if not success:
            return web.json_response({"status": "error", "message": "Crawler-Service nicht erreichbar."}, status=502)
        return web.json_response({"status": "ok", "action": action})

    async def _handle_crawler_documents(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        try:
            limit = int(request.query.get("limit", "50") or 50)
        except ValueError:
            limit = 50
        limit = max(1, min(100, limit))
        recent_only = request.query.get("recent", "false").lower() in {"1", "true", "yes"}
        try:
            documents = self.jarvis.get_crawler_documents(limit=limit, only_recent=recent_only)
        except Exception as exc:
            self.logger.warning("Crawler-Dokumente konnten nicht geladen werden: %s", exc)
            return web.json_response({"status": "error", "message": "Dokumente nicht verfuegbar."}, status=500)
        return web.json_response({"status": "ok", "documents": documents})

    async def _handle_crawler_config(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        return web.json_response(
            {
                "status": "ok",
                "config": self.jarvis.get_crawler_service_config(),
                "client": self.jarvis.get_crawler_client_settings(),
                "security": self.jarvis.get_crawler_security_status(),
            }
        )

    async def _handle_crawler_config_update(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        service_config = payload.get("service_config") or {}
        client_settings = payload.get("client_settings") or {}
        success_service = True
        success_client = True
        if service_config:
            success_service = self.jarvis.update_crawler_service_config(service_config)
        if client_settings:
            success_client = self.jarvis.update_crawler_client_settings(client_settings)
        if not (success_service and success_client):
            return web.json_response({"status": "error", "message": "Einstellungen konnten nicht gespeichert werden."}, status=500)
        return web.json_response(
            {
                "status": "ok",
                "config": self.jarvis.get_crawler_service_config(),
                "client": self.jarvis.get_crawler_client_settings(),
            }
        )

    async def _handle_crawler_security(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        mode = str(payload.get("mode") or "").lower()
        if mode not in {"allow", "block"}:
            return web.json_response({"status": "error", "message": "Unbekannter Modus."}, status=400)
        self.jarvis.set_crawler_safe_mode(mode)
        return web.json_response({"status": "ok", "security": self.jarvis.get_crawler_security_status()})

    async def _handle_commands_list(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        commands = self.jarvis.list_custom_commands()
        return web.json_response({"status": "ok", "commands": commands})

    async def _handle_commands_create(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        pattern = str(payload.get("pattern") or "").strip()
        response = str(payload.get("response") or "").strip()
        category = str(payload.get("category") or "custom").strip()
        if not pattern or not response:
            return web.json_response({"status": "error", "message": "Pattern und Antwort sind erforderlich."}, status=400)
        try:
            success = self.jarvis.add_custom_command_entry(pattern, response, category=category or "custom")
        except ValueError as exc:
            return web.json_response({"status": "error", "message": str(exc)}, status=400)
        except Exception as exc:
            self.logger.error("Custom-Command konnte nicht angelegt werden: %s", exc)
            return web.json_response({"status": "error", "message": "Befehl konnte nicht angelegt werden."}, status=500)
        return web.json_response({"status": "ok", "success": bool(success)})

    async def _handle_plugins_overview(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        plugins = self.jarvis.get_plugin_overview()
        return web.json_response({"status": "ok", "plugins": plugins})

    async def _handle_plugins_update(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        name = str(payload.get("name") or "").strip()
        action = str(payload.get("action") or "").strip().lower()
        if not name or action not in {"enable", "disable", "reload"}:
            return web.json_response({"status": "error", "message": "Name oder Aktion fehlt."}, status=400)
        if action == "reload":
            success = self.jarvis.reload_plugin(name)
        else:
            success = self.jarvis.set_plugin_state(name, action == "enable")
        if not success:
            return web.json_response({"status": "error", "message": "Plugin-Aktion fehlgeschlagen."}, status=400)
        return web.json_response(
            {
                "status": "ok",
                "success": True,
                "plugins": self.jarvis.get_plugin_overview(),
            }
        )

    async def _handle_memory_snapshot(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        try:
            limit = int(request.query.get("limit", "12") or 12)
        except ValueError:
            limit = 12
        limit = max(1, min(50, limit))
        query = (request.query.get("q") or "").strip()
        snapshot = self.jarvis.get_memory_snapshot(limit=limit, query=query or None)
        return web.json_response(
            {
                "status": "ok",
                "memory": snapshot,
                "query": query or None,
            }
        )

    async def _handle_logs_clear(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        if self.jarvis.clear_logs():
            return web.json_response({"status": "ok"})
        return web.json_response({"status": "error", "message": "Logs konnten nicht geleert werden."}, status=500)

    async def _handle_security_status(self, request: web.Request) -> web.Response:
        if not self._check_network_guards(request):
            return self._unauthorized()
        needs_setup = self.jarvis.requires_authenticator_setup()
        if not needs_setup and not (self._verify_token(request) or self._allow_guest(request)):
            return self._unauthorized()
        status = self.jarvis.get_security_status()
        return web.json_response({"status": "ok", "security": status})

    async def _handle_security_role(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        role = str(payload.get("role") or "").strip().lower()
        level = str(payload.get("level") or "").strip().lower() or None
        if not role:
            return web.json_response({"status": "error", "message": "Rolle fehlt."}, status=400)
        valid_roles = getattr(self.jarvis.security_manager.access_controller, "ROLE_THRESHOLDS", {}) or {}
        if role not in valid_roles:
            return web.json_response({"status": "error", "message": "Unbekannte Rolle."}, status=400)
        if level:
            valid_levels = {"low", "normal", "elevated", "critical"}
            if level not in valid_levels:
                return web.json_response({"status": "error", "message": "Unbekannte Sicherheitsstufe."}, status=400)
        status = self.jarvis.set_security_profile(role=role, level=level)
        return web.json_response({"status": "ok", "security": status})

    async def _handle_security_safe_mode(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        action = str(payload.get("action") or "status").strip().lower()
        reasons = payload.get("reasons") if isinstance(payload, dict) else None
        if action == "enter":
            result = self.jarvis.enter_safe_mode(reasons=reasons if isinstance(reasons, list) else None)
        elif action == "exit":
            result = self.jarvis.exit_safe_mode()
        else:
            result = self.jarvis.get_safe_mode_status()
        return web.json_response({"status": "ok", "safe_mode": result, "security": self.jarvis.get_security_status()})

    async def _handle_authenticator_qr(self, request: web.Request) -> web.Response:
        if not self._check_network_guards(request):
            return self._unauthorized()
        needs_setup = self.jarvis.requires_authenticator_setup()
        if not needs_setup and not (self._verify_token(request) or self._allow_guest(request)):
            return self._unauthorized()
        if qrcode is None:
            self.logger.error("qrcode Bibliothek nicht installiert.")
            return web.json_response({"status": "error", "message": "QR-Code Bibliothek nicht verfügbar."}, status=500)
        payload = self.jarvis.get_pending_authenticator_setup()
        if not payload or not payload.get("provisioning_uri"):
            return web.json_response({"status": "error", "message": "Kein Authenticator-Setup aktiv."}, status=404)
        try:
            provision_uri = payload["provisioning_uri"]
            qr_builder = qrcode.QRCode(version=1, box_size=8, border=4)
            qr_builder.add_data(provision_uri)
            qr_builder.make(fit=True)
            image = qr_builder.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            data = buffer.getvalue()
        except Exception as exc:
            self.logger.error("QR-Code konnte nicht generiert werden: %s", exc)
            return web.json_response({"status": "error", "message": "QR-Code konnte nicht generiert werden."}, status=500)
        headers = {
            "Cache-Control": "no-store, max-age=0",
            "X-Content-Type-Options": "nosniff",
        }
        return web.Response(body=data, content_type="image/png", headers=headers)

    async def _handle_authenticator_init(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = self.jarvis.begin_authenticator_setup()
        except RuntimeError as exc:
            return web.json_response({"status": "error", "message": str(exc)}, status=400)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Authenticator-Setup konnte nicht gestartet werden: %s", exc)
            return web.json_response({"status": "error", "message": "Setup konnte nicht gestartet werden."}, status=500)
        return web.json_response({
            "status": "ok",
            "authenticator": payload,
            "security": self.jarvis.get_security_status(),
        })

    async def _handle_authenticator_confirm(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        code = str(payload.get("code") or "").strip()
        if not code:
            return web.json_response({"status": "error", "message": "Code erforderlich."}, status=400)
        if not self.jarvis.confirm_authenticator_setup(code):
            return web.json_response({"status": "error", "message": "Code konnte nicht bestaetigt werden."}, status=400)
        return web.json_response({"status": "ok", "security": self.jarvis.get_security_status()})

    async def _handle_authenticator_verify(self, request: web.Request) -> web.Response:
        if not self._authorize_read(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        code = str(payload.get("code") or "").strip()
        if not code:
            return web.json_response({"status": "error", "message": "Code erforderlich."}, status=400)
        verified = self.jarvis.verify_authenticator_code(code)
        status_code = 200 if verified else 401
        return web.json_response({"status": "ok", "verified": bool(verified)}, status=status_code)

    async def _handle_voice_enroll(self, request: web.Request) -> web.Response:
        if not self._authorize_command(request):
            return self._unauthorized()
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "Ungueltiges JSON."}, status=400)
        code = str(payload.get("code") or "").strip()
        audio_b64 = payload.get("audio") or payload.get("audio_base64")
        profile = str(payload.get("profile") or "default").strip() or "default"
        if not audio_b64:
            return web.json_response({"status": "error", "message": "Audio-Daten fehlen."}, status=400)
        if not self.jarvis.verify_authenticator_code(code):
            return web.json_response({"status": "error", "message": "Authenticator-Code ungueltig."}, status=401)
        try:
            audio_blob = base64.b64decode(audio_b64)
        except Exception:
            return web.json_response({"status": "error", "message": "Audio konnte nicht dekodiert werden."}, status=400)
        if not audio_blob:
            return web.json_response({"status": "error", "message": "Audio ist leer."}, status=400)
        success = self.jarvis.enroll_voice_profile(audio_blob, profile=profile)
        if not success:
            return web.json_response({"status": "error", "message": "Stimmmuster konnte nicht gespeichert werden."}, status=500)
        return web.json_response({
            "status": "ok",
            "security": self.jarvis.get_security_status(),
        })

    # Helpers -----------------------------------------------------------
    def _collect_status_payload(self) -> Dict[str, Any]:
        runtime = dict(self.jarvis.get_runtime_status())
        runtime["ready"] = self._ready_event.is_set()
        try:
            system_stats = self.jarvis.system_control.get_system_status()
        except Exception as exc:
            self.logger.debug("Systemstatus nicht verfuegbar: %s", exc)
            system_stats = {}
        try:
            metrics = self.jarvis.get_system_metrics(include_details=False)
        except Exception:
            metrics = {}
        return {
            "runtime": runtime,
            "system": system_stats,
            "metrics": metrics,
            "security": self.jarvis.get_security_status(),
        }

    def _unauthorized(self) -> web.Response:
        return web.json_response({"status": "error", "message": "Nicht autorisiert."}, status=401)

    def _authorize_read(self, request: web.Request) -> bool:
        if not self._check_network_guards(request):
            return False
        if self._verify_token(request):
            return True
        if self._allow_guest(request):
            return True
        return not self.token

    def _authorize_command(self, request: web.Request) -> bool:
        if not self._check_network_guards(request):
            return False
        if self._verify_token(request):
            return True
        if self._allow_guest(request):
            return True
        return not self.token

    def _check_network_guards(self, request: web.Request) -> bool:
        client_ip = self._client_ip(request)
        if self.allowed_ips and client_ip not in self.allowed_ips:
            self.logger.warning("Verbindung von nicht erlaubter IP %s geblockt.", client_ip)
            return False
        if self._rate_limit_max_requests > 0 and client_ip:
            bucket = self._rate_limit_buckets.setdefault(client_ip, deque())
            now = time.time()
            window_start = now - self._rate_limit_window
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= self._rate_limit_max_requests:
                self.logger.warning("Rate-Limit fuer %s erreicht (%s/%ss).", client_ip, self._rate_limit_max_requests, self._rate_limit_window)
                return False
            bucket.append(now)
        return True

    def _verify_token(self, request: web.Request) -> bool:
        if not self.token:
            return False
        return self._match_token(request)

    def _match_token(self, request: web.Request) -> bool:
        def _normalize(value) -> Optional[str]:
            if value is None:
                return None
            try:
                return str(value).strip()
            except Exception:
                return None

        expected = _normalize(self.token)
        if not expected:
            return False

        header_token = _normalize(request.headers.get("X-Auth-Token"))
        if header_token and header_token == expected:
            return True
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            value = _normalize(auth_header[7:])
            if value and value == expected:
                return True
        query_token = _normalize(request.query.get("token"))
        if query_token and query_token == expected:
            return True
        return False

    def _allow_guest(self, request: web.Request) -> bool:
        if not self.allow_guest_commands:
            return False
        client_ip = self._client_ip(request)
        return client_ip in {"127.0.0.1", "::1", "localhost"}

    def _execute_command_sync(self, text: str, metadata: Dict[str, Any]) -> str:
        return self.jarvis.execute_remote_command(
            text,
            metadata=dict(metadata or {}),
            source="web-ui",
            timeout=self.command_timeout,
        )
    async def _telemetry_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(5)
                metrics = self.jarvis.get_system_metrics(include_details=False)
                await self._broadcast(
                    {
                        "type": "system_metrics",
                        "timestamp": time.time(),
                        "payload": metrics,
                    }
                )
        except asyncio.CancelledError:
            return
        except Exception as exc:
            self.logger.debug("Telemetry-Loop gestoppt: %s", exc)

    @staticmethod
    def _client_ip(request: web.Request) -> str:
        peername = request.transport.get_extra_info("peername") if request.transport else None
        if isinstance(peername, (tuple, list)) and peername:
            return str(peername[0])
        if request.remote:
            return request.remote
        return "unknown"
