# =============================================================================
# test_cuve.py — Phase 1 : Test de distance JSN-SR04T via AJ-SR04M
# Matériel : ESP32 (3.3V) + level shifter BSS138 + module AJ-SR04M (5V)
# GPIO 23 → Trig (OUTPUT) | GPIO 22 → Echo (INPUT)
# MicroPython v1.20+ recommandé
# =============================================================================

from machine import Pin, time_pulse_us
import time

# -----------------------------------------------------------------------------
# CONFIGURATION — modifier ici si vous changez de broches
# -----------------------------------------------------------------------------
PIN_TRIG = 23          # GPIO reliée au Trig du AJ-SR04M (via level shifter)
PIN_ECHO = 22          # GPIO reliée à l'Echo du AJ-SR04M (via level shifter)

# Vitesse du son dans l'air à ~20°C = 343 m/s = 0.0343 cm/µs
# La durée de l'écho correspond à l'aller-retour, donc on divise par 2
VITESSE_SON_CM_US = 0.0343   # cm par microseconde

# Timeout Echo : si l'écho ne revient pas en 38 ms, le capteur est hors portée
# 38 ms correspond à une distance de ~650 cm (bien au-delà de la portée du JSN-SR04T)
TIMEOUT_US = 38000     # microsecondes

# Nombre d'échantillons pour le filtre médiane
NB_ECHANTILLONS = 5

# Intervalle entre chaque affichage (secondes)
INTERVALLE_S = 1.0

# -----------------------------------------------------------------------------
# INITIALISATION DES BROCHES
# -----------------------------------------------------------------------------
trig = Pin(PIN_TRIG, Pin.OUT)   # Trig en sortie
echo = Pin(PIN_ECHO, Pin.IN)    # Echo en entrée

# S'assurer que Trig est bas au démarrage (état repos)
trig.value(0)

print("=" * 60)
print("  Test JSN-SR04T / AJ-SR04M — Jauge de cuve à eau")
print(f"  Trig=GPIO{PIN_TRIG}  Echo=GPIO{PIN_ECHO}")
print(f"  Filtre médiane sur {NB_ECHANTILLONS} échantillons")
print("=" * 60)
print()
time.sleep(0.5)  # Laisser le module se stabiliser


# -----------------------------------------------------------------------------
# FONCTION : mesure_distance_cm()
# Envoie une impulsion Trig et mesure la durée de l'écho.
# Retourne la distance en cm, ou None si hors portée / timeout.
# -----------------------------------------------------------------------------
def mesure_distance_cm():
    """
    Protocole de déclenchement du AJ-SR04M en mode impulsion :
      1. Mettre Trig à 0 pendant 2 µs (état propre)
      2. Mettre Trig à 1 pendant ≥ 10 µs (impulsion de déclenchement)
      3. Remettre Trig à 0
      4. Mesurer la durée pendant laquelle Echo reste à 1
      5. Distance (cm) = durée (µs) × vitesse_son (cm/µs) / 2
    """
    # Étape 1 : stabiliser Trig à 0
    trig.value(0)
    time.sleep_us(2)

    # Étape 2 : impulsion Trig ≥ 10 µs
    trig.value(1)
    time.sleep_us(10)

    # Étape 3 : fin de l'impulsion
    trig.value(0)

    # Étape 4 : mesurer la durée de l'écho (en µs)
    # time_pulse_us() attend que la broche passe à 1, puis mesure le temps
    # jusqu'à ce qu'elle repasse à 0. Retourne -1 si timeout.
    duree_us = time_pulse_us(echo, 1, TIMEOUT_US)

    # Étape 5 : vérifier le timeout
    if duree_us < 0:
        # Valeur négative = timeout ou erreur de lecture
        return None

    # Étape 6 : calculer la distance
    # duree_us = temps aller-retour → diviser par 2 pour la distance simple
    distance_cm = (duree_us * VITESSE_SON_CM_US) / 2.0

    # Sanity check : JSN-SR04T ne mesure pas en dessous de ~20 cm (zone aveugle)
    # ni au-delà de ~600 cm (limite physique)
    if distance_cm < 20.0 or distance_cm > 600.0:
        return None  # Valeur hors plage physique du capteur

    return distance_cm


# -----------------------------------------------------------------------------
# FONCTION : mediane(liste)
# Calcule la valeur médiane d'une liste de nombres.
# La médiane est plus robuste que la moyenne contre les valeurs aberrantes.
# -----------------------------------------------------------------------------
def mediane(valeurs):
    """
    Trie la liste et retourne la valeur centrale.
    Exemple : [45, 44, 99, 45, 44] → trié : [44, 44, 45, 45, 99] → médiane : 45
    Le faux écho à 99 cm est ignoré !
    """
    triee = sorted(valeurs)
    n = len(triee)
    return triee[n // 2]


# -----------------------------------------------------------------------------
# BOUCLE PRINCIPALE
# -----------------------------------------------------------------------------
compteur = 0                     # Numéro de mesure affiché
tampon = []                      # Tampon pour le filtre médiane

print("Démarrage des mesures... (Ctrl+C pour arrêter)\n")

while True:
    # --- Mesure brute individuelle ---
    distance_brute = mesure_distance_cm()

    if distance_brute is None:
        # Timeout ou hors portée : afficher un avertissement
        compteur += 1
        print(f"[Mesure {compteur:>3}] ⚠ HORS PORTÉE ou timeout — vérifier câblage et orientation capteur")
        time.sleep(INTERVALLE_S)
        continue

    # --- Ajout dans le tampon médiane ---
    tampon.append(distance_brute)

    # Garder seulement les NB_ECHANTILLONS dernières valeurs (fenêtre glissante)
    if len(tampon) > NB_ECHANTILLONS:
        tampon.pop(0)  # Supprimer la valeur la plus ancienne

    # --- Calcul de la médiane (seulement si le tampon est plein) ---
    if len(tampon) == NB_ECHANTILLONS:
        distance_mediane_cm = mediane(tampon)
        distance_mediane_m  = distance_mediane_cm / 100.0

        compteur += 1
        print(
            f"[Mesure {compteur:>3}] "
            f"Distance brute : {distance_brute:>6.1f} cm | "
            f"Médiane ({NB_ECHANTILLONS}) : {distance_mediane_cm:>6.1f} cm | "
            f"{distance_mediane_m:.3f} m"
        )
    else:
        # Tampon en cours de remplissage (5 premières mesures)
        compteur += 1
        print(
            f"[Mesure {compteur:>3}] "
            f"Distance brute : {distance_brute:>6.1f} cm | "
            f"Remplissage tampon ({len(tampon)}/{NB_ECHANTILLONS})..."
        )

    # --- Attendre avant la prochaine mesure ---
    # Note : laisser ≥ 60 ms entre deux mesures pour éviter que l'écho
    # d'une mesure précédente soit capté comme Echo de la suivante.
    time.sleep(INTERVALLE_S)
