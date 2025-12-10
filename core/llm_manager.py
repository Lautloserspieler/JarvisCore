# ... (keeping existing code until download_model, only showing the changed method)

# Find line ~1070 in original file and replace download_model() with:

    def download_model(self, model_key: str, progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None) -> bool:
        if requests is None:  # pragma: no cover - fallback, sollte praktisch nicht passieren
            raise RuntimeError("Das Paket 'requests' ist nicht installiert und wird fuer den Download benoetigt.")
        info = self.available_models.get(model_key)
        if not info:
            raise ValueError(f"Unbekanntes Modell: {model_key}")

        filename = info.get("name") or f"{model_key}.gguf"
        target_path = self.models_dir / filename
        if target_path.exists():
            self.logger.info("Modell bereits vorhanden: %s", target_path)
            if progress_cb:
                try:
                    size = target_path.stat().st_size
                except OSError:
                    size = 0
                progress_cb(
                    {
                        "model": model_key,
                        "status": "already_exists",
                        "downloaded": size,
                        "total": size,
                        "percent": 100,
                    }
                )
            return True

        url = self._resolve_download_url(info)
        if not url:
            raise RuntimeError("Download-URL konnte nicht bestimmt werden.")

        tmp_path = target_path.with_suffix(target_path.suffix + ".download")
        tmp_path.parent.mkdir(parents=True, exist_ok=True)

        # Get HuggingFace token from settings
        headers = {}
        if self.settings:
            try:
                llm_config = self.settings.get('llm', {})
                if isinstance(llm_config, dict):
                    token = llm_config.get('huggingface_token')
                    if token and isinstance(token, str) and token.strip():
                        headers['Authorization'] = f"Bearer {token.strip()}"
                        self.logger.info("Using HuggingFace token for download")
            except Exception as exc:
                self.logger.debug(f"Could not retrieve HuggingFace token: {exc}")

        self.logger.info("Starte Download fuer %s (%s)", model_key, url)
        downloaded = 0
        total = 0
        start_time = time.time()
        last_emit = 0.0

        def emit_progress(force: bool = False, status: str = "in_progress", message: Optional[str] = None) -> None:
            if not progress_cb:
                return
            now = time.time()
            nonlocal last_emit
            if not force and (now - last_emit) < 0.5:
                return
            percent = None
            if total:
                percent = (downloaded / total) * 100
            speed = None
            eta = None
            elapsed = max(now - start_time, 1e-3)
            if elapsed > 0:
                speed = downloaded / elapsed
                if total and downloaded < total and speed > 0:
                    eta = (total - downloaded) / speed
            payload = {
                "model": model_key,
                "status": status,
                "downloaded": downloaded,
                "total": total,
                "percent": percent,
                "speed": speed,
                "eta": eta,
            }
            if message:
                payload["message"] = message
            progress_cb(payload)
            last_emit = now

        response = None
        try:
            response = requests.get(url, stream=True, timeout=30, headers=headers)
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", "0")) or 0
            chunk_size = 4 * 1024 * 1024  # 4 MB
            emit_progress(force=True)
            with open(tmp_path, "wb") as handle:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    downloaded += len(chunk)
                    emit_progress()
            if not total:
                total = downloaded
            os.replace(tmp_path, target_path)
            self.logger.info("Modell heruntergeladen: %s", target_path)
            emit_progress(force=True)
            return True
        except Exception as exc:
            self.logger.error("Download fuer %s fehlgeschlagen: %s", model_key, exc)
            with contextlib.suppress(Exception):
                if tmp_path.exists():
                    tmp_path.unlink()
            raise
        finally:
            if response is not None:
                response.close()
