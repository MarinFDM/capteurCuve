# capteurCuve

Jauge de cuve à eau connectée → Home Assistant via ESPHome sur ESP32.

## Matériel

| Composant | Détail |
|-----------|--------|
| Microcontrôleur | ESP32 (USB-C, CP2102) |
| Capteur ultrason | JSN-SR04T étanche + module driver AJ-SR04M (logique 5V) |
| Adaptateur niveau | Level shifter bidirectionnel 3.3V ↔ 5V |

**Câblage :**
- ESP32 3.3V → pin LV du level shifter
- Alimentation 5V → pin HV du level shifter
- ESP32 GPIO13 (Trig) / GPIO12 (Echo) → côté LV
- Module AJ-SR04M Trig/Echo → côté HV

## Cuve

| Paramètre | Valeur |
|-----------|--------|
| Forme | Rectangulaire |
| Dimensions (L × l × H) | 224 cm × 140 cm × 153,3 cm |
| Volume total | 3 000 L (valeur réelle fournie — les dimensions géométriques donneraient ~4 807 L) |
| Hauteur capteur / fond | 139,3 cm |

---

## Phase 1 — Test MicroPython (validation câblage)

Utiliser Thonny avec le script MicroPython pour vérifier le câblage et relever
les distances réelles :
- **Cuve vide** → noter `DIST_VIDE_M` (≈ 1,393 m au départ)
- **Cuve pleine** → noter `DIST_PLEIN_M` (≈ 0,200 m au départ — zone aveugle capteur ≥ 20 cm)

> **Note GPIO Phase 1 vs Phase 2 :** Le script MicroPython de test utilisait GPIO23 (Trig)
> et GPIO22 (Echo). La configuration ESPHome utilise GPIO13 (Trig) et GPIO12 (Echo).
> **Vérifiez votre câblage avant de flasher la Phase 2.**

---

## Phase 2 — Production ESPHome

### Fichiers

```
esphome/
├── capteur_cuve.yaml       # Configuration principale ESPHome
├── secrets.yaml.example    # Template secrets (commité, sans vraies valeurs)
└── secrets.yaml            # Vos vraies valeurs (ignoré par git, à créer localement)
```

### Pré-requis

- [ESPHome](https://esphome.io) installé (`pip install esphome` ou via Home Assistant add-on)
- Python 3.9+

### 1. Configurer les secrets

```bash
cp esphome/secrets.yaml.example esphome/secrets.yaml
# Éditer esphome/secrets.yaml et remplir :
#   wifi_ssid, wifi_password, ap_password, ota_password, api_encryption_key
```

> ⚠️ `esphome/secrets.yaml` est dans `.gitignore` — ce fichier avec vos vraies valeurs
> ne sera jamais commité. Ne commitez jamais de mots de passe ou clés API.

### 2. Adapter les paramètres d'étalonnage

Ouvrir `esphome/capteur_cuve.yaml` et modifier les `substitutions` :

```yaml
substitutions:
  DIST_VIDE_M:    "1.393"  # distance capteur→eau, cuve vide  (mesure Phase 1)
  DIST_PLEIN_M:   "0.200"  # distance capteur→eau, cuve pleine (mesure Phase 1)
                            # ⚠ Zone aveugle JSN-SR04T ~20-25 cm : ne pas descendre sous 0.20 m
  VOLUME_MAX_L:   "3000"   # volume réel de la cuve (litres)
                            # Note : dimensions géom. donneraient ~4807 L — utiliser la valeur mesurée
  SEUIL_ALERTE_L: "300"    # seuil alerte bas niveau (litres)
  PIN_TRIG: GPIO13          # broche Trig ESP32 (différent de la Phase 1 MicroPython : GPIO23)
  PIN_ECHO: GPIO12          # broche Echo ESP32 (différent de la Phase 1 MicroPython : GPIO22)
```

**Formules :**
- `niveau (%) = (DIST_VIDE_M − distance) / (DIST_VIDE_M − DIST_PLEIN_M) × 100` (clampé 0–100)
- `volume (L) = niveau% / 100 × VOLUME_MAX_L`

**Note sur VOLUME_MAX_L :** La valeur 3 000 L est celle fournie par l'utilisateur et correspond
au volume réel utilisable. Les dimensions géométriques de la cuve (224×140×153,3 cm) donneraient
théoriquement ~4 807 L. `VOLUME_MAX_L` doit toujours correspondre à la mesure physique réelle.

### 3. Flasher l'ESP32

**Première fois (USB) :**
```bash
esphome run esphome/capteur_cuve.yaml
```

**Mises à jour suivantes (OTA) :**
```bash
esphome run esphome/capteur_cuve.yaml --device <IP_ESP32>
```

**Compilation seule (vérification) :**
```bash
esphome compile esphome/capteur_cuve.yaml
```

### 4. Entités Home Assistant disponibles

Une fois le nœud intégré dans HA (via la découverte automatique mDNS) :

| Entité | Type | Unité | Description |
|--------|------|-------|-------------|
| `sensor.capteur_cuve_distance_brute` | sensor | m | Distance capteur → surface eau (filtre médiane + filtre zone aveugle) |
| `sensor.capteur_cuve_niveau_eau` | sensor | % | Niveau d'eau calculé |
| `sensor.capteur_cuve_volume_eau` | sensor | L | Volume d'eau restant |
| `binary_sensor.capteur_cuve_alerte_bas_niveau` | binary_sensor | — | ON si volume < 300 L (10 %), avec anti-chattering 30 s |

### 5. Alerte bas niveau dans Home Assistant

Exemple d'automatisation HA (YAML) :

```yaml
automation:
  - alias: "Alerte cuve eau basse"
    trigger:
      - platform: state
        entity_id: binary_sensor.capteur_cuve_alerte_bas_niveau
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: "⚠️ Niveau cuve bas : {{ states('sensor.capteur_cuve_volume_eau') }} L restants"
```

---

## Licence

MIT
