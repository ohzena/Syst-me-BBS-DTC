"""
benchmark - Suite de benchmarks pour signatures BBS et Digital Travel Credentials

Architecture modulaire pour mesurer et visualiser les performances des 
implementations BBS dans le contexte des DTC.
"""

__version__ = "1.0.0"
__author__ = "BBS-DTC Project"
__description__ = "Benchmark suite for BBS signatures in Digital Travel Credentials"

from .config import BenchmarkConfig, get_config, DTC_SCENARIOS
from .runner import BenchmarkRunner
from .collector import BenchmarkCollector
from .scenarios import ScenarioRunner

__all__ = [
    'BenchmarkConfig',
    'get_config', 
    'DTC_SCENARIOS',
    'BenchmarkRunner',
    'BenchmarkCollector', 
    'ScenarioRunner',
    'run_benchmarks',
    'quick_benchmark',
    '__version__',
    '__author__',
    '__description__'
]

def quick_benchmark(config_name='quick', visualize=True):
    """
    Fonction utilitaire pour lancer rapidement un benchmark
    
    Args:
        config_name (str): Type de config ('quick', 'standard', 'comprehensive')
        visualize (bool): Generer automatiquement les graphiques
    
    Returns:
        dict: Resultats du benchmark
    """
    runner = BenchmarkRunner(config_name)
    core_results = runner.run_core_benchmarks()
    
    if visualize:
        runner.generate_reports(core_results)
    
    return core_results

def run_benchmarks(config_name='standard', verbose=False):
    """
    Fonction principale pour lancer les benchmarks
    
    Args:
        config_name (str): Type de config ('quick', 'standard', 'comprehensive')
        verbose (bool): Mode verbeux avec details
    
    Returns:
        bool: Succes des benchmarks
    """
    runner = BenchmarkRunner(config_name)
    
    if verbose:
        print("Demarrage des benchmarks complets...")
    
    core_results = runner.run_core_benchmarks()
    
    if verbose:
        print("Generation des rapports et visualisations...")
    
    runner.generate_reports(core_results)
    
    if verbose:
        print("Benchmarks termines avec succes")
    
    return True

def get_available_scenarios():
    """
    Retourne la liste des scenarios DTC disponibles
    
    Returns:
        list: Noms des scenarios disponibles
    """
    scenario_runner = ScenarioRunner()
    return scenario_runner.get_available_scenarios()

def validate_dtc_config(config_path):
    """
    Valide un fichier de configuration DTC
    
    Args:
        config_path (str): Chemin vers le fichier JSON
        
    Returns:
        tuple: (is_valid, errors_list)
    """
    from .data.manager import DataManager
    manager = DataManager()
    profile = manager.load_profile(config_path)
    warnings = manager.validate_profile(profile)
    return len(warnings) == 0, warnings

DEFAULT_CONFIG = {
    'message_counts': [2, 4, 8, 10, 16, 32, 64, 128],
    'disclosure_percentages': [0.0, 0.1, 0.15, 0.25, 0.5, 0.75, 1.0],
    'iterations': 15,
    'output_formats': ['png']
}

PACKAGE_INFO = {
    'name': 'benchmark',
    'version': __version__,
    'description': __description__,
    'author': __author__,
    'modules': [
        'config', 'runner', 'collector', 'scenarios',
        'data.manager', 'data.schemas', 
        'visualization.graphs', 'visualization.extra_graphs'
    ]
}