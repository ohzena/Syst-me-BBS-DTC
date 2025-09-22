#!/usr/bin/env python3
"""
data_personalized.py - Interface simplifiée pour profils existants

Interface pour utiliser les profils existants dans data/custom
Lecture et adaptation pour BBS
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

def load_profile_for_benchmark(profile_name: str) -> Dict[str, Any]:
    """Charge un profil pour les benchmarks depuis custom data"""
    # Use the correct path to the custom profiles directory
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    custom_dir = os.path.join(script_dir, "custom")
    adapter = ProfileAdapter(custom_dir)
    
    try:
        profile = adapter.load_profile(profile_name)
        
        # Ensure proper structure for benchmark
        if 'profile' not in profile:
            profile = {'profile': profile}
            
        return profile
        
    except Exception as e:
        logger.error(f"Failed to load profile {profile_name}: {e}")
        raise

@dataclass
class ProfileAttribute:
    """Attribut d'un profil pour BBS"""
    name: str
    value: str
    privacy_level: str = "normal"
    
    def to_bbs_message(self) -> bytes:
        """Convertit l'attribut en message BBS"""
        return f"{self.name}:{self.value}".encode('utf-8')

class ProfileAdapter:
    """Adaptateur pour transformer les profils JSON en données BBS"""
    
    def __init__(self, custom_data_dir: str = "custom"):
        self.custom_data_dir = Path(custom_data_dir)
        if not self.custom_data_dir.exists():
            self.custom_data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ProfileAdapter initialized: {self.custom_data_dir}")
    
    def load_profile(self, profile_name: str) -> Dict[str, Any]:
        """Charge un profil depuis custom ou un chemin absolu"""
        from pathlib import Path
        
        # Si profile_name contient un chemin (slash), l'utiliser directement
        if '/' in profile_name or '\\' in profile_name:
            profile_path = Path(profile_name)
            if not profile_path.exists():
                raise FileNotFoundError(f"Profile path '{profile_name}' not found")
        else:
            # Sinon, chercher dans le dossier custom
            clean_name = profile_name.replace('.json', '')
            profile_path = self.custom_data_dir / f"{clean_name}.json"
            
            if not profile_path.exists():
                available = self.list_available_profiles()
                raise FileNotFoundError(
                    f"Profile '{clean_name}' not found. Available: {available}"
                )
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_available_profiles(self) -> List[str]:
        """Liste les profils disponibles"""
        if not self.custom_data_dir.exists():
            return []
        
        return [f.stem for f in self.custom_data_dir.glob("*.json")]
    
    def get_profile_attributes(self, profile_name: str) -> List[ProfileAttribute]:
        """Convertit les attributs d'un profil en ProfileAttribute"""
        profile = self.load_profile(profile_name)
        
        attributes = []
        
        holder = profile.get('credential_holder', {})
        for key, value in holder.items():
            if value and isinstance(value, (str, int, float)):
                attr = ProfileAttribute(
                    name=f"holder_{key}",
                    value=str(value),
                    privacy_level="normal"
                )
                attributes.append(attr)
        
        for attr_name in profile.get('attributes', []):
            metadata = profile.get('attribute_metadata', {})
            if attr_name in metadata:
                example_value = metadata[attr_name].get('example_value', f"value_{attr_name}")
                privacy = "sensitive" if metadata[attr_name].get('sensitive', False) else "normal"
            else:
                example_value = f"example_{attr_name}"
                privacy = "normal"
            
            attr = ProfileAttribute(
                name=attr_name,
                value=str(example_value),
                privacy_level=privacy
            )
            attributes.append(attr)
        
        return attributes
    
    def get_bbs_messages(self, profile_name: str) -> List[bytes]:
        """Convertit un profil en messages BBS"""
        attributes = self.get_profile_attributes(profile_name)
        return [attr.to_bbs_message() for attr in attributes]
    
    def get_disclosure_patterns(self, profile_name: str) -> List[Dict[str, Any]]:
        """Récupère les patterns de divulgation d'un profil"""
        profile = self.load_profile(profile_name)
        
        patterns = []
        for pattern in profile.get('disclosure_patterns', []):
            disclosed = pattern.get('disclosed', [])
            hidden = pattern.get('hidden', [])
            
            all_attributes = self.get_profile_attributes(profile_name)
            attr_names = [attr.name for attr in all_attributes]
            
            disclosed_indices = []
            for attr_name in disclosed:
                if attr_name in attr_names:
                    disclosed_indices.append(attr_names.index(attr_name))
            
            pattern_info = {
                'name': pattern.get('name', 'Unnamed Pattern'),
                'description': pattern.get('description', ''),
                'disclosed_attributes': disclosed,
                'disclosed_indices': disclosed_indices,
                'hidden_attributes': hidden,
                'privacy_level': pattern.get('privacy_level', 'medium'),
                'use_case': pattern.get('use_case', 'general')
            }
            patterns.append(pattern_info)
        
        return patterns
    
    def get_test_parameters(self, profile_name: str) -> Dict[str, Any]:
        """Récupère les paramètres de test d'un profil"""
        profile = self.load_profile(profile_name)
        test_params = profile.get('test_parameters', {})
        
        return {
            'iterations': test_params.get('custom_iterations', test_params.get('iterations', 5)),
            'attribute_variations': test_params.get('attribute_variations', [1, 2, 4, 8, 16, 32]),
            'disclosure_rates': test_params.get('disclosure_rate_variations', [0, 25, 50, 75, 100]),
            'measure_memory': test_params.get('measure_memory', False),
        }
    
    def generate_attribute_variations(self, profile_name: str, target_counts: List[int]) -> List[List[bytes]]:
        """Génère des variations du profil avec différents nombres d'attributs"""
        base_attributes = self.get_profile_attributes(profile_name)
        variations = []
        
        for count in target_counts:
            if count <= len(base_attributes):
                selected = base_attributes[:count]
            else:
                selected = base_attributes.copy()
                original_count = len(selected)
                
                while len(selected) < count:
                    index = len(selected) % original_count
                    original = base_attributes[index]
                    
                    duplicated = ProfileAttribute(
                        name=f"{original.name}_var_{len(selected)}",
                        value=f"{original.value}_extended",
                        privacy_level=original.privacy_level
                    )
                    selected.append(duplicated)
            
            messages = [attr.to_bbs_message() for attr in selected[:count]]
            variations.append(messages)
        
        return variations
    
    def get_profile_summary(self, profile_name: str) -> Dict[str, Any]:
        """Génère un résumé du profil"""
        try:
            profile = self.load_profile(profile_name)
            attributes = self.get_profile_attributes(profile_name)
            patterns = self.get_disclosure_patterns(profile_name)
            test_params = self.get_test_parameters(profile_name)
            
            return {
                'name': profile.get('name', profile_name),
                'description': profile.get('description', ''),
                'holder': profile.get('credential_holder', {}).get('full_name', 'Unknown'),
                'total_attributes': len(attributes),
                'disclosure_patterns': len(patterns),
                'iterations': test_params['iterations'],
                'estimated_complexity': self._estimate_complexity(len(attributes), len(patterns)),
                'recommended_for': self._get_recommendations(len(attributes), len(patterns))
            }
            
        except Exception as e:
            return {
                'name': profile_name,
                'error': str(e),
                'total_attributes': 0,
                'disclosure_patterns': 0
            }
    
    def _estimate_complexity(self, attr_count: int, pattern_count: int) -> str:
        """Estime la complexité du profil"""
        if attr_count <= 5 and pattern_count <= 2:
            return "simple"
        elif attr_count <= 15 and pattern_count <= 5:
            return "moderate"
        elif attr_count <= 30 and pattern_count <= 10:
            return "complex"
        else:
            return "very_complex"
    
    def _get_recommendations(self, attr_count: int, pattern_count: int) -> List[str]:
        """Génère des recommandations d'usage"""
        recommendations = []
        
        if attr_count <= 8:
            recommendations.append("quick_testing")
        if attr_count >= 10:
            recommendations.append("performance_testing")
        if pattern_count >= 3:
            recommendations.append("privacy_analysis")
        if attr_count >= 20:
            recommendations.append("scalability_testing")
        
        return recommendations if recommendations else ["basic_testing"]

class BenchmarkDataProvider:
    """Fournisseur de donnees pour les benchmarks a partir des profils"""
    
    def __init__(self, adapter: ProfileAdapter = None):
        self.adapter = adapter or ProfileAdapter()
    
    def get_test_data_for_profile(self, profile_name: str) -> Dict[str, Any]:
        """Prepare toutes les donnees necessaires pour un benchmark"""
        
        #  Utiliser self.adapter.get_profile_attributes au lieu de self.get_profile_attributes
        attributes = self.adapter.get_profile_attributes(profile_name)
        patterns = self.adapter.get_disclosure_patterns(profile_name)
        test_params = self.adapter.get_test_parameters(profile_name)
        
        base_messages = [attr.to_bbs_message() for attr in attributes]
        
        variations = self.adapter.generate_attribute_variations(
            profile_name, 
            test_params['attribute_variations']
        )
        
        return {
            'profile_name': profile_name,
            'base_messages': base_messages,
            'total_attributes': len(attributes),
            'attribute_variations': variations,
            'disclosure_patterns': patterns,
            'test_parameters': test_params,
            'recommended_iterations': test_params['iterations']
        }
    
    def get_default_disclosure_indices(self, profile_name: str, pattern_name: str = None) -> List[int]:
        """Recupere les indices de divulgation pour un pattern donne"""
        patterns = self.adapter.get_disclosure_patterns(profile_name)
        
        if not patterns:
            total_attrs = len(self.adapter.get_profile_attributes(profile_name))
            return list(range(total_attrs // 2))
        
        target_pattern = None
        if pattern_name:
            for pattern in patterns:
                if pattern['name'] == pattern_name:
                    target_pattern = pattern
                    break
        
        if not target_pattern:
            target_pattern = patterns[0]
        
        return target_pattern.get('disclosed_indices', [])

def load_profile_for_benchmark(profile_name: str = None) -> Dict[str, Any]:
    """Interface simple pour charger un profil pour benchmark"""
    # Use the correct path to the custom profiles directory
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    custom_dir = os.path.join(script_dir, "custom")
    adapter = ProfileAdapter(custom_dir)
    
    if profile_name is None:
        available = adapter.list_available_profiles()
        ellen_profiles = [p for p in available if 'ellen' in p.lower()]
        if ellen_profiles:
            profile_name = ellen_profiles[0]
        elif available:
            profile_name = available[0]
        else:
            raise FileNotFoundError("No profiles found in custom/")
    
    provider = BenchmarkDataProvider(adapter)
    return provider.get_test_data_for_profile(profile_name)

def list_available_profiles() -> List[str]:
    """Liste tous les profils disponibles"""
    # Use the correct path to the custom profiles directory
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    custom_dir = os.path.join(script_dir, "custom")
    adapter = ProfileAdapter(custom_dir)
    return adapter.list_available_profiles()

def get_profile_info(profile_name: str) -> Dict[str, Any]:
    """Récupère les informations d'un profil"""
    # Use the correct path to the custom profiles directory
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    custom_dir = os.path.join(script_dir, "custom")
    adapter = ProfileAdapter(custom_dir)
    return adapter.get_profile_summary(profile_name)