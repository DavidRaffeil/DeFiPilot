# gui/main_window.py — V4.7.1
"""DeFiPilot — Tableau de bord principal (V4.7.1).

Version stable avec :
- Cartes « Contexte », « Allocation (policy) », « Score & version », « Journal ».
- Carte « Métriques clés » avec pastilles dynamiques.
- Tableau récapitulatif détaillé de l'état courant.
- Tableau « Historique des signaux » (dernières lignes du JSONL).
- Barre de statut avec horodatages et état du JSONL.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkfont

JSONL_ENV_KEYS = (
    "DEFIPILOT_JOURNAL",
    "DEFIPILOT_SIGNALS_JSONL",
    "SIGNALS_JSONL_PATH",
    "MARKET_SIGNALS_JSONL",
)
DEFAULT_JSONL_PATH = Path("journal_signaux.jsonl")
REFRESH_MS = 1_000
APP_VERSION = "V4.7.1"
APP_TITLE = f"DeFiPilot — Tableau de bord ({APP_VERSION})"
MIN_SIZE = (1120, 680)


def _resolve_jsonl_path() -> Path:
    for key in JSONL_ENV_KEYS:
        val = os.getenv(key)
        if val:
            try:
                return Path(val).expanduser().resolve()
            except OSError:
                return Path(val).expanduser()
    return DEFAULT_JSONL_PATH


def _now_tz() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).astimezone()
        except Exception:
            return None
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text).astimezone()
        except Exception:
            return None
    return None


def _fmt_datetime(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    return dt.astimezone().strftime("%d/%m/%Y %H:%M:%S")


def _fmt_hms(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    return dt.astimezone().strftime("%H:%M:%S")


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_compact(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


@dataclass
class LastEvent:
    timestamp: Optional[datetime]
    context: Optional[str]
    last_context: Optional[str]
    policy: Optional[Dict[str, Any]]
    score: Optional[float]
    version: Optional[str]
    run_id: Optional[str]
    metrics: Optional[Dict[str, Any]]
    raw_line: Optional[str]
    journal_path_label: str


def read_last_event(path: Path) -> LastEvent:
    label = str(path)
    if not path.exists():
        return LastEvent(
            timestamp=None,
            context=None,
            last_context=None,
            policy=None,
            score=None,
            version=None,
            run_id=None,
            metrics=None,
            raw_line=None,
            journal_path_label=label,
        )

    try:
        with path.open("r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f if line.strip()]
    except OSError:
        return LastEvent(
            timestamp=None,
            context=None,
            last_context=None,
            policy=None,
            score=None,
            version=None,
            run_id=None,
            metrics=None,
            raw_line=None,
            journal_path_label=label,
        )

    if not lines:
        return LastEvent(
            timestamp=None,
            context=None,
            last_context=None,
            policy=None,
            score=None,
            version=None,
            run_id=None,
            metrics=None,
            raw_line=None,
            journal_path_label=label,
        )

    raw = lines[-1]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {}

    ts = _parse_timestamp(payload.get("timestamp")) or _now_tz()
    context = payload.get("context")
    last_context = payload.get("last_context") or payload.get("previous_context")
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else None
    score = _safe_float(payload.get("score"))
    version = payload.get("version") or payload.get("defipilot_version")
    run_id = payload.get("run_id") or payload.get("id")
    metrics = payload.get("metrics_locales") or payload.get("metrics")
    if not isinstance(metrics, dict):
        metrics = None

    return LastEvent(
        timestamp=ts,
        context=context,
        last_context=last_context,
        policy=policy,
        score=score,
        version=version,
        run_id=run_id,
        metrics=metrics,
        raw_line=raw,
        journal_path_label=label,
    )


def read_history_events(path: Path, max_events: int = 100) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if not path.exists():
        return events

    try:
        with path.open("r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f if line.strip()]
    except OSError:
        return events

    if not lines:
        return events

    for raw in lines[-max_events:]:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        ts = _parse_timestamp(payload.get("timestamp")) or _now_tz()
        metrics = payload.get("metrics_locales") or payload.get("metrics") or {}
        if not isinstance(metrics, dict):
            metrics = {}
        events.append(
            {
                "timestamp": ts,
                "context": payload.get("context"),
                "score": _safe_float(payload.get("score")),
                "apr_mean": _safe_float(metrics.get("apr_mean")),
                "tvl_sum": _safe_float(metrics.get("tvl_sum")),
                "volume_sum": _safe_float(metrics.get("volume_sum")),
                "volatility_cv": _safe_float(metrics.get("volatility_cv")),
                "apr_trend_avg": _safe_float(metrics.get("apr_trend_avg")),
            }
        )
    return events


def _metric_color(name: str, value: Optional[float]) -> str:
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


class Card(ttk.Frame):
    def __init__(self, master: tk.Misc, title: str, wrap: int = 420) -> None:
        super().__init__(master, padding=(12, 10))
        self.configure(borderwidth=1, relief="groove")
        title_font = tkfont.Font(self, family="Segoe UI", size=11, weight="bold")
        value_font = tkfont.Font(self, family="Segoe UI", size=11)
        ttk.Label(self, text=title, font=title_font).grid(row=0, column=0, sticky="w")
        self.value_label = ttk.Label(
            self,
            text="—",
            font=value_font,
            wraplength=wrap,
            justify="left",
        )
        self.value_label.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

    def set_value(self, text: str) -> None:
        self.value_label.configure(text=text or "—")


class StatusBar(ttk.Frame):
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
        status = f"Dernière donnée : {_fmt_hms(last_data)} | Interface : {_fmt_hms(last_ui)}"
        if indicator:
            status += f"   •   {indicator}"
        self.label.configure(text=status)


class MetricRow:
    def __init__(self, master: ttk.Frame, label: str, row: int) -> None:
        name_font = tkfont.Font(master, family="Segoe UI", size=10, weight="bold")
        value_font = tkfont.Font(master, family="Segoe UI", size=10)
        emoji_font = tkfont.Font(master, family="Segoe UI Emoji", size=14)

        ttk.Label(master, text=label, font=name_font).grid(row=row, column=0, sticky="w", pady=2)
        self.emoji_label = ttk.Label(master, text="🟡", font=emoji_font)
        self.emoji_label.grid(row=row, column=1, sticky="w", padx=(8, 4))
        self.value_label = ttk.Label(master, text="—", font=value_font)
        self.value_label.grid(row=row, column=2, sticky="w")

    def update(self, value: str, emoji: str) -> None:
        self.value_label.configure(text=value)
        self.emoji_label.configure(text=emoji)


class KeyMetricsCard(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=(12, 10))
        self.configure(borderwidth=1, relief="groove")

        title_font = tkfont.Font(self, family="Segoe UI", size=11, weight="bold")
        ttk.Label(self, text="Métriques clés", font=title_font).grid(row=0, column=0, columnspan=3, sticky="w")

        self.rows: Dict[str, MetricRow] = {}
        self.rows["apr_mean"] = MetricRow(self, "APR moyen", row=1)
        self.rows["tvl_sum"] = MetricRow(self, "TVL", row=2)
        self.rows["volume_sum"] = MetricRow(self, "Volume 24h", row=3)
        self.rows["volatility_cv"] = MetricRow(self, "Volatilité", row=4)
        self.rows["apr_trend_avg"] = MetricRow(self, "Tendance APR", row=5)

    def update_metrics(self, metrics: Optional[Dict[str, Any]]) -> None:
        data = metrics or {}
        for key, row in self.rows.items():
            raw = data.get(key)
            val = _safe_float(raw)
            if val is None:
                row.update("—", "🟡")
                continue
            if key == "apr_mean":
                display = f"{val * 100:.2f} %"
            elif key in ("tvl_sum", "volume_sum"):
                display = f"{val / 1_000_000.0:.2f} M$"
            elif key == "volatility_cv":
                display = f"{val:.2f}"
            elif key == "apr_trend_avg":
                display = f"{val * 100:.2f} %"
            else:
                display = _fmt_compact(val)
            row.update(display, _metric_color(key, val))


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(*MIN_SIZE)
        self.geometry(f"{MIN_SIZE[0]}x{MIN_SIZE[1]}")

        self._jsonl_path = _resolve_jsonl_path()
        self._last_raw_line: Optional[str] = None
        self._last_data_dt: Optional[datetime] = None
        self._last_ui_dt: Optional[datetime] = None

        self._setup_theme()
        self._build_menu()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ttk.Frame(self, padding=12)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=3)
        container.rowconfigure(1, weight=2)

        cards = ttk.Frame(container)
        cards.grid(row=0, column=0, sticky="nsew")
        for col in range(3):
            cards.columnconfigure(col, weight=1, uniform="card")
        for row in range(2):
            cards.rowconfigure(row, weight=1)

        self.card_context = Card(cards, "Contexte")
        self.card_context.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        self.card_policy = Card(cards, "Allocation (policy)")
        self.card_policy.grid(row=0, column=1, sticky="nsew", padx=8, pady=(0, 8))

        self.card_metrics = KeyMetricsCard(cards)
        self.card_metrics.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(8, 0), pady=(0, 8))

        self.card_score = Card(cards, "Score & version")
        self.card_score.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))

        self.card_journal = Card(cards, "Journal")
        self.card_journal.grid(row=1, column=1, sticky="nsew", padx=8, pady=(8, 0))

        bottom = ttk.Frame(container, padding=(0, 8, 0, 0))
        bottom.grid(row=1, column=0, sticky="nsew")
        bottom.columnconfigure(0, weight=1)
        bottom.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(bottom)
        notebook.grid(row=0, column=0, sticky="nsew")

        tab_summary = ttk.Frame(notebook)
        tab_summary.columnconfigure(0, weight=1)
        tab_summary.rowconfigure(0, weight=1)

        self._summary_tree = ttk.Treeview(
            tab_summary,
            columns=("key", "value"),
            show="headings",
            height=10,
            selectmode="browse",
        )
        self._summary_tree.heading("key", text="Clé")
        self._summary_tree.heading("value", text="Valeur")
        self._summary_tree.column("key", width=260, anchor="w", stretch=False)
        self._summary_tree.column("value", anchor="w", stretch=True)

        yscroll_sum = ttk.Scrollbar(tab_summary, orient=tk.VERTICAL, command=self._summary_tree.yview)
        self._summary_tree.configure(yscrollcommand=yscroll_sum.set)
        self._summary_tree.grid(row=0, column=0, sticky="nsew")
        yscroll_sum.grid(row=0, column=1, sticky="ns")

        notebook.add(tab_summary, text="Résumé actuel")

        tab_history = ttk.Frame(notebook)
        tab_history.columnconfigure(0, weight=1)
        tab_history.rowconfigure(0, weight=1)

        self._history_tree = ttk.Treeview(
            tab_history,
            columns=("ts", "context", "score", "apr", "tvl", "vol", "volume", "trend"),
            show="headings",
            height=10,
            selectmode="browse",
        )

        headings: Dict[str, str] = {
            "ts": "Timestamp",
            "context": "Contexte",
            "score": "Score",
            "apr": "APR moyen",
            "tvl": "TVL (M$)",
            "vol": "Volatilité",
            "volume": "Volume 24h (M$)",
            "trend": "Tendance APR",
        }
        widths: Dict[str, int] = {
            "ts": 160,
            "context": 110,
            "score": 70,
            "apr": 90,
            "tvl": 90,
            "vol": 90,
            "volume": 130,
            "trend": 110,
        }

        self._history_sort_state: Dict[str, bool] = {}

        for key, title in headings.items():
            self._history_tree.heading(
                key,
                text=title,
                command=lambda c=key: self._on_history_heading_click(c),
            )
            self._history_tree.column(key, width=widths.get(key, 90), anchor="e", stretch=False)

        self._history_tree.column("ts", anchor="w")
        self._history_tree.column("context", anchor="w")

        yscroll_hist = ttk.Scrollbar(tab_history, orient=tk.VERTICAL, command=self._history_tree.yview)
        self._history_tree.configure(yscrollcommand=yscroll_hist.set)
        self._history_tree.grid(row=0, column=0, sticky="nsew")
        yscroll_hist.grid(row=0, column=1, sticky="ns")

        notebook.add(tab_history, text="Historique des signaux")

        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=0, sticky="ew")

        self._refresh_data(force=True)
        self.after(REFRESH_MS, self._tick)

    def _setup_theme(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#f6f7fb")
        style.configure("TLabel", background="#f6f7fb")
        style.configure("Treeview", background="white", fieldbackground="white", font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Ouvrir un journal…", command=self._select_jsonl_path)
        file_menu.add_command(label="Actualiser maintenant", command=self._refresh_now)
        file_menu.add_command(label="Exporter le tableau en CSV…", command=self._export_table_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.destroy)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="À propos", command=self._show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)

        self.config(menu=menubar)

    def _select_jsonl_path(self) -> None:
        initial_dir = self._jsonl_path.parent if self._jsonl_path.exists() else Path.cwd()
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Sélectionner un journal JSONL",
            initialdir=initial_dir,
            filetypes=(("JSON Lines", "*.jsonl"), ("Tous les fichiers", "*.*")),
        )
        if file_path:
            self._jsonl_path = Path(file_path)
            self._refresh_data(force=True)

    def _show_about(self) -> None:
        messagebox.showinfo(
            "À propos",
            f"DeFiPilot — Tableau de bord\nVersion : {APP_VERSION}\nJournal : {self._jsonl_path}",
        )

    def _tick(self) -> None:
        self._refresh_data()
        self.after(REFRESH_MS, self._tick)

    def _refresh_now(self) -> None:
        self._refresh_data(force=True)

    def _refresh_data(self, *, force: bool = False) -> None:
        event = read_last_event(self._jsonl_path)
        if (not event.timestamp or event.raw_line == self._last_raw_line) and not force:
            self._update_history_table()
            return

        self._last_raw_line = event.raw_line
        self._last_data_dt = event.timestamp

        ctx_lines: List[str] = []
        if event.context:
            ctx_lines.append(str(event.context))
        if event.last_context:
            ctx_lines.append(f"Contexte précédent : {event.last_context}")
        self.card_context.set_value("\n".join(ctx_lines) if ctx_lines else "—")

        if event.policy:
            parts = []
            for k, v in event.policy.items():
                try:
                    parts.append(f"{k}: {float(v)*100:.2f} %")
                except Exception:
                    parts.append(f"{k}: {v}")
            self.card_policy.set_value("\n".join(parts))
        else:
            self.card_policy.set_value("—")

        score_lines: List[str] = []
        score_lines.append(f"Score : {event.score:.4f}" if event.score is not None else "Score : —")
        score_lines.append(f"Version : {event.version or '—'}")
        score_lines.append(f"Run ID : {event.run_id or '—'}")
        score_lines.append(f"Horodatage : {_fmt_datetime(event.timestamp)}")
        self.card_score.set_value("\n".join(score_lines))

        journal_lines: List[str] = [f"Fichier : {event.journal_path_label}"]
        if not self._jsonl_path.exists():
            status = "introuvable"
        elif event.raw_line:
            status = "OK"
        else:
            status = "vide"
        journal_lines.append(f"Statut : {status}")
        journal_lines.append(f"Source JSONL : {self._jsonl_path}")
        self.card_journal.set_value("\n".join(journal_lines))

        self.card_metrics.update_metrics(event.metrics if isinstance(event.metrics, dict) else None)

        self._summary_tree.delete(*self._summary_tree.get_children())
        self._summary_tree.insert("", "end", values=("Horodatage", _fmt_datetime(event.timestamp)))
        self._summary_tree.insert("", "end", values=("Version", event.version or "—"))
        self._summary_tree.insert("", "end", values=("Run ID", event.run_id or "—"))
        self._summary_tree.insert("", "end", values=("Contexte", event.context or "—"))
        self._summary_tree.insert("", "end", values=("Contexte précédent", event.last_context or "—"))
        self._summary_tree.insert(
            "",
            "end",
            values=("Score", f"{event.score:.6f}" if event.score is not None else "—"),
        )

        if event.policy:
            for k, v in event.policy.items():
                try:
                    val = f"{float(v)*100:.2f} %"
                except Exception:
                    val = str(v)
                self._summary_tree.insert("", "end", values=(f"Policy · {k}", val))

        if event.metrics and isinstance(event.metrics, dict):
            for key, value in event.metrics.items():
                self._summary_tree.insert(
                    "",
                    "end",
                    values=(f"Métrique · {key}", _fmt_compact(value)),
                )

        self._summary_tree.insert("", "end", values=("Journal", event.journal_path_label))
        self._summary_tree.insert("", "end", values=("JSON brut", event.raw_line or "—"))

        self._update_history_table()

        self._last_ui_dt = _now_tz()
        indicator = (
            "🟢 JSONL OK"
            if event.raw_line
            else ("🟡 JSONL vide" if self._jsonl_path.exists() else "🔴 JSONL introuvable")
        )
        self.status_bar.set_status(self._last_data_dt, self._last_ui_dt, indicator=indicator)

    def _update_history_table(self) -> None:
        events = read_history_events(self._jsonl_path, max_events=100)
        events = list(reversed(events))

        self._history_tree.delete(*self._history_tree.get_children())
        for ev in events:
            ts_txt = _fmt_datetime(ev.get("timestamp"))
            ctx = ev.get("context") or "—"
            score = ev.get("score")
            score_txt = f"{score:.4f}" if isinstance(score, float) else "—"

            apr = ev.get("apr_mean")
            apr_txt = f"{apr * 100:.2f} %" if isinstance(apr, float) else "—"

            tvl = ev.get("tvl_sum")
            tvl_txt = f"{(tvl / 1_000_000.0):.2f}" if isinstance(tvl, float) else "—"

            vol = ev.get("volatility_cv")
            vol_txt = f"{vol:.2f}" if isinstance(vol, float) else "—"

            volume = ev.get("volume_sum")
            volume_txt = f"{(volume / 1_000_000.0):.2f}" if isinstance(volume, float) else "—"

            trend = ev.get("apr_trend_avg")
            trend_txt = f"{trend * 100:.2f} %" if isinstance(trend, float) else "—"

            self._history_tree.insert(
                "",
                "end",
                values=(
                    ts_txt,
                    ctx,
                    score_txt,
                    apr_txt,
                    tvl_txt,
                    vol_txt,
                    volume_txt,
                    trend_txt,
                ),
            )

    def _on_history_heading_click(self, column_id: str) -> None:
        item_ids = list(self._history_tree.get_children(""))
        ascending = self._history_sort_state.get(column_id, True)

        def key_func(item_id: str) -> Any:
            value = self._history_tree.set(item_id, column_id)
            text = str(value).strip()
            normalized = (
                text.replace("%", "")
                .replace("M$", "")
                .replace("m$", "")
                .replace(" ", "")
                .replace("\u202f", "")
                .replace(",", ".")
            )
            if normalized:
                try:
                    return float(normalized)
                except ValueError:
                    pass
            dt_text = text.replace("\u202f", " ").strip()
            if column_id in {"ts", "timestamp", "datetime"} or ("T" in dt_text and ":" in dt_text):
                iso_text = dt_text.replace("Z", "+00:00")
                try:
                    return datetime.fromisoformat(iso_text)
                except ValueError:
                    pass
                for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                    try:
                        return datetime.strptime(dt_text, fmt)
                    except ValueError:
                        continue
            return text.lower()

        sorted_ids = sorted(item_ids, key=key_func, reverse=not ascending)
        for index, item_id in enumerate(sorted_ids):
            self._history_tree.move(item_id, "", index)
        if sorted_ids:
            self._history_tree.see(sorted_ids[0])
        self._history_sort_state[column_id] = not ascending

    def _export_table_csv(self) -> None:
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter le tableau en CSV",
            defaultextension=".csv",
            filetypes=(("CSV", "*.csv"), ("Tous les fichiers", "*.*")),
        )
        if not file_path:
            return

        rows: List[tuple[Any, Any]] = []
        for iid in self._summary_tree.get_children(""):
            vals = self._summary_tree.item(iid, "values")
            if vals:
                rows.append(vals)

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Clé", "Valeur"])
                writer.writerows(rows)
            messagebox.showinfo("Export réussi", f"Tableau exporté vers : {file_path}")
        except Exception as exc:
            messagebox.showerror("Erreur d'export", str(exc))


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
