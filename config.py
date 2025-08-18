"""
config.py - Configuration globale du projet BBS-DTC

Configuration centralisée pour l'ensemble du projet
"""

from pathlib import Path

# Configuration globale du projet
PROJECT_CONFIG = {
    'bbs': {
        'curve': 'BLS12-381',
        'security_bits': 128,
        'max_messages': 50,
        'api_id': b"BBS_BLS12381G1_XMD:SHA-256_SSWU_RO_"
    },
    
    'dtc': {
        'default_issuer': 'Government',
        'credential_ttl': 365 * 24 * 3600,  # 1 an en secondes
        'supported_types': ['passport', 'visa', 'identity_card'],
        'version': '1.0.0'
    },
    
    'benchmark': {
        # Paramètres corrects pour BenchmarkConfig
        'message_counts': [2, 4, 8, 10, 16, 32, 64, 128],
        'disclosure_percentages': [0.0, 0.1, 0.15, 0.25, 0.5, 0.75, 1.0],
        'batch_sizes': [1, 5, 10, 20, 50],
        'iterations': 10,
        
        # Seuils de performance (ms)
        'performance_thresholds': {
            'sign': 100.0,
            'verify': 100.0,
            'proof_gen': 300.0,
            'proof_verify': 200.0
        },
        
        # Configuration des sorties
        'output_formats': ['png', 'pdf'],
        'graph_style': 'seaborn-v0_8',
        'dpi': 300,
        
        # Chemins
        'results_dir': 'metrics',
        'custom_data_dir': 'benchmark/data/custom'
    },
    
    'paths': {
        'project_root': Path(__file__).parent,
        'bbs_core': Path(__file__).parent / 'BBSCore',
        'dtc': Path(__file__).parent / 'DTC',
        'demo': Path(__file__).parent / 'Demo',
        'benchmark': Path(__file__).parent / 'benchmark',
        'tests': Path(__file__).parent / 'Tests',
        'metrics': Path(__file__).parent / 'metrics',
        'docs': Path(__file__).parent / 'docs'
    },
    
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'bbs_dtc.log'
    }
}

def get_project_config(section: str = None):
    """
    Récupère la configuration du projet
    
    Args:
        section: Section spécifique de la config (bbs, dtc, benchmark, etc.)
    
    Returns:
        dict: Configuration demandée ou complète
    """
    if section:
        return PROJECT_CONFIG.get(section, {})
    return PROJECT_CONFIG

def get_benchmark_config_dict():
    """
    Retourne la configuration benchmark dans le format attendu par BenchmarkConfig
    
    Returns:
        dict: Configuration pour initialiser BenchmarkConfig
    """
    benchmark_conf = PROJECT_CONFIG['benchmark'].copy()
    
    # S'assurer que tous les champs sont dans le bon format
    return {
        'message_counts': benchmark_conf.get('message_counts'),
        'disclosure_percentages': benchmark_conf.get('disclosure_percentages'),
        'batch_sizes': benchmark_conf.get('batch_sizes'),
        'iterations': benchmark_conf.get('iterations', 10),
        'performance_thresholds': benchmark_conf.get('performance_thresholds'),
        'output_formats': benchmark_conf.get('output_formats'),
        'graph_style': benchmark_conf.get('graph_style', 'seaborn-v0_8'),
        'dpi': benchmark_conf.get('dpi', 300),
        'results_dir': benchmark_conf.get('results_dir', 'metrics'),
        'custom_data_dir': benchmark_conf.get('custom_data_dir', 'benchmark/data/custom')
    }

def update_project_config(updates: dict, section: str = None):
    """
    Met à jour la configuration du projet
    
    Args:
        updates: Dictionnaire des mises à jour
        section: Section spécifique à mettre à jour
    """
    if section and section in PROJECT_CONFIG:
        PROJECT_CONFIG[section].update(updates)
    else:
        for key, value in updates.items():
            if key in PROJECT_CONFIG and isinstance(PROJECT_CONFIG[key], dict):
                PROJECT_CONFIG[key].update(value)
            else:
                PROJECT_CONFIG[key] = value

# Alias pour compatibilité
BBS_CONFIG = PROJECT_CONFIG.get('bbs', {})
DTC_CONFIG = PROJECT_CONFIG.get('dtc', {})
BENCHMARK_CONFIG = PROJECT_CONFIG.get('benchmark', {})