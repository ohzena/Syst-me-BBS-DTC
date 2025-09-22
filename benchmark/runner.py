# benchmark/runner.py
import sys
import os
from pathlib import Path
import json
import argparse
from typing import List, Dict, Any, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from benchmark.collector import BenchmarkCollector
from benchmark.visualization.graphs import GraphGenerator
from benchmark.visualization.extra_graphs import ExtraGraphGenerator
from benchmark.config import (
    load_profile_config, validate_profile, determine_scenarios_from_profile,
    get_all_scenarios, get_config
)

def load_ellen_kampire_config():
    """Charge la configuration par défaut d'Ellen Kampire"""
    config_path = Path(__file__).parent / "data" / "custom" / "ellen_kampire_dtc.json"
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"Loaded default user config: {config['name']}")
        return config
    else:
        print("Default user config not found, using defaults")
        return {
            "name": "Ellen KAMPIRE - Default",
            "attributes": [
                "passport_number", "full_name", "nationality", "birth_date", 
                "expiry_date", "issuing_country", "document_type", 
                "visa_status", "entry_date", "purpose_of_visit"
            ],
            "disclosure_patterns": [
                {
                    "name": "Default 50% Disclosure",
                    "disclosed": ["full_name", "nationality", "document_type", "visa_status", "purpose_of_visit"],
                    "hidden": ["passport_number", "birth_date", "expiry_date", "issuing_country", "entry_date"]
                }
            ],
            "test_parameters": {
                "custom_iterations": 15,
                "attribute_variations": [1, 2, 4, 8, 16, 32, 64, 128],
                "disclosure_rate_variations": [0, 10, 15, 25, 50, 75, 100]
            }
        }

def run_default_ellen_kampire():
    """Exécute le benchmark par défaut avec Ellen Kampire (mode simple)"""
    print("Running BBS-DTC Benchmark Suite for Default Profile\n")

    # Charger la configuration d'Ellen Kampire
    ellen_config = load_ellen_kampire_config()
    iterations = ellen_config["test_parameters"]["custom_iterations"]
    
    print(f"User Profile: {ellen_config['name']}")
    print(f"Attributes: {len(ellen_config['attributes'])}")
    print(f"Iterations: {iterations}")
    print(f"Default Disclosure: 50% (5/10 attributes)")
    
    # Collecte des métriques avec le Collector
    print("\nCollecting BBS performance metrics...")
    collector = BenchmarkCollector()
    
    print("  - Measuring batch performance...")
    collector.measure_batch_performance(
        batch_sizes=[1, 5, 10, 20, 50], 
        iterations=iterations
    )
    
    print("  - Measuring disclosure rate impact...")
    collector.measure_disclosure_rate(
        attribute_count=len(ellen_config['attributes']), 
        rates=ellen_config["test_parameters"]["disclosure_rate_variations"],
        iterations=iterations
    )
    
    print("  - Measuring scalability...")
    collector.measure_scalability(
        attribute_counts=ellen_config["test_parameters"]["attribute_variations"],
        iterations=iterations
    )

    # Génération des graphiques (chacun charge ses propres données CSV)
    graphs_dir = Path("benchmark/metrics/graphs")
    graphs_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating main performance graphs...")
    main_graphs = GraphGenerator()
    main_graphs.generate_all_graphs()  # Pas de paramètre - charge les CSV

    print("\nGenerating advanced analysis graphs...")
    extra_graphs = ExtraGraphGenerator()
    extra_graphs.generate_all_graphs()  # Pas de paramètre - charge les CSV

    print("\nBenchmark Complete!")
    print("Results saved in:")
    print("   CSV data:    benchmark/metrics/csv/")
    print("   Graphs:      benchmark/metrics/graphs/basic/ & benchmark/metrics/graphs/advanced/")
    print(f"\nProfile used: Ellen Kampire ({len(ellen_config['attributes'])} attributes, {iterations} iterations)")

class BenchmarkRunner:
    def __init__(self, profile_path: str = None, config_name: str = None):
        self.profile_path = profile_path
        self.config = get_config(config_name)
        self.profile = None
        self.collector = None
    
    def load_profile(self, profile_path: str = None) -> Dict[str, Any]:
        if profile_path:
            self.profile_path = profile_path
        
        if self.profile_path:
            profile = load_profile_config(self.profile_path)
            if profile and validate_profile(profile):
                self.profile = profile
                return profile
        
        # Fallback Ellen Kampire
        default_path = Path(__file__).parent / "data" / "custom" / "ellen_kampire_dtc.json"
        if default_path.exists():
            profile = load_profile_config(str(default_path))
            if profile and validate_profile(profile):
                self.profile = profile
                return profile
        
        # Built-in default
        from benchmark.config import BENCHMARK_UTILS
        self.profile = BENCHMARK_UTILS["default_profile"]
        return self.profile
    
    def initialize_collector(self):
        self.collector = BenchmarkCollector(self.profile_path)
    
    def determine_execution_plan(self, scenarios: List[str] = None) -> Dict[str, Any]:
        if not self.profile:
            self.load_profile()
        
        plan = {
            "profile": self.profile,
            "scenarios": [],
            "iterations": self.config.iterations,
            "execution_mode": "default"
        }
        
        if scenarios:
            plan["scenarios"] = scenarios
            plan["execution_mode"] = "custom_scenarios"
        else:
            auto_scenarios = determine_scenarios_from_profile(self.profile)
            plan["scenarios"] = auto_scenarios
            plan["execution_mode"] = "profile_based"
        
        test_params = self.profile.get('test_parameters', {})
        if 'custom_iterations' in test_params:
            plan["iterations"] = test_params['custom_iterations']
        
        return plan
    
    def execute_benchmarks(self, scenarios: List[str] = None, iterations: int = None):
        if not self.profile:
            self.load_profile()
        if not self.collector:
            self.initialize_collector()
        
        plan = self.determine_execution_plan(scenarios)
        
        if iterations:
            plan["iterations"] = iterations
        
        print(f"Running benchmarks: {plan['profile']['name']}")
        print(f"Mode: {plan['execution_mode']}, Iterations: {plan['iterations']}")
        
        if plan["scenarios"]:
            print(f"Scenarios: {', '.join(plan['scenarios'])}")
            self.collector.run_multiple_scenarios(plan["scenarios"], plan["iterations"])
        else:
            print("Running default benchmarks...")
            self.collector.run_default_benchmarks(plan["iterations"])
        
        return plan
    
    def generate_visualizations(self, scenarios: List[str] = None):
        graphs_dir = Path("benchmark/metrics/graphs")
        graphs_dir.mkdir(parents=True, exist_ok=True)
        
        print("Generating graphs...")
        try:
            basic_graphs = GraphGenerator()
            basic_graphs.generate_all_graphs()
        except Exception as e:
            print(f"Error generating basic graphs: {e}")
        
        try:
            advanced_graphs = ExtraGraphGenerator()
            advanced_graphs.generate_all_graphs()
        except Exception as e:
            print(f"Error generating advanced graphs: {e}")
    
    def run_full_suite(self, scenarios: List[str] = None, iterations: int = None, 
                       generate_graphs: bool = True):
        try:
            plan = self.execute_benchmarks(scenarios, iterations)
            
            if generate_graphs:
                self.generate_visualizations(plan.get("scenarios"))
            
            print("Benchmark suite completed!")
            print("Results in: benchmark/metrics/")
            return True
            
        except Exception as e:
            print(f"Benchmark failed: {e}")
            return False

def create_argument_parser():
    parser = argparse.ArgumentParser(description="BBS-DTC Benchmark Runner")
    
    parser.add_argument('--profile', '-p', type=str, help='Path to JSON profile file')
    parser.add_argument('--scenarios', '-s', nargs='+',
                       choices=['credential_issuance', 'travel_demo', 'dtc_complete',
                                'auto_privacy', 'blind_signature', 'interactive_disclosure'],
                       help='Specific scenarios to run')
    parser.add_argument('--iterations', '-i', type=int, help='Number of iterations')
    parser.add_argument('--config', '-c', choices=['default', 'quick', 'comprehensive'],
                       default='default', help='Benchmark configuration')
    parser.add_argument('--no-graphs', action='store_true', help='Skip graph generation')
    parser.add_argument('--list-scenarios', action='store_true', help='List available scenarios')
    parser.add_argument('--validate-profile', type=str, help='Validate profile and exit')
    
    return parser

def main():
    # Vérifier si aucun argument n'est fourni -> mode simple Ellen Kampire
    if len(sys.argv) == 1:
        run_default_ellen_kampire()
        return
    
    # Sinon, utiliser la logique modulaire avec arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if args.list_scenarios:
        print("Available scenarios:")
        for scenario in get_all_scenarios():
            print(f"  {scenario}")
        return
    
    if args.validate_profile:
        profile = load_profile_config(args.validate_profile)
        if profile and validate_profile(profile):
            print(f"Profile {args.validate_profile} is valid")
        else:
            print(f"Profile {args.validate_profile} is invalid")
        return
    
    runner = BenchmarkRunner(profile_path=args.profile, config_name=args.config)
    
    success = runner.run_full_suite(
        scenarios=args.scenarios,
        iterations=args.iterations,
        generate_graphs=not args.no_graphs
    )
    
    exit(0 if success else 1)

# Utility functions
def run_default_benchmarks(profile_path: str = None, iterations: int = 15):
    runner = BenchmarkRunner(profile_path=profile_path)
    return runner.run_full_suite(scenarios=None, iterations=iterations)

def run_scenario_benchmarks(scenarios: List[str], profile_path: str = None, iterations: int = 5):
    runner = BenchmarkRunner(profile_path=profile_path)
    return runner.run_full_suite(scenarios=scenarios, iterations=iterations)

if __name__ == "__main__":
    main()