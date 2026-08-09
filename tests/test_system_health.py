# tests/test_system_health.py – V6.0.0
"""Tests unitaires dédiés pour la Rotation des Logs, Nettoyage Automatique et Surveillance Système (Étape 3.2)."""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest

from core.system_health import (
    enregistrer_heartbeat,
    nettoyer_fichiers_temporaires,
    rotate_log_file,
    verifier_sante_daemon,
)


class TestSystemHealth(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = Path(tempfile.mkdtemp(prefix="defipilot_health_test_"))
        self.log_path = self.test_dir / "test_journal.log"
        self.health_path = self.test_dir / "health.json"

    def tearDown(self) -> None:
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_log_rotation(self) -> None:
        """Vérifier la rotation automatique des fichiers journaux lorsqu'ils dépassent la taille maximale."""
        # Création d'un fichier log dépassant 200 octets
        contenu_initial = "Ligne de journalisation de test pour valider la rotation des fichiers log.\n" * 10
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(contenu_initial)

        self.assertGreater(self.log_path.stat().st_size, 200)

        # Déclenchement de la rotation avec max_bytes=200
        rotated = rotate_log_file(self.log_path, max_bytes=200, backup_count=3)
        self.assertTrue(rotated)

        # Le fichier log.1 doit contenir le contenu initial
        log_backup_1 = Path(f"{self.log_path}.1")
        self.assertTrue(log_backup_1.exists())
        self.assertEqual(log_backup_1.stat().st_size, len(contenu_initial.encode("utf-8")))

    def test_heartbeat_health_check(self) -> None:
        """Vérifier l'enregistrement continu du heartbeat et la détection d'état HEALTHY."""
        payload = enregistrer_heartbeat(
            health_path=self.health_path,
            loop_count=42,
            run_id="run_test_health_123",
            extra_data={"mode": "simulation"},
        )

        self.assertEqual(payload["loop_count"], 42)
        self.assertTrue(self.health_path.exists())

        res_sante = verifier_sante_daemon(health_path=self.health_path, max_lag_seconds=30.0)
        self.assertTrue(res_sante["healthy"])
        self.assertEqual(res_sante["status"], "HEALTHY")
        self.assertEqual(res_sante["data"]["loop_count"], 42)

    def test_stale_heartbeat_detection(self) -> None:
        """Vérifier la détection d'un daemon bloqué ou inactif (STALE_HEARTBEAT)."""
        timestamp_obsolete = (
            (datetime.now(timezone.utc) - timedelta(seconds=600))
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        data_obsolete = {
            "timestamp": timestamp_obsolete,
            "status": "HEALTHY",
            "loop_count": 5,
        }
        with open(self.health_path, "w", encoding="utf-8") as f:
            json.dump(data_obsolete, f)

        res_sante = verifier_sante_daemon(health_path=self.health_path, max_lag_seconds=30.0)
        self.assertFalse(res_sante["healthy"])
        self.assertEqual(res_sante["status"], "STALE_HEARTBEAT")

    def test_temp_files_cleanup(self) -> None:
        """Vérifier le nettoyage sécurisé des fichiers temporaires .tmp obsolètes."""
        tmp_file_old = self.test_dir / "stale_data.tmp"
        tmp_file_recent = self.test_dir / "recent_data.tmp"
        valid_file = self.test_dir / "data.json"

        tmp_file_old.write_text("old_tmp")
        tmp_file_recent.write_text("recent_tmp")
        valid_file.write_text("{}")

        # Modifier le mtime du fichier ancien à 2 jours passés (172800 sec)
        mtime_passé = time.time() - 172800
        os.utime(tmp_file_old, (mtime_passé, mtime_passé))

        nettoyes = nettoyer_fichiers_temporaires(dir_path=self.test_dir, max_age_seconds=86400.0)
        self.assertIn(tmp_file_old, nettoyes)
        self.assertFalse(tmp_file_old.exists())
        self.assertTrue(tmp_file_recent.exists())
        self.assertTrue(valid_file.exists())


if __name__ == "__main__":
    unittest.main()
