# Guide de Calibration — Capteur Cuve à Eau

Ce document explique comment calibrer votre capteur de cuve à eau pour obtenir des mesures précises de niveau et de volume.

---

## 🎯 Objectif

Mesurer les **distances réelles** entre le capteur et la surface de l'eau dans deux conditions :
1. **Cuve VIDE** → `DIST_VIDE_M`
2. **Cuve PLEINE** → `DIST_PLEIN_M`

Ces valeurs seront ensuite utilisées dans la configuration ESPHome pour calculer le niveau (%) et le volume (litres).

---

## 📋 Pré-requis

- ✅ ESP32 + JSN-SR04T/AJ-SR04M câblés avec level shifter
- ✅ MicroPython installé sur l'ESP32
- ✅ Thonny IDE installé sur votre ordinateur
- ✅ Script `test_cuve.py` du dépôt
- ✅ Cuve accessible (vide ET pleine pour les mesures)

---

## 🔧 Étape 1 : Installation MicroPython

Si ce n'est pas déjà fait :

1. **Télécharger** le firmware MicroPython pour ESP32 :  
   [micropython.org/download/esp32](https://micropython.org/download/esp32/)  
   → Choisir la version stable la plus récente (ex. `esp32-20230602-v1.20.0.bin`)

2. **Installer esptool.py** (si nécessaire) :
   ```bash
   pip install esptool
   ```

3. **Effacer la flash de l'ESP32** :
   ```bash
   esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
   ```
   (Remplacer `/dev/ttyUSB0` par votre port série : `/dev/ttyACM0` sous Linux, `COM3` sous Windows)

4. **Flasher MicroPython** :
   ```bash
   esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-*.bin
   ```

5. **Vérifier** : débrancher/rebrancher l'ESP32, puis lancer Thonny → l'ESP32 doit apparaître dans la liste des interpréteurs.

---

## 🔬 Étape 2 : Exécution du script de test

1. **Ouvrir Thonny**

2. **Sélectionner l'interpréteur MicroPython** :
   - Menu : `Exécuter` → `Sélectionner l'interpréteur...`
   - Choisir : `MicroPython (ESP32)` sur le port série de l'ESP32

3. **Ouvrir le script** `test_cuve.py` (bouton "Ouvrir")

4. **Vérifier les GPIO** dans le script :
   ```python
   PIN_TRIG = 23   # GPIO23 (Trig)
   PIN_ECHO = 22   # GPIO22 (Echo)
   ```
   > **Note :** Ces GPIO (23/22) sont les mêmes pour Phase 1 et Phase 2.  
   > Pas de recâblage nécessaire entre les phases.

5. **Exécuter** (F5 ou bouton ▶️)

Le script affiche en continu les mesures :

```
==============================================================
  Test JSN-SR04T / AJ-SR04M — Jauge de cuve à eau
  Trig=GPIO23  Echo=GPIO22
  Filtre médiane sur 5 échantillons
==============================================================

Démarrage des mesures... (Ctrl+C pour arrêter)

[Mesure   1] Distance brute :  138.7 cm | Remplissage tampon (1/5)...
[Mesure   2] Distance brute :  139.1 cm | Remplissage tampon (2/5)...
[Mesure   3] Distance brute :  139.3 cm | Remplissage tampon (3/5)...
[Mesure   4] Distance brute :  138.9 cm | Remplissage tampon (4/5)...
[Mesure   5] Distance brute :  139.0 cm | Remplissage tampon (5/5)...
[Mesure   6] Distance brute :  139.2 cm | Médiane (5) :  139.0 cm | 1.390 m
[Mesure   7] Distance brute :  139.1 cm | Médiane (5) :  139.1 cm | 1.391 m
...
```

---

## 📏 Étape 3 : Mesure DIST_VIDE_M (cuve vide)

1. **S'assurer que la cuve est VIDE** (ou au minimum d'eau utilisable)

2. **Monter le capteur** à sa position définitive au-dessus de la cuve

3. **Lancer le script** (si ce n'est pas déjà fait)

4. **Attendre la stabilisation** (le filtre médiane se remplit en 5 mesures)

5. **Noter la valeur médiane stable** affichée en mètres (dernière colonne)

**Exemple :**
```
[Mesure  42] Distance brute :  139.3 cm | Médiane (5) :  139.1 cm | 1.391 m
```

→ **DIST_VIDE_M = 1.391** (à noter pour la configuration ESPHome)

**Recommandation :** Faire plusieurs relevés à quelques minutes d'intervalle et prendre la moyenne pour plus de précision.

---

## 📏 Étape 4 : Mesure DIST_PLEIN_M (cuve pleine)

1. **Remplir la cuve au niveau maximum d'eau utilisable**  
   (= niveau d'eau lorsque la cuve est considérée "pleine" pour votre usage)

2. **Le script doit toujours être en cours d'exécution**  
   (sinon, le relancer)

3. **Attendre la stabilisation** des mesures

4. **Vérifier que la distance mesurée est ≥ 20 cm** (zone aveugle du capteur)

   - ✅ **Si distance ≥ 20 cm** : noter la valeur
   - ❌ **Si distance < 20 cm** : le capteur est **trop proche de la surface**  
     → **Remonter le capteur** ou accepter que le niveau "100%" corresponde à une distance de 20 cm minimum

**Exemple :**
```
[Mesure  89] Distance brute :   20.3 cm | Médiane (5) :   20.1 cm | 0.201 m
```

→ **DIST_PLEIN_M = 0.201** (ou arrondir à **0.20** si proche de la limite)

**⚠️ Attention zone aveugle :**  
Si la mesure affiche `NAN` ou `HORS PORTÉE`, c'est que le capteur est dans la zone aveugle (<20 cm). **Remonter le capteur de quelques centimètres.**

---

## 📝 Étape 5 : Récapitulatif des valeurs

Compléter ce tableau :

| Paramètre | Votre valeur (m) | Description |
|-----------|------------------|-------------|
| **DIST_VIDE_M** | ____________ | Distance capteur → surface, cuve VIDE |
| **DIST_PLEIN_M** | ____________ | Distance capteur → surface, cuve PLEINE (≥ 0.20 m) |
| **VOLUME_MAX_L** | 3000 | Volume réel utilisable de la cuve (fourni) |

---

## ⚙️ Étape 6 : Mise à jour de la configuration ESPHome

1. Ouvrir le fichier `esphome/capteur_cuve.yaml`

2. Modifier les `substitutions` avec **vos valeurs mesurées** :

```yaml
substitutions:
  DIST_VIDE_M:    "1.391"   # ⬅️ Remplacer par votre valeur
  DIST_PLEIN_M:   "0.201"   # ⬅️ Remplacer par votre valeur
  VOLUME_MAX_L:   "3000"    # Volume réel de la cuve (fourni)
  SEUIL_ALERTE_L: "300"     # Seuil alerte (10% de VOLUME_MAX_L)
```

3. **Sauvegarder** le fichier

4. **Flasher l'ESP32** avec ESPHome (voir README.md Phase 2)

---

## ✅ Validation

Une fois la configuration ESPHome déployée et l'ESP32 intégré à Home Assistant :

1. **Vérifier** l'entité `sensor.capteur_cuve_niveau_eau` :
   - Cuve vide → doit afficher **≈ 0%**
   - Cuve pleine → doit afficher **≈ 100%**

2. **Vérifier** l'entité `sensor.capteur_cuve_volume_eau` :
   - Cuve pleine → doit afficher **≈ 3000 L**
   - Cuve à moitié → doit afficher **≈ 1500 L**

3. **Si les valeurs sont incohérentes**, revérifier `DIST_VIDE_M` et `DIST_PLEIN_M`.

---

## 🔄 Recalibration

Si vous déplacez le capteur ou modifiez la cuve, **recommencer la calibration** (Étapes 3-6).

---

## 🛠️ Dépannage calibration

### Problème : Le script affiche toujours "HORS PORTÉE"

**Causes possibles :**
- Câblage incorrect (Trig/Echo inversés, level shifter mal connecté)
- Alimentation 5V insuffisante
- GPIO incorrects dans le script

**Solutions :**
1. Vérifier le câblage (voir schéma dans README.md)
2. Vérifier l'alimentation 5V avec un multimètre
3. Vérifier les valeurs `PIN_TRIG` et `PIN_ECHO` dans `test_cuve.py`

### Problème : Mesures instables (fluctuent de plusieurs cm)

**Causes possibles :**
- Échos parasites (objets proches, parois métalliques)
- Surface de l'eau agitée

**Solutions :**
1. Attendre que l'eau se calme
2. Éloigner le capteur des parois (>30 cm recommandé)
3. Augmenter `NB_ECHANTILLONS` dans le script (ex. passer de 5 à 11)

### Problème : Distance mesurée < 20 cm impossible à atteindre

**Cause :** Zone aveugle du capteur JSN-SR04T/AJ-SR04M (~20-25 cm)

**Solution :** 
- **Remonter le capteur** de quelques centimètres
- **Ou accepter** que le niveau "100%" corresponde à une distance de 20 cm (→ il restera toujours ~20 cm d'eau "invisible" au capteur)

---

**🎯 Objectif atteint :** Vous disposez maintenant des valeurs de calibration précises pour déployer la Phase 2 ESPHome !
