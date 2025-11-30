# gui/main_window.py — V5.1.1
"""DeFiPilot — Tableau de bord principal (V5.1.1).

Interface de monitoring en temps réel des signaux et du contrôle :

- Cartes « Contexte », « Allocation (policy) », « Score & version », « Journal », « ControlPilot ».
- Carte « Métriques clés » avec pastilles dynamiques (APR, TVL, Volume, Volatilité, Tendance APR).
- Onglet « Résumé actuel » (signaux + contrôle + état DeFiPilot).
- Onglet « Historique des signaux » (dernières lignes du JSONL).
- Barre de statut avec horodatages et indicateurs (verrouillage, fraîcheur).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ajout du dossier racine du projet dans sys.path pour permettre "import core"
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import csv
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
APP_VERSION = "V5.1.1"
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
    """Convertit un timestamp brut (str/float/int/None) en datetime timezone-aware."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).astimezone()
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text).astimezone()
        except ValueError:
            return None
    return None


def _fmt_datetime(dt: Optional[datetime]) -> str:
    """Formate un datetime complet JJ/MM/AAAA HH:MM:SS."""
    return dt.astimezone().strftime("%d/%m/%Y %H:%M:%S") if dt else "—"


def _fmt_hms(dt: Optional[datetime]) -> str:
    """Formate seulement l'heure HH:MM:SS."""
    return dt.astimezone().strftime("%H:%M:%S") if dt else "—"


def _safe_float(value: Any) -> Optional[float]:
    """Convertit en float ou renvoie None en cas d'erreur."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_compact(value: Any) -> str:
    """Format compact pour les valeurs numériques ou objets simples."""
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _is_fresh_timestamp(timestamp: Optional[datetime], max_age_seconds: int = 120) -> bool:
    """Indique si un timestamp est récent (moins de max_age_seconds)."""
    if not timestamp:
        return False
    delta = _now_tz() - timestamp
    return delta <= timedelta(seconds=max_age_seconds)


def _metric_color(name: str, value: Optional[float]) -> str:
    """Retourne un emoji de couleur en fonction de la métrique."""
    if value is None:
        return "🟡"
    key = name.lower()
    if key == "apr_mean":
        return "🟢" if value > 0.10 else "🟡" if value >= 0.05 else "🔴"
    if key == "tvl_sum":
        millions = value / 1_000_000.0
        return "🟢" if millions > 10 else "🟡" if millions >= 2 else "🔴"
    if key == "volume_sum":
        millions = value / 1_000_000.0
        return "🟢" if millions > 1 else "🟡" if millions >= 0.3 else "🔴"
    if key == "volatility_cv":
        return "🟢" if value < 0.25 else "🟡" if value <= 0.45 else "🔴"
    if key == "apr_trend_avg":
        return "🟢" if value > 0 else "🟡" if value == 0 else "🔴"
    return "🟡"


# ---------------------------------------------------------------------------
# Widgets de base
# ---------------------------------------------------------------------------


class Card(ttk.Frame):
    """Petite carte avec un titre et un bloc de texte."""

    def __init__(self, master: tk.Misc, title: str, wrap: int = 420) -> None:
        super().__init__(master, padding=(12, 10))
        self.configure(borderwidth=1, relief="groove")
        self.columnconfigure(0, weight=1)

        title_font = tkfont.Font(self, family="Segoe UI", size=11, weight="bold")
        ttk.Label(self, text=title, font=title_font).grid(row=0, column=0, sticky="w")

        self.value_label = ttk.Label(
            self,
            text="—",
            wraplength=wrap,
            justify="left",
        )
        self.value_label.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

    def set_value(self, text: str) -> None:
        self.value_label.configure(text=text or "—")


class StatusBar(ttk.Frame):
    """Barre de statut en bas de la fenêtre."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=(8, 4))
        self.columnconfigure(0, weight=1)
        self.label = ttk.Label(self, text="", anchor="w")
        self.label.grid(row=0, column=0, sticky="ew")

    def set_status(
        self,
        last_data: Optional[datetime],
        last_ui: Optional[datetime],
        indicator: str = "",
    ) -> None:
        base = f"Dernière donnée : {_fmt_hms(last_data)} | Interface : {_fmt_hms(last_ui)}"
        if indicator:
            base = f"{base}   •   {indicator}"
        self.label.configure(text=base)


class MetricRow(ttk.Frame):
    """Ligne d'une métrique dans la carte « Métriques clés »."""

    def __init__(self, master: tk.Misc, label_text: str) -> None:
        super().__init__(master)
        self.columnconfigure(2, weight=1)

        ttk.Label(self, text=label_text).grid(row=0, column=0, sticky="w")
        self.emoji_label = ttk.Label(self, text="🟡", width=2)
        self.emoji_label.grid(row=0, column=1, sticky="w")
        self.value_label = ttk.Label(self, text="—", font=("Segoe UI", 10, "bold"))
        self.value_label.grid(row=0, column=2, sticky="e")

    def update(self, value: str, emoji: str) -> None:  # type: ignore[override]
        self.value_label.configure(text=value or "—")
        self.emoji_label.configure(text=emoji or "🟡")


class KeyMetricsCard(ttk.Frame):
    """Carte regroupant les métriques clés avec pastilles."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=(12, 10))
        self.configure(borderwidth=1, relief="groove")
        self.columnconfigure(0, weight=1)

        title_font = tkfont.Font(self, family="Segoe UI", size=11, weight="bold")
        ttk.Label(self, text="Métriques clés", font=title_font).grid(row=0, column=0, sticky="w")

        self._rows: Dict[str, MetricRow] = {}
        labels = {
            "apr_mean": "APR moyen",
            "tvl_sum": "TVL",
            "volume_sum": "Volume 24h",
            "volatility_cv": "Volatilité",
            "apr_trend_avg": "Tendance APR",
        }
        for idx, (key, label) in enumerate(labels.items(), start=1):
            row = MetricRow(self, label)
            row.grid(row=idx, column=0, sticky="ew", pady=2)
            self._rows[key] = row

    def update_metrics(self, metrics: Optional[Dict[str, Any]]) -> None:
        values = metrics or {}
        for name, row in self._rows.items():
            val = _safe_float(values.get(name))
            if name == "apr_mean":
                text = f"{val * 100:.2f} %" if val is not None else "—"
            elif name in {"tvl_sum", "volume_sum"}:
                text = f"{(val or 0) / 1_000_000:.2f} M$" if val is not None else "—"
            elif name == "apr_trend_avg":
                text = f"{val * 100:.2f} pts" if val is not None else "—"
            elif name == "volatility_cv":
                text = f"{val:.3f}" if val is not None else "—"
            else:
                text = _fmt_compact(val)
            row.update(text, _metric_color(name, val))


# ---------------------------------------------------------------------------
# Fenêtre principale
# ---------------------------------------------------------------------------


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.minsize(*MIN_SIZE)
        self.geometry(f"{MIN_SIZE[0]}x{MIN_SIZE[1]}")

        self._signals_path = _resolve_jsonl_path(JSONL_ENV_KEYS, DEFAULT_JSONL_PATH)
        self._control_path = _resolve_jsonl_path(CONTROL_JSONL_ENV_KEYS, DEFAULT_CONTROL_JSONL_PATH)

        self._last_signal_raw: Optional[str] = None
        self._last_signal_dt: Optional[datetime] = None
        self._last_ui_dt: Optional[datetime] = None

        self._history_rows: List[Dict[str, Any]] = []
        self._history_sort_column: Optional[str] = None
        self._history_sort_reverse: bool = False

        self._setup_theme()
        self._build_menu()
        self._build_layout()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._refresh(force=True)
        self.after(REFRESH_MS, self._tick)

    # ------------------------------------------------------------------ #
    # Setup UI
    # ------------------------------------------------------------------ #

    def _setup_theme(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=24)
        style.configure("TNotebook", padding=4)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Journal des signaux…", command=self._select_signals_path)
        file_menu.add_command(label="Journal de contrôle…", command=self._select_control_path)
        file_menu.add_separator()
        file_menu.add_command(label="Actualiser maintenant", command=lambda: self._refresh(force=True))
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

        self.card_journal = Card(top_frame, "Journal")
        self.card_journal.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        self.card_control = Card(top_frame, "ControlPilot")
        self.card_control.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)

        # Bas : résumé + historique
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
        resume_scroll = ttk.Scrollbar(self.resume_tab, orient="vertical", command=self.tree_resume.yview)
        self.tree_resume.configure(yscrollcommand=resume_scroll.set)
        self.tree_resume.grid(row=0, column=0, sticky="nsew")
        resume_scroll.grid(row=0, column=1, sticky="ns")

        self.notebook.add(self.resume_tab, text="Résumé actuel")

        # Onglet Historique
        self.history_tab = ttk.Frame(self.notebook)
        self.history_tab.columnconfigure(0, weight=1)
        self.history_tab.rowconfigure(0, weight=1)

        columns = [
            "timestamp",
            "context",
            "score",
            "apr",
            "tvl",
            "vol",
            "volume",
            "trend",
        ]
        headings = {
            "timestamp": "Horodatage",
            "context": "Contexte",
            "score": "Score",
            "apr": "APR moyen",
            "tvl": "TVL (M$)",
            "vol": "Volatilité",
            "volume": "Volume 24h (M$)",
            "trend": "Tendance APR",
        }

        self.tree_history = ttk.Treeview(
            self.history_tab,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=8,
        )

        for col in columns:
            self.tree_history.heading(col, text=headings[col], command=lambda c=col: self._on_history_heading_click(c))
            anchor = "e" if col not in {"timestamp", "context"} else "w"
            width = 150 if col == "timestamp" else 120
            if col == "context":
                width = 180
            self.tree_history.column(col, width=width, anchor=anchor)

        history_scroll_y = ttk.Scrollbar(self.history_tab, orient="vertical", command=self.tree_history.yview)
        history_scroll_x = ttk.Scrollbar(self.history_tab, orient="horizontal", command=self.tree_history.xview)
        self.tree_history.configure(yscrollcommand=history_scroll_y.set, xscrollcommand=history_scroll_x.set)
        self.tree_history.grid(row=0, column=0, sticky="nsew")
        history_scroll_y.grid(row=0, column=1, sticky="ns")
        history_scroll_x.grid(row=1, column=0, sticky="ew")

        self.notebook.add(self.history_tab, text="Historique des signaux")

        # Barre de statut
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=0, sticky="ew")

    # ------------------------------------------------------------------ #
    # Actions menu
    # ------------------------------------------------------------------ #

    def _select_signals_path(self) -> None:
        initial_dir = self._signals_path.parent if self._signals_path.exists() else Path.cwd()
        path_str = filedialog.askopenfilename(
            parent=self,
            title="Sélectionner un journal de signaux",
            initialdir=initial_dir,
            filetypes=[("JSON Lines", "*.jsonl"), ("Tous les fichiers", "*.*")],
        )
        if not path_str:
            return
        self._signals_path = Path(path_str)
        self._refresh(force=True)

    def _select_control_path(self) -> None:
        initial_dir = self._control_path.parent if self._control_path.exists() else Path.cwd()
        path_str = filedialog.askopenfilename(
            parent=self,
            title="Sélectionner un journal de contrôle",
            initialdir=initial_dir,
            filetypes=[("JSON Lines", "*.jsonl"), ("Tous les fichiers", "*.*")],
        )
        if not path_str:
            return
        self._control_path = Path(path_str)
        self._refresh(force=True)

    def _export_history_csv(self) -> None:
        if not self._history_rows:
            messagebox.showwarning("Export", "Aucune donnée d’historique à exporter.")
            return
        path_str = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter l'historique",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Tous les fichiers", "*.*")],
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            with path.open("w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=[
                        "timestamp",
                        "context",
                        "score",
                        "apr",
                        "tvl",
                        "vol",
                        "volume",
                        "trend",
                    ],
                )
                writer.writeheader()
                for row in self._history_rows:
                    writer.writerow(
                        {
                            "timestamp": _fmt_datetime(row.get("timestamp")),
                            "context": row.get("context") or "",
                            "score": f"{row.get('score'):.4f}" if row.get("score") is not None else "",
                            "apr": f"{row.get('apr') * 100:.4f}" if row.get("apr") is not None else "",
                            "tvl": f"{row.get('tvl'):.4f}" if row.get("tvl") is not None else "",
                            "vol": f"{row.get('vol'):.4f}" if row.get("vol") is not None else "",
                            "volume": f"{row.get('volume'):.4f}" if row.get("volume") is not None else "",
                            "trend": f"{row.get('trend'):.4f}" if row.get("trend") is not None else "",
                        }
                    )
        except OSError as exc:
            messagebox.showerror("Export", f"Impossible d'écrire le fichier : {exc}")
            return
        messagebox.showinfo("Export", f"Export CSV terminé : {path}")

    def _show_about(self) -> None:
        messagebox.showinfo(
            "À propos",
            f"DeFiPilot — Tableau de bord\nVersion : {APP_VERSION}\nSignaux : {self._signals_path}\nContrôle : {self._control_path}",
        )

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

        # Pas de nouveau signal et pas de refresh forcé -> mise à jour minimale
        last_raw_repr = json.dumps(signal_payload, sort_keys=True) if signal_payload else None
        if not force and last_raw_repr == self._last_signal_raw:
            self._update_history(signals_history)
            self._update_status(signal_payload)
            return

        self._last_signal_raw = last_raw_repr
        self._last_signal_dt = _parse_timestamp(signal_payload.get("timestamp")) if signal_payload else None

        self._update_cards(signal_payload, anomalies, control_events)
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
        try:
            events = safe_read_jsonl(
                self._control_path,
                max_lines=50,
                wait_if_locked=True,
                timeout_s=2.0,
                parse=True,
            )
        except Exception:
            events = []
        result: List[Dict[str, Any]] = []
        for payload in events:
            if isinstance(payload, dict):
                result.append(payload)
        return result

    def _analyze_control(self, events: List[Dict[str, Any]]) -> Optional[ResumeAnomalies]:
        if not events:
            return None
        try:
            return analyser_anomalies(events)
        except Exception:
            return None

    def _read_state(self) -> Optional[Dict[str, Any]]:
        try:
            state = get_state()
        except Exception:
            return None
        return state if isinstance(state, dict) else None

    def _read_strategy_snapshot(self) -> Optional[Dict[str, Any]]:
        """Lit le dernier snapshot de stratégie (si disponible)."""
        try:
            snapshot = lire_dernier_snapshot()
        except Exception:
            return None
        return snapshot if isinstance(snapshot, dict) else None

    # ------------------------------------------------------------------ #
    # Mise à jour des cartes / résumé / historique / statut
    # ------------------------------------------------------------------ #

    def _update_cards(
        self,
        signal_payload: Optional[Dict[str, Any]],
        anomalies: Optional[ResumeAnomalies],
        control_events: List[Dict[str, Any]],
    ) -> None:
        # Contexte
        ctx_lines: List[str] = []
        if signal_payload:
            context = signal_payload.get("context")
            last_context = signal_payload.get("last_context") or signal_payload.get("previous_context")
            ts = _parse_timestamp(signal_payload.get("timestamp"))
            if context:
                ctx_lines.append(f"Contexte : {context}")
            if last_context and last_context != context:
                ctx_lines.append(f"Précédent : {last_context}")
            ctx_lines.append(f"Horodatage : {_fmt_datetime(ts)}")
            note = signal_payload.get("note") or signal_payload.get("comment")
            if note:
                ctx_lines.append(f"Note : {note}")
        self.card_context.set_value("\n".join(ctx_lines) if ctx_lines else "—")

        # Policy
        policy = signal_payload.get("policy") if signal_payload else None
        self.card_policy.set_value(self._format_policy(policy))

        # Métriques
        metrics = None
        if signal_payload:
            for key in ("metrics_locales", "metrics"):
                cand = signal_payload.get(key)
                if isinstance(cand, dict):
                    metrics = cand
                    break
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

        control_text = self._format_control_card(anomalies, control_events)
        self.card_control.set_value(control_text)

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
        exists = self._signals_path.exists()
        try:
            size = self._signals_path.stat().st_size if exists else 0
        except OSError:
            size = 0
        locked_state = self._safe_is_locked(self._signals_path)
        ts = _parse_timestamp(signal_payload.get("timestamp")) if signal_payload else None
        fresh = _is_fresh_timestamp(ts)
        lines = [
            f"Chemin : {self._signals_path}",
            f"Présence : {'oui' if exists else 'non'}",
            f"Taille : {size / 1024:.1f} Ko" if exists else "Taille : —",
            f"Verrou : {self._bool_str(locked_state)}",
            f"Fraîcheur : {'OK' if fresh else 'Ancien' if ts else 'Inconnu'}",
        ]
        control_label = self._format_control_summary(anomalies, control_events)
        if control_label:
            lines.append(control_label)
        return "\n".join(lines)

    def _format_control_card(
        self,
        anomalies: Optional[ResumeAnomalies],
        control_events: List[Dict[str, Any]],
    ) -> str:
        if anomalies is None and not control_events:
            return "Aucun événement de contrôle disponible."
        summary = self._resume_to_dict(anomalies)
        level = summary.get("level") or summary.get("niveau") or summary.get("severity")
        headline = summary.get("headline") or summary.get("title") or summary.get("resume") or summary.get("summary")
        details = summary.get("details") or summary.get("message") or ""
        count = summary.get("count") or summary.get("nb_anomalies") or summary.get("total")
        ts = summary.get("timestamp")
        if not isinstance(ts, datetime) and control_events:
            ts = _parse_timestamp(control_events[-1].get("timestamp"))
        lines = []
        if level:
            lines.append(f"Statut : {level}")
        if headline:
            lines.append(f"Résumé : {headline}")
        if details:
            lines.append(f"Détails : {details}")
        if count is not None:
            lines.append(f"Anomalies : {count}")
        if ts:
            lines.append(f"Dernier contrôle : {_fmt_datetime(ts)}")
        return "\n".join(lines) if lines else "Contrôle : —"

    def _format_control_summary(
        self,
        anomalies: Optional[ResumeAnomalies],
        control_events: List[Dict[str, Any]],
    ) -> str:
        if anomalies is None and not control_events:
            return "Contrôle : aucun événement"
        summary = self._resume_to_dict(anomalies)
        level = summary.get("level") or summary.get("niveau") or summary.get("severity")
        resume_text = summary.get("resume") or summary.get("summary") or summary.get("message")
        count = summary.get("count") or summary.get("nb_anomalies") or summary.get("total")
        parts = ["Contrôle :"]
        if level:
            parts.append(f"niveau {level}")
        if count is not None:
            parts.append(f"{count} anomalies")
        if resume_text:
            parts.append(str(resume_text))
        if len(parts) == 1 and control_events:
            ts = _parse_timestamp(control_events[-1].get("timestamp"))
            parts.append(f"Dernier {_fmt_datetime(ts)}")
        return " ".join(parts)

    def _resume_to_dict(self, resume: Optional[ResumeAnomalies]) -> Dict[str, Any]:
        if resume is None:
            return {}
        if isinstance(resume, dict):
            return dict(resume)
        if hasattr(resume, "to_dict"):
            try:
                raw = resume.to_dict()
                if isinstance(raw, dict):
                    return dict(raw)
            except Exception:
                pass
        data: Dict[str, Any] = {}
        for attr in dir(resume):
            if attr.startswith("_"):
                continue
            try:
                value = getattr(resume, attr)
            except Exception:
                continue
            if callable(value):
                continue
            data[attr] = value
        return data

    def _update_resume(
        self,
        signal_payload: Optional[Dict[str, Any]],
        anomalies: Optional[ResumeAnomalies],
        control_events: List[Dict[str, Any]],
        state_snapshot: Optional[Dict[str, Any]],
        strategy_snapshot: Optional[Dict[str, Any]],
    ) -> None:
        for item in self.tree_resume.get_children():
            self.tree_resume.delete(item)
        rows: List[Tuple[str, str]] = []

        # Signaux
        if signal_payload:
            ts = _parse_timestamp(signal_payload.get("timestamp"))
            rows.append(("Journal signaux", str(self._signals_path)))
            rows.append(("Contexte", str(signal_payload.get("context") or "—")))
            rows.append(
                (
                    "Contexte précédent",
                    str(
                        signal_payload.get("last_context")
                        or signal_payload.get("previous_context")
                        or "—"
                    ),
                )
            )
            score = _safe_float(signal_payload.get("score"))
            rows.append(("Score", f"{score:.4f}" if score is not None else "—"))
            version = signal_payload.get("version") or signal_payload.get("defipilot_version") or "—"
            rows.append(("Version", str(version)))
            run_id = signal_payload.get("run_id") or signal_payload.get("id") or "—"
            rows.append(("Run ID", str(run_id)))
            rows.append(("Horodatage signal", _fmt_datetime(ts)))
            metrics = None
            for key in ("metrics_locales", "metrics"):
                cand = signal_payload.get(key)
                if isinstance(cand, dict):
                    metrics = cand
                    break
            if metrics:
                for key in ("apr_mean", "tvl_sum", "volume_sum", "volatility_cv", "apr_trend_avg"):
                    val = _safe_float(metrics.get(key))
                    rows.append((f"Métrique · {key}", _fmt_compact(val)))
        else:
            rows.append(("Journal signaux", str(self._signals_path)))
            rows.append(("Contexte", "—"))

        # Contrôle
        rows.append(("Journal contrôle", str(self._control_path)))
        summary = self._resume_to_dict(anomalies)
        level = summary.get("level") or summary.get("niveau") or summary.get("severity") or "—"
        resume_text = summary.get("resume") or summary.get("summary") or summary.get("message") or "—"
        count = summary.get("count") or summary.get("nb_anomalies") or summary.get("total")
        rows.append(("Contrôle · niveau", str(level)))
        rows.append(("Contrôle · résumé", str(resume_text)))
        rows.append(("Contrôle · nombre d'anomalies", str(count) if count is not None else "—"))
        if control_events:
            control_ts = _parse_timestamp(control_events[-1].get("timestamp"))
            rows.append(("Contrôle · horodatage", _fmt_datetime(control_ts)))

        # État DeFiPilot
        if state_snapshot:
            important_keys = ["mode", "cycle", "profil", "strategie", "etat", "segment"]
            for key in important_keys:
                if key in state_snapshot:
                    rows.append((f"État · {key}", _fmt_compact(state_snapshot[key])))
            if not any(k in state_snapshot for k in important_keys):
                for idx, (k, v) in enumerate(state_snapshot.items()):
                    if idx >= 5:
                        break
                    rows.append((f"État · {k}", _fmt_compact(v)))

        # Snapshot stratégie
        if strategy_snapshot:
            snap_ts = _parse_timestamp(strategy_snapshot.get("timestamp"))
            rows.append(("Stratégie · version", _fmt_compact(strategy_snapshot.get("version"))))
            rows.append(("Stratégie · contexte", _fmt_compact(strategy_snapshot.get("context"))))
            decision_score = _safe_float(strategy_snapshot.get("decision_score"))
            rows.append(
                (
                    "Stratégie · décision",
                    f"{decision_score:.3f}" if decision_score is not None else "—",
                )
            )
            rows.append(("Stratégie · profil", _fmt_compact(strategy_snapshot.get("profil"))))
            rows.append(("Stratégie · nb signaux", _fmt_compact(strategy_snapshot.get("nb_signaux"))))
            rows.append(("Stratégie · horodatage", _fmt_datetime(snap_ts)))

            scoring = strategy_snapshot.get("scoring")
            if isinstance(scoring, dict):
                solde_ref = _safe_float(scoring.get("solde_reference_usd"))
                gain_jour = _safe_float(scoring.get("gain_total_journalier_usd"))
                rows.append(
                    (
                        "Stratégie · solde réf (USD)",
                        f"{solde_ref:.2f}" if solde_ref is not None else "—",
                    )
                )
                rows.append(
                    (
                        "Stratégie · gain jour (USD)",
                        f"{gain_jour:.2f}" if gain_jour is not None else "—",
                    )
                )
                top3 = scoring.get("resultats_top3")
                if isinstance(top3, list) and top3:
                    first = top3[0]
                    label = None
                    s_val: Optional[float] = None
                    g_val: Optional[float] = None
                    if isinstance(first, (list, tuple)) and first:
                        try:
                            label = first[0]
                        except Exception:
                            label = str(first)
                        if len(first) > 1:
                            s_val = _safe_float(first[1])
                        if len(first) > 2:
                            g_val = _safe_float(first[2])
                    else:
                        label = str(first)

                    parts: List[str] = []
                    if label is not None:
                        parts.append(str(label))
                    if s_val is not None:
                        parts.append(f"score={s_val:.3f}")
                    if g_val is not None:
                        parts.append(f"gain={g_val:.2f} USD")
                    if parts:
                        rows.append(("Stratégie · Top 1", " | ".join(parts)))

        for key, value in rows:
            self.tree_resume.insert("", "end", values=(key, value))

    def _update_history(self, history: Iterable[Dict[str, Any]]) -> None:
        events: List[Dict[str, Any]] = []
        for payload in history:
            if not isinstance(payload, dict):
                continue
            ts = _parse_timestamp(payload.get("timestamp"))
            metrics = None
            for key in ("metrics_locales", "metrics"):
                cand = payload.get(key)
                if isinstance(cand, dict):
                    metrics = cand
                    break
            entry = {
                "timestamp": ts,
                "context": payload.get("context") if isinstance(payload.get("context"), str) else None,
                "score": _safe_float(payload.get("score")),
                "apr": _safe_float((metrics or {}).get("apr_mean")),
                "tvl": _safe_float((metrics or {}).get("tvl_sum")),
                "volume": _safe_float((metrics or {}).get("volume_sum")),
                "vol": _safe_float((metrics or {}).get("volatility_cv")),
                "trend": _safe_float((metrics or {}).get("apr_trend_avg")),
            }
            events.append(entry)
        self._history_rows = events
        self._render_history_rows()

    def _render_history_rows(self) -> None:
        data = list(self._history_rows)
        if self._history_sort_column:
            data.sort(
                key=lambda row: self._history_sort_key(row, self._history_sort_column or ""),
                reverse=self._history_sort_reverse,
            )
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)
        for row in data:
            values = [
                _fmt_datetime(row.get("timestamp")),
                row.get("context") or "—",
                f"{row.get('score'):.4f}" if row.get("score") is not None else "—",
                f"{row.get('apr') * 100:.2f} %" if row.get("apr") is not None else "—",
                f"{row.get('tvl') / 1_000_000:.2f} M$" if row.get("tvl") is not None else "—",
                f"{row.get('vol'):.3f}" if row.get("vol") is not None else "—",
                f"{row.get('volume') / 1_000_000:.2f} M$" if row.get("volume") is not None else "—",
                f"{row.get('trend') * 100:.2f} pts" if row.get("trend") is not None else "—",
            ]
            self.tree_history.insert("", "end", values=values)

    def _history_sort_key(self, row: Dict[str, Any], column: str) -> Any:
        value = row.get(column)
        if isinstance(value, datetime):
            return value.timestamp()
        if value is None:
            return float("-inf")
        if isinstance(value, (int, float)):
            return value
        try:
            return float(value)
        except (TypeError, ValueError):
            return str(value)

    def _on_history_heading_click(self, column_id: str) -> None:
        if self._history_sort_column == column_id:
            self._history_sort_reverse = not self._history_sort_reverse
        else:
            self._history_sort_column = column_id
            self._history_sort_reverse = False
        self._render_history_rows()

    def _safe_is_locked(self, path: Path) -> Optional[bool]:
        try:
            return bool(is_locked(path))
        except TypeError:
            try:
                return bool(is_locked(str(path)))
            except Exception:
                return None
        except Exception:
            return None

    def _bool_str(self, value: Optional[bool]) -> str:
        if value is True:
            return "oui"
        if value is False:
            return "non"
        return "?"

    def _tick_state_indicator(self, locked: Optional[bool], fresh: Optional[bool]) -> str:
        parts: List[str] = []
        if locked is True:
            parts.append("Journal verrouillé")
        elif locked is False:
            parts.append("Journal libre")
        if fresh is False:
            parts.append("Données anciennes")
        elif fresh is True:
            parts.append("Données fraîches")
        return " | ".join(parts)

    def _update_status(self, signal_payload: Optional[Dict[str, Any]]) -> None:
        ts = _parse_timestamp(signal_payload.get("timestamp")) if signal_payload else self._last_signal_dt
        locked_state = self._safe_is_locked(self._signals_path)
        fresh_state = _is_fresh_timestamp(ts) if ts else None
        indicator = self._tick_state_indicator(locked_state, fresh_state)
        self.status_bar.set_status(ts, self._last_ui_dt, indicator=indicator)


# ---------------------------------------------------------------------------
# Entrée
# ---------------------------------------------------------------------------


def run() -> None:
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run()
