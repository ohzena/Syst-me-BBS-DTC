"""
benchmark/data/schemas.py - Schémas simplifiés pour validation basique

Validation minimale et flexible pour les profils JSON existants
"""

from typing import Dict, Any, List, Tuple

class SimpleValidator:
    """Validateur simplifié pour les profils utilisateur"""
    
    @staticmethod
    def validate_profile(profile_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validation basique d'un profil utilisateur"""
        errors = []
        
        if not isinstance(profile_data, dict):
            errors.append("Profile must be a JSON object")
            return False, errors
        
        if 'attributes' in profile_data:
            attributes = profile_data['attributes']
            if not isinstance(attributes, list):
                errors.append("'attributes' must be a list")
            elif not attributes:
                errors.append("'attributes' cannot be empty")
            elif not all(isinstance(attr, str) for attr in attributes):
                errors.append("All attributes must be strings")
        
        if 'disclosure_patterns' in profile_data:
            patterns = profile_data['disclosure_patterns']
            if not isinstance(patterns, list):
                errors.append("'disclosure_patterns' must be a list")
            else:
                for i, pattern in enumerate(patterns):
                    if not isinstance(pattern, dict):
                        errors.append(f"Pattern {i} must be an object")
                        continue
                    
                    if 'disclosed' not in pattern and 'hidden' not in pattern:
                        errors.append(f"Pattern {i}: either 'disclosed' or 'hidden' required")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_disclosure_pattern(pattern: Dict, all_attributes: List[str]) -> Tuple[bool, str]:
        """Valide un pattern de divulgation"""
        disclosed = set(pattern.get('disclosed', []))
        hidden = set(pattern.get('hidden', []))
        all_attrs = set(all_attributes)
        
        if not disclosed and not hidden:
            return False, "Pattern must specify 'disclosed' or 'hidden'"
        
        invalid_disclosed = disclosed - all_attrs
        if invalid_disclosed:
            return False, f"Unknown disclosed attributes: {invalid_disclosed}"
        
        invalid_hidden = hidden - all_attrs
        if invalid_hidden:
            return False, f"Unknown hidden attributes: {invalid_hidden}"
        
        overlap = disclosed & hidden
        if overlap:
            return False, f"Attributes both disclosed and hidden: {overlap}"
        
        return True, ""
    
    @staticmethod
    def get_pattern_stats(pattern: Dict, total_attributes: int) -> Dict[str, Any]:
        """Calcule les statistiques d'un pattern"""
        disclosed_count = len(pattern.get('disclosed', []))
        hidden_count = len(pattern.get('hidden', []))
        
        if disclosed_count > 0 and hidden_count == 0:
            disclosure_rate = disclosed_count / total_attributes
        elif hidden_count > 0 and disclosed_count == 0:
            disclosure_rate = (total_attributes - hidden_count) / total_attributes
        else:
            disclosure_rate = disclosed_count / total_attributes
        
        return {
            'disclosed_count': disclosed_count,
            'hidden_count': hidden_count,
            'disclosure_rate': disclosure_rate,
            'privacy_level': SimpleValidator._assess_privacy_level(disclosure_rate)
        }
    
    @staticmethod
    def _assess_privacy_level(disclosure_rate: float) -> str:
        """Évalue le niveau de confidentialité"""
        if disclosure_rate <= 0.25:
            return "high"
        elif disclosure_rate <= 0.5:
            return "medium"
        elif disclosure_rate <= 0.75:
            return "low"
        else:
            return "minimal"

class ProfileAnalyzer:
    """Analyseur pour les profils utilisateur"""
    
    def __init__(self):
        self.validator = SimpleValidator()
    
    def analyze_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse complète d'un profil"""
        is_valid, errors = self.validator.validate_profile(profile_data)
        
        attributes = profile_data.get('attributes', [])
        patterns = profile_data.get('disclosure_patterns', [])
        
        analysis = {
            'valid': is_valid,
            'errors': errors,
            'warnings': [],
            'stats': {
                'total_attributes': len(attributes),
                'disclosure_patterns': len(patterns),
                'estimated_performance': self._estimate_performance(len(attributes))
            },
            'patterns_analysis': []
        }
        
        for i, pattern in enumerate(patterns):
            pattern_valid, pattern_error = self.validator.validate_disclosure_pattern(pattern, attributes)
            
            if pattern_valid:
                pattern_stats = self.validator.get_pattern_stats(pattern, len(attributes))
                analysis['patterns_analysis'].append({
                    'index': i,
                    'name': pattern.get('name', f'Pattern {i}'),
                    'valid': True,
                    **pattern_stats
                })
            else:
                analysis['patterns_analysis'].append({
                    'index': i,
                    'name': pattern.get('name', f'Pattern {i}'),
                    'valid': False,
                    'error': pattern_error
                })
                analysis['warnings'].append(f"Pattern {i}: {pattern_error}")
        
        if len(attributes) > 32:
            analysis['warnings'].append("Large number of attributes may impact performance")
        
        if not patterns:
            analysis['warnings'].append("No disclosure patterns defined")
        
        return analysis
    
    def _estimate_performance(self, attribute_count: int) -> str:
        """Estime les performances basées sur le nombre d'attributs"""
        if attribute_count <= 8:
            return "excellent"
        elif attribute_count <= 16:
            return "good"
        elif attribute_count <= 32:
            return "moderate"
        else:
            return "challenging"
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur l'analyse"""
        recommendations = []
        
        stats = analysis['stats']
        patterns = analysis['patterns_analysis']
        
        if stats['total_attributes'] > 50:
            recommendations.append("Consider reducing the number of attributes for better performance")
        elif stats['total_attributes'] < 3:
            recommendations.append("Consider adding more attributes for realistic testing")
        
        if not patterns:
            recommendations.append("Add disclosure patterns to test selective disclosure")
        else:
            disclosure_rates = [p.get('disclosure_rate', 0) for p in patterns if p.get('valid')]
            if disclosure_rates:
                rate_range = max(disclosure_rates) - min(disclosure_rates)
                if rate_range < 0.3:
                    recommendations.append("Add patterns with more diverse disclosure rates")
        
        performance = stats['estimated_performance']
        if performance == "challenging":
            recommendations.append("Consider testing with fewer attributes first")
        elif performance == "excellent":
            recommendations.append("This profile is well-suited for performance testing")
        
        return recommendations

def validate_user_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Interface simple pour valider un profil utilisateur"""
    analyzer = ProfileAnalyzer()
    analysis = analyzer.analyze_profile(profile_data)
    recommendations = analyzer.generate_recommendations(analysis)
    
    return {
        'valid': analysis['valid'],
        'errors': analysis['errors'],
        'warnings': analysis['warnings'],
        'stats': analysis['stats'],
        'patterns': analysis['patterns_analysis'],
        'recommendations': recommendations,
        'summary': f"{analysis['stats']['total_attributes']} attributes, "
                  f"{analysis['stats']['disclosure_patterns']} patterns, "
                  f"performance: {analysis['stats']['estimated_performance']}"
    }

def check_profile_compatibility(profile_data: Dict[str, Any]) -> bool:
    """Check rapide de compatibilité"""
    is_valid, errors = SimpleValidator.validate_profile(profile_data)
    return is_valid and len(errors) == 0

__all__ = [
    'SimpleValidator',
    'ProfileAnalyzer', 
    'validate_user_profile',
    'check_profile_compatibility'
]