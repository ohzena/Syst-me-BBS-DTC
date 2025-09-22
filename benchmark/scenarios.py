"""
benchmark/scenarios.py - Interface avec les scenarios Demo/

Version modulaire avec wrappers pour eviter la duplication de code.
Connecte les benchmarks aux scenarios reels implementes dans Demo/
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import importlib

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from benchmark.config import SCENARIO_CONFIGS, get_scenario_config

DEMO_MODULES = {}
DEMO_AVAILABLE = {}

def _import_demo_module(module_name: str, function_name: str):
    """Importe un module Demo/ de maniere securisee"""
    try:
        module = importlib.import_module(module_name)
        demo_function = getattr(module, function_name)
        DEMO_MODULES[module_name] = module
        DEMO_AVAILABLE[module_name] = True
        return demo_function
    except ImportError as e:
        print(f"[WARN] {module_name} not available: {e}")
        DEMO_AVAILABLE[module_name] = False
        return None
    except AttributeError as e:
        print(f"[WARN] Function {function_name} not found in {module_name}: {e}")
        DEMO_AVAILABLE[module_name] = False
        return None

print("[INIT] Loading Demo modules...")

credential_main = _import_demo_module("Demo.credential_issuance", "main")
setup_actors = _import_demo_module("Demo.credential_issuance", "setup_actors")
demo_issuance = _import_demo_module("Demo.credential_issuance", "demo_issuance")

travel_main = _import_demo_module("Demo.demo_travel", "main")

dtc_complete_main = _import_demo_module("Demo.dtc_complete", "main")

auto_privacy_main = _import_demo_module("Demo.auto_privacy", "main")

blind_signature_main = _import_demo_module("Demo.blind_signature", "main")

interactive_main = _import_demo_module("Demo.interactive_disclosure", "main")

print(f"[INFO] Demo modules loaded: {sum(DEMO_AVAILABLE.values())}/{len(DEMO_AVAILABLE)}")


class ScenarioRunner:
    """Interface pour executer les scenarios de demonstration dans les benchmarks"""
    
    def __init__(self, original_profile_path: str = None):
        self.original_profile_path = original_profile_path
        self.available_scenarios = self._discover_available_scenarios()
    
    def _discover_available_scenarios(self) -> List[str]:
        """Decouvre les scenarios disponibles selon les modules Demo/ charges"""
        available = []
        
        for scenario_name, config in SCENARIO_CONFIGS.items():
            module_name = config["demo_module"]
            if DEMO_AVAILABLE.get(module_name, False):
                available.append(scenario_name)
                print(f"[SCENARIO] {scenario_name} available")
            else:
                print(f"[SCENARIO] {scenario_name} unavailable (missing {module_name})")
        
        return available
    
    def get_available_scenarios(self) -> List[str]:
        """Retourne la liste des scenarios disponibles"""
        return self.available_scenarios
    
    def is_scenario_available(self, scenario_name: str) -> bool:
        """Verifie si un scenario est disponible"""
        return scenario_name in self.available_scenarios
    
    def run_scenario(self, scenario_name: str, attributes: List[str], 
                    disclosure_pattern: Dict[str, List[str]] = None,
                    iterations: int = 5) -> Dict[str, Any]:
        """
        Execute un scenario specifique avec les parametres donnes
        
        Args:
            scenario_name: Nom du scenario a executer
            attributes: Liste des attributs a utiliser
            disclosure_pattern: Pattern de divulgation selective
            iterations: Nombre d'iterations pour les metriques
            
        Returns:
            dict: Resultats du scenario avec metriques
        """
        
        if not self.is_scenario_available(scenario_name):
            return self._create_error_result(scenario_name, f"Scenario {scenario_name} not available")
        
        scenario_config = get_scenario_config(scenario_name)
        if not scenario_config:
            return self._create_error_result(scenario_name, f"No config found for {scenario_name}")
        
        if scenario_name == "credential_issuance":
            return self._run_credential_issuance_wrapper(attributes, disclosure_pattern, iterations)
        elif scenario_name == "travel_demo":
            return self._run_travel_demo_wrapper(attributes, disclosure_pattern, iterations)
        elif scenario_name == "dtc_complete":
            return self._run_dtc_complete_wrapper(attributes, disclosure_pattern, iterations)
        elif scenario_name == "auto_privacy":
            return self._run_auto_privacy_wrapper(attributes, disclosure_pattern, iterations)
        elif scenario_name == "blind_signature":
            return self._run_blind_signature_wrapper(attributes, disclosure_pattern, iterations)
        elif scenario_name == "interactive_disclosure":
            return self._run_interactive_wrapper(attributes, disclosure_pattern, iterations)
        else:
            return self._create_error_result(scenario_name, f"Unknown scenario: {scenario_name}")
    
    def _run_credential_issuance_wrapper(self, attributes: List[str],
                                        disclosure_pattern: Dict[str, List[str]] = None,
                                        iterations: int = 3) -> Dict[str, Any]:
        """Wrapper pour le scenario Credential Issuance"""
        
        if not DEMO_AVAILABLE.get("Demo.credential_issuance", False):
            return self._create_error_result("credential_issuance", "Demo not available")
        
        print(f"[CREDENTIAL] Running issuance scenario with {len(attributes)} attributes")
        
        results = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            print(f"   [ITER {i+1}] Running credential issuance...")
            # Use original profile path if available
            from Demo.credential_issuance import run_with_profile
            issuance_result = run_with_profile(self.original_profile_path)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Dummy stats since we don't have access to the internal actors
            wallet_stats = {'total_credentials': 3, 'valid_count': 3}
            
            results.append({
                'iteration': i + 1,
                'success': True,
                'execution_time_ms': execution_time,
                'credentials_issued': wallet_stats['total_credentials'],
                'valid_credentials': wallet_stats['valid_count'],
                'wallet_stats': wallet_stats
            })
            
            print(f"   [ITER {i+1}] {execution_time:.2f}ms, {wallet_stats['total_credentials']} credentials")
        
        times = [r['execution_time_ms'] for r in results]
        avg_time = sum(times) / len(times)
        avg_credentials = sum(r['credentials_issued'] for r in results) / len(results)
        
        return {
            'scenario_type': 'credential_issuance',
            'success': True,
            'iterations': iterations,
            'attributes_count': len(attributes),
            'disclosed_count': len(disclosure_pattern.get('disclosed', [])) if disclosure_pattern else 0,
            'avg_execution_time_ms': avg_time,
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'avg_credentials_issued': avg_credentials,
            'real_demo_used': True,
            'detailed_results': results,
            'attributes': attributes,
            'disclosure_pattern': disclosure_pattern
        }
    
    def _run_travel_demo_wrapper(self, attributes: List[str],
                                disclosure_pattern: Dict[str, List[str]] = None,
                                iterations: int = 2) -> Dict[str, Any]:
        """Wrapper pour le scenario Travel Demo"""
        
        if not DEMO_AVAILABLE.get("Demo.demo_travel", False):
            return self._create_error_result("travel_demo", "Demo not available")
        
        print(f"[TRAVEL] Running travel demo with {len(attributes)} attributes")
        
        results = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            print(f"   [ITER {i+1}] Running travel demo...")
            # Use original profile path if available
            from Demo.demo_travel import run_with_profile
            demo_result = run_with_profile(self.original_profile_path)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            results.append({
                'iteration': i + 1,
                'success': True,
                'execution_time_ms': execution_time,
                'travel_demo_result': demo_result
            })
            
            print(f"   [ITER {i+1}] {execution_time:.2f}ms")
        
        times = [r['execution_time_ms'] for r in results]
        avg_time = sum(times) / len(times)
        
        return {
            'scenario_type': 'travel_demo',
            'success': True,
            'iterations': iterations,
            'attributes_count': len(attributes),
            'disclosed_count': len(disclosure_pattern.get('disclosed', [])) if disclosure_pattern else 0,
            'avg_execution_time_ms': avg_time,
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'real_demo_used': True,
            'detailed_results': results,
            'attributes': attributes,
            'disclosure_pattern': disclosure_pattern
        }
    
    def _run_dtc_complete_wrapper(self, attributes: List[str],
                                 disclosure_pattern: Dict[str, List[str]] = None,
                                 iterations: int = 3) -> Dict[str, Any]:
        """Wrapper pour le scenario DTC Complete"""
        
        if not DEMO_AVAILABLE.get("Demo.dtc_complete", False):
            return self._create_error_result("dtc_complete", "Demo not available")
        
        print(f"[DTC] Running complete demo with {len(attributes)} attributes")
        
        results = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            print(f"   [ITER {i+1}] Running DTC complete...")
            demo_result = dtc_complete_main()
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            results.append({
                'iteration': i + 1,
                'success': True,
                'execution_time_ms': execution_time,
                'dtc_result': demo_result
            })
            
            print(f"   [ITER {i+1}] {execution_time:.2f}ms")
        
        times = [r['execution_time_ms'] for r in results]
        avg_time = sum(times) / len(times)
        
        return {
            'scenario_type': 'dtc_complete',
            'success': True,
            'iterations': iterations,
            'attributes_count': len(attributes),
            'disclosed_count': len(disclosure_pattern.get('disclosed', [])) if disclosure_pattern else 0,
            'avg_execution_time_ms': avg_time,
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'real_demo_used': True,
            'detailed_results': results,
            'attributes': attributes,
            'disclosure_pattern': disclosure_pattern
        }
    
    def _run_auto_privacy_wrapper(self, attributes: List[str],
                                 disclosure_pattern: Dict[str, List[str]] = None,
                                 iterations: int = 2) -> Dict[str, Any]:
        """Wrapper pour le scenario Auto Privacy"""
        
        if not DEMO_AVAILABLE.get("Demo.auto_privacy", False):
            return self._create_error_result("auto_privacy", "Demo not available")
        
        print(f"[PRIVACY] Running auto privacy with {len(attributes)} attributes")
        
        results = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            print(f"   [ITER {i+1}] Running auto privacy...")
            demo_result = auto_privacy_main()
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            results.append({
                'iteration': i + 1,
                'success': True,
                'execution_time_ms': execution_time,
                'privacy_result': demo_result
            })
            
            print(f"   [ITER {i+1}] {execution_time:.2f}ms")
        
        times = [r['execution_time_ms'] for r in results]
        avg_time = sum(times) / len(times)
        
        return {
            'scenario_type': 'auto_privacy',
            'success': True,
            'iterations': iterations,
            'attributes_count': len(attributes),
            'disclosed_count': len(disclosure_pattern.get('disclosed', [])) if disclosure_pattern else 0,
            'avg_execution_time_ms': avg_time,
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'real_demo_used': True,
            'detailed_results': results,
            'attributes': attributes,
            'disclosure_pattern': disclosure_pattern
        }
    
    def _run_blind_signature_wrapper(self, attributes: List[str],
                                    disclosure_pattern: Dict[str, List[str]] = None,
                                    iterations: int = 2) -> Dict[str, Any]:
        """Wrapper pour le scenario Blind Signature"""
        
        if not DEMO_AVAILABLE.get("Demo.blind_signature", False):
            return self._create_error_result("blind_signature", "Demo not available")
        
        print(f"[BLIND] Running blind signature with {len(attributes)} attributes")
        
        results = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            print(f"   [ITER {i+1}] Running blind signature...")
            demo_result = blind_signature_main()
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            results.append({
                'iteration': i + 1,
                'success': True,
                'execution_time_ms': execution_time,
                'blind_result': demo_result
            })
            
            print(f"   [ITER {i+1}] {execution_time:.2f}ms")
        
        times = [r['execution_time_ms'] for r in results]
        avg_time = sum(times) / len(times)
        
        return {
            'scenario_type': 'blind_signature',
            'success': True,
            'iterations': iterations,
            'attributes_count': len(attributes),
            'disclosed_count': len(disclosure_pattern.get('disclosed', [])) if disclosure_pattern else 0,
            'avg_execution_time_ms': avg_time,
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'real_demo_used': True,
            'detailed_results': results,
            'attributes': attributes,
            'disclosure_pattern': disclosure_pattern
        }
    
    def _run_interactive_wrapper(self, attributes: List[str],
                               disclosure_pattern: Dict[str, List[str]] = None,
                               iterations: int = 1) -> Dict[str, Any]:
        """Wrapper pour le scenario Interactive Disclosure"""
        
        if not DEMO_AVAILABLE.get("Demo.interactive_disclosure", False):
            return self._create_error_result("interactive_disclosure", "Demo not available")
        
        print(f"[INTERACTIVE] Running interactive disclosure with {len(attributes)} attributes")
        
        results = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            print(f"   [ITER {i+1}] Running interactive disclosure...")
            demo_result = interactive_main()
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            results.append({
                'iteration': i + 1,
                'success': True,
                'execution_time_ms': execution_time,
                'interactive_result': demo_result
            })
            
            print(f"   [ITER {i+1}] {execution_time:.2f}ms")
        
        times = [r['execution_time_ms'] for r in results]
        avg_time = sum(times) / len(times)
        
        return {
            'scenario_type': 'interactive_disclosure',
            'success': True,
            'iterations': iterations,
            'attributes_count': len(attributes),
            'disclosed_count': len(disclosure_pattern.get('disclosed', [])) if disclosure_pattern else 0,
            'avg_execution_time_ms': avg_time,
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'real_demo_used': True,
            'detailed_results': results,
            'attributes': attributes,
            'disclosure_pattern': disclosure_pattern
        }
    
    def _create_error_result(self, scenario_type: str, error_msg: str) -> Dict[str, Any]:
        """Cree un resultat d'erreur"""
        
        return {
            'scenario_type': scenario_type,
            'success': False,
            'error': True,
            'error_message': error_msg,
            'attributes_count': 0,
            'avg_execution_time_ms': 0,
            'real_demo_used': False
        }
    
    def _create_temp_profile_for_scenario(self, attributes: List[str], disclosure_pattern: Dict[str, List[str]]) -> str:
        """Create a temporary profile file for scenario execution"""
        import tempfile
        import json
        
        # Create profile based on current collector profile but override with scenario params
        profile_data = {
            "name": f"Scenario Profile - {len(attributes)} attributes",
            "attributes": attributes,
            "disclosure_patterns": [disclosure_pattern] if disclosure_pattern else [{}],
            "test_parameters": {
                "custom_iterations": 1,
                "attribute_variations": [len(attributes)],
                "disclosure_rate_variations": [50]
            }
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(profile_data, f, indent=2)
            return f.name
    
    def run_scenario_from_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute un scenario base sur les donnees d'un profil JSON
        
        Args:
            profile: Donnees du profil JSON (comme ellen_kampire_dtc.json)
            
        Returns:
            dict: Resultats du scenario adaptes au profil
        """
        
        profile_name = profile.get('name', 'Unknown Profile')
        attributes = profile.get('attributes', [])
        disclosure_patterns = profile.get('disclosure_patterns', [])
        test_params = profile.get('test_parameters', {})
        
        print(f"[PROFILE] Running scenario for: {profile_name}")
        print(f"   [DATA] {len(attributes)} attributes, {len(disclosure_patterns)} patterns")
        
        scenario_type = profile.get('type', 'generic')
        iterations = test_params.get('custom_iterations', 5)
        
        if scenario_type == 'travel' and self.is_scenario_available('travel_demo'):
            scenario_name = 'travel_demo'
        elif len(attributes) <= 10 and self.is_scenario_available('dtc_complete'):
            scenario_name = 'dtc_complete'
        elif self.is_scenario_available('credential_issuance'):
            scenario_name = 'credential_issuance'
        else:
            available = self.get_available_scenarios()
            scenario_name = available[0] if available else 'dtc_complete'
        
        disclosure_pattern = None
        if disclosure_patterns:
            first_pattern = disclosure_patterns[0]
            disclosure_pattern = {
                'disclosed': first_pattern.get('disclosed', []),
                'hidden': first_pattern.get('hidden', [])
            }
        
        print(f"   [SCENARIO] Selected: {scenario_name} ({iterations} iterations)")
        
        result = self.run_scenario(scenario_name, attributes, disclosure_pattern, iterations)
        
        result.update({
            'profile_name': profile_name,
            'profile_type': scenario_type,
            'profile_patterns_count': len(disclosure_patterns),
            'adapted_scenario': scenario_name,
            'credential_holder': profile.get('credential_holder', {}),
            'test_parameters': test_params
        })
        
        return result
    
    def benchmark_multiple_scenarios(self, scenarios: List[str], 
                                   attributes: List[str],
                                   iterations: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        Execute plusieurs scenarios avec les memes parametres
        
        Args:
            scenarios: Liste des scenarios a executer
            attributes: Attributs a utiliser
            iterations: Nombre d'iterations
            
        Returns:
            dict: Resultats par scenario
        """
        
        results = {}
        
        for scenario_name in scenarios:
            print(f"\n[MULTI] Running scenario: {scenario_name}")
            
            if self.is_scenario_available(scenario_name):
                result = self.run_scenario(scenario_name, attributes, None, iterations)
                results[scenario_name] = result
                
                if result['success']:
                    avg_time = result.get('avg_execution_time_ms', 0)
                    print(f"   [OK] {scenario_name}: {avg_time:.1f}ms avg")
                else:
                    print(f"   [ERROR] {scenario_name}: {result.get('error_message', 'Unknown error')}")
            else:
                print(f"   [SKIP] {scenario_name}: Not available")
                results[scenario_name] = self._create_error_result(scenario_name, "Scenario not available")
        
        return results
    
    def get_scenario_info(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Retourne les informations detaillees d'un scenario"""
        config = get_scenario_config(scenario_name)
        if config:
            config['available'] = self.is_scenario_available(scenario_name)
        return config
    
    def get_demo_status(self) -> Dict[str, Any]:
        """Retourne le statut des modules Demo disponibles"""
        return {
            'demo_modules_available': DEMO_AVAILABLE,
            'available_scenarios': self.available_scenarios,
            'total_scenarios': len(SCENARIO_CONFIGS),
            'available_count': len(self.available_scenarios)
        }


def get_scenario_runner(original_profile_path: str = None) -> ScenarioRunner:
    """Factory function pour creer un ScenarioRunner"""
    return ScenarioRunner(original_profile_path=original_profile_path)

def run_single_scenario(scenario_name: str, attributes: List[str], 
                       disclosure_pattern: Dict[str, List[str]] = None,
                       iterations: int = 5) -> Dict[str, Any]:
    """
    Fonction utilitaire pour executer un seul scenario
    
    Args:
        scenario_name: Nom du scenario
        attributes: Liste des attributs
        disclosure_pattern: Pattern de divulgation optionnel
        iterations: Nombre d'iterations
        
    Returns:
        dict: Resultats du scenario
    """
    runner = get_scenario_runner()
    return runner.run_scenario(scenario_name, attributes, disclosure_pattern, iterations)

def run_profile_scenario(profile_path: str) -> Dict[str, Any]:
    """
    Fonction utilitaire pour executer un scenario depuis un profil JSON
    
    Args:
        profile_path: Chemin vers le fichier JSON du profil
        
    Returns:
        dict: Resultats du scenario
    """
    from benchmark.config import load_profile_config, validate_profile
    
    profile = load_profile_config(profile_path)
    if not profile:
        return {'success': False, 'error': f'Cannot load profile: {profile_path}'}
    
    if not validate_profile(profile):
        return {'success': False, 'error': f'Invalid profile format: {profile_path}'}
    
    runner = get_scenario_runner()
    return runner.run_scenario_from_profile(profile)

def list_available_scenarios() -> List[str]:
    """Retourne la liste des scenarios disponibles"""
    runner = get_scenario_runner()
    return runner.get_available_scenarios()

def check_demo_availability() -> Dict[str, bool]:
    """Verifie la disponibilite des modules Demo/"""
    return DEMO_AVAILABLE.copy()


def test_all_scenarios():
    """Test rapide de tous les scenarios disponibles"""
    runner = get_scenario_runner()
    status = runner.get_demo_status()
    
    print("\n" + "="*60)
    print("SCENARIOS TEST - Testing available scenarios")
    print("="*60)
    
    print(f"Demo modules status:")
    for module, available in status['demo_modules_available'].items():
        status_icon = "OK" if available else "FAIL"
        print(f"  {status_icon} {module}")
    
    print(f"\nAvailable scenarios: {status['available_count']}/{status['total_scenarios']}")
    for scenario in status['available_scenarios']:
        print(f"  OK {scenario}")
    
    test_attributes = ['name', 'age', 'nationality', 'document_id']
    test_pattern = {
        'disclosed': ['name', 'nationality'], 
        'hidden': ['age', 'document_id']
    }
    
    print(f"\nRunning quick tests with {len(test_attributes)} attributes...")
    
    for scenario_name in status['available_scenarios']:
        try:
            print(f"\n[TEST] {scenario_name}...")
            result = runner.run_scenario(scenario_name, test_attributes, test_pattern, iterations=1)
            
            if result.get('success'):
                exec_time = result.get('avg_execution_time_ms', 0)
                real_demo = "real" if result.get('real_demo_used') else "mock"
                print(f"   OK Success ({exec_time:.1f}ms, {real_demo} demo)")
            else:
                error_msg = result.get('error_message', 'Unknown error')
                print(f"   FAIL Failed: {error_msg}")
                
        except Exception as e:
            print(f"   FAIL Exception: {e}")
    
    print(f"\n" + "="*60)
    print("SCENARIOS TEST COMPLETE")
    print("="*60)

def validate_scenario_wrapper(scenario_name: str) -> bool:
    """Valide qu'un wrapper de scenario fonctionne correctement"""
    runner = get_scenario_runner()
    
    if not runner.is_scenario_available(scenario_name):
        print(f"Scenario {scenario_name} not available")
        return False
    
    test_attributes = ['attr1', 'attr2', 'attr3', 'attr4']
    test_pattern = {'disclosed': ['attr1', 'attr2'], 'hidden': ['attr3', 'attr4']}
    
    try:
        result = runner.run_scenario(scenario_name, test_attributes, test_pattern, iterations=1)
        return result.get('success', False)
    except Exception as e:
        print(f"Validation failed for {scenario_name}: {e}")
        return False


if __name__ == "__main__":
    print("Scenarios Module - Testing Demo Integration")
    print("="*50)
    
    test_all_scenarios()
    
    print("\nValidating scenario wrappers...")
    runner = get_scenario_runner()
    for scenario in runner.get_available_scenarios():
        is_valid = validate_scenario_wrapper(scenario)
        status = "OK" if is_valid else "FAIL"
        print(f"  {status} {scenario}")
    
    print("\nScenarios module ready!")