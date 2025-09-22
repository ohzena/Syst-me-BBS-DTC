# BBS-DTC Benchmark 

Systeme de benchmarking modulaire pour les signatures BBS et Digital Travel Credentials (DTC) avec support des profils personnalises et scenarios realistes.

## Architecture Modulaire

```
benchmark/
├── config.py              # Configuration centralisee et utilitaires
├── scenarios.py           # Interface vers Demo/ avec wrappers
├── collector.py           # Collecteur principal de metriques  
├── runner.py              # Orchestrateur principal
├── data/custom/           # Profils JSON personnalises
│   ├── ellen_kampire_dtc.json
│   └── Berissa_kawaya_dtc.json
└── visualization/         # Generation des graphiques
    ├── base_graphs.py
    └── extra_graphs.py
```

## Utilisation

### 1. Execution Simple (Recommandee)

```bash
# Benchmark complet avec profil par defaut (Ellen Kampire)
python benchmark/runner.py

# Benchmark rapide (moins d'iterations)
python benchmark/runner.py --config quick --iterations 3

# Benchmark complet sans graphiques
python benchmark/runner.py --no-graphs
```

### 2. Profils Personnalises

```bash
# Utiliser un profil JSON specifique
python benchmark/runner.py --profile benchmark/data/custom/Berissa_kawaya_dtc.json

# Valider un profil avant utilisation
python benchmark/runner.py --validate-profile mon_profil.json
```

### 3. Scenarios Specifiques

```bash
# Lister les scenarios disponibles
python benchmark/runner.py --list-scenarios

# Executer des scenarios specifiques
python benchmark/runner.py --scenarios dtc_complete credential_issuance

# Scenario de voyage uniquement
python benchmark/runner.py --scenarios travel_demo --iterations 2
```

### 4. Configurations Predefinies

```bash
# Configuration rapide (test/debug)
python benchmark/runner.py --config quick

# Configuration complete (recherche)
python benchmark/runner.py --config comprehensive --iterations 20
```

## Scenarios Disponibles

### `dtc_complete`
- **Description**: Demonstration complete des fonctionnalites DTC
- **Source**: `Demo/dtc_complete.py` 
- **Metriques**: Temps de flux complet, signature, verification, preuve
- **Recommande pour**: Profils avec <= 10 attributs

### `credential_issuance` 
- **Description**: Processus complet d'emission de credentials
- **Source**: `Demo/credential_issuance.py`
- **Metriques**: Temps d'emission, presentation, verification, taille wallet
- **Recommande pour**: Profils avec > 10 attributs

### `travel_demo`
- **Description**: Demonstration complete de voyage avec DTC
- **Source**: `Demo/demo_travel.py`
- **Metriques**: Flux de voyage, verification frontiere, preservation privacy
- **Recommande pour**: Profils de type "travel"

### `auto_privacy`
- **Description**: Protection automatique de la privacy selon RGPD
- **Source**: `Demo/auto_privacy.py`
- **Metriques**: Temps moteur privacy, conformite RGPD, adaptation contextuelle
- **Recommande pour**: Tests de conformite RGPD

### `blind_signature`
- **Description**: Demonstration des signatures aveugles BBS
- **Source**: `Demo/blind_signature.py`
- **Metriques**: Temps signature aveugle, temps devoilement, verification age
- **Recommande pour**: Tests de privacy renforcee

### `interactive_disclosure`
- **Description**: Demonstration interactive de divulgation selective
- **Source**: `Demo/interactive_disclosure.py`
- **Metriques**: Temps choix interactif, temps divulgation, score privacy
- **Recommande pour**: Tests utilisateur interactifs

## Metriques Collectees

### CSV Generes par Defaut
- `batch_performance.csv` - Performance par taille de batch
- `disclosure_rate.csv` - Impact du taux de divulgation  
- `scalability.csv` - Scalabilite selon nombre d'attributs
- `benchmark_summary.json` - Rapport de synthese

### CSV par Scenario (si scenarios specifies)
- `batch_performance_dtc_complete.csv`
- `disclosure_rate_credential.csv`
- `scalability_travel.csv`
- `scenario_[nom].csv` - Resultats specifiques du scenario
- `scenario_[nom]_details.json` - Details complets

### Graphiques Generes
- **Basic** (`benchmark/metrics/graphs/basic/`):
  - Performance vs Nombre d'Attributs
  - Taille Preuves vs Nombre d'Attributs  
  - Performance vs Taux de Divulgation
  - Scalabilite vs Taille de Batch

- **Advanced** (`benchmark/metrics/graphs/advanced/`):
  - Utilisation Memoire vs Attributs
  - Analyse des Goulots d'Etranglement

## Profils JSON

### Structure d'un Profil

```json
{
  "name": "Mon Profil DTC",
  "type": "travel",
  "credential_holder": {
    "full_name": "Ellen Kampire",
    "nationality": "Rwandaise",
    "birth_date": "1996-03-15"
  },
  "attributes": [
    "passport_number", "full_name", "nationality", 
    "birth_date", "expiry_date", "visa_status"
  ],
  "disclosure_patterns": [
    {
      "name": "Border Control",
      "disclosed": ["full_name", "nationality", "visa_status"],
      "hidden": ["passport_number", "birth_date", "expiry_date"]
    }
  ],
  "test_parameters": {
    "custom_iterations": 10,
    "attribute_variations": [4, 8, 16, 32],
    "disclosure_rate_variations": [25, 50, 75, 100]
  }
}
```

### Profils Predefinis

**Ellen Kampire** (`ellen_kampire_dtc.json`)
- Voyageuse rwandaise, 28 ans
- 10 attributs de voyage standard
- Divulgation 50% par defaut (5/10 attributs)

**Berissa Kawaya** (`Berissa_kawaya_dtc.json`) 
- Voyageuse malienne, 28 ans
- 12 attributs etendus avec informations visa
- Patterns de divulgation multiples

## Utilisation Programmatique

### Execution Simple en Python

```python
from benchmark.runner import BenchmarkRunner

# Benchmark avec profil par defaut
runner = BenchmarkRunner()
runner.run_full_suite()

# Benchmark avec profil specifique
runner = BenchmarkRunner(profile_path="mon_profil.json")
runner.run_full_suite(scenarios=["dtc_complete"], iterations=10)
```

### Execution de Scenarios Individuels

```python
from benchmark.scenarios import run_single_scenario

# Executer un scenario specifique
result = run_single_scenario(
    scenario_name="dtc_complete",
    attributes=["name", "age", "nationality"],
    iterations=5
)

print(f"Temps moyen: {result['avg_execution_time_ms']:.2f}ms")
```

### Collecte de Metriques Directe

```python
from benchmark.collector import BenchmarkCollector

# Creer collector avec profil
collector = BenchmarkCollector("mon_profil.json")

# Mesures par defaut
collector.run_default_benchmarks(iterations=5)

# Mesures par scenario
collector.measure_scenario_performance("credential_issuance", iterations=3)
```

## Configuration Avancee

### Fichier `config.py`

```python
# Personnaliser les parametres de test
custom_config = BenchmarkConfig(
    message_counts=[2, 4,8, 10, 16, 32, 64, 128],
    disclosure_percentages=[0.2, 0.4, 0.6, 0.8, 1.0],
    iterations=15,
    output_formats=["png", "pdf", "svg"]
)
```

### Ajout de Nouveaux Scenarios

1. **Ajouter dans `config.py`**:
```python
SCENARIO_CONFIGS["mon_scenario"] = {
    "name": "Mon Nouveau Scenario",
    "demo_module": "Demo.mon_module",
    "demo_function": "ma_fonction",
    "default_iterations": 5,
    "csv_prefix": "mon_scenario"
}
```

2. **Creer le wrapper dans `scenarios.py`**:
```python
def _run_mon_scenario_wrapper(self, attributes, disclosure_pattern, iterations):
    # Votre logique de wrapper ici
    return result
```

## Interpretation des Resultats

### Metriques Cles

- **`sign_time_ms`**: Temps de signature BBS (objectif: < 100ms)
- **`proof_gen_time_ms`**: Temps generation preuve ZK (objectif: < 300ms)  
- **`proof_size_bytes`**: Taille preuve en octets (objectif: < 1KB)
- **`avg_execution_time_ms`**: Temps moyen d'execution du scenario


## Depannage

### Problemes Courants

**"Demo modules not available"**
```bash
# Verifier que les modules Demo/ sont presents
ls Demo/
# S'assurer que __init__.py existe dans Demo/
```

**"Scenario not available"**
```bash
# Lister les scenarios disponibles  
python benchmark/runner.py --list-scenarios
```

**"Profile validation failed"**
```bash
# Valider le profil JSON
python benchmark/runner.py --validate-profile mon_profil.json
```

### Mode Debug

```bash
# Execution avec traces detaillees
python benchmark/runner.py --config quick --iterations 1

# Test des scenarios individuellement
python benchmark/scenarios.py
```

## Exemples d'Utilisation

### Recherche Academique
```bash
# Benchmark complet pour publication
python benchmark/runner.py --config comprehensive --iterations 50
```

### Developpement/Debug
```bash
# Test rapide pendant developpement
python benchmark/runner.py --config quick --no-graphs --iterations 2
```

### Evaluation de Performance
```bash
# Focus sur un scenario specifique
python benchmark/runner.py --scenarios dtc_complete --iterations 20
```

### Demonstration
```bash
# Demonstration avec profil realiste
python benchmark/runner.py --profile demo_profile.json --scenarios travel_demo
```

### Tests de Privacy
```bash
# Tests des fonctionnalites privacy
python benchmark/runner.py --scenarios auto_privacy blind_signature
```

### Tests Interactifs
```bash
# Test de l'interface utilisateur
python benchmark/runner.py --scenarios interactive_disclosure --iterations 1
```

## Fichiers de Sortie

Tous les resultats sont sauvegardes dans le dossier `benchmark/metrics/`:

```
benchmark/metrics/
├── csv/                    # Donnees brutes CSV
│   ├── batch_performance.csv
│   ├── disclosure_rate.csv
│   ├── scalability.csv
│   ├── scenario_*.csv
│   └── benchmark_summary.json
├── graphs/                 # Graphiques generes
│   ├── basic/             # Graphiques de base (PNG/PDF)
│   └── advanced/          # Analyses avancees
└── reports/               # Rapports detailles
```

## Integration Continue

Le systeme peut etre integre dans des pipelines CI/CD:

```yaml
# Exemple GitHub Actions
- name: Run BBS Benchmarks
  run: |
    python benchmark/runner.py --config quick --no-graphs
    # Verifier les seuils de performance
```

## Scenarios par Type d'Utilisation

### Pour Debutants
- `dtc_complete` - Vue d'ensemble complete
- `interactive_disclosure` - Apprentissage interactif

### Pour Developpeurs
- `credential_issuance` - Tests de performance
- `auto_privacy` - Tests conformite
- `blind_signature` - Tests privacy avancee

### Pour Recherche
- `travel_demo` - Cas d'usage realiste
- Tous les scenarios avec `--config comprehensive`

---

*Developpe pour l'ecosysteme BBS-DTC educatif - Version modulaire avec support des profils JSON*