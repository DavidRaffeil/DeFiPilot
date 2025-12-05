# gui/main_window.py — V5.3.0
"""DeFiPilot — Tableau de bord principal (V5.3.0).

Interface de monitoring en temps réel des signaux, du contrôle et de la stratégie :

- Cartes « Contexte », « Allocation (policy) », « Score & version », « Stratégie & Performances », « Journal », « ControlPilot ».
- Carte « Métriques clés » avec pastilles dynamiques (APR, TVL, Volume, Volatilité, Tendance APR).
- Onglet « Résumé actuel » (signaux + contrôle + état DeFiPilot + snapshot stratégie).
- Onglet « Historique des signaux » (dernières lignes du JSONL).
- Barre de statut avec horodatages et indicateurs simples.
- Intégration V5.3 : lecture du journal stratégique via core.journal_strategy.lire_derniere_entree_strategique().
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ajout du dossier racine du projet dans sys.path pour permettre "import core"
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkfont

from core.sync_guard import safe_read_jsonl, is_locked
from core.state_manager import get_state
from control.control_pilot import ResumeAnomalies, analyser_anomalies
from core.strategy_snapshot import lire_dernier_snapshot
from core.journal_strategy import lire_derniere_entree_strategique


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JSONL_ENV_KEYS: Tuple[str, ...] = (
    "DEFIPILOT_JOURNAL",
    "DEFIPILOT_SIGNALS_JSONL",
    "SIGNALS_JSONL_PATH",
    "MARKET_SIGNALS_JSONL",
)
DEFAULT_JSONL_PATH = Path("journal_signaux.jsonl")

CONTROL_JSONL_ENV_KEYS: Tuple[str, ...] = (
    "DEFIPILOT_CONTROL_JSONL",
    "CONTROL_JSONL_PATH",
)
DEFAULT_CONTROL_JSONL_PATH = Path("journal_control.jsonl")

REFRESH_MS = 1_000
APP_VERSION = "V5.3.0"
APP_TITLE = f"DeFiPilot — Tableau de bord ({APP_VERSION})"
MIN_SIZE = (1180, 720)


# ---------------------------------------------------------------------------
# Fonctions utilitaires
# ---------------------------------------------------------------------------


def _resolve_jsonl_path(keys: Sequence[str], default_path: Path) -> Path:
    """Résout le chemin d'un JSONL à partir d'une liste de variables d'environnement."""
    for key in keys:
        val = os.getenv(key)
        if not val:
            continue
        try:
            return Path(val).expanduser().resolve()
        except OSError:
            return Path(val).expanduser()
    return default_path


def _now_tz() -> datetime:
    """Renvoie l'heure actuelle en timezone locale (à partir de UTC)."""
    return datetime.now(timezone.utc).astimezone()


def _parse_timestamp(value: Any) -> Optional[datetime]:
    """Best effort pour parser un timestamp ISO 8601 ou similaire."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    txt = value.strip()
    if not txt:
        return None
    # Normalisation Z → +00:00
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(txt).astimezone()
    except Exception:
        return None


def _fmt_datetime(dt: datetime) -> str:
    """Formate un datetime lisible."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _fmt_compact(value: float) -> str:
    """Formate un nombre en notation compacte (K/M)."""
    n = float(value)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000:
        return f"{sign}{n/1_000_000:.2f} M"
    if n >= 1_000:
        return f"{sign}{n/1_000:.2f} K"
    return f"{sign}{n:.2f}"


def _safe_float(value: Any) -> Optional[float]:
    """Convertit une valeur en float ou renvoie None en cas d'échec."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Widgets de base
# ---------------------------------------------------------------------------


class Card(ttk.Frame):
    """Carte simple avec un titre et un contenu texte multi-lignes."""

    def __init__(self, master: tk.Misc, title: str, **kwargs: Any) -> None:
        super().__init__(master, padding=8, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        title_label = ttk.Label(self, text=title, style="CardTitle.TLabel")
        title_label.grid(row=0, column=0, sticky="w")

        self._text = tk.Text(self, height=6, wrap="word", relief="flat")
        self._text.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self._text.configure(state="disabled")

    def set_value(self, text: str) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", text or "")
        self._text.configure(state="disabled")


class KeyMetricsCard(Card):
    """Carte spécialisée pour les métriques clés (APR, TVL, etc.)."""

    def __init__(self, master: tk.Misc, **kwargs: Any) -> None:
        super().__init__(master, title="Métriques clés", **kwargs)

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        lines: List[str] = []
        for key in ("apr", "tvl", "volume", "volatilite", "tendance_apr"):
            if key not in metrics:
                continue
            val = metrics[key]
            num = _safe_float(val)
            if num is not None:
                formatted = _fmt_compact(num)
            else:
                formatted = str(val)
            lines.append(f"{key.upper()} : {formatted}")
        self.set_value("\n".join(lines) if lines else "Aucune métrique disponible.")


# ---------------------------------------------------------------------------
# Fenêtre principale
# ---------------------------------------------------------------------------


class MainWindow(tk.Tk):
    """Fenêtre principale du tableau de bord DeFiPilot."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(*MIN_SIZE)

        # Styles de base
        self._init_styles()

        # Chemins des journaux
        self._signals_path = _resolve_jsonl_path(JSONL_ENV_KEYS, DEFAULT_JSONL_PATH)
        self._control_path = _resolve_jsonl_path(CONTROL_JSONL_ENV_KEYS, DEFAULT_CONTROL_JSONL_PATH)

        # État interne de rafraîchissement
        self._last_signal_raw: Optional[str] = None
        self._last_signal_dt: Optional[datetime] = None
        self._last_ui_dt: Optional[datetime] = None

        # Widgets principaux
        self._build_menu()
        self._build_layout()
        self._build_statusbar()

        # Démarrage de la boucle de rafraîchissement
        self.after(REFRESH_MS, self._tick)

    # ------------------------------------------------------------------ #
    # Construction UI
    # ------------------------------------------------------------------ #

    def _init_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("CardTitle.TLabel", font=("Segoe UI", 10, "bold"))

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Actualiser maintenant", command=lambda: self._refresh(force=True))
        file_menu.add_separator()
        file_menu.add_command(label="Exporter l'historique en CSV…", command=self._export_history_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.destroy)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="À propos", command=self._show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)

        self.config(menu=menubar)

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=10)
        container.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=3)
        container.rowconfigure(1, weight=2)

        # Cartes du haut
        top_frame = ttk.Frame(container)
        top_frame.grid(row=0, column=0, sticky="nsew")
        for col in range(3):
            top_frame.columnconfigure(col, weight=1, uniform="topcols")
        for row in range(2):
            top_frame.rowconfigure(row, weight=1)

        self.card_context = Card(top_frame, "Contexte")
        self.card_context.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.card_policy = Card(top_frame, "Allocation (policy)")
        self.card_policy.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.card_metrics = KeyMetricsCard(top_frame)
        self.card_metrics.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        self.card_score = Card(top_frame, "Score & version")
        self.card_score.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.card_strategy = Card(top_frame, "Stratégie & Performances")
        self.card_strategy.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        self.card_journal = Card(top_frame, "Journal")
        self.card_journal.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)

        # Bas : résumé + historique + ControlPilot (texte dans l'onglet Résumé)
        bottom_frame = ttk.Frame(container)
        bottom_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(bottom_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Onglet Résumé
        self.resume_tab = ttk.Frame(self.notebook)
        self.resume_tab.columnconfigure(0, weight=1)
        self.resume_tab.rowconfigure(0, weight=1)

        self.tree_resume = ttk.Treeview(
            self.resume_tab,
            columns=("key", "value"),
            show="headings",
            selectmode="browse",
            height=8,
        )
        self.tree_resume.heading("key", text="Clé")
        self.tree_resume.heading("value", text="Valeur")
        self.tree_resume.column("key", width=220, anchor="w")
        self.tree_resume.column("value", anchor="w")
        self.tree_resume.grid(row=0, column=0, sticky="nsew")

        # Onglet Historique
        self.history_tab = ttk.Frame(self.notebook)
        self.history_tab.columnconfigure(0, weight=1)
        self.history_tab.rowconfigure(0, weight=1)

        self.history_text = tk.Text(self.history_tab, wrap="none", height=10)
        self.history_text.grid(row=0, column=0, sticky="nsew")

        self.notebook.add(self.resume_tab, text="Résumé actuel")
        self.notebook.add(self.history_tab, text="Historique des signaux")

    def _build_statusbar(self) -> None:
        status = ttk.Frame(self, padding=(10, 4))
        status.grid(row=1, column=0, sticky="ew")
        status.columnconfigure(0, weight=1)
        status.columnconfigure(1, weight=0)

        self.status_left = ttk.Label(status, text="Prêt.")
        self.status_left.grid(row=0, column=0, sticky="w")

        self.status_right = ttk.Label(status, text="—")
        self.status_right.grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------ #
    # Boucle de rafraîchissement
    # ------------------------------------------------------------------ #

    def _tick(self) -> None:
        self._refresh(force=False)
        self.after(REFRESH_MS, self._tick)

    def _refresh(self, *, force: bool) -> None:
        self._last_ui_dt = _now_tz()

        signals_history = self._read_signals()
        signal_payload = signals_history[-1] if signals_history else None

        control_events = self._read_control_events()
        anomalies = self._analyze_control(control_events)
        state_snapshot = self._read_state()
        strategy_snapshot = self._read_strategy_snapshot()

        last_raw_repr = json.dumps(signal_payload, sort_keys=True) if signal_payload else None
        if not force and last_raw_repr == self._last_signal_raw:
            # Pas de nouveau signal : on met tout de même à jour la carte stratégie et le statut
            self._update_strategy_card()
            self._update_history(signals_history)
            self._update_status(signal_payload)
            return

        self._last_signal_raw = last_raw_repr
        self._last_signal_dt = _parse_timestamp(signal_payload.get("timestamp")) if signal_payload else None

        self._update_cards(signal_payload, anomalies, control_events)
        self._update_strategy_card()
        self._update_resume(signal_payload, anomalies, control_events, state_snapshot, strategy_snapshot)
        self._update_history(signals_history)
        self._update_status(signal_payload)

    # ------------------------------------------------------------------ #
    # Lecture des données
    # ------------------------------------------------------------------ #

    def _read_signals(self) -> List[Dict[str, Any]]:
        try:
            payloads = safe_read_jsonl(
                self._signals_path,
                max_lines=120,
                wait_if_locked=True,
                timeout_s=2.0,
                parse=True,
            )
        except Exception:
            payloads = []
        result: List[Dict[str, Any]] = []
        for payload in payloads:
            if isinstance(payload, dict):
                result.append(payload)
        return result

    def _read_control_events(self) -> List[Dict[str, Any]]:
        if not self._control_path.exists():
            return []
        try:
            payloads = safe_read_jsonl(
                self._control_path,
                max_lines=200,
                wait_if_locked=True,
                timeout_s=2.0,
                parse=True,
            )
        except Exception:
            return []
        events: List[Dict[str, Any]] = []
        for payload in payloads:
            if isinstance(payload, dict):
                events.append(payload)
        return events

    def _read_state(self) -> Dict[str, Any]:
        try:
            state = get_state() or {}
            if isinstance(state, dict):
                return state
        except Exception:
            pass
        return {}

    def _read_strategy_snapshot(self) -> Optional[Dict[str, Any]]:
        try:
            snapshot = lire_dernier_snapshot()
        except Exception:
            return None
        if isinstance(snapshot, dict):
            return snapshot
        return None

    # ------------------------------------------------------------------ #
    # Mise à jour des cartes
    # ------------------------------------------------------------------ #

    def _update_cards(
        self,
        signal_payload: Optional[Dict[str, Any]],
        anomalies: Optional[ResumeAnomalies],
        control_events: List[Dict[str, Any]],
    ) -> None:
        # Contexte
        context_text = "Contexte : —"
        if signal_payload:
            ctx = signal_payload.get("context") or signal_payload.get("contexte")
            if ctx:
                context_text = f"Contexte : {ctx}"
        self.card_context.set_value(context_text)

        # Policy (allocation)
        policy_text = self._format_policy(signal_payload.get("policy") if signal_payload else None)
        self.card_policy.set_value(policy_text)

        # Métriques clés (placeholder basé sur le dernier signal)
        metrics: Dict[str, Any] = {}
        if signal_payload:
            for key in ("apr", "tvl", "volume", "volatilite", "tendance_apr"):
                if key in signal_payload:
                    metrics[key] = signal_payload[key]
        self.card_metrics.update_metrics(metrics)

        # Score & version
        score_lines: List[str] = []
        if signal_payload:
            score = _safe_float(signal_payload.get("score"))
            version = signal_payload.get("version") or signal_payload.get("defipilot_version")
            run_id = signal_payload.get("run_id") or signal_payload.get("id")
            score_lines.append(f"Score : {score:.4f}" if score is not None else "Score : —")
            if version:
                score_lines.append(f"Version : {version}")
            if run_id:
                score_lines.append(f"Run ID : {run_id}")
        else:
            score_lines.append("Score : —")
        self.card_score.set_value("\n".join(score_lines))

        # Journal + contrôle
        journal_text = self._format_journal_text(signal_payload, anomalies, control_events)
        self.card_journal.set_value(journal_text)

    def _update_strategy_card(self) -> None:
        try:
            data = lire_derniere_entree_strategique()
        except Exception:
            data = None
        if not isinstance(data, dict) or not data:
            self.card_strategy.set_value("Aucune décision stratégique disponible pour le moment.")
            return

        lines: List[str] = []
        context = data.get("context") or data.get("contexte")
        lines.append(f"Contexte : {context}" if context else "Contexte : —")

        profil_lines = self._format_strategy_profil(data.get("profil"))
        if profil_lines:
            lines.extend(profil_lines)

        allocation_lines = self._format_strategy_allocation(data.get("allocation_avant_usd"))
        if allocation_lines:
            lines.extend(allocation_lines)

        ts_raw = data.get("timestamp")
        ts = _parse_timestamp(ts_raw)
        if ts:
            lines.append(f"Dernière mise à jour : {_fmt_datetime(ts)}")
        elif ts_raw:
            lines.append(f"Dernière mise à jour : {ts_raw}")

        self.card_strategy.set_value("\n".join(lines) if lines else "Données stratégiques indisponibles.")

    def _format_strategy_profil(self, profil: Any) -> List[str]:
        if profil is None:
            return ["Policy active : —"]
        if not isinstance(profil, dict):
            return [f"Policy active : {profil}"]

        mapping = {
            "prudent": "Prudent",
            "prudente": "Prudent",
            "modere": "Modere",
            "modere": "Modere",
            "modere ": "Modere",
            "modéré": "Modere",
            "risque": "Risque",
        }
        lines = ["Policy active :"]
        for key, value in profil.items():
            norm = key.lower().strip()
            norm = norm.replace("é", "e").replace("è", "e")
            label = mapping.get(norm, key)
            num = _safe_float(value)
            formatted = f"{num * 100:.0f} %" if num is not None else str(value)
            lines.append(f"  - {label} : {formatted}")
        return lines

    def _format_strategy_allocation(self, allocation: Any) -> List[str]:
        if allocation is None:
            return []
        if not isinstance(allocation, dict):
            return [f"Allocation actuelle (USD) : {allocation}"]
        lines = ["Allocation actuelle (USD) :"]
        for key, value in allocation.items():
            num = _safe_float(value)
            formatted = f"{num:.2f}" if num is not None else str(value)
            lines.append(f"  - {key} : {formatted}")
        return lines

    def _format_policy(self, policy: Optional[Dict[str, Any]]) -> str:
        if not policy:
            return "Aucune allocation disponible."
        lines: List[str] = []
        for key in sorted(policy.keys()):
            val = policy[key]
            num = _safe_float(val)
            if num is not None and 0 <= num <= 1:
                formatted = f"{num * 100:.2f} %"
            elif num is not None:
                formatted = _fmt_compact(num)
            else:
                formatted = str(val)
            lines.append(f"{key} : {formatted}")
        return "\n".join(lines)

    def _format_journal_text(
        self,
        signal_payload: Optional[Dict[str, Any]],
        anomalies: Optional[ResumeAnomalies],
        control_events: List[Dict[str, Any]],
    ) -> str:
        parts: List[str] = []

        if signal_payload:
            ts = signal_payload.get("timestamp")
            ctx = signal_payload.get("context") or signal_payload.get("contexte")
            parts.append("Dernier signal :")
            if ts:
                parts.append(f"  - timestamp : {ts}")
            if ctx:
                parts.append(f"  - contexte : {ctx}")

        if anomalies:
            parts.append("")
            parts.append("Anomalies ControlPilot :")
            parts.append(f"  - niveau : {anomalies.niveau}")
            parts.append(f"  - nb_alertes : {len(anomalies.alertes)}")

        if control_events:
            parts.append("")
            parts.append(f"Événements contrôle récents : {len(control_events)}")

        return "\n".join(parts) if parts else "Aucun journal disponible."

    def _update_resume(
        self,
        signal_payload: Optional[Dict[str, Any]],
        anomalies: Optional[ResumeAnomalies],
        control_events: List[Dict[str, Any]],
        state_snapshot: Dict[str, Any],
        strategy_snapshot: Optional[Dict[str, Any]],
    ) -> None:
        self.tree_resume.delete(*self.tree_resume.get_children())

        def add_row(label: str, value: Any) -> None:
            self.tree_resume.insert("", "end", values=(label, str(value)))

        add_row("Version GUI", APP_VERSION)
        if signal_payload:
            add_row("Dernier signal contexte", signal_payload.get("context") or "—")
        if anomalies:
            add_row("Niveau anomalies", anomalies.niveau)
        if state_snapshot:
            add_row("Nb positions", len(state_snapshot.get("positions", [])))
        if strategy_snapshot:
            add_row("Contexte stratégie", strategy_snapshot.get("context"))
            add_row("Profil stratégie", strategy_snapshot.get("profil"))

    def _update_history(self, signals_history: List[Dict[str, Any]]) -> None:
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        for payload in signals_history[-50:]:
            try:
                line = json.dumps(payload, ensure_ascii=False)
            except Exception:
                line = str(payload)
            self.history_text.insert("end", line + "\n")
        self.history_text.configure(state="disabled")

    def _update_status(self, signal_payload: Optional[Dict[str, Any]]) -> None:
        if self._last_signal_dt:
            age = _now_tz() - self._last_signal_dt
            age_s = int(age.total_seconds())
            self.status_left.config(text=f"Dernier signal il y a {age_s}s")
        else:
            self.status_left.config(text="Aucun signal reçu.")

        self.status_right.config(text=_fmt_datetime(_now_tz()))

    # ------------------------------------------------------------------ #
    # Actions diverses
    # ------------------------------------------------------------------ #

    def _export_history_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return
        signals = self._read_signals()
        if not signals:
            messagebox.showinfo("Export CSV", "Aucune donnée à exporter.")
            return
        keys: List[str] = sorted({k for payload in signals for k in payload.keys()})
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = __import__("csv").DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for payload in signals:
                    row = {k: payload.get(k, "") for k in keys}
                    writer.writerow(row)
        except Exception as exc:
            messagebox.showerror("Export CSV", f"Erreur lors de l'export : {exc}")
            return
        messagebox.showinfo("Export CSV", f"Historique exporté vers {path}.")

    def _show_about(self) -> None:
        messagebox.showinfo(
            "À propos",
            f"DeFiPilot — Tableau de bord\nVersion : {APP_VERSION}\nSignaux : {self._signals_path}\nContrôle : {self._control_path}",
        )

    def _analyze_control(self, control_events: List[Dict[str, Any]]) -> Optional[ResumeAnomalies]:
        try:
            return analyser_anomalies(control_events)
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Lancement
# ---------------------------------------------------------------------------


def main() -> None:
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
