# gui/main_window.py — V4.1.3
"""Interface graphique minimale de DeFiPilot avec barre de statut dynamique.

Objectif V4.1.3 :
- Afficher dans la barre de statut (bas de fenêtre) :
  "Dernière donnée lue : HH:MM:SS | Mise à jour interface : HH:MM:SS"
- Lecture robuste du dernier événement de `journal_signaux.jsonl` (format JSONL).
- Repli sur l'heure de modification du fichier si aucun timestamp exploitable.
- Rafraîchissement automatique via `after()` (toutes les 1s).
- Aucune dépendance externe (Tkinter + standard lib).
"""

from __future__ import annotations

import io
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk


VERSION = "V4.1.3"
APP_TITLE = "DeFiPilot — Dashboard (min)"
MIN_WIDTH = 860
MIN_HEIGHT = 540


@dataclass(slots=True)
class UiState:
    """État d'affichage minimal (lecture seule au départ)."""
    contexte: str = "—"
    policy: str = "—"
    nb_pools: int = 0
    run_id: Optional[str] = None
    mode: str = "Simulation"  # ou "Réel"


class MainWindow(tk.Tk):
    """Fenêtre principale Tkinter avec barre de statut rafraîchie automatiquement."""

    _ISO_PATTERN = re.compile(
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
    )

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        # self.iconbitmap(...)  # TODO: icône personnalisée (plus tard)

        # État UI + timers
        self.state = UiState()
        self._last_data_time: str | None = None
        self._last_ui_update_time: datetime | float | None = None
        self._status_after_id: str | None = None

        # Construction de l’interface
        self._build_layout()
        self._populate_placeholders()
        self._ensure_status_label()

        # Démarrage de la boucle de mise à jour de la barre de statut
        self._update_status_bar()

    # -- Construction UI --------------------------------------------------
    def _build_layout(self) -> None:
        """Construit le squelette d'interface minimal."""
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        # Barre supérieure (actions minimales)
        toolbar = ttk.Frame(root)
        toolbar.pack(fill=tk.X, side=tk.TOP)

        self.btn_refresh = ttk.Button(
            toolbar,
            text="Actualiser",
            command=self._on_refresh_clicked,
        )
        self.btn_refresh.pack(side=tk.LEFT)

        ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(8, 12))

        # Zone de contenu (grid 2 colonnes)
        content = ttk.Frame(root)
        content.pack(fill=tk.BOTH, expand=True)

        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        # Cartes d'infos (placeholders)
        self.card_contexte = self._make_card(content, "Contexte du marché")
        self.card_policy = self._make_card(content, "Allocation active (policy)")
        self.card_pools = self._make_card(content, "Pools surveillées")
        self.card_run = self._make_card(content, "Exécution en cours")

        self.card_contexte.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self.card_policy.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        self.card_pools.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))
        self.card_run.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))

        # Barre de statut (création unique)
        self.status: ttk.Label = ttk.Label(
            self,
            anchor="w",
            text="Dernière donnée lue : --:--:-- | Mise à jour interface : --:--:--",
        )
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

    def _ensure_status_label(self) -> None:
        """Réutilise une barre de statut existante connue, sinon conserve self.status."""
        label_types = (tk.Label, ttk.Label)
        if hasattr(self, "status_label") and isinstance(self.status_label, label_types):
            self.status = self.status_label  # type: ignore[assignment]
            return
        if hasattr(self, "status_bar") and isinstance(self.status_bar, label_types):
            self.status = self.status_bar  # type: ignore[assignment]
            return
        if hasattr(self, "footer_label") and isinstance(self.footer_label, label_types):
            self.status = self.footer_label  # type: ignore[assignment]
            return
        # par défaut : self.status créé dans _build_layout

    def _make_card(self, parent: tk.Widget, title: str) -> ttk.Frame:
        """Crée un cadre stylé simple (carte)."""
        frame = ttk.Frame(parent, padding=12, relief=tk.GROOVE)
        lbl_title = ttk.Label(frame, text=title, font=("Segoe UI", 12, "bold"))
        lbl_title.pack(anchor="w", pady=(0, 8))
        body = ttk.Label(frame, text="—", justify=tk.LEFT)
        body.pack(anchor="w")
        frame._body = body  # type: ignore[attr-defined]
        return frame

    # -- Données d'exemple (placeholders) ---------------------------------
    def _populate_placeholders(self) -> None:
        """Alimente les cartes avec les valeurs par défaut."""
        self._set_card_text(self.card_contexte, f"Contexte: {self.state.contexte}")
        self._set_card_text(self.card_policy, f"Policy: {self.state.policy}")
        self._set_card_text(self.card_pools, f"Nb de pools surveillées: {self.state.nb_pools}")
        run = self.state.run_id or "—"
        self._set_card_text(self.card_run, f"run_id: {run}\nMode: {self.state.mode}")

    def _set_card_text(self, card: ttk.Frame, text: str) -> None:
        """Met à jour le texte d'une carte."""
        body: ttk.Label = card._body  # type: ignore[attr-defined]
        body.configure(text=text)

    # -- Actions -----------------------------------------------------------
    def _on_refresh_clicked(self) -> None:
        """Bouton 'Actualiser' : force un rafraîchissement immédiat de la barre."""
        self._update_status_bar()

    # -- Barre de statut ---------------------------------------------------
    def _format_hhmmss(self, dt: datetime | float | None) -> str:
        """Formate un instant en HH:MM:SS local ou renvoie un placeholder."""
        if dt is None:
            return "--:--:--"
        try:
            if isinstance(dt, (int, float)):
                local_dt = datetime.fromtimestamp(float(dt))
            else:
                local_dt = dt
                if local_dt.tzinfo is not None:
                    local_dt = local_dt.astimezone()
            return local_dt.strftime("%H:%M:%S")
        except Exception as exc:  # robustesse ultime
            print(f"[MainWindow] Erreur formatage heure: {exc}")
            return "--:--:--"

    def _read_last_data_time_from_journal(self, path: Path = Path("journal_signaux.jsonl")) -> str | None:
        """Lit le dernier horodatage exploitable du journal fourni (JSONL).
        Ordre :
          1) 'timestamp' / 'time' / 'ts' si présent dans la dernière ligne JSON valide,
          2) Sinon regex ISO-8601 dans la ligne,
          3) Sinon repli sur mtime du fichier.
        """
        try:
            if not path.exists():
                return None

            last_line = ""
            stat_result = None
            try:
                stat_result = path.stat()
            except OSError:
                stat_result = None

            with path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if line:
                        last_line = line

            if not last_line:
                if stat_result is not None:
                    return self._format_hhmmss(stat_result.st_mtime)
                return None

            timestamp_dt = self._extract_datetime_from_line(last_line)
            if timestamp_dt is not None:
                return self._format_hhmmss(timestamp_dt)

            if stat_result is not None:
                return self._format_hhmmss(stat_result.st_mtime)

            return None

        except FileNotFoundError:
            return None
        except Exception as exc:
            print(f"[MainWindow] Erreur lecture journal {os.fspath(path)}: {exc}")
            return None

    def _extract_datetime_from_line(self, line: str) -> datetime | float | None:
        """Tente d'extraire un horodatage d'une ligne JSON ou texte."""
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            payload = None

        if isinstance(payload, dict):
            for key in ("timestamp", "time", "ts"):
                if key in payload:
                    parsed = self._coerce_to_datetime(payload.get(key))
                    if parsed is not None:
                        return parsed

        match = self._ISO_PATTERN.search(line)
        if match:
            parsed = self._coerce_to_datetime(match.group(1))
            if parsed is not None:
                return parsed

        return None

    def _coerce_to_datetime(self, value: object) -> datetime | float | None:
        """Convertit différents formats de timestamp en datetime ou timestamp."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str) and value:
            iso_value = value.strip()
            if iso_value.endswith("Z"):
                iso_value = iso_value[:-1] + "+00:00"
            # normaliser ±HHMM -> ±HH:MM
            if re.search(r"[+-]\d{4}$", iso_value):
                iso_value = f"{iso_value[:-5]}{iso_value[-5:-2]}:{iso_value[-2:]}"
            iso_value = iso_value.replace(" ", "T")
            try:
                dt = datetime.fromisoformat(iso_value)
            except ValueError:
                return None
            if dt.tzinfo is not None:
                dt = dt.astimezone()
            return dt
        return None

    def _update_status_bar(self) -> None:
        """Met à jour la barre de statut et replanifie le rafraîchissement."""
        try:
            self._last_data_time = self._read_last_data_time_from_journal()
        except Exception as exc:
            print(f"[MainWindow] Erreur inattendue lecture journal: {exc}")
            self._last_data_time = None

        self._last_ui_update_time = datetime.now()
        status_line = (
            "Dernière donnée lue : "
            f"{self._last_data_time or '--:--:--'}"
            " | Mise à jour interface : "
            f"{self._format_hhmmss(self._last_ui_update_time)}"
        )
        self.status.configure(text=status_line)

        if self._status_after_id is not None:
            try:
                self.after_cancel(self._status_after_id)
            except Exception:
                pass
            finally:
                self._status_after_id = None

        self._status_after_id = self.after(1000, self._update_status_bar)


# ---------------------------------------------------------------------------
# Lancement autonome
# ---------------------------------------------------------------------------
def run() -> None:
    """Point d'entrée programme pour lancer la fenêtre principale."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run()
