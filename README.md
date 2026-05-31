# Capteur Cuve à Eau — ESPHome + Home Assistant

Jauge de cuve à eau connectée via ESP32, capteur ultrason JSN-SR04T/AJ-SR04M et ESPHome.

---

## 📦 Matériel

| Composant | Référence |
|-----------|-----------|
| **Microcontrôleur** | ESP32 (USB-C, CP2102) |
| **Capteur ultrason** | JSN-SR04T étanche + module driver AJ-SR04M (logique 5V) |
| **Adaptateur niveau** | Level shifter bidirectionnel 3.3V ↔ 5V |

### 🔌 Câblage

**ESP32 (3.3V) ↔ Level Shifter ↔ Module AJ-SR04M (5V)**

```
ESP32               Level Shifter          AJ-SR04M
─────               ─────────────          ────────
3.3V    ──────────► LV
                    
GPIO17  ──────────► LV1 ────► HV1 ──────► Trig
GPIO16  ◄──────────  LV2 ◄──── HV2 ◄────── Echo

GND     ──────────────────────────────────► GND

5V      ──────────► HV ────────────────────► 5V (VCC)
```

> **⚠️ Note GPIO Phase 1 vs Phase 2**  
> Le script MicroPython de test (Phase 1) utilisait **GPIO23** (Trig) et **GPIO22** (Echo).  
> La configuration ESPHome (Phase 2) utilise **GPIO17** (Trig) et **GPIO16** (Echo).  
> **Vérifiez et adaptez votre câblage avant de flasher !**

---

## 🏗️ Structure du projet

```
📁 capteurCuve/
├── 📁 esphome/
│   ├── capteur_cuve.yaml        # Configuration ESPHome principale
│   ├── secrets.yaml.example     # Template secrets (commité, sans valeurs sensibles)
│   └── secrets.yaml             # Vos vraies valeurs (ignoré par git, à créer)
├── test_cuve.py                 # Script MicroPython Phase 1 (validation câblage)
├── boite_corps_v3-2.STL         # Boîtier 3D (corps)
├── boite_couvercle_v3-2.STL     # Boîtier 3D (couvercle)
└── README.md                    # Ce fichier
```

---

## 📏 Spécifications cuve

| Paramètre | Valeur |
|-----------|--------|
| **Forme** | Rectangulaire |
| **Dimensions** (L × l × H) | 224 cm × 140 cm × 153.3 cm |
| **Volume utilisable** | **3 000 L** (valeur réelle fournie) |
| **Volume géométrique théorique** | ~4 807 L (dimensions × 100%) |

> **Note :** Le volume configuré dans ESPHome (`VOLUME_MAX_L = 3000`) correspond au volume **réel utilisable** de la cuve, pas au volume géométrique théorique.

---

## 🚀 Déploiement

### Phase 1 — Test et calibration (MicroPython)

**Objectif :** Valider le câblage et mesurer les distances réelles.

#### 1.1 Installer MicroPython sur l'ESP32

1. Télécharger le firmware MicroPython pour ESP32 : [micropython.org/download/esp32](https://micropython.org/download/esp32/)
2. Flasher avec `esptool.py` :
   ```bash
   esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
   esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-*.bin
   ```

#### 1.2 Exécuter le script de test

1. Ouvrir **Thonny** (IDE Python pour MicroPython)
2. Connecter l'ESP32 en USB
3. Sélectionner l'interpréteur : `MicroPython (ESP32)` sur le port série approprié
4. Ouvrir `test_cuve.py` et **l'exécuter** (F5)

#### 1.3 Relever les mesures de calibration

Le script affiche en continu les distances mesurées avec filtre médiane.

**Mesures à noter :**

| Condition | Paramètre ESPHome | Valeur à relever |
|-----------|-------------------|------------------|
| **Cuve VIDE** (capteur → fond) | `DIST_VIDE_M` | Distance affichée en **mètres** |
| **Cuve PLEINE** (capteur → surface eau max) | `DIST_PLEIN_M` | Distance affichée en **mètres** |

> **⚠️ Zone aveugle du capteur**  
> Le JSN-SR04T/AJ-SR04M ne peut **pas mesurer en dessous de ~20 cm**.  
> `DIST_PLEIN_M` doit être **≥ 0.20 m** sous peine de lectures erratiques.

**Exemple de sortie :**

```
[Mesure  42] Distance brute :  139.3 cm | Médiane (5) :  139.1 cm | 1.391 m
```

→ Cuve vide : noter `DIST_VIDE_M = 1.391`  
→ Cuve pleine : noter `DIST_PLEIN_M = 0.200` (minimum conseillé)

---

### Phase 2 — Production (ESPHome)

**Objectif :** Déployer la configuration finale sur Home Assistant.

#### 2.1 Pré-requis

- **ESPHome** installé :
  - Via Home Assistant : add-on ESPHome (recommandé)
  - Ou standalone : `pip install esphome`
- **Python 3.9+**
- **Mesures de calibration** relevées en Phase 1

#### 2.2 Configurer les secrets

```bash
cd esphome/
cp secrets.yaml.example secrets.yaml
```

Éditez `secrets.yaml` et renseignez :

```yaml
wifi_ssid: "VotreSSID"
wifi_password: "VotreMotDePasseWiFi"
ap_password: "motdepasseAP"         # Pour le point d'accès de secours
ota_password: "motdepasseOTA"       # Générer avec secrets.token_hex(16)
api_encryption_key: "cléBase64=="   # Générer avec ESPHome ou secrets.token_bytes(32)
```

> **🔒 Sécurité :** `secrets.yaml` est dans `.gitignore` — **ne le commitez jamais**.

#### 2.3 Adapter les paramètres de calibration

Ouvrir `esphome/capteur_cuve.yaml` et modifier les `substitutions` :

```yaml
substitutions:
  # ⚠️ REMPLACER PAR VOS VALEURS MESURÉES EN PHASE 1
  DIST_VIDE_M:    "1.391"   # Distance capteur→surface, cuve VIDE (mesure Phase 1)
  DIST_PLEIN_M:   "0.200"   # Distance capteur→surface, cuve PLEINE (mesure Phase 1)
                             # ⚠️ Minimum absolu : 0.20 m (zone aveugle capteur)
  VOLUME_MAX_L:   "3000"    # Volume réel utilisable de la cuve (litres)
  SEUIL_ALERTE_L: "300"     # Seuil alerte bas niveau (10% de VOLUME_MAX_L)
  
  # GPIO ESP32 (vérifier votre câblage !)
  PIN_TRIG: GPIO17
  PIN_ECHO: GPIO16
```

**Formules de calcul :**

- **Niveau (%)** = `(DIST_VIDE_M - distance_mesurée) / (DIST_VIDE_M - DIST_PLEIN_M) × 100`  
  *(clampé entre 0 et 100)*

- **Volume (L)** = `niveau% / 100 × VOLUME_MAX_L`

#### 2.4 Valider la configuration

```bash
esphome compile esphome/capteur_cuve.yaml
```

Si la compilation réussit ✅, passer au flash.

#### 2.5 Flasher l'ESP32

**Première fois (USB obligatoire) :**

```bash
esphome run esphome/capteur_cuve.yaml
```

Sélectionner le port série (ex. `/dev/ttyUSB0`).

**Mises à jour suivantes (OTA sans fil) :**

```bash
esphome run esphome/capteur_cuve.yaml --device <IP_ESP32>
```

#### 2.6 Intégration Home Assistant

1. L'ESP32 se connecte au WiFi
2. Home Assistant détecte automatiquement le nœud via **mDNS** (Notifications → "ESPHome")
3. Cliquer sur **"Configurer"** et entrer la clé API (`api_encryption_key`)

---

## 📊 Entités Home Assistant disponibles

Une fois le nœud intégré :

| Entité | Type | Unité | Description |
|--------|------|-------|-------------|
| `sensor.capteur_cuve_distance_brute` | sensor | m | Distance capteur → surface eau (filtre médiane 7 échantillons) |
| `sensor.capteur_cuve_niveau_eau` | sensor | % | Niveau d'eau calculé (0-100%) |
| `sensor.capteur_cuve_volume_eau` | sensor | L | Volume d'eau restant (litres) |
| `binary_sensor.capteur_cuve_alerte_bas_niveau` | binary_sensor | — | ON si volume < `SEUIL_ALERTE_L` (anti-chattering 30s) |

---

## 🔔 Automatisation Home Assistant (exemple)

**Alerte notification si niveau bas :**

```yaml
automation:
  - alias: "Alerte cuve eau basse"
    trigger:
      - platform: state
        entity_id: binary_sensor.capteur_cuve_alerte_bas_niveau
        to: "on"
    action:
      - service: notify.mobile_app_votre_telephone
        data:
          title: "⚠️ Niveau cuve bas"
          message: "Il reste {{ states('sensor.capteur_cuve_volume_eau') }} L d'eau dans la cuve."
```

**Carte Lovelace (exemple) :**

```yaml
type: entities
title: Cuve à Eau
entities:
  - entity: sensor.capteur_cuve_volume_eau
    name: Volume restant
  - entity: sensor.capteur_cuve_niveau_eau
    name: Niveau
  - entity: binary_sensor.capteur_cuve_alerte_bas_niveau
    name: Alerte bas niveau
```

---

## 🧪 Dépannage

### Problème : Distance affichée = 0 ou NaN

**Causes possibles :**
- Câblage incorrect (vérifier level shifter, Trig/Echo inversés)
- Capteur hors portée (>4 m) ou zone aveugle (<20 cm)
- Alimentation 5V insuffisante pour le module AJ-SR04M

**Solutions :**
1. Vérifier le câblage avec le script Phase 1 (`test_cuve.py`)
2. Activer les logs ESPHome : `logger: level: DEBUG`
3. Vérifier l'alimentation 5V stable

### Problème : Valeurs fluctuantes malgré le filtre médiane

**Causes possibles :**
- Échos parasites (objet proche du capteur, paroi métallique)
- Montage instable du capteur (vibrations)

**Solutions :**
1. Augmenter `window_size` du filtre médiane (ex. `11` au lieu de `7`)
2. Éloigner le capteur des parois latérales (>30 cm recommandé)
3. Fixer solidement le capteur

### Problème : ESP32 redémarre en boucle

**Causes possibles :**
- Alimentation insuffisante (courant trop faible)
- Conflit GPIO (strapping pins)

**Solutions :**
1. Utiliser une alimentation 5V/2A minimum
2. Éviter GPIO 0, 2, 12, 15 (strapping pins ESP32)

---

## 📜 Licence

MIT

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Ouvrir une issue ou une PR sur GitHub.

---

**🏷️ Tags :** ESP32, ESPHome, Home Assistant, JSN-SR04T, AJ-SR04M, cuve eau, ultrason, IoT
