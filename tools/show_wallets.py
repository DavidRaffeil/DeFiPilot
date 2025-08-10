# tools/show_wallets.py – V3.4
"""
Utilitaire de lecture seule : liste les wallets disponibles et affiche le wallet par défaut.
"""

from core.wallets_manager import list_wallet_names, get_default_wallet


def main() -> None:
    try:
        wallets = list_wallet_names()
        default_wallet = get_default_wallet()
    except Exception as exc:  # Catch WalletConfigError specifically
        if exc.__class__.__name__ == "WalletConfigError":
            print(f"Erreur de configuration des wallets : {exc}")
            return
        raise

    print("Wallets disponibles : " + ", ".join(wallets))
    print(f"Wallet par défaut : {default_wallet['name']}")


if __name__ == "__main__":
    main()