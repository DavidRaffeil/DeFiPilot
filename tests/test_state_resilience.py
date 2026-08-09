# tests/test_state_resilience.py – V6.0.0
"""Tests unitaires dédiés pour la Gestion de l'État et Résilience au Redémarrage (Étape 3.1)."""

import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from core.state_manager import (
    StateLockError,
    acquire_state_lock,
    get_state,
    load_state,
    release_state_lock,
    save_state,
    start_auto_save,
    stop_auto_save,
    update_state,
)


class TestStateResilience(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp(prefix="defipilot_state_test_")
        self.state_path = Path(self.test_dir) / "state.json"
        self.lock_path = Path(self.test_dir) / "defipilot.lock"

    def tearDown(self) -> None:
        release_state_lock()
        stop_auto_save()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_atomic_save_and_load(self) -> None:
        """Vérifier la sauvegarde atomique et le rechargement exact de l'état."""
        nouvel_etat = {"version": "V6.0.0", "balances": {"USDC": 1500.0, "WETH": 1.2}}
        update_state(nouvel_etat, path=self.state_path)
        save_state(nouvel_etat, path=self.state_path)

        self.assertTrue(self.state_path.exists())
        bak_path = self.state_path.with_suffix(self.state_path.suffix + ".bak")
        
        # Deuxième sauvegarde pour s'assurer que le fichier backup est généré
        update_state({"version": "V6.0.0", "balances": {"USDC": 2000.0}}, path=self.state_path)
        save_state(None, path=self.state_path)
        self.assertTrue(bak_path.exists())

        etat_charge = load_state(path=self.state_path)
        self.assertEqual(etat_charge.get("balances", {}).get("USDC"), 2000.0)

    def test_corruption_recovery_from_backup(self) -> None:
        """Vérifier la restauration automatique transparente depuis le fichier .bak en cas de corruption de state.json."""
        etat_sain = {"version": "V6.0.0", "status": "OK", "balances": {"USDC": 5000.0}}
        save_state(etat_sain, path=self.state_path)

        # Deuxième écriture pour générer le backup sain
        etat_mis_a_jour = {"version": "V6.0.0", "status": "OK_V2", "balances": {"USDC": 5000.0}}
        save_state(etat_mis_a_jour, path=self.state_path)

        # Simulation d'une corruption brutale du fichier principal (écriture tronquée ou JSON corrompu)
        with open(self.state_path, "w", encoding="utf-8") as f:
            f.write("{ INVALID_CORRUPTED_JSON_DATA_--- ")

        # Rechargement : doit automatiquement basculer sur state.json.bak
        etat_restaure = load_state(path=self.state_path)
        self.assertIsNotNone(etat_restaure)
        self.assertEqual(etat_restaure.get("version"), "V6.0.0")

    def test_file_lock_prevents_concurrent_instances(self) -> None:
        """Vérifier que le verrou de fichier (acquire_state_lock) empêche l'exécution simultanée d'une seconde instance."""
        acquire_state_lock(self.lock_path)
        self.assertTrue(self.lock_path.exists())

        # Tentative d'acquisition du même verrou dans le même processus ou instance concurrente
        with self.assertRaises(StateLockError):
            acquire_state_lock(self.lock_path)

        # Libération et vérification de la ré-acquisition
        release_state_lock()
        acquire_state_lock(self.lock_path)
        release_state_lock()

    def test_auto_save_thread_safety(self) -> None:
        """Vérifier le démarrage, le fonctionnement thread-safe et l'arrêt propre de l'auto-save."""
        start_auto_save(interval_seconds=0.2, path=self.state_path)
        update_state({"test_key": "auto_save_val"}, path=self.state_path)

        # Attendre le déclenchement de l'auto-save
        import time
        time.sleep(0.5)

        stop_auto_save()
        self.assertTrue(self.state_path.exists())


if __name__ == "__main__":
    unittest.main()
