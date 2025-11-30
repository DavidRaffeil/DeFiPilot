# tools/update_readme.py — V5.0
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys


def update_readme(version: str, screenshot: str) -> None:
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("[ERREUR] README.md introuvable.")
        sys.exit(1)

    backup_path = Path(f"README.backup.{version}.md")
    shutil.copy(readme_path, backup_path)
    print(f"[OK] Sauvegarde du README existant → {backup_path}")

    content = readme_path.read_text(encoding="utf-8")

    # Mise à jour de la version du badge
    import re
    content = re.sub(
        r"!\[Version\]\([^)]+\)",
        f"![Version](https://img.shields.io/badge/Version-{version}%20Stable-blue)",
        content,
    )

    # Mise à jour du numéro de version dans la section Nouveautés
    content = re.sub(
        r"(## 🆕 Nouveautés / What's New — Version )[\d\.]+",
        rf"\1{version}",
        content,
    )

    # Mise à jour de la capture d’écran si présente
    if Path(screenshot).exists():
        content = re.sub(
            r"!\[Capture d’écran DeFiPilot [^\]]+\]\([^)]+\)",
            f"![Capture d’écran DeFiPilot {version}](assets/{Path(screenshot).name})",
            content,
        )
    else:
        print(f"[AVERTISSEMENT] Capture non trouvée : {screenshot}")

    readme_path.write_text(content, encoding="utf-8")
    print(f"[OK] README.md mis à jour pour la version {version}")
    print(f"[INFO] Capture : {screenshot}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Met à jour automatiquement le README pour une nouvelle version.")
    parser.add_argument("--version", required=True, help="Numéro de version (ex: V5.0)")
    parser.add_argument("--screenshot", required=False, default="", help="Chemin vers la nouvelle capture d’écran")
    args = parser.parse_args()

    update_readme(args.version, args.screenshot)
