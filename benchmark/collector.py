import time
import statistics
import sys
import os
import csv
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from BBSCore.KeyGen import BBSKeyGen
from BBSCore.ZKProof import BBSWithProofs
from benchmark.config import (
    get_config, get_csv_filename, load_profile_config, 
    validate_profile, BENCHMARK_UTILS
)
from benchmark.scenarios import get_scenario_runner, ScenarioRunner

@dataclass
class BenchmarkResult:
    key_gen_time_ms: float
    sign_time_ms: float
    verify_time_ms: float
    proof_gen_time_ms: float
    proof_verify_time_ms: float
    signature_size_bytes: int
    proof_size_bytes: int
    sk_size_bytes: int
    pk_size_bytes: int

class BenchmarkCollector:
    """
    Collecteur de metriques BBS principal avec support des scenarios
    """
    
    def __init__(self, profile_path: str = None):
        self.csv_dir = Path("benchmark/metrics/csv")
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        
        self.profile = self._load_profile(profile_path)
        self.scenario_runner = get_scenario_runner(original_profile_path=profile_path)
        
        print(f"Using profile: {self.profile['name']}")
        print(f"Base attributes: {len(self.profile['attributes'])}")
        print(f"Available scenarios: {len(self.scenario_runner.get_available_scenarios())}")

    def _load_profile(self, profile_path: str = None) -> Dict[str, Any]:
        """Charge un profil JSON ou utilise le profil par defaut"""
        
        if profile_path:
            profile = load_profile_config(profile_path)
            if profile and validate_profile(profile):
                print(f"[PROFILE] Loaded custom profile: {profile_path}")
                return profile
            else:
                print(f"[WARNING] Failed to load {profile_path}, using default")
        
        default_path = Path(__file__).parent / "data" / "custom" / "ellen_kampire_dtc.json"
        if default_path.exists():
            profile = load_profile_config(str(default_path))
            if profile and validate_profile(profile):
                print(f"[PROFILE] Loaded default profile: Ellen Kampire")
                return profile
        
        print(f"[PROFILE] Using built-in default profile")
        return BENCHMARK_UTILS["default_profile"]

    def _write_csv(self, filename: str, headers: List[str], rows: List[List], scenario: str = None):
        """Sauvegarde les donnees en CSV avec nommage par scenario"""
        
        if scenario:
            base_name = filename.replace('.csv', '')
            filename = f"{base_name}_{scenario}.csv"
        
        filepath = self.csv_dir / filename
        
        with open(filepath, "w", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        
        print(f"CSV saved: {filepath}")

    def _create_profile_attributes(self, count: int) -> List[bytes]:
        """Cree des attributs bases sur le profil charge"""
        base_attrs = self.profile["attributes"]
        holder = self.profile.get("credential_holder", {})
        
        profile_values = {
            "passport_number": holder.get("passport_number", "XX1234567890"),
            "full_name": holder.get("full_name", "Profile User"),
            "nationality": holder.get("nationality", "Unknown"),
            "birth_date": holder.get("birth_date", "1990-01-01"),
            "expiry_date": "2030-12-31",
            "issuing_country": holder.get("birth_country", "Unknown"),
            "document_type": "Passport",
            "visa_status": "Valid",
            "entry_date": "2024-01-01",
            "purpose_of_visit": "Tourism"
        }
        
        attributes = []
        
        for i in range(min(count, len(base_attrs))):
            attr_name = base_attrs[i]
            value = profile_values.get(attr_name, f"value_{i}")
            attributes.append(f"{attr_name}:{value}".encode())
        
        for i in range(len(base_attrs), count):
            attributes.append(f"extra_attr_{i}:value_{i}".encode())
            
        return attributes

    def _run_bbs_benchmark(self, attributes: List[bytes], disclosed_indices: List[int], iterations: int = 5):
        """Execute un benchmark BBS natif"""
        disclosed_messages = [attributes[i] for i in disclosed_indices]
        bbs = BBSWithProofs(max_messages=len(attributes))

        key_gen_times, sign_times, verify_time, proof_gen_times, proof_verify_times = [], [], [], [], []
        sig_size = proof_size = sk_size = pk_size = 0

        print(f"   [BBS] Running {iterations} iterations with {len(attributes)} attrs, {len(disclosed_indices)} disclosed...")

        for i in range(iterations):
            start = time.perf_counter()
            sk, pk = BBSKeyGen.generate_keypair()
            key_gen_times.append((time.perf_counter() - start) * 1000)
            if i == 0:
                sk_size, pk_size = len(sk.to_bytes()), len(pk.to_bytes())

            start = time.perf_counter()
            sig = bbs.sign(sk, attributes, b"header")
            sign_times.append((time.perf_counter() - start) * 1000)
            if i == 0:
                sig_size = len(sig.to_bytes())

            start = time.perf_counter()
            bbs.verify(pk, sig, attributes, b"header")
            verify_time.append((time.perf_counter() - start) * 1000)

            start = time.perf_counter()
            proof = bbs.generate_proof(pk, sig, b"header", attributes, disclosed_indices, b"presentation")
            proof_gen_times.append((time.perf_counter() - start) * 1000)
            if i == 0:
                proof_size = len(proof.to_bytes())

            start = time.perf_counter()
            bbs.verify_proof(pk, proof, b"header", disclosed_messages, disclosed_indices, b"presentation")
            proof_verify_times.append((time.perf_counter() - start) * 1000)

        return BenchmarkResult(
            key_gen_time_ms=statistics.mean(key_gen_times),
            sign_time_ms=statistics.mean(sign_times),
            verify_time_ms=statistics.mean(verify_time),
            proof_gen_time_ms=statistics.mean(proof_gen_times),
            proof_verify_time_ms=statistics.mean(proof_verify_times),
            signature_size_bytes=sig_size,
            proof_size_bytes=proof_size,
            sk_size_bytes=sk_size,
            pk_size_bytes=pk_size
        )

    def measure_batch_performance(self, batch_sizes: List[int] = None, iterations: int = None, scenario: str = None):
        """Mesure les performances de traitement par lots"""
        
        if batch_sizes is None:
            batch_sizes = [1, 5, 10, 20, 50]
        if iterations is None:
            iterations = 5
            
        print(f"Measuring batch performance{' for ' + scenario if scenario else ''}...")
        
        rows = []
        profile_attrs = self._create_profile_attributes(len(self.profile["attributes"]))
        
        if self.profile.get("disclosure_patterns"):
            default_disclosed = self.profile["disclosure_patterns"][0]["disclosed"]
            disclosed_indices = [i for i, attr in enumerate(self.profile["attributes"]) 
                               if attr in default_disclosed]
        else:
            disclosed_indices = list(range(len(self.profile["attributes"]) // 2))
        
        for batch in batch_sizes:
            print(f"Batch size: {batch}")
            result = self._run_bbs_benchmark(profile_attrs, disclosed_indices, iterations)
            avg_time_per_op = result.sign_time_ms / batch if batch > 1 else result.sign_time_ms
            rows.append([batch, result.sign_time_ms, avg_time_per_op])
            
        self._write_csv("batch_performance.csv", 
                       ["batch_size", "total_sign_time_ms", "avg_time_per_op_ms"], 
                       rows, scenario)

    def measure_disclosure_rate(self, attribute_count: int = None, rates: List[int] = None, 
                               iterations: int = None, scenario: str = None):
        """Mesure l'impact du taux de divulgation"""
        
        if attribute_count is None:
            attribute_count = len(self.profile["attributes"])
        if rates is None:
            rates = [0, 10, 15, 25, 50, 75, 100]
        if iterations is None:
            iterations = 5
            
        print(f"Measuring disclosure rate impact{' for ' + scenario if scenario else ''}...")
        
        rows = []
        attributes = self._create_profile_attributes(attribute_count)
        
        for rate in rates:
            disclosed_count = int((attribute_count * rate) / 100)
            disclosed_indices = list(range(disclosed_count))
            
            print(f"Disclosure rate: {rate}% ({disclosed_count}/{attribute_count} attrs)")
            result = self._run_bbs_benchmark(attributes, disclosed_indices, iterations)
            
            rows.append([
                rate, 
                disclosed_count,
                result.proof_gen_time_ms,
                result.proof_verify_time_ms,
                result.proof_size_bytes
            ])
            
        self._write_csv("disclosure_rate.csv", 
                       ["disclosure_percent", "disclosed_count", "proof_gen_time_ms", 
                        "proof_verify_time_ms", "proof_size_bytes"], 
                       rows, scenario)

    def measure_scalability(self, attribute_counts: List[int] = None, iterations: int = None, scenario: str = None):
        """Mesure la scalabilite selon le nombre d'attributs"""
        
        if attribute_counts is None:
            attribute_counts = [1, 2, 4, 8, 10, 16, 32, 64, 128]
        if iterations is None:
            iterations = 5
            
        print(f"Measuring scalability{' for ' + scenario if scenario else ''}...")
        
        rows = []
        default_disclosed_ratio = 0.5  
        
        for count in attribute_counts:
            attributes = self._create_profile_attributes(count)
            disclosed_count = max(1, int(count * default_disclosed_ratio))
            disclosed_indices = list(range(disclosed_count))
            
            print(f"Attributes: {count} (disclosing {disclosed_count})")
            result = self._run_bbs_benchmark(attributes, disclosed_indices, iterations)
            
            rows.append([
                count,
                result.key_gen_time_ms,
                result.sign_time_ms,
                result.verify_time_ms,
                result.proof_gen_time_ms,
                result.proof_verify_time_ms,
                result.signature_size_bytes,
                result.proof_size_bytes,
                result.sk_size_bytes,
                result.pk_size_bytes
            ])
            
        self._write_csv("scalability.csv", 
                       ["attribute_count", "key_gen_time_ms", "sign_time_ms", 
                        "verify_time_ms", "proof_gen_time_ms", "proof_verify_time_ms",
                        "signature_size_bytes", "proof_size_bytes", 
                        "sk_size_bytes", "pk_size_bytes"], 
                       rows, scenario)


    def measure_scenario_performance(self, scenario_name: str, iterations: int = None):
        """
        Mesure les performances d'un scenario specifique
        
        Args:
            scenario_name: Nom du scenario a mesurer
            iterations: Nombre d'iterations (utilise config du scenario si None)
        """
        
        if not self.scenario_runner.is_scenario_available(scenario_name):
            print(f"Scenario {scenario_name} not available")
            return
            
        scenario_config = self.scenario_runner.get_scenario_info(scenario_name)
        if iterations is None:
            iterations = scenario_config.get('default_iterations', 5)
            
        print(f"Measuring scenario performance: {scenario_name}")
        print(f"Description: {scenario_config.get('description', 'N/A')}")
        print(f"Iterations: {iterations}")
        
        # LIGNE CORRIGÉE : Utiliser 'run_scenario' au lieu de 'run_scenario_from_profile'
        result = self.scenario_runner.run_scenario(
            scenario_name, 
            self.profile["attributes"], 
            self.profile.get("disclosure_patterns", [{}])[0], # Utilise le premier pattern par défaut
            iterations
        )
        
        if not result.get('success'):
            print(f"Scenario execution failed: {result.get('error_message', 'Unknown error')}")
            return
        
        print(f"Running native BBS benchmarks for {scenario_name}...")
        
        self.measure_batch_performance(scenario=scenario_name, iterations=iterations)
        self.measure_disclosure_rate(scenario=scenario_name, iterations=iterations)
        self.measure_scalability(scenario=scenario_name, iterations=iterations)
        
        self._save_scenario_results(scenario_name, result)
        
        print(f"Scenario {scenario_name} benchmarking complete")


    def _save_scenario_results(self, scenario_name: str, result: Dict[str, Any]):
        """Sauvegarde les resultats specifiques d'un scenario"""
        
        scenario_csv = f"scenario_{scenario_name}.csv"
        
        headers = [
            "scenario_name", "success", "iterations", "attributes_count", "disclosed_count",
            "avg_execution_time_ms", "min_time_ms", "max_time_ms", "real_demo_used",
            "profile_name", "profile_type"
        ]
        
        row = [
            result.get('scenario_type', scenario_name),
            result.get('success', False),
            result.get('iterations', 0),
            result.get('attributes_count', 0),
            result.get('disclosed_count', 0),
            result.get('avg_execution_time_ms', 0),
            result.get('min_time_ms', 0),
            result.get('max_time_ms', 0),
            result.get('real_demo_used', False),
            result.get('profile_name', 'Unknown'),
            result.get('profile_type', 'generic')
        ]
        
        self._write_csv(scenario_csv, headers, [row])
        
        json_path = self.csv_dir / f"scenario_{scenario_name}_details.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Scenario details saved: {json_path}")

    def run_multiple_scenarios(self, scenarios: List[str], iterations: int = 5):
        """
        Execute plusieurs scenarios en sequence
        
        Args:
            scenarios: Liste des scenarios a executer
            iterations: Nombre d'iterations par scenario
        """
        
        print(f"Running multiple scenarios: {', '.join(scenarios)}")
        
        for scenario_name in scenarios:
            print(f"\n{'='*60}")
            print(f"SCENARIO: {scenario_name}")
            print(f"{'='*60}")
            
            self.measure_scenario_performance(scenario_name, iterations)
        
        print(f"\nAll scenarios completed!")

    def run_profile_scenarios(self, iterations: int = None):
        """
        Execute les scenarios appropries selon le profil charge
        
        Args:
            iterations: Nombre d'iterations (utilise config profil si None)
        """
        
        from benchmark.config import determine_scenarios_from_profile
        
        scenarios = determine_scenarios_from_profile(self.profile)
        
        if iterations is None:
            iterations = self.profile.get('test_parameters', {}).get('custom_iterations', 5)
        
        print(f"Running scenarios for profile: {self.profile['name']}")
        print(f"Selected scenarios: {', '.join(scenarios)}")
        
        self.run_multiple_scenarios(scenarios, iterations)

    def generate_summary_report(self, scenario: str = None):
        """Genere un rapport de synthese"""
        
        summary = {
            "profile": self.profile["name"],
            "holder": self.profile.get("credential_holder", {}).get("full_name", "Unknown"),
            "total_attributes": len(self.profile["attributes"]),
            "scenario_suffix": scenario,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "available_scenarios": self.scenario_runner.get_available_scenarios(),
            "demo_status": self.scenario_runner.get_demo_status()
        }
        
        if self.profile.get("disclosure_patterns"):
            pattern = self.profile["disclosure_patterns"][0]
            summary.update({
                "default_disclosure_rate": f"{len(pattern['disclosed'])}/{len(self.profile['attributes'])} attributes",
                "disclosed_attributes": len(pattern["disclosed"]),
                "hidden_attributes": len(pattern["hidden"])
            })
        
        csv_files = []
        for csv_file in self.csv_dir.glob("*.csv"):
            if scenario and scenario in csv_file.name:
                csv_files.append(csv_file.name)
            elif not scenario:
                csv_files.append(csv_file.name)
        
        summary["csv_files_generated"] = csv_files
        
        report_name = f"benchmark_summary_{scenario}.json" if scenario else "benchmark_summary.json"
        summary_path = self.csv_dir / report_name
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Summary report saved: {summary_path}")
        return summary

    def run_default_benchmarks(self, iterations: int = 5):
        """
        Execute les benchmarks par defaut (sans scenario specifique)
        Utilise quand aucun scenario n'est choisi
        """
        
        print(f"Running default BBS benchmarks...")
        print(f"Profile: {self.profile['name']}")
        print(f"Iterations: {iterations}")
        
        self.measure_batch_performance(iterations=iterations)
        self.measure_disclosure_rate(iterations=iterations)
        self.measure_scalability(iterations=iterations)
        self.generate_summary_report()
        
        print(f"Default benchmarks complete!")


if __name__ == "__main__":
    print("BenchmarkCollector - Testing with default profile")
    print("="*50)
    
    collector = BenchmarkCollector()
    
    print("\n1. Testing default benchmarks...")
    collector.run_default_benchmarks(iterations=3)
    
    print("\n2. Testing scenario benchmarks...")
    available_scenarios = collector.scenario_runner.get_available_scenarios()
    
    if available_scenarios:
        test_scenario = available_scenarios[0]
        print(f"   Testing scenario: {test_scenario}")
        collector.measure_scenario_performance(test_scenario, iterations=2)
    else:
        print("   No scenarios available for testing")
    
    print("\n3. Testing profile scenarios...")
    collector.run_profile_scenarios(iterations=2)
    
    print("\nBenchmarkCollector testing complete!")