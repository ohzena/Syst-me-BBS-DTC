"""
benchmark/config.py - Configuration globale pour les benchmarks BBS-DTC

Centralise toutes les configurations par defaut pour les mesures de performance
Version amelioree avec support des scenarios et profils JSON
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

@dataclass
class BenchmarkConfig:
    """Configuration principale des benchmarks"""
    
    message_counts: List[int] = None
    disclosure_percentages: List[float] = None
    batch_sizes: List[int] = None
    iterations: int = 10
    
    output_formats: List[str] = None
    graph_style: str = "seaborn-v0_8"
    dpi: int = 300
    
    results_dir: str = "metrics"
    custom_data_dir: str = "data/custom"
    
    def __post_init__(self):
        """Initialise les valeurs par defaut"""
        if self.message_counts is None:
            self.message_counts = [2, 4, 8, 10, 16, 32, 64, 128]
            
        if self.disclosure_percentages is None:
            self.disclosure_percentages = [0, 0.1, 0.25, 0.5, 0.75, 1.0]
            
        if self.batch_sizes is None:
            self.batch_sizes = [1, 5, 10, 20, 50]
        
        if self.output_formats is None:
            self.output_formats = ["png", "pdf"]

DEFAULT_CONFIG = BenchmarkConfig()

SCENARIO_CONFIGS = {
    "credential_issuance": {
        "name": "Credential Issuance Process", 
        "description": "Processus complet d'emission de credentials",
        "demo_module": "Demo.credential_issuance",
        "demo_function": "main",
        "supported_attributes": range(1, 129),
        "default_iterations": 5,
        "csv_prefix": "credential",
        "metrics": ["issuance_time", "presentation_time", "verification_time", "wallet_size"]
    },
    
    "travel_demo": {
        "name": "Travel Demo Complete",
        "description": "Demonstration complete de voyage avec DTC",
        "demo_module": "Demo.demo_travel",
        "demo_function": "main",
        "supported_attributes": range(4, 65),
        "default_iterations": 3,
        "csv_prefix": "travel",
        "metrics": ["travel_flow_time", "border_verification_time", "privacy_preservation"]
    },
    
    "dtc_complete": {
        "name": "DTC Complete Demo",
        "description": "Demonstration complete des fonctionalites DTC",
        "demo_module": "Demo.dtc_complete",
        "demo_function": "main",
        "supported_attributes": range(1, 65),
        "default_iterations": 3,
        "csv_prefix": "dtc_complete",
        "metrics": ["complete_flow_time", "sign_time", "verify_time", "proof_time"]
    },
    
    "auto_privacy": {
        "name": "Auto Privacy Protection",
        "description": "Protection automatique de la privacy selon RGPD",
        "demo_module": "Demo.auto_privacy",
        "demo_function": "main",
        "supported_attributes": range(1, 33),
        "default_iterations": 2,
        "csv_prefix": "auto_privacy",
        "metrics": ["privacy_engine_time", "rgpd_compliance", "context_adaptation"]
    },
    
    "blind_signature": {
        "name": "Blind Signature Demo",
        "description": "Demonstration des signatures aveugles BBS",
        "demo_module": "Demo.blind_signature",
        "demo_function": "main",
        "supported_attributes": range(1, 33),
        "default_iterations": 2,
        "csv_prefix": "blind_signature",
        "metrics": ["blind_sign_time", "unblind_time", "age_verification_time"]
    },
    
    "interactive_disclosure": {
        "name": "Interactive Disclosure Demo",
        "description": "Demonstration interactive de divulgation selective",
        "demo_module": "Demo.interactive_disclosure",
        "demo_function": "main",
        "supported_attributes": range(1, 33),
        "default_iterations": 1,
        "csv_prefix": "interactive",
        "metrics": ["interactive_choice_time", "disclosure_time", "privacy_score"]
    }
}

DTC_SCENARIOS = {
    "travel_basic": {
        "name": "Travel Credential - Basic",
        "attributes": ["passport_number", "nationality", "birth_date", "expiry_date"],
        "disclosure_patterns": [
            {"disclosed": ["nationality"], "hidden": ["passport_number", "birth_date", "expiry_date"]},
            {"disclosed": ["nationality", "birth_date"], "hidden": ["passport_number", "expiry_date"]},
            {"disclosed": ["nationality", "birth_date", "expiry_date"], "hidden": ["passport_number"]}
        ]
    },
    
    "travel_extended": {
        "name": "Travel Credential - Extended", 
        "attributes": [
            "passport_number", "nationality", "birth_date", "expiry_date",
            "issuing_country", "document_type", "mrz_data", "biometric_hash",
            "visa_status", "entry_date", "permitted_stay", "sponsor_info"
        ],
        "disclosure_patterns": [
            {"disclosed": ["nationality", "visa_status"], "hidden": ["passport_number", "birth_date", "biometric_hash", "mrz_data", "expiry_date", "issuing_country", "document_type", "entry_date", "permitted_stay", "sponsor_info"]},
            {"disclosed": ["nationality", "visa_status", "permitted_stay"], "hidden": ["passport_number", "birth_date", "biometric_hash", "mrz_data", "expiry_date", "issuing_country", "document_type", "entry_date", "sponsor_info"]},
            {"disclosed": ["nationality", "visa_status", "permitted_stay", "entry_date"], "hidden": ["passport_number", "birth_date", "biometric_hash", "mrz_data", "expiry_date", "issuing_country", "document_type", "sponsor_info"]}
        ]
    },
    
    "identity_verification": {
        "name": "Identity Verification",
        "attributes": [
            "full_name", "birth_date", "birth_place", "gender", 
            "address", "photo_hash", "signature_hash", "id_number"
        ],
        "disclosure_patterns": [
            {"disclosed": ["full_name"], "hidden": ["birth_date", "birth_place", "gender", "address", "photo_hash", "signature_hash", "id_number"]},
            {"disclosed": ["full_name", "birth_date"], "hidden": ["birth_place", "gender", "address", "photo_hash", "signature_hash", "id_number"]},
            {"disclosed": ["full_name", "birth_date", "address"], "hidden": ["birth_place", "gender", "photo_hash", "signature_hash", "id_number"]}
        ]
    }
}

GRAPH_CONFIG = {
    "colors": {
        "primary": "#2E86AB",
        "secondary": "#A23B72", 
        "success": "#F18F01",
        "warning": "#C73E1D",
        "info": "#6A994E"
    },
    
    "styles": {
        "line_width": 2.5,
        "marker_size": 8,
        "alpha": 0.8,
        "grid_alpha": 0.3
    },
    
    "titles": {
        "performance_vs_attributes": "Performance vs Nombre d'Attributs",
        "proof_size_vs_attributes": "Taille des Preuves vs Nombre d'Attributs", 
        "performance_vs_disclosure": "Performance vs Taux de Divulgation",
        "proof_size_vs_disclosure": "Taille des Preuves vs Taux de Divulgation",
        "scalability_vs_batch": "Scalabilite vs Taille de Batch",
        "memory_vs_attributes": "Utilisation Memoire vs Nombre d'Attributs",
        "bottleneck_analysis": "Analyse des Goulots d'Etranglement"
    }
}

METRICS_TO_COLLECT = [
    "signature_time_ms",
    "verification_time_ms", 
    "proof_generation_time_ms",
    "proof_verification_time_ms",
    "proof_size_bytes",
    "signature_size_bytes",
    "memory_usage_mb",
    "cpu_usage_percent"
]

def get_config(config_name: str = None) -> BenchmarkConfig:
    """Retourne la configuration demandee ou celle par defaut"""
    if config_name == "quick":
        config = BenchmarkConfig(
            message_counts=[8, 32, 64],
            iterations=5,
            output_formats=["png"]
        )
    elif config_name == "comprehensive":
        config = BenchmarkConfig(
            message_counts=[2, 4, 8, 16, 32, 64, 96, 128],
            disclosure_percentages=[0.1, 0.25, 0.5, 0.75, 0.9, 1.0],
            iterations=20,
            output_formats=["png", "pdf", "svg"]
        )
    else:
        config = DEFAULT_CONFIG
    
    return config

def get_scenario_config(scenario_name: str) -> Optional[Dict[str, Any]]:
    """Retourne la configuration d'un scenario specifique"""
    return SCENARIO_CONFIGS.get(scenario_name)

def get_all_scenarios() -> List[str]:
    """Retourne la liste de tous les scenarios disponibles"""
    return list(SCENARIO_CONFIGS.keys())

def load_profile_config(profile_path: str) -> Dict[str, Any]:
    """Charge un profil JSON personnalise"""
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        return profile
    except FileNotFoundError:
        print(f"Warning: Profile {profile_path} not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {profile_path}: {e}")
        return {}

def determine_scenarios_from_profile(profile: Dict[str, Any]) -> List[str]:
    """Determine quels scenarios executer selon le profil JSON"""
    scenarios = []
    
    profile_type = profile.get('type', 'generic')
    attributes_count = len(profile.get('attributes', []))
    
    if profile_type == 'travel':
        scenarios.append('travel_demo')
    
    if attributes_count <= 10:
        scenarios.append('dtc_complete')
    else:
        scenarios.append('credential_issuance')
    
    if not scenarios:
        scenarios.append('dtc_complete')
    
    return scenarios

def get_csv_filename(metric_type: str, scenario: str = None) -> str:
    """Genere le nom de fichier CSV selon le type de metrique et le scenario"""
    if scenario:
        return f"{metric_type}_{scenario}.csv"
    else:
        return f"{metric_type}.csv"

def validate_profile(profile: Dict[str, Any]) -> bool:
    """Valide la structure d'un profil JSON"""
    required_fields = ['name', 'attributes']
    
    for field in required_fields:
        if field not in profile:
            print(f"Error: Missing required field '{field}' in profile")
            return False
    
    if not isinstance(profile['attributes'], list) or len(profile['attributes']) == 0:
        print("Error: 'attributes' must be a non-empty list")
        return False
    
    return True

BENCHMARK_UTILS = {
    "default_profile": {
        "name": "Default BBS Benchmark",
        "attributes": [
            "passport_number", "full_name", "nationality", "birth_date", 
            "expiry_date", "issuing_country", "document_type", 
            "visa_status", "entry_date", "purpose_of_visit"
        ],
        "disclosure_patterns": [
            {
                "name": "50% Disclosure",
                "disclosed": ["full_name", "nationality", "document_type", "visa_status", "purpose_of_visit"],
                "hidden": ["passport_number", "birth_date", "expiry_date", "issuing_country", "entry_date"]
            }
        ]
    },
    
    "memory_profiling": {
        "enabled": False,
        "interval_ms": 100,
        "max_samples": 1000
    },
    
    "performance_baseline": {
        "min_iterations": 3,
        "max_iterations": 50,
        "warmup_iterations": 2
    }
}