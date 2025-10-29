# gui/main_window.py — V4.1.16
"""DeFiPilot — Tableau de bord (V4.1.16)

Amélioration :
- Colonne « Clé » désormais fixe (désactivation du redimensionnement manuel).
- Conserve la largeur 200 px pour stabilité visuelle.
"""

from __future__ import annotations
import csv
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont

# ============================
# Configuration
# ============================
JSONL_ENV_KEYS: tuple[str, ...] = (
    "DEFIPILOT_JOURNAL",
    "DEFIPILOT_SIGNALS_JSONL",
    "SIGNALS_JSONL_PATH",
    "MARKET_SIGNALS_JSONL",
)
DEFAULT_JSONL_PATH = Path("journal_signaux.jsonl")
REFRESH_MS = 1000

APP_TITLE = "DeFiPilot — Tableau de bord (V4.1.16)"
MIN_SIZE = (1024, 640)

# ============================
# Fonctions utilitaires
# ============================
def _resolve_jsonl_path() -> Path:
    for key in JSONL_ENV_KEYS:
        val = os.getenv(key)
        if val:
            try:
                return Path(val).expanduser().resolve()
            except Exception:
                return Path(val).expanduser()
    return DEFAULT_JSONL_PATH

def _now_tz() -> datetime:
    return datetime.now(timezone.utc).astimezone()

def _fmt_hms(dt: Optional[datetime]) -> str:
    if not isinstance(dt, datetime):
        return "--:--:--"
    return dt.astimezone().strftime("%H:%M:%S")

def _fmt_compact(value: Any) -> str:
    try:
        val = float(value)
    except Exception:
        return str(value)
    abs_val = abs(val)
    if abs_val >= 1_000_000_000:
        return f"{val/1_000_000_000:.2f} B"
    elif abs_val >= 1_000_000:
        return f"{val/1_000_000:.2f} M"
    elif abs_val >= 1_000:
        return f"{val/1_000:.2f} K"
    return f"{val:.2f}"

# ============================
# Lecture JSONL simplifiée
# ============================
@dataclass
class LastEvent:
    timestamp: Optional[datetime]
    context: Optional[str]
    last_context: Optional[str]
    policy: Optional[Dict[str, float]]
    score: Optional[float]
    version: Optional[str]
    run_id: Optional[str]
    metrics: Optional[Dict[str, float]]
    journal_path_label: Optional[str]
    raw_line: Optional[str]

def read_last_event(path: Path) -> LastEvent:
    if not path.exists():
        return LastEvent(None, None, None, None, None, None, None, None, None, None)
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        raw = lines[-1] if lines else None
        if not raw:
            return LastEvent(None, None, None, None, None, None, None, None, str(path), None)
        obj = json.loads(raw)
        return LastEvent(
            timestamp=_now_tz(),
            context=obj.get("context"),
            last_context=obj.get("last_context"),
            policy=obj.get("policy"),
            score=obj.get("score"),
            version=obj.get("version"),
            run_id=obj.get("run_id"),
            metrics=obj.get("metrics_locales"),
            journal_path_label=str(path),
            raw_line=raw,
        )
    except Exception:
        return LastEvent(None, None, None, None, None, None, None, None, str(path), None)

# ============================
# UI
# ============================
class Card(ttk.Frame):
    def __init__(self, master: tk.Misc, title: str) -> None:
        super().__init__(master, padding=(12, 10))
        self.columnconfigure(0, weight=1)
        self.configure(borderwidth=1, relief="groove")
        self._title = ttk.Label(self, text=title, font=("Segoe UI", 11, "bold"))
        self._title.grid(row=0, column=0, sticky="w")
        self._value = ttk.Label(self, text="—", font=("Segoe UI", 12), wraplength=460, justify="left")
        self._value.grid(row=1, column=0, sticky="w", pady=(6, 0))
    def set_value(self, text: str) -> None:
        self._value.configure(text=text)

class StatusBar(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=(6, 3))
        self.columnconfigure(0, weight=1)
        self._label = ttk.Label(self, text="", anchor="w")
        self._label.grid(row=0, column=0, sticky="ew")
    def set_status(self, last_data: Optional[datetime], last_ui: Optional[datetime], *, indicator: str = "") -> None:
        txt = f"Dernière donnée lue : {_fmt_hms(last_data)} | Mise à jour interface : {_fmt_hms(last_ui)}"
        if indicator:
            txt += f"   •   {indicator}"
        self._label.configure(text=txt)

class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{MIN_SIZE[0]}x{MIN_SIZE[1]}")
        self.minsize(*MIN_SIZE)
        self._setup_theme()
        self._build_menu()

        root = ttk.Frame(self, padding=12)
        root.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        grid = ttk.Frame(root)
        grid.grid(row=0, column=0, sticky="nsew")
        for i in range(2):
            grid.columnconfigure(i, weight=1, uniform="card")
            grid.rowconfigure(i, weight=1)

        self.card_context = Card(grid, "Contexte")
        self.card_context.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self.card_policy = Card(grid, "Allocation (policy)")
        self.card_policy.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        self.card_score = Card(grid, "Score")
        self.card_score.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))
        self.card_journal = Card(grid, "Journal")
        self.card_journal.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))

        summary = ttk.Frame(root, padding=(0, 12, 0, 0))
        summary.grid(row=1, column=0, sticky="nsew")
        summary.columnconfigure(0, weight=1)
        summary.rowconfigure(0, weight=1)

        self._summary_tree = ttk.Treeview(
            summary,
            columns=("col_key", "col_value"),
            show="headings",
            height=10,
            selectmode="browse",
        )
        self._summary_tree.heading("col_key", text="Clé")
        self._summary_tree.heading("col_value", text="Valeur")
        self._summary_tree.column("col_key", width=200, anchor="w", stretch=False)  # fixe
        self._summary_tree.column("col_value", anchor="e", stretch=True)

        yscroll = ttk.Scrollbar(summary, orient=tk.VERTICAL, command=self._summary_tree.yview)
        xscroll = ttk.Scrollbar(summary, orient=tk.HORIZONTAL, command=self._summary_tree.xview)
        self._summary_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self._summary_tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        self.status = StatusBar(self)
        self.status.grid(row=2, column=0, sticky="ew")

        self._jsonl_path = _resolve_jsonl_path()
        self._last_ui_dt: Optional[datetime] = None
        self.after(100, self._tick)

    def _setup_theme(self) -> None:
        style = ttk.Style(self)
        for name in ("clam", "vista", "default"):
            try:
                style.theme_use(name)
                break
            except Exception:
                continue
        style.configure("TFrame", background="#f6f7fb")
        style.configure("TLabel", background="#f6f7fb")
        style.configure("Treeview", background="white", fieldbackground="white", padding=(6, 3))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Actualiser maintenant", command=self._refresh_now)
        filemenu.add_command(label="Exporter le tableau en CSV…", command=self._export_table_csv)
        filemenu.add_separator()
        filemenu.add_command(label="Quitter", command=self.destroy)
        menubar.add_cascade(label="Fichier", menu=filemenu)
        self.config(menu=menubar)

    def _tick(self) -> None:
        last = read_last_event(self._jsonl_path)
        self._set_cards_from_last(last)
        indicator = "🟢 JSONL OK" if last.raw_line else ("🟡 JSONL vide" if self._jsonl_path.exists() else "🔴 JSONL introuvable")
        self._last_ui_dt = _now_tz()
        self.status.set_status(last.timestamp, self._last_ui_dt, indicator=indicator)
        self._update_summary_table(last, last.raw_line)
        self.after(REFRESH_MS, self._tick)

    def _refresh_now(self) -> None:
        last = read_last_event(self._jsonl_path)
        indicator = "🟢 JSONL OK" if last.raw_line else ("🟡 JSONL vide" if self._jsonl_path.exists() else "🔴 JSONL introuvable")
        self._last_ui_dt = _now_tz()
        self.status.set_status(last.timestamp, self._last_ui_dt, indicator=indicator)
        self._update_summary_table(last, last.raw_line)

    def _export_table_csv(self) -> None:
        try:
            default_name = f"defipilot_recap_{_now_tz().strftime('%Y%m%d_%H%M%S')}.csv"
            path = filedialog.asksaveasfilename(
                title="Exporter en CSV",
                defaultextension=".csv",
                initialfile=default_name,
                filetypes=(("CSV", "*.csv"), ("Tous les fichiers", "*.*")),
            )
            if not path:
                return
            rows = [("Clé", "Valeur")]
            for iid in self._summary_tree.get_children(""):
                vals = self._summary_tree.item(iid, "values")
                if len(vals) >= 2:
                    rows.append((str(vals[0]), str(vals[1])))
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(rows)
        except Exception as exc:
            messagebox.showerror("Export CSV", f"Échec de l'export : {exc}")
            return
        messagebox.showinfo("Export CSV", f"Exporté avec succès :\n{path}")

    def _set_cards_from_last(self, last: LastEvent) -> None:
        ctx_txt = last.context or "—"
        if last.last_context:
            ctx_txt = f"{ctx_txt}\nlast_context : {last.last_context}"
        self.card_context.set_value(ctx_txt)
        if last.policy:
            parts = [f"{k}: {v:.2f}" for k, v in sorted(last.policy.items(), key=lambda kv: -kv[1])]
            policy_txt = ", ".join(parts)
        else:
            policy_txt = "—"
        self.card_policy.set_value(policy_txt)
        score_txt = f"{last.score:.4f}" if last.score else "—"
        ts_txt = _fmt_hms(last.timestamp)
        lines = [f"Score : {score_txt}"]
        if last.version:
            lines.append(f"Version : {last.version}")
        lines.append(f"Horodatage : {ts_txt}")
        self.card_score.set_value("\n".join(lines))
        j_label = last.journal_path_label or str(self._jsonl_path)
        status = "OK" if (self._jsonl_path.exists() and last.raw_line) else ("vide" if self._jsonl_path.exists() else "introuvable")
        self.card_journal.set_value(f"{j_label} ({status})\nSource JSONL : {self._jsonl_path}")

    def _update_summary_table(self, last: LastEvent, raw: Optional[str]) -> None:
        tree = self._summary_tree
        for iid in tree.get_children():
            tree.delete(iid)
        metrics = last.metrics or {}
        rows = [
            ("contexte", last.context or "—"),
            ("last_context", last.last_context or "—"),
            ("score", f"{last.score:.4f}" if last.score else "—"),
            ("policy", ", ".join([f"{k}: {v:.2f}" for k, v in sorted((last.policy or {}).items(), key=lambda kv: -kv[1])]) if last.policy else "—"),
            ("version", last.version or "—"),
            ("run_id", last.run_id or "—"),
            ("timestamp", _fmt_hms(last.timestamp)),
            ("metrics.apr_mean", f"{metrics.get('apr_mean', '—'):.4f}" if metrics.get('apr_mean') else "—"),
            ("metrics.volume_sum", _fmt_compact(metrics.get('volume_sum', '—'))),
            ("metrics.tvl_sum", _fmt_compact(metrics.get('tvl_sum', '—'))),
            ("journal_path", last.journal_path_label or str(self._jsonl_path)),
            ("json_raw", raw or "—"),
        ]
        for key, value in rows:
            tree.insert("", "end", values=(key, value))

# ============================
# Main
# ============================
def main(argv: Optional[list[str]] = None) -> int:
    _ = argv or sys.argv[1:]
    app = MainWindow()
    app.mainloop()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
