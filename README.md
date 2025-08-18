# BBS Digital Travel Credentials (DTC)

Une implémentation éducative complète du schéma de signature BBS (Boneh-Boyen-Shacham) appliqué aux credentials de voyage numériques avec divulgation sélective et préservation de la confidentialité.

## Vue d'ensemble

Ce projet démontre l'utilisation des signatures BBS pour créer un système de credentials de voyage respectueux de la vie privée, permettant aux voyageurs de prouver sélectivement leurs attributs (âge, nationalité, visa, etc.) sans révéler d'informations inutiles.

### Fonctionnalités principales

- Signatures BBS multi-messages avec courbe BLS12-381
- Preuves zero-knowledge pour la divulgation sélective
- Signatures aveugles pour l'émission préservant la confidentialité
- Workflow complet DTC : Émetteur → Porteur → Vérificateur
- Unlinkability entre les présentations
- Benchmarks de performance avec visualisations automatiques
- Suite de tests complète

## Installation

### Prérequis

- Python 3.8+
- pip (gestionnaire de packages Python)
- Git (pour cloner le repository)

### Étapes d'installation

1. Cloner le repository
   ```bash
   git clone <repository-url>
   cd BBS-DTC
   ```

2. Créer un environnement virtuel (recommandé)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. Installer les dépendances
   ```bash
   pip install -r requirements.txt
   ```

4. Vérifier l'installation
   ```bash
   python main.py demo
   ```

### Dépendances principales

- `py_ecc` - Opérations BLS12-381 optimisées
- `pycryptodome` - Fonctions de hashage SHAKE-256
- `base58` - Encodage des clés et signatures
- `matplotlib` - Génération de graphiques
- `seaborn` - Visualisations avancées
- `pandas` - Manipulation de données
- `numpy` - Calculs numériques

## Utilisation

### Commandes disponibles

Le projet propose plusieurs commandes pour explorer les différentes fonctionnalités :

#### 1. Démonstration BBS de base
```bash
python main.py demo
```
**Ce que cela fournit :**
- Génération de clés BBS
- Signatures multi-messages
- Preuves zero-knowledge avec divulgation sélective
- Démonstration des opérations cryptographiques de base

#### 2. Scénario de voyage complet
```bash
python main.py travel
```
**Ce que cela fournit :**
- Workflow DTC complet avec credentials de voyage
- Check-in aéroport, contrôle frontières, vérification hôtel
- Divulgation sélective selon le contexte
- Démonstration d'unlinkability

#### 3. Émission de credentials
```bash
python main.py credential
```
**Ce que cela fournit :**
- Processus complet d'émission de credentials
- Interactions émetteur-porteur-vérificateur
- Workflows de présentation de credentials
- Démonstration de gestion de wallet

#### 4. Protection automatique de la vie privée
```bash
python main.py privacy
```
**Ce que cela fournit :**
- Démonstration de conformité RGPD
- Moteur de privacy automatique
- Protection d'attributs selon le contexte
- Calculs de score de privacy

#### 5. Signatures aveugles
```bash
python main.py blind
```
**Ce que cela fournit :**
- Démonstration du protocole de signature aveugle
- Vérification d'âge sans révéler l'âge exact
- Préservation renforcée de la privacy
- Génération de commitments et preuves

#### 6. Divulgation interactive
```bash
python main.py interactive
```
**Ce que cela fournit :**
- Interface de divulgation sélective interactive
- Contrôle utilisateur de la révélation d'attributs
- Évaluation en temps réel de l'impact privacy
- Outil d'apprentissage de la privacy

#### 7. Suite de tests complète
```bash
python main.py test
```
**Ce que cela fournit :**
- Suite de tests BBS complète
- Validation du workflow DTC
- Tests de sécurité et de résistance
- Tests d'intégration et de performance

#### 8. Benchmarks de performance
```bash
python main.py benchmark
```
**Ce que cela fournit :**
- Mesures de performance détaillées
- Génération automatique de graphiques de performance
- Analyse de scalabilité et consommation mémoire
- Export en format PNG

**Note :** Pour plus de détails sur la collecte de métriques et la génération de graphiques, voir `benchmark/README.md`

#### 9. Démonstration complète
```bash
python main.py all
```
**Ce que cela fournit :**
- Exécute tous les tests et démonstrations
- Rapport de performance complet
- Toutes les visualisations et métriques
- Validation complète du système

### Options avancées

#### Mode verbose
```bash
python main.py <commande> --verbose
```
Affiche les détails techniques et métriques de performance.

#### Désactiver les optimisations
```bash
python main.py <commande> --no-optimization
```
Désactive les optimisations pour comparaison des performances.

#### Profil utilisateur personnalisé
```bash
python main.py <commande> --custom-user profile.json
```
Utilise un profil JSON personnalisé au lieu d'Ellen Kampire par défaut.

## Sorties générées

### Résultats de benchmark
Lors de l'exécution des benchmarks, le système génère :

**Fichiers CSV :**
- `batch_performance.csv` - Performance par taille de batch
- `disclosure_rate.csv` - Impact du taux de divulgation
- `scalability.csv` - Scalabilité selon le nombre d'attributs
- `benchmark_summary.json` - Rapport de synthèse

**Graphiques de visualisation :**
1. Performance vs Nombre d'attributs
2. Taille des preuves vs Attributs
3. Performance vs Taux de divulgation
4. Scalabilité vs Taille de batch
5. Utilisation mémoire vs Attributs
6. Analyse des goulots d'étranglement

Tous les graphiques sauvegardés dans `metrics/graphs/` au format PNG.

**Pour plus de détails :** Voir `benchmark/README.md` pour la documentation complète sur la collecte de métriques et la génération de graphiques.

### Résultats de tests
L'exécution des tests fournit :
- Statut réussite/échec pour chaque module de test
- Détection de régression de performance
- Résultats de validation de sécurité
- Résultats des tests d'intégration

## Structure du projet

```
BBS-DTC/
├── BBSCore/                 # Implémentation cryptographique BBS
│   ├── Setup.py            # Paramètres système et générateurs
│   ├── KeyGen.py           # Génération de clés BBS
│   ├── bbsSign.py          # Signatures et vérification
│   ├── ZKProof.py          # Preuves zero-knowledge
│   └── BlindSign.py        # Signatures aveugles
├── DTC/                     # Layer Digital Trust Certificate
│   ├── dtc.py              # Structures de données DTC
│   ├── DTCIssuer.py        # Émission de credentials
│   ├── DTCHolder.py        # Stockage et présentation
│   └── DTCVerifier.py      # Vérification des preuves
├── Demo/                    # Démonstrations et scénarios
│   ├── dtc_complete.py     # Démo DTC complète
│   ├── demo_travel.py      # Scénario de voyage
│   ├── credential_issuance.py  # Flux de credentials
│   ├── auto_privacy.py     # Protection privacy
│   ├── blind_signature.py  # Démo signature aveugle
│   └── interactive_disclosure.py  # Divulgation interactive
├── Test/                    # Suite de tests complète
├── benchmark/               # Système de benchmarks
│   ├── collector.py        # Collection de métriques
│   ├── scenarios.py        # Scénarios de test
│   └── visualization/      # Génération de graphiques
├── metrics/                 # Résultats générés et graphiques
│   ├── graphs/             # Graphiques PNG, PDF, SVG
│   └── reports/            # Rapports HTML et JSON
├── main.py                  # Point d'entrée principal
└── requirements.txt         # Dépendances Python
```

## Sécurité et conformité

### Conformité aux standards

- Courbe BLS12-381 avec sécurité 128-bit
- Hash SHA-256 (configurable vers SHAKE-256)
- Spécifications IETF pour les signatures BBS
- Standards W3C pour les Verifiable Credentials

### Fonctionnalités de sécurité

- Résistance à la forgerie - Tests automatisés
- Détection de modification - Intégrité des messages
- Protection contre le replay - Nonces uniques
- Divulgation sélective - Preuves zero-knowledge
- Unlinkability - Impossibilité de corrélation

### Avertissement important

Ce projet est conçu à des fins éducatives et de recherche. Ne pas utiliser en production sans :
- Audit de sécurité formel
- Implémentation cryptographique constant-time
- Protection contre les attaques par canal auxiliaire
- Infrastructure de gestion des clés sécurisée

## Dépannage

### Problèmes courants

#### Erreur d'installation des dépendances
```bash
# Mettre à jour pip
pip install --upgrade pip
# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall
```

#### Timeout lors des benchmarks
Les opérations cryptographiques BBS peuvent prendre du temps. Utiliser le mode sans optimisation :
```bash
python main.py benchmark --no-optimization
```

#### Problèmes de visualisation
Assurer que matplotlib fonctionne :
```bash
python -c "import matplotlib.pyplot as plt; plt.plot([1,2,3]); print('Matplotlib OK')"
```

### Vérification de l'installation

Test complet du système :
```bash
python main.py demo  # Doit terminer avec "Demo completed successfully"
```

## Licence

Utilisation éducative uniquement.
