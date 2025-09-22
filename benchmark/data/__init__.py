"""
benchmark.data - Gestion des donnees et configurations pour benchmarks BBS-DTC

Ce module fournit les outils pour:
- Charger et valider les configurations JSON
- Gerer les schemas de validation
- Creer des templates pour differents scenarios DTC
- Valider les donnees de benchmarks
"""

__version__ = "1.0.0"
__description__ = "Data management for BBS-DTC benchmarks"

from .manager import DataManager
try:
    from .schemas import (
        SimpleValidator,
        ProfileAnalyzer
    )
except ImportError:
    # Schemas are optional
    SimpleValidator = None
    ProfileAnalyzer = None

__all__ = [
    'DataManager',
    'SimpleValidator',
    'ProfileAnalyzer',
    'create_default_dtc_config',
    'validate_dtc_scenario',
    'get_template_configs'
]

DEFAULT_TEMPLATES = {
    'travel_basic': {
        'name': 'Travel Credential Basic',
        'attributes': ['passport_number', 'nationality', 'birth_date', 'expiry_date'],
        'disclosure_patterns': [
            {'disclosed': ['nationality'], 'hidden': ['passport_number', 'birth_date', 'expiry_date']}
        ]
    },
    
    'identity_simple': {
        'name': 'Identity Verification Simple',
        'attributes': ['full_name', 'birth_date', 'id_number', 'address'],
        'disclosure_patterns': [
            {'disclosed': ['full_name'], 'hidden': ['birth_date', 'id_number', 'address']}
        ]
    },
    
    'business_executive': {
        'name': 'Business Executive Travel',
        'attributes': ['full_name', 'company', 'job_title', 'visa_type', 'business_purpose'],
        'disclosure_patterns': [
            {'disclosed': ['full_name', 'company'], 'hidden': ['job_title', 'visa_type', 'business_purpose']}
        ]
    }
}

def create_default_dtc_config(template_type='basic'):
    """
    Cree une configuration DTC par defaut
    
    Args:
        template_type (str): Type de template ('basic', 'comprehensive', 'quick')
        
    Returns:
        dict: Configuration par defaut
    """
    if template_type in DEFAULT_TEMPLATES:
        return DEFAULT_TEMPLATES[template_type]
    return DEFAULT_TEMPLATES['travel_basic']

def validate_dtc_scenario(scenario_data):
    """
    Valide un scenario DTC
    
    Args:
        scenario_data (dict): Donnees du scenario a valider
        
    Returns:
        tuple: (is_valid, errors_list)
    """
    required_fields = ['name', 'attributes']
    errors = []
    
    for field in required_fields:
        if field not in scenario_data:
            errors.append(f"Missing required field: {field}")
    
    if not isinstance(scenario_data.get('attributes', []), list):
        errors.append("'attributes' must be a list")
    
    return len(errors) == 0, errors

def get_template_configs():
    """
    Retourne tous les templates de configuration disponibles
    
    Returns:
        dict: Templates disponibles par type
    """
    return DEFAULT_TEMPLATES

def load_dtc_config(config_path):
    """
    Charge une configuration DTC depuis un fichier
    
    Args:
        config_path (str): Chemin vers le fichier JSON
        
    Returns:
        dict: Configuration chargee et validee
    """
    manager = DataManager()
    return manager.load_profile(config_path)

def save_dtc_config(config_data, filename):
    """
    Sauvegarde une configuration DTC
    
    Args:
        config_data (dict): Donnees de configuration
        filename (str): Nom du fichier de sortie
        
    Returns:
        str: Chemin du fichier sauvegarde
    """
    import json
    from pathlib import Path
    
    manager = DataManager()
    output_path = manager.custom_data_dir / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    return str(output_path)

PACKAGE_INFO = {
    'name': 'benchmark.data',
    'version': __version__,
    'description': __description__,
    'dependencies': ['jsonschema (optional)'],
    'key_classes': ['DataManager', 'ConfigValidator'],
    'supported_formats': ['JSON'],
    'validation_types': ['benchmark_config', 'scenario_config', 'results']
}