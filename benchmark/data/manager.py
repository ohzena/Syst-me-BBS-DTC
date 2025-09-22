"""
benchmark/data/manager.py - Gestionnaire simplifié de données JSON

Lecture et validation des profils existants dans custom
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    """Gestionnaire simplifié - lecture seule des profils existants"""
    
    def __init__(self, custom_data_dir: str = "custom"):
        if not os.path.isabs(custom_data_dir):
            project_root = self._find_project_root()
            self.custom_data_dir = project_root / custom_data_dir
        else:
            self.custom_data_dir = Path(custom_data_dir)
        
        self.custom_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"DataManager initialisé: {self.custom_data_dir}")
    
    def _find_project_root(self) -> Path:
        """Trouve la racine du projet"""
        current = Path(__file__).resolve()
        markers = ['requirements.txt', 'BBSCore', 'README.md']
        
        for parent in [current] + list(current.parents):
            if any((parent / marker).exists() for marker in markers):
                return parent
        
        return current.parent.parent.parent
    
    def list_available_profiles(self) -> List[str]:
        """Liste tous les profils JSON disponibles"""
        if not self.custom_data_dir.exists():
            return []
        
        profiles = []
        for json_file in self.custom_data_dir.glob("*.json"):
            profiles.append(json_file.stem)
        
        return sorted(profiles)
    
    def load_profile(self, profile_name: str) -> Dict[str, Any]:
        """Charge un profil depuis custom"""
        clean_name = profile_name.replace('.json', '')
        profile_path = self.custom_data_dir / f"{clean_name}.json"
        
        if not profile_path.exists():
            available = self.list_available_profiles()
            raise FileNotFoundError(
                f"Profile '{clean_name}' not found in {self.custom_data_dir}\n"
                f"Available profiles: {available}"
            )
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                raise ValueError("Profile must be a JSON object")
            
            if 'attributes' not in data:
                data['attributes'] = []
            
            if 'name' not in data:
                data['name'] = clean_name
            
            logger.info(f"Loaded profile: {data.get('name', clean_name)}")
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {profile_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading {profile_path}: {e}")
            raise
    
    def get_profile_summary(self, profile_name: str) -> str:
        """Retourne un résumé d'un profil"""
        try:
            profile = self.load_profile(profile_name)
            
            name = profile.get('name', 'Unknown')
            holder = profile.get('credential_holder', {})
            holder_name = holder.get('full_name', holder.get('name', 'Unknown'))
            
            attributes = profile.get('attributes', [])
            patterns = profile.get('disclosure_patterns', [])
            test_params = profile.get('test_parameters', {})
            
            summary = f"""
                PROFILE: {name}
                Holder: {holder_name}
                Attributes: {len(attributes)}
                Disclosure patterns: {len(patterns)}
                Iterations: {test_params.get('custom_iterations', test_params.get('iterations', 'N/A'))}
            """.strip()
            
            if len(attributes) <= 15:
                summary += f"\nAttributes: {', '.join(attributes)}"
            
            return summary
            
        except Exception as e:
            return f"Error loading profile '{profile_name}': {e}"
    
    def validate_profile(self, profile_data: Dict[str, Any]) -> List[str]:
        """Validation basique d'un profil"""
        warnings = []
        
        if 'attributes' not in profile_data:
            warnings.append("No 'attributes' field found")
        elif not profile_data['attributes']:
            warnings.append("Empty attributes list")
        
        if 'disclosure_patterns' not in profile_data:
            warnings.append("No 'disclosure_patterns' field found")
        
        attributes = set(profile_data.get('attributes', []))
        for i, pattern in enumerate(profile_data.get('disclosure_patterns', [])):
            disclosed = set(pattern.get('disclosed', []))
            hidden = set(pattern.get('hidden', []))
            
            invalid_disclosed = disclosed - attributes
            if invalid_disclosed:
                warnings.append(f"Pattern {i}: unknown disclosed attributes: {invalid_disclosed}")
            
            invalid_hidden = hidden - attributes
            if invalid_hidden:
                warnings.append(f"Pattern {i}: unknown hidden attributes: {invalid_hidden}")
        
        return warnings
    
    def get_default_profile_name(self) -> str:
        """Retourne le nom du profil par défaut (Ellen Kampire)"""
        available = self.list_available_profiles()
        
        ellen_candidates = [p for p in available if 'ellen' in p.lower() and 'kampire' in p.lower()]
        if ellen_candidates:
            return ellen_candidates[0]
        
        if available:
            return available[0]
        
        raise FileNotFoundError("No profiles found in custom/")
    
    def check_profile_compatibility(self, profile_name: str) -> Dict[str, Any]:
        """Vérifie la compatibilité d'un profil avec le système BBS"""
        try:
            profile = self.load_profile(profile_name)
            warnings = self.validate_profile(profile)
            
            attributes = profile.get('attributes', [])
            patterns = profile.get('disclosure_patterns', [])
            
            compatibility = {
                'status': 'compatible',
                'warnings': warnings,
                'recommendations': [],
                'stats': {
                    'total_attributes': len(attributes),
                    'disclosure_patterns': len(patterns),
                    'max_disclosed': 0,
                    'min_disclosed': len(attributes)
                }
            }
            
            for pattern in patterns:
                disclosed_count = len(pattern.get('disclosed', []))
                compatibility['stats']['max_disclosed'] = max(compatibility['stats']['max_disclosed'], disclosed_count)
                compatibility['stats']['min_disclosed'] = min(compatibility['stats']['min_disclosed'], disclosed_count)
            
            if len(attributes) > 50:
                compatibility['recommendations'].append("Large number of attributes may impact performance")
            
            if compatibility['stats']['max_disclosed'] == len(attributes):
                compatibility['recommendations'].append("Consider adding patterns with selective disclosure")
            
            if warnings:
                compatibility['status'] = 'compatible_with_warnings'
            
            return compatibility
            
        except Exception as e:
            return {
                'status': 'incompatible',
                'error': str(e),
                'warnings': [],
                'recommendations': ['Fix the profile format and try again']
            }

def load_user_profile(profile_name: str = None) -> Dict[str, Any]:
    """Interface simple pour charger un profil utilisateur"""
    manager = DataManager()
    
    if profile_name is None:
        profile_name = manager.get_default_profile_name()
    
    return manager.load_profile(profile_name)

def list_user_profiles() -> List[str]:
    """Interface simple pour lister les profils"""
    manager = DataManager()
    return manager.list_available_profiles()

def get_user_profile_summary(profile_name: str = None) -> str:
    """Interface simple pour obtenir un résumé"""
    manager = DataManager()
    
    if profile_name is None:
        profile_name = manager.get_default_profile_name()
    
    return manager.get_profile_summary(profile_name)