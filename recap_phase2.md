# Récapitulatif Phase 2 ESPHome — Configuration Propre

**Date :** 2026-05-31  
**Session :** e3ad1a2e-3e2e-4e4f-8703-2effee0c02d2  
**Projet :** Cuve (capteurCuve)  
**Orchestrateur :** 40eb84c7-1146-4d1d-8db8-814637494489

---

## 🎯 Objectif accompli

Reprise complète de la Phase 2 depuis zéro avec une configuration ESPHome propre, bien documentée et prête pour la production, en tenant compte des informations de calibration d'une cuve rectangulaire de 3000 L.

---

## 📦 Livrables créés/modifiés

### 1. Configuration ESPHome (`esphome/capteur_cuve.yaml`)

**Changements majeurs :**
- ✨ **Restructuration complète** avec annotations détaillées et contexte
- 🎯 **Paramètres de calibration clairement identifiés** dans les `substitutions` :
  - `DIST_VIDE_M` : Distance capteur → surface, cuve VIDE (⚠️ à remplacer par mesure Phase 1)
  - `DIST_PLEIN_M` : Distance capteur → surface, cuve PLEINE (⚠️ à remplacer par mesure Phase 1, minimum 0.20 m)
  - `VOLUME_MAX_L` : Volume réel de la cuve (3000 L)
  - `SEUIL_ALERTE_L` : Seuil alerte bas niveau (300 L = 10%)
- 🔧 **Valeurs par défaut sûres** : 1.40 m (vide) / 0.20 m (plein) avec avertissements explicites
- 📍 **GPIO Phase 2** : GPIO17 (Trig) / GPIO16 (Echo)
  - ⚠️ Différents de Phase 1 MicroPython (GPIO23/GPIO22)
- 🚨 **Protection zone aveugle** : filtre lambda rejette mesures <20 cm
- 🔧 **Filtre médiane optimisé** : `window_size: 7` pour éliminer faux échos

**Entités Home Assistant produites :**
1. `sensor.capteur_cuve_distance_brute` — Distance (m), filtre médiane 7 échantillons
2. `sensor.capteur_cuve_niveau_eau` — Niveau (%), calculé via formule
3. `sensor.capteur_cuve_volume_eau` — Volume (L), calculé via niveau%
4. `binary_sensor.capteur_cuve_alerte_bas_niveau` — Alerte si <300 L (anti-chattering 30s)

**Formules de calcul :**
```
niveau (%) = (DIST_VIDE_M - distance_mesurée) / (DIST_VIDE_M - DIST_PLEIN_M) × 100
volume (L) = niveau% / 100 × VOLUME_MAX_L
```

---

### 2. Template secrets (`esphome/secrets.yaml.example`)

**Améliorations :**
- 🔒 Instructions plus claires avec exemples de génération de clés
- 📋 Commentaires détaillés pour chaque paramètre
- 🛡️ Rappel explicite : ne jamais commiter `secrets.yaml`

**Paramètres à configurer :**
- `wifi_ssid` / `wifi_password`
- `ap_password` (fallback AP)
- `ota_password` (générer avec `secrets.token_hex(16)`)
- `api_encryption_key` (générer avec ESPHome ou `secrets.token_bytes(32)`)

---

### 3. Documentation principale (`README.md`)

**Restructuration complète** avec :

#### Section Matériel
- Table des composants (ESP32, JSN-SR04T/AJ-SR04M, level shifter)
- **Schéma de câblage détaillé** avec niveau logique (3.3V ↔ 5V)
- ⚠️ Avertissement GPIO Phase 1 vs Phase 2

#### Section Cuve
- Spécifications : dimensions (224×140×153.3 cm)
- Volume réel utilisable : **3000 L** (vs ~4807 L géométrique théorique)

#### Phase 1 — Test MicroPython
- Instructions installation MicroPython
- Utilisation du script `test_cuve.py` avec Thonny
- Mesures à relever : DIST_VIDE_M et DIST_PLEIN_M

#### Phase 2 — Production ESPHome
- Pré-requis (ESPHome, Python 3.9+)
- Configuration des secrets (étape par étape)
- **Adaptation des paramètres de calibration** (substitutions YAML)
- Commandes de compilation/flash (USB + OTA)
- Intégration Home Assistant (auto-détection mDNS)

#### Entités Home Assistant
- Table détaillée des 4 entités disponibles
- Device class, state class, unités

#### Automatisation exemple
- Code YAML pour alerte notification mobile
- Exemple carte Lovelace

#### Dépannage
- Distance = 0 ou NaN
- Valeurs fluctuantes
- ESP32 redémarre en boucle
- Solutions détaillées pour chaque cas

---

### 4. Nouveau guide de calibration (`CALIBRATION.md`)

**Document détaillé pas-à-pas** pour guider l'utilisateur dans la Phase 1 :

#### Contenu
1. **Objectif** : mesurer DIST_VIDE_M et DIST_PLEIN_M
2. **Pré-requis** : matériel, logiciels, cuve accessible
3. **Étape 1** : Installation MicroPython (esptool.py, flash firmware)
4. **Étape 2** : Exécution script `test_cuve.py` avec Thonny
   - Vérification GPIO
   - Interprétation des sorties console
5. **Étape 3** : Mesure DIST_VIDE_M (cuve vide)
   - Attendre stabilisation filtre médiane
   - Noter la valeur en mètres
   - Recommandation : moyenne de plusieurs relevés
6. **Étape 4** : Mesure DIST_PLEIN_M (cuve pleine)
   - Remplir au niveau max utilisable
   - Vérifier distance ≥ 20 cm (zone aveugle)
   - Remonter capteur si <20 cm
7. **Étape 5** : Tableau récapitulatif à compléter
8. **Étape 6** : Mise à jour config ESPHome avec valeurs mesurées
9. **Validation** : vérifier entités HA (0%/100%, volume correct)
10. **Recalibration** : quand recommencer
11. **Dépannage calibration** :
    - Script affiche "HORS PORTÉE"
    - Mesures instables
    - Distance <20 cm inatteignable

---

## ⚙️ Choix techniques ESPHome

### 1. Capteur ultrason (`ultrasonic` platform)
- `trigger_pin: GPIO17` / `echo_pin: GPIO16`
- `pulse_time: 10us` (standard JSN-SR04T)
- `timeout: 2m` (couvre plage 0.20-2.00 m)
- `update_interval: 5s` (compromis réactivité/charge)

### 2. Filtre médiane
- `window_size: 7` (nombre impair pour médiane claire)
- `send_every: 1` (publication à chaque nouvelle médiane)
- Élimine faux échos (valeurs aberrantes) sans latence excessive

### 3. Protection zone aveugle
- Filtre lambda : `return (x < 0.20f) ? NAN : x;`
- Rejette toute mesure <20 cm (zone aveugle physique du JSN-SR04T)
- `filter_out: nan` après pour ne pas propager les NAN

### 4. Calculs template sensors
- **Niveau** : formule linéaire avec clamping 0-100%
- **Volume** : dérivé du niveau (pas de calcul géométrique direct)
- Utilisation de `isnan()` pour gestion robuste des erreurs

### 5. Binary sensor alerte
- `delayed_on: 30s` : anti-chattering pour éviter alertes intempestives
- Device class `problem` : affichage approprié dans HA

---

## 📊 Paramètres à adapter sur site

**Avant déploiement en production**, l'utilisateur DOIT :

1. **Mesurer les distances réelles** avec le script Phase 1 (`test_cuve.py`)
2. **Modifier** `esphome/capteur_cuve.yaml` :

```yaml
substitutions:
  DIST_VIDE_M:    "X.XXX"   # ⚠️ Remplacer par mesure cuve vide (Phase 1)
  DIST_PLEIN_M:   "X.XXX"   # ⚠️ Remplacer par mesure cuve pleine (Phase 1), ≥ 0.20 m
  VOLUME_MAX_L:   "3000"    # Déjà renseigné (volume réel fourni)
  SEUIL_ALERTE_L: "300"     # Ajuster si besoin (10% par défaut)
  PIN_TRIG: GPIO17          # Vérifier câblage réel
  PIN_ECHO: GPIO16          # Vérifier câblage réel
```

3. **Créer** `esphome/secrets.yaml` depuis le template
4. **Compiler et flasher** (voir README.md Phase 2)

---

## ✅ Validation effectuée

- [x] **Compilation ESPHome** : OK (config syntaxiquement valide)
- [x] **Documentation complète** : README + CALIBRATION + secrets.yaml.example
- [x] **Annotations code** : chaque paramètre est expliqué
- [x] **Valeurs par défaut sûres** : 1.40 m / 0.20 m avec warnings explicites ⚠️
- [x] **Guide utilisateur** : pas-à-pas Phase 1 (MicroPython) + Phase 2 (ESPHome)
- [x] **Gestion erreurs** : filtres NAN, zone aveugle, anti-chattering
- [x] **3 entités requises** : distance_brute (m), niveau_eau (%), volume_eau (L)
- [x] **Bonus** : binary_sensor alerte_bas_niveau

---

## 🔗 Pull Request créée

**PR #3** : [refactor: Phase 2 ESPHome — configuration propre et documentation complète](https://github.com/MarinFDM/capteurCuve/pull/3)

**Branche :** `phase2-esphome-clean` → `main`

**Commit :** `77f8797`

**Titre :** refactor: Phase 2 ESPHome clean - configuration simplifiée et documentation complète

**Description PR :** Restructuration complète avec objectifs, changements détaillés, paramètres clés, validation, et référence à la session de calibration.

---

## 🛠️ Commandes de validation (pour l'utilisateur)

### Compilation seule (vérification syntaxe)
```bash
esphome compile esphome/capteur_cuve.yaml
```

### Flash USB (première fois)
```bash
esphome run esphome/capteur_cuve.yaml
```

### Flash OTA (mises à jour)
```bash
esphome run esphome/capteur_cuve.yaml --device <IP_ESP32>
```

---

## 📌 Points d'attention pour le Validateur

### 1. Valeurs de calibration
- ⚠️ Les valeurs `DIST_VIDE_M = 1.40` et `DIST_PLEIN_M = 0.20` sont des **placeholders sûrs**
- L'utilisateur **DOIT** les remplacer par ses mesures réelles (guide CALIBRATION.md)
- Documentation insiste lourdement sur ce point (annotations ⚠️, README, CALIBRATION.md)

### 2. GPIO Phase 1 vs Phase 2
- **Phase 1 MicroPython** : GPIO23 (Trig) / GPIO22 (Echo)
- **Phase 2 ESPHome** : GPIO17 (Trig) / GPIO16 (Echo)
- Utilisateur averti dans README et CALIBRATION.md de vérifier son câblage

### 3. Zone aveugle capteur
- JSN-SR04T/AJ-SR04M : **ne mesure pas <20 cm**
- `DIST_PLEIN_M` minimum absolu : **0.20 m**
- Filtre lambda rejette automatiquement les mesures <20 cm
- Documentation explique comment remonter le capteur si nécessaire

### 4. Volume réel vs géométrique
- Volume configuré : **3000 L** (valeur réelle fournie)
- Volume géométrique théorique : ~4807 L (224×140×153.3 cm)
- Documentation explique cette différence (cuve non remplie à 100% géométrique)

### 5. Secrets jamais commités
- `secrets.yaml` dans `.gitignore`
- Seul `secrets.yaml.example` (template sans valeurs sensibles) est commité
- Instructions claires pour copier et renseigner

---

## 🎯 Hypothèses faites

1. **Cuve rectangulaire 3000 L** : volume réel utilisable (vs théorique géométrique)
2. **Capteur monté à ~1.40 m** au-dessus du fond (valeur par défaut prudente)
3. **Zone pleine à 20 cm** minimum du capteur (contrainte physique JSN-SR04T)
4. **ESP32-WROOM-32** standard (pas WROVER) : GPIO16/17 disponibles
5. **Level shifter BSS138** ou équivalent bidirectionnel 3.3V↔5V
6. **Utilisateur a accès à la cuve** vide ET pleine pour calibration

---

## 📝 Message si bloqué

Aucun blocage rencontré. Tous les livrables sont produits et validés.

---

## 🏁 Statut final

**✅ DONE**

- Configuration ESPHome propre et documentée
- 3 entités Home Assistant requises + 1 binary sensor bonus
- Guide de calibration complet (CALIBRATION.md)
- Documentation utilisateur exhaustive (README.md)
- PR #3 créée et prête pour review
- Aucun merge effectué (interdit ⛔)

---

## 📎 Artifacts de référence Phase 1 (non utilisés directement)

- `39ec85a8-6c54-48db-af29-e7ffaa439c14` : Script MicroPython + Instructions Thonny
- `6c22be32-c789-46f7-b2ce-4f7c131519ff` : Schéma de câblage

Ces artifacts étaient disponibles mais non nécessaires : le script `test_cuve.py` était déjà présent dans le dépôt et le schéma de câblage a été réécrit en texte dans le README pour plus de clarté.

---

**🎉 Phase 2 ESPHome reprise depuis zéro avec succès !**
