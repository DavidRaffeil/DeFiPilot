"""Interface CLI centrale pour DeFiPilot.

Ce module propose un menu texte permettant de lancer une simulation,
d'afficher les dernières entrées du journal, de changer de profil actif ou
de quitter l'application.
"""

from __future__ import annotations

import importlib
import re
import subprocess
import sys
from pathlib import Path

# Import dynamique du module profil pour pouvoir le recharger après modification
try:  # Protection contre tout problème d'importation
    import core.profil as profil_module
except Exception as import_error:  # pragma: no cover - improbable
    profil_module = None
    print(f"[ERREUR] Impossible d'importer core.profil : {import_error}")


def _afficher_menu(profil_actif: str) -> None:
    """Affiche le menu principal avec le profil actif."""
    print("=== ControlPilot – Centre de Commande DeFiPilot ===")
    print(f"Profil actif : {profil_actif}\n")
    print("[1] Lancer une simulation")
    print("[2] Afficher les 5 dernières lignes du journal logs/journal_resume.csv")
    print("[3] Changer de profil actif")
    print("[4] Quitter")


def _lancer_simulation() -> None:
    """Exécute ``main.py`` dans un sous-processus."""
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as exc:
        print(f"[ERREUR] Échec du lancement de la simulation : {exc}")
    except Exception as exc:  # pragma: no cover - pour toute autre erreur
        print(f"[ERREUR] Problème inattendu lors de l'exécution : {exc}")


def _afficher_journal() -> None:
    """Affiche les cinq dernières lignes du fichier de journal."""
    journal_path = Path("logs/journal_resume.csv")
    try:
        with journal_path.open("r", encoding="utf-8") as fichier:
            lignes = fichier.readlines()
            for ligne in lignes[-5:]:
                print(ligne.rstrip())
    except FileNotFoundError:
        print("[INFO] Aucun journal trouvé à logs/journal_resume.csv")
    except Exception as exc:
        print(f"[ERREUR] Lecture du journal impossible : {exc}")


def _changer_profil() -> None:
    """Permet de modifier le profil actif dans ``core/profil.py``."""
    choix = input("Choisir un profil (prudent, modere, agressif) : ")
    choix = choix.strip().lower()

    if choix not in {"prudent", "modere", "agressif"}:
        print("[INFO] Profil invalide, aucune modification effectuée.")
        return

    try:
        profil_file = Path("core/profil.py")
        contenu = profil_file.read_text(encoding="utf-8")
        nouveau_contenu = re.sub(
            r'PROFIL_ACTIF\s*=\s*".*?"',
            f'PROFIL_ACTIF = "{choix}"',
            contenu,
        )
        profil_file.write_text(nouveau_contenu, encoding="utf-8")

        # Recharger le module pour que le changement soit pris en compte
        if profil_module is not None:
            importlib.reload(profil_module)

        print(f"[OK] Profil actif changé en {choix}.")
    except Exception as exc:
        print(f"[ERREUR] Impossible de changer le profil : {exc}")


def main() -> None:
    """Boucle principale du menu CLI."""
    while True:
        try:
            profil_actif = (
                profil_module.charger_profil_utilisateur()["nom"]
                if profil_module is not None
                else "inconnu"
            )
        except Exception as exc:  # pragma: no cover - sécurité
            print(f"[ERREUR] Chargement du profil impossible : {exc}")
            profil_actif = "inconnu"

        _afficher_menu(profil_actif)
        choix = input("Votre choix : ").strip()

        if choix == "1":
            _lancer_simulation()
        elif choix == "2":
            _afficher_journal()
        elif choix == "3":
            _changer_profil()
        elif choix == "4":
            print("Fermeture de ControlPilot.")
            break
        else:
            print("[INFO] Option invalide, veuillez choisir de 1 à 4.")


if __name__ == "__main__":  # pragma: no cover - exécution directe
    main()
