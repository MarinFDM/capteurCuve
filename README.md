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
| Volume total | 3 000 L |
| Hauteur capteur / fond | 139,3 cm |

---

## Phase 1 — Test MicroPython (validation câblage)

Utiliser Thonny avec le script MicroPython pour vérifier le câblage et relever
les distances réelles :
- **Cuve vide** → noter `DIST_VIDE_M` (≈ 1,393 m au départ)
- **Cuve pleine** → noter `DIST_PLEIN_M` (≈ 0,02 m au départ)

---

## Phase 2 — Production ESPHome

### Fichiers

```
esphome/
├── capteur_cuve.yaml   # Configuration principale ESPHome
└── secrets.yaml        # Secrets Wi-Fi / OTA / API (à ne pas committer)
```

### Pré-requis

- [ESPHome](https://esphome.io) installé (`pip install esphome` ou via Home Assistant add-on)
- Python 3.9+

### 1. Configurer les secrets

```bash
cp esphome/secrets.yaml esphome/secrets.yaml.local   # optionnel
# Éditer esphome/secrets.yaml et remplir :
#   wifi_ssid, wifi_password, ota_password, api_encryption_key
```

> ⚠️ `secrets.yaml` est dans `.gitignore` — ne jamais y mettre de vraies valeurs
> dans un fichier versionné.

### 2. Adapter les paramètres d'étalonnage

Ouvrir `esphome/capteur_cuve.yaml` et modifier les `substitutions` :

```yaml
substitutions:
  DIST_VIDE_M:   "1.393"   # distance capteur→eau, cuve vide  (mesure Phase 1)
  DIST_PLEIN_M:  "0.020"   # distance capteur→eau, cuve pleine (mesure Phase 1)
  VOLUME_MAX_L:  "3000"    # volume total de la cuve (litres)
  SEUIL_ALERTE_L: "300"    # seuil alerte bas niveau (litres)
  PIN_TRIG: GPIO13          # broche Trig ESP32
  PIN_ECHO: GPIO12          # broche Echo ESP32
```

**Formules :**
- `niveau (%) = (DIST_VIDE_M − distance) / (DIST_VIDE_M − DIST_PLEIN_M) × 100` (clampé 0–100)
- `volume (L) = niveau% / 100 × VOLUME_MAX_L`

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
| `sensor.capteur_cuve_distance_brute` | sensor | m | Distance capteur → surface eau (filtre médiane) |
| `sensor.capteur_cuve_niveau_eau` | sensor | % | Niveau d'eau calculé |
| `sensor.capteur_cuve_volume_eau` | sensor | L | Volume d'eau restant |
| `binary_sensor.capteur_cuve_alerte_bas_niveau` | binary_sensor | — | ON si volume < 300 L (10 %) |

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
