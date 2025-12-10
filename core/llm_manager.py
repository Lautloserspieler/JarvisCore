    def _candidate_model_paths(self, model_key: str) -> List[Path]:
        info = self.available_models.get(model_key)
        if not info:
            return []
        names: List[str] = []
        primary = info.get("name")
        if primary:
            names.append(primary)  # Mistral-Nemo-Instruct-2407-Q4_K_M.gguf
            # Also support the variant without dash before Q4_K_M
            base = Path(primary)
            stem = base.stem
            
            # For Mistral: also try without the leading dash
            # e.g., Mistral-Nemo-Instruct-2407.Q4_K_M.gguf (old variant)
            if "Mistral" in primary:
                # Generate old variant: replace -Q4_K_M with .Q4_K_M
                old_style = primary.replace("-Q4_K_M.gguf", ".Q4_K_M.gguf")
                if old_style != primary:
                    names.append(old_style)
                # Also try with other Q variants
                for qvar in ["Q4_K_S", "Q5_K_M", "Q6_K_M", "Q8_0"]:
                    names.append(f"Mistral-Nemo-Instruct-2407-{qvar}.gguf")
                    names.append(f"Mistral-Nemo-Instruct-2407.{qvar}.gguf")
            
            # Standard variant handling for other formats
            suffix = base.suffix.lower() if base.suffix else ''
            if suffix == '.safetensors':
                names.extend([
                    f"{stem}.gguf",
                    f"{stem}.Q4_K_M.gguf",
                    f"{stem}.Q4_K_S.gguf",
                    f"{stem}.Q5_K_M.gguf",
                ])
        for alias in info.get("alt_names", []):
            if alias:
                names.append(alias)
        seen: Set[str] = set()
        candidates: List[Path] = []
        for name in names:
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(self.models_dir / name)
        return candidates
