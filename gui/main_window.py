# gui/main_window.py — V4.1.0
"""Interface graphique minimale de DeFiPilot (squelette).

Objectifs (V4.1.0):
- Fenêtre principale Tkinter (titre, taille minimale, icône optionnelle plus tard).
- Barre de statut (version + horodatage rafraîchi à l'ouverture).
- Zone centrale avec placeholders (contexte, policy, pools, run_id, mode).
- Aucune dépendance externe (Tkinter standard) ; lecture seule pour l'instant.

Évolutions prévues (V4.1.x):
- Lecture du dernier `journal_signaux.jsonl` pour afficher contexte/policy (étape 4).
- Rafraîchissement périodique (étape 3) avec `after(...)`.
- Intégration contrôlée avec les modules core (sans import non validé ici).

Langue: commentaires et messages en FR (priorité utilisateur). UI simple.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import ttk


VERSION = "V4.1.0"
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
    """Fenêtre principale Tkinter (squelette minimal)."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        # self.iconbitmap(...)  # TODO: icône personnalisée (plus tard, pas de logo tiers)

        self.state = UiState()

        self._build_layout()
        self._populate_placeholders()
        self._update_status()

    # -- Construction UI --------------------------------------------------
    def _build_layout(self) -> None:
        # Conteneur principal
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

        # Barre de statut
        self.status = ttk.Label(self, anchor="w")
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

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
        self._set_card_text(self.card_contexte, f"Contexte: {self.state.contexte}")
        self._set_card_text(self.card_policy, f"Policy: {self.state.policy}")
        self._set_card_text(self.card_pools, f"Nb de pools surveillées: {self.state.nb_pools}")
        run = self.state.run_id or "—"
        self._set_card_text(self.card_run, f"run_id: {run}\nMode: {self.state.mode}")

    def _set_card_text(self, card: ttk.Frame, text: str) -> None:
        body: ttk.Label = card._body  # type: ignore[attr-defined]
        body.configure(text=text)

    # -- Actions -----------------------------------------------------------
    def _on_refresh_clicked(self) -> None:
        """Bouton "Actualiser" (pour l'instant: rafraîchit l'horodatage de la barre de statut)."""
        # Étape 2/3/4 ajouteront la lecture des journaux et la mise à jour réelle.
        self._update_status()

    # -- Statut ------------------------------------------------------------
    def _update_status(self) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status.configure(text=f"{APP_TITLE} | Version {VERSION} | Dernière mise à jour: {now}")


# ---------------------------------------------------------------------------
# Lancement autonome
# ---------------------------------------------------------------------------
def run() -> None:
    """Point d'entrée programme pour lancer la fenêtre principale."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run()
