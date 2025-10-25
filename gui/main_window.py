# gui/main_window.py — V4.1.4
"""Interface graphique minimale de DeFiPilot avec barre de statut dynamique
et cartes alimentées par le dernier enregistrement du journal.

Objectif V4.1.4 :
- Afficher dans la barre de statut (bas de fenêtre) :
  "Dernière donnée lue : HH:MM:SS | Mise à jour interface : HH:MM:SS".
- Lecture robuste du dernier événement de `journal_signaux.jsonl` (format JSONL).
- Repli sur l'heure de modification du fichier si aucun timestamp exploitable.
- Rafraîchissement automatique via `after()` (toutes les 1s).
- Mise à jour des cartes principales avec la dernière entrée du journal :
  * Contexte du marché → champ `context` (favorable / neutre / défavorable)
  * Allocation active (policy) → dict formaté (prudent / modéré / risque)
  * Exécution en cours → `run_id` (ou `—`)
- Aucune dépendance externe (Tkinter + standard lib).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk


VERSION = "V4.1.4"
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


def _read_last_entry(path: str = "journal_signaux.jsonl") -> dict[str, object] | None:
    """Retourne la dernière entrée JSON valide du journal ou None en cas d'échec.

    - Ignore les lignes vides.
    - Ne lève pas d'exception : renvoie None en cas de problème.
    """
    try:
        last_line = ""
        with open(path, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if line:
                    last_line = line
        if not last_line:
            return None
        try:
            payload = json.loads(last_line)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    except FileNotFoundError:
        return None
    except OSError as exc:
        print(f"[MainWindow] Erreur ouverture journal {path}: {exc}")
        return None
    except Exception as exc:
        print(f"[MainWindow] Erreur inattendue lecture journal {path}: {exc}")
        return None


class MainWindow(tk.Tk):
    """Fenêtre principale Tkinter avec barre de statut et cartes dynamiques."""

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
        self._update_cards_from_last_journal()
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

        # Colonne gauche
        self.card_contexte = self._make_card(content, "Contexte du marché")
        self.card_contexte.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        self.card_policy = self._make_card(content, "Allocation active (policy)")
        self.card_policy.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        # Colonne droite
        self.card_run = self._make_card(content, "Exécution en cours")
        self.card_run.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

        self.card_pools = self._make_card(content, "Pools surveillées")
        self.card_pools.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

    def _ensure_status_label(self) -> None:
        """Crée la barre de statut en bas si absente."""
        if getattr(self, "status", None) is not None:
            return
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status = ttk.Label(status_frame, text="—")
        self.status.pack(fill=tk.X, padx=8, pady=6)

    def _make_card(self, parent: ttk.Frame, title: str) -> ttk.Frame:
        """Fabrique une carte simple avec un titre et un label de contenu."""
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
        self._set_card_text(self.card_run, f"{run}\nMode: {self.state.mode}")

    def _set_card_text(self, card: ttk.Frame, text: str) -> None:
        """Met à jour le texte d'une carte."""
        body: ttk.Label = card._body  # type: ignore[attr-defined]
        body.configure(text=text)

    # -- Actions -----------------------------------------------------------
    def _on_refresh_clicked(self) -> None:
        """Bouton 'Actualiser' : force un rafraîchissement immédiat."""
        self._update_cards_from_last_journal()
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
        """Lit un horodatage exploitable du journal fourni (JSONL).
        Ordre :
          1) 'timestamp' / 'time' / 'ts' si présent dans la dernière ligne JSON valide,
          2) Sinon regex ISO-8601 dans la ligne,
          3) Sinon repli sur mtime du fichier.
        Renvoie l'heure locale au format HH:MM:SS ou None.
        """
        try:
            last_line = ""
            with open(path, "r", encoding="utf-8") as h:
                for raw in h:
                    s = raw.strip()
                    if s:
                        last_line = s
            if not last_line:
                raise FileNotFoundError

            try:
                data = json.loads(last_line)
            except json.JSONDecodeError:
                data = None

            # 1) Clé explicite
            if isinstance(data, dict):
                for k in ("timestamp", "time", "ts"):
                    v = data.get(k) if k in data else None
                    dt = self._parse_iso_dt(v)
                    if dt is not None:
                        return self._format_hhmmss(dt)

            # 2) Regex ISO-8601 dans la ligne brute
            m = self._ISO_PATTERN.search(last_line)
            if m:
                dt = self._parse_iso_dt(m.group(1))
                if dt is not None:
                    return self._format_hhmmss(dt)

            # 3) Repli : mtime du fichier
            mtime = path.stat().st_mtime
            return self._format_hhmmss(mtime)
        except Exception:
            return None

    def _parse_iso_dt(self, value: object) -> datetime | None:
        """Parsage résilient d'un timestamp ISO-8601 (supporte Z et ±HHMM)."""
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

        # Met à jour aussi les cartes périodiquement
        self._update_cards_from_last_journal()

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

    def _update_cards_from_last_journal(self) -> None:
        """Actualise les cartes principales avec la dernière entrée du journal."""
        entry = _read_last_entry("journal_signaux.jsonl")

        contexte_display = "—"
        policy_display = "—"
        run_display = "—"

        if isinstance(entry, dict):
            # Contexte
            raw_context = entry.get("context")
            if isinstance(raw_context, str):
                cleaned_context = raw_context.strip()
                if cleaned_context:
                    normalized = cleaned_context.lower()
                    mapping = {
                        "favorable": "favorable",
                        "neutre": "neutre",
                        "défavorable": "défavorable",
                        "defavorable": "défavorable",
                    }
                    contexte_display = mapping.get(normalized, cleaned_context)

            # Policy
            raw_policy = entry.get("policy")
            if isinstance(raw_policy, dict):
                normalized_policy = {str(k).lower(): v for k, v in raw_policy.items()}
                order = ("prudent", "modéré", "risque")
                label_map = {
                    "prudent": "Prudent",
                    "modéré": "Modéré",
                    "risque": "Risque",
                }

                lines: list[str] = []
                for key in order:
                    value = normalized_policy.get(key)
                    if value is None and key == "modéré":
                        value = normalized_policy.get("modere")  # tolère sans accent
                    if value is None:
                        continue

                    if isinstance(value, (int, float)):
                        number = float(value)
                        if 0.0 <= number <= 1.0:
                            percent = round(number * 100.0, 1)
                            formatted_value = (
                                f"{int(percent)} %" if percent.is_integer() else f"{percent:.1f} %"
                            )
                        else:
                            formatted_value = str(value)
                    else:
                        formatted_value = str(value)

                    lines.append(f"{label_map[key]} : {formatted_value}")

                if lines:
                    policy_display = "\n".join(lines)

            # run_id
            raw_run = entry.get("run_id")
            if isinstance(raw_run, str):
                cleaned_run = raw_run.strip()
                if cleaned_run:
                    run_display = cleaned_run
            elif raw_run not in (None, ""):
                run_display = str(raw_run)

        # Écriture dans les cartes
        self._set_card_text(self.card_contexte, contexte_display)
        self._set_card_text(self.card_policy, policy_display)
        self._set_card_text(self.card_run, f"{run_display}\nMode: {self.state.mode}")


# ---------------------------------------------------------------------------
# Lancement autonome
# ---------------------------------------------------------------------------

def run() -> None:
    """Point d'entrée programme pour lancer la fenêtre principale."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run()
