"""
Test - Suite de Tests Complète pour BBS Digital Trust Certificates

Cette suite de tests couvre tous les aspects du système BBS-DTC :
- Tests unitaires pour BBSCore et DTC
- Tests d'intégration bout-en-bout
- Tests de performance et benchmarks  
- Tests de sécurité cryptographique
- Tests de visualisation et CLI

Structure des Tests:
├── test_bbs_core.py                 # Tests unitaires BBSCore
│   ├── test_keygen_validity()       # Génération de clés
│   ├── test_bbs_signature_valid()   # Signature et vérification OK
│   ├── test_bbs_signature_invalid() # Signature invalide rejetée
│   ├── test_blindsign_cycle()       # Blindage / déblindage
│   ├── test_zkproof_validity()      # Preuve ZK valide
│   └── test_security_utils_hash()   # Utilitaires de sécurité
│
├── test_dtc_core.py                 # Tests unitaires DTC
│   ├── test_issuer_schema_compliance()
│   ├── test_holder_store_retrieve()
│   ├── test_verifier_accepts_valid()
│   └── test_verifier_rejects_invalid()
│
├── test_integration.py              # Tests d'intégration complets
│   ├── test_full_flow_success()
│   ├── test_full_flow_tampered_credential()
│   └── test_demo_travel_with_benchmark_data()
│
├── test_performance.py              # Tests de performance
│   ├── test_signature_time_vs_attributes()
│   ├── test_proof_time_vs_attributes()
│   ├── test_verification_time_vs_disclosure()
│   └── test_proof_size_measurements()
│
├── test_benchmark_visualization.py  # Tests des graphes et CSV
│   ├── test_graph_png_generated()
│   ├── test_csv_json_generated()
│   └── test_fake_data_graph_generation()
│
├── test_security.py                 # Tests de sécurité
│   ├── test_tampered_proof_rejected()
│   ├── test_invalid_public_key_rejected()
│   └── test_hidden_attribute_mismatch()
│
└── test_cli.py                      # Tests CLI benchmark runner
    ├── test_cli_with_config()
    ├── test_cli_default_config()
    └── test_cli_missing_file()

Usage:
    python -m unittest Test.test_bbs_core          # Tests BBSCore seulement
    python -m unittest Test.test_integration       # Tests d'intégration
    python -m unittest Test.test_performance       # Benchmarks performance
    python -m unittest discover Test/              # Tous les tests
"""

# Import des modules de test principaux
from . import test_bbs_core
from . import test_dtc_core
from . import test_integration
from . import test_performance
from . import test_benchmark_visualization
from . import test_security
from . import test_cli

__all__ = [
    # Modules de test par catégorie
    'test_bbs_core',           # Tests unitaires cryptographiques
    'test_dtc_core',           # Tests unitaires métier DTC
    'test_integration',        # Tests bout-en-bout
    'test_performance',        # Benchmarks et métriques
    'test_benchmark_visualization',  # Tests visualisation
    'test_security',           # Tests sécurité avancés
    'test_cli',               # Tests interfaces CLI
]

def run_all_tests():
    """Exécuter tous les tests de la suite"""
    import unittest
    
    # Découvrir et exécuter tous les tests
    loader = unittest.TestLoader()
    suite = loader.discover('Test', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_core_tests():
    """Exécuter seulement les tests core (BBS + DTC)"""
    import unittest
    
    suite = unittest.TestSuite()
    
    # Charger tests core
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromModule(test_bbs_core))
    suite.addTests(loader.loadTestsFromModule(test_dtc_core))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_integration_tests():
    """Exécuter tests d'intégration et performance"""
    import unittest
    
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    suite.addTests(loader.loadTestsFromModule(test_integration))
    suite.addTests(loader.loadTestsFromModule(test_performance))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_security_tests():
    """Exécuter tests de sécurité"""
    import unittest
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_security)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()