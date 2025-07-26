# core/seuil.py

def calculer_seuil_dynamique(profil_utilisateur):
    """
    Calcule un seuil dynamique basé sur le profil de l'utilisateur.
    Exemple simplifié : seuil fixe pour chaque profil, ajustable si besoin.
    """
    base_seuil = {
        "prudent": 100,
        "modere": 50,
        "equilibre": 30,
        "dynamique": 20,
        "agressif": 10
    }

    nom = profil_utilisateur.get("nom", "modere")
    return base_seuil.get(nom, 50)
