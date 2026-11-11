"""HESS (batarya + süperkapasitör) enerji yönetimi: FLC ve FRL yeniden üretimi."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict:
    """config/default.yaml dosyasını (veya verilen yolu) okuyup sözlük döndürür."""
    path = Path(path) if path else ROOT / "config" / "default.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
