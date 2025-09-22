"""
Tests de performance pour le système BBS-DTC

Ces tests mesurent les performances du système BBS avec différents paramètres :
- Temps de signature vs nombre d'attributs
- Temps de génération de preuve vs nombre d'attributs  
- Temps de vérification vs nombre d'attributs révélés
- Taille des preuves
"""

import unittest
import time
import statistics
import sys
from typing import List, Dict, Any
import json

# Import des modules BBS et DTC
from BBSCore.KeyGen import BBSKeyGen
from BBSCore.bbsSign import BBSSignatureScheme
from BBSCore.ZKProof import BBSProofScheme
from DTC.DTCIssuer import DTCIssuer
from DTC.DTCHolder import DTCHolder
from DTC.DTCVerifier import DTCVerifier


class PerformanceBenchmark:
    """Utilitaire pour mesurer les performances"""
    
    def __init__(self):
        self.results = []
        
    def time_operation(self, operation_name: str, operation_func, iterations: int = 10):
        """Mesure le temps d'une opération avec plusieurs itérations"""
        times = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            result = operation_func()
            end_time = time.perf_counter()
            times.append(end_time - start_time)
            
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        
        benchmark_result = {
            'operation': operation_name,
            'avg_time_ms': avg_time * 1000,
            'std_dev_ms': std_dev * 1000,
            'min_time_ms': min(times) * 1000,
            'max_time_ms': max(times) * 1000,
            'iterations': iterations
        }
        
        self.results.append(benchmark_result)
        return benchmark_result
        
    def get_results(self):
        """Retourne tous les résultats"""
        return self.results
        
    def print_results(self):
        """Affiche les résultats formatés"""
        print("\n" + "="*60)
        print("RÉSULTATS DE PERFORMANCE")
        print("="*60)
        
        for result in self.results:
            print(f"\nOpération: {result['operation']}")
            print(f"  Temps moyen: {result['avg_time_ms']:.2f} ± {result['std_dev_ms']:.2f} ms")
            print(f"  Min/Max: {result['min_time_ms']:.2f} / {result['max_time_ms']:.2f} ms")
            print(f"  Itérations: {result['iterations']}")


class TestSignatureTimeVsAttributes(unittest.TestCase):
    """Tests temps de signature vs nombre d'attributs"""

    def setUp(self):
        """Configuration initiale"""
        self.benchmark = PerformanceBenchmark()
        self.keypair = BBSKeyGen.keygen()
        self.iterations = 5  # Réduit pour tests rapides
        
    def test_signature_scaling(self):
        """Test évolution du temps de signature avec le nombre d'attributs"""
        
        attribute_counts = [1, 5, 10, 15, 20, 25, 30]
        signature_times = []
        
        for count in attribute_counts:
            # Créer BBS scheme avec capacité suffisante
            bbs = BBSSignatureScheme(max_messages=count)
            
            # Générer messages de test
            messages = [f"attribute_{i}_value".encode() for i in range(count)]
            header = b"performance_test_header"
            
            # Mesurer temps de signature
            def sign_operation():
                return bbs.sign(self.keypair.secret_key, messages, header)
            
            result = self.benchmark.time_operation(
                f"signature_{count}_attrs",
                sign_operation,
                self.iterations
            )
            
            signature_times.append({
                'attribute_count': count,
                'avg_time_ms': result['avg_time_ms'],
                'throughput_ops_per_sec': 1000 / result['avg_time_ms']
            })
            
        # Analyse des résultats
        print(f"\n SIGNATURE PERFORMANCE")
        print(f"{'Attributs':<10} {'Temps (ms)':<12} {'Ops/sec':<10}")
        print("-" * 35)
        
        for data in signature_times:
            print(f"{data['attribute_count']:<10} {data['avg_time_ms']:<12.2f} {data['throughput_ops_per_sec']:<10.2f}")
            
        # Vérifications
        self.assertGreater(len(signature_times), 0)
        
        # Le temps doit croître de manière raisonnable (pas exponentielle)
        first_time = signature_times[0]['avg_time_ms']
        last_time = signature_times[-1]['avg_time_ms']
        growth_factor = last_time / first_time
        
        # Croissance ne doit pas être excessive (< 10x pour 30x plus d'attributs)
        self.assertLess(growth_factor, 10.0, "Signature scaling too poor")
        
        # Tous les temps doivent être raisonnables (< 1 seconde)
        for data in signature_times:
            self.assertLess(data['avg_time_ms'], 1000, f"Signature too slow: {data['avg_time_ms']}ms")
            
    def test_signature_batch_performance(self):
        """Test performance signature en lot"""
        
        bbs = BBSSignatureScheme(max_messages=10)
        messages = [f"batch_msg_{i}".encode() for i in range(10)]
        
        # Test différentes tailles de lots
        batch_sizes = [1, 10, 50, 100]
        
        for batch_size in batch_sizes:
            def batch_sign_operation():
                signatures = []
                for i in range(batch_size):
                    header = f"batch_{i}".encode()
                    sig = bbs.sign(self.keypair.secret_key, messages, header)
                    signatures.append(sig)
                return signatures
            
            result = self.benchmark.time_operation(
                f"batch_sign_{batch_size}",
                batch_sign_operation,
                iterations=3  # Moins d'itérations pour les gros lots
            )
            
            avg_per_signature = result['avg_time_ms'] / batch_size
            
            print(f"\n🔄 Lot de {batch_size} signatures:")
            print(f"  Temps total: {result['avg_time_ms']:.2f} ms")
            print(f"  Temps par signature: {avg_per_signature:.2f} ms")
            
        print(" Tests de signature en lot terminés")


class TestProofTimeVsAttributes(unittest.TestCase):
    """Tests temps de génération de preuve vs nombre d'attributs"""

    def setUp(self):
        """Configuration initiale"""
        self.benchmark = PerformanceBenchmark()
        self.keypair = BBSKeyGen.keygen()
        self.iterations = 3
        
    def test_proof_generation_scaling(self):
        """Test évolution temps génération preuve"""
        
        attribute_counts = [5, 10, 15, 20, 25]
        proof_times = []
        
        for count in attribute_counts:
            # Setup
            bbs = BBSSignatureScheme(max_messages=count)
            proof_scheme = BBSProofScheme(max_messages=count)
            
            messages = [f"proof_attr_{i}".encode() for i in range(count)]
            header = b"proof_test_header"
            
            # Créer signature
            signature = bbs.sign(self.keypair.secret_key, messages, header)
            
            # Test génération preuve avec différents taux de révélation
            for reveal_ratio in [0.2, 0.5, 0.8]:  # 20%, 50%, 80% révélés
                revealed_count = max(1, int(count * reveal_ratio))
                disclosed_indices = list(range(revealed_count))
                
                def proof_generation():
                    return proof_scheme.proof_gen(
                        self.keypair.public_key,
                        signature,
                        header,
                        messages,
                        disclosed_indices
                    )
                
                result = self.benchmark.time_operation(
                    f"proof_gen_{count}_attrs_{int(reveal_ratio*100)}pct_revealed",
                    proof_generation,
                    self.iterations
                )
                
                proof_times.append({
                    'total_attributes': count,
                    'revealed_attributes': revealed_count,
                    'reveal_ratio': reveal_ratio,
                    'avg_time_ms': result['avg_time_ms']
                })
                
        # Analyse des résultats
        print(f"\n PROOF GENERATION PERFORMANCE")
        print(f"{'Total':<6} {'Révélés':<8} {'Ratio':<6} {'Temps (ms)':<12}")
        print("-" * 35)
        
        for data in proof_times:
            print(f"{data['total_attributes']:<6} {data['revealed_attributes']:<8} {data['reveal_ratio']:<6.1f} {data['avg_time_ms']:<12.2f}")
            
        # Vérifications
        self.assertGreater(len(proof_times), 0)
        
        # Temps doivent rester raisonnables
        for data in proof_times:
            self.assertLess(data['avg_time_ms'], 2000, f"Proof generation too slow: {data['avg_time_ms']}ms")
            
        print(" Tests génération preuve terminés")
        
    def test_proof_verification_scaling(self):
        """Test évolution temps vérification preuve"""
        
        attribute_counts = [5, 10, 20, 30]
        verification_times = []
        
        for count in attribute_counts:
            bbs = BBSSignatureScheme(max_messages=count)
            proof_scheme = BBSProofScheme(max_messages=count)
            
            messages = [f"verify_attr_{i}".encode() for i in range(count)]
            header = b"verify_test_header"
            
            # Signature et preuve
            signature = bbs.sign(self.keypair.secret_key, messages, header)
            disclosed_indices = list(range(min(5, count)))  # Révéler jusqu'à 5 attributs
            disclosed_messages = [messages[i] for i in disclosed_indices]
            
            proof = proof_scheme.proof_gen(
                self.keypair.public_key,
                signature,
                header,
                messages,
                disclosed_indices
            )
            
            # Mesurer vérification
            def proof_verification():
                return proof_scheme.proof_verify(
                    self.keypair.public_key,
                    proof,
                    header,
                    disclosed_messages,
                    disclosed_indices
                )
            
            result = self.benchmark.time_operation(
                f"proof_verify_{count}_attrs",
                proof_verification,
                self.iterations
            )
            
            verification_times.append({
                'attribute_count': count,
                'avg_time_ms': result['avg_time_ms'],
                'verifications_per_sec': 1000 / result['avg_time_ms']
            })
            
        # Analyse
        print(f"\n PROOF VERIFICATION PERFORMANCE")
        print(f"{'Attributs':<10} {'Temps (ms)':<12} {'Verif/sec':<12}")
        print("-" * 40)
        
        for data in verification_times:
            print(f"{data['attribute_count']:<10} {data['avg_time_ms']:<12.2f} {data['verifications_per_sec']:<12.2f}")
            
        # Vérifications
        for data in verification_times:
            self.assertLess(data['avg_time_ms'], 1500, f"Verification too slow: {data['avg_time_ms']}ms")
            
        print(" Tests vérification preuve terminés")


class TestVerificationTimeVsDisclosure(unittest.TestCase):
    """Tests temps vérification vs nombre d'attributs révélés"""

    def setUp(self):
        """Configuration initiale"""
        self.benchmark = PerformanceBenchmark()
        self.keypair = BBSKeyGen.keygen()
        self.total_attributes = 20
        self.iterations = 5
        
        # Setup commun
        self.bbs = BBSSignatureScheme(max_messages=self.total_attributes)
        self.proof_scheme = BBSProofScheme(max_messages=self.total_attributes)
        
        self.messages = [f"disclosure_attr_{i}".encode() for i in range(self.total_attributes)]
        self.header = b"disclosure_test_header"
        self.signature = self.bbs.sign(self.keypair.secret_key, self.messages, self.header)
        
    def test_verification_vs_disclosure_rate(self):
        """Test temps vérification selon taux de révélation"""
        
        disclosure_rates = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0]  # 10% à 100%
        verification_results = []
        
        for rate in disclosure_rates:
            disclosed_count = max(1, int(self.total_attributes * rate))
            disclosed_indices = list(range(disclosed_count))
            disclosed_messages = [self.messages[i] for i in disclosed_indices]
            
            # Générer preuve
            proof = self.proof_scheme.proof_gen(
                self.keypair.public_key,
                self.signature,
                self.header,
                self.messages,
                disclosed_indices
            )
            
            # Mesurer vérification
            def verification_operation():
                return self.proof_scheme.proof_verify(
                    self.keypair.public_key,
                    proof,
                    self.header,
                    disclosed_messages,
                    disclosed_indices
                )
            
            result = self.benchmark.time_operation(
                f"verify_disclosure_{int(rate*100)}pct",
                verification_operation,
                self.iterations
            )
            
            verification_results.append({
                'disclosure_rate': rate,
                'disclosed_count': disclosed_count,
                'hidden_count': self.total_attributes - disclosed_count,
                'avg_time_ms': result['avg_time_ms']
            })
            
            # Vérifier que résultat est valide
            is_valid = verification_operation()
            self.assertTrue(is_valid, f"Verification failed for {rate*100}% disclosure")
            
        # Analyse des résultats
        print(f"\n VERIFICATION vs DISCLOSURE RATE")
        print(f"{'Taux':<6} {'Révélés':<8} {'Cachés':<7} {'Temps (ms)':<12}")
        print("-" * 40)
        
        for data in verification_results:
            print(f"{data['disclosure_rate']*100:<6.0f}% {data['disclosed_count']:<8} {data['hidden_count']:<7} {data['avg_time_ms']:<12.2f}")
            
        # Vérifications
        # Le temps ne doit pas varier énormément selon le taux de révélation
        times = [r['avg_time_ms'] for r in verification_results]
        time_variation = (max(times) - min(times)) / statistics.mean(times)
        
        self.assertLess(time_variation, 0.5, "Verification time varies too much with disclosure rate")
        
        print(" Tests vérification vs révélation terminés")
        
    def test_batch_verification_performance(self):
        """Test performance vérification en lot"""
        
        # Préparer plusieurs preuves
        proofs_and_data = []
        
        for i in range(10):
            disclosed_indices = [i % self.total_attributes]  # Révéler un attribut différent
            disclosed_messages = [self.messages[j] for j in disclosed_indices]
            
            proof = self.proof_scheme.proof_gen(
                self.keypair.public_key,
                self.signature,
                self.header,
                self.messages,
                disclosed_indices
            )
            
            proofs_and_data.append((proof, disclosed_messages, disclosed_indices))
            
        # Test vérification séquentielle vs lot
        def sequential_verification():
            results = []
            for proof, disclosed_msgs, disclosed_idx in proofs_and_data:
                result = self.proof_scheme.proof_verify(
                    self.keypair.public_key,
                    proof,
                    self.header,
                    disclosed_msgs,
                    disclosed_idx
                )
                results.append(result)
            return all(results)
            
        result = self.benchmark.time_operation(
            "batch_verify_10_proofs",
            sequential_verification,
            iterations=3
        )
        
        avg_per_verification = result['avg_time_ms'] / 10
        
        print(f"\n🔄 Vérification lot de 10 preuves:")
        print(f"  Temps total: {result['avg_time_ms']:.2f} ms")
        print(f"  Temps par vérification: {avg_per_verification:.2f} ms")
        print(f"  Vérifications/seconde: {10000/result['avg_time_ms']:.2f}")
        
        self.assertTrue(sequential_verification(), "Batch verification failed")
        
        print(" Tests vérification en lot terminés")


class TestProofSizeMeasurements(unittest.TestCase):
    """Tests mesure taille des preuves"""

    def setUp(self):
        """Configuration initiale"""
        self.benchmark = PerformanceBenchmark()
        self.keypair = BBSKeyGen.keygen()
        
    def test_proof_size_vs_attributes(self):
        """Test taille preuve selon nombre d'attributs"""
        
        attribute_counts = [5, 10, 15, 20, 25, 30]
        size_results = []
        
        for count in attribute_counts:
            bbs = BBSSignatureScheme(max_messages=count)
            proof_scheme = BBSProofScheme(max_messages=count)
            
            messages = [f"size_attr_{i}".encode() for i in range(count)]
            header = b"size_test_header"
            
            signature = bbs.sign(self.keypair.secret_key, messages, header)
            
            # Tester différents taux de révélation
            for reveal_ratio in [0.2, 0.5, 0.8]:
                disclosed_count = max(1, int(count * reveal_ratio))
                disclosed_indices = list(range(disclosed_count))
                
                proof = proof_scheme.proof_gen(
                    self.keypair.public_key,
                    signature,
                    self.header,
                    messages,
                    disclosed_indices
                )
                
                # Mesurer taille
                proof_bytes = proof.to_bytes()
                proof_size = len(proof_bytes)
                
                size_results.append({
                    'total_attributes': count,
                    'disclosed_count': disclosed_count,
                    'hidden_count': count - disclosed_count,
                    'reveal_ratio': reveal_ratio,
                    'proof_size_bytes': proof_size,
                    'proof_size_kb': proof_size / 1024,
                    'bytes_per_hidden_attr': proof_size / max(1, count - disclosed_count)
                })
                
        # Analyse des résultats
        print(f"\n PROOF SIZE ANALYSIS")
        print(f"{'Total':<6} {'Cachés':<7} {'Ratio':<6} {'Taille (B)':<11} {'KB':<6} {'B/Caché':<8}")
        print("-" * 50)
        
        for data in size_results:
            print(f"{data['total_attributes']:<6} {data['hidden_count']:<7} {data['reveal_ratio']:<6.1f} "
                  f"{data['proof_size_bytes']:<11} {data['proof_size_kb']:<6.2f} {data['bytes_per_hidden_attr']:<8.1f}")
                  
        # Vérifications
        # Les preuves BBS doivent avoir une taille constante (propriété importante)
        sizes_by_hidden = {}
        for data in size_results:
            hidden = data['hidden_count']
            if hidden not in sizes_by_hidden:
                sizes_by_hidden[hidden] = []
            sizes_by_hidden[hidden].append(data['proof_size_bytes'])
            
        # Pour un nombre donné d'attributs cachés, la taille doit être constante
        for hidden_count, sizes in sizes_by_hidden.items():
            if len(sizes) > 1:
                size_variation = (max(sizes) - min(sizes)) / statistics.mean(sizes)
                self.assertLess(size_variation, 0.1, 
                    f"Proof size varies too much for {hidden_count} hidden attributes")
                    
        # Taille globale doit rester raisonnable (< 10KB)
        for data in size_results:
            self.assertLess(data['proof_size_kb'], 10.0, 
                f"Proof too large: {data['proof_size_kb']:.2f} KB")
                
        print(" Tests taille preuve terminés")
        
    def test_signature_size_consistency(self):
        """Test taille signature constante"""
        
        # Tester signatures avec différents nombres d'attributs
        signature_sizes = []
        
        for count in [1, 5, 10, 20, 30]:
            bbs = BBSSignatureScheme(max_messages=count)
            messages = [f"sig_size_{i}".encode() for i in range(count)]
            
            signature = bbs.sign(self.keypair.secret_key, messages, b"size_test")
            sig_bytes = signature.to_bytes()
            
            signature_sizes.append({
                'attribute_count': count,
                'signature_size': len(sig_bytes)
            })
            
        print(f"\n SIGNATURE SIZE ANALYSIS")
        print(f"{'Attributs':<10} {'Taille (B)':<12}")
        print("-" * 25)
        
        for data in signature_sizes:
            print(f"{data['attribute_count']:<10} {data['signature_size']:<12}")
            
        # Vérifier que toutes les signatures ont la même taille (80 bytes)
        expected_size = 80  # 48 (A) + 32 (e) bytes
        for data in signature_sizes:
            self.assertEqual(data['signature_size'], expected_size, 
                f"Signature size inconsistent: {data['signature_size']} != {expected_size}")
                
        print(" Tests taille signature terminés")
        
    def test_storage_efficiency(self):
        """Test efficacité stockage credentials"""
        
        # Créer DTC issuer/holder pour test réaliste
        issuer = DTCIssuer("STORAGE_TEST")
        holder = DTCHolder("storage_user")
        
        # Différents types de credentials
        credentials = []
        
        # Passeport
        passport = issuer.issue_passport({
            "document_type": "passport",
            "document_number": "STORAGE123",
            "nationality": "FR",
            "given_names": "Storage",
            "surname": "Test",
            "date_of_birth": "1990-01-01",
            "place_of_birth": "Paris, France",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "Test Authority"
        })
        credentials.append(('passport', passport))
        
        # Visa
        visa = issuer.issue_visa({
            "document_type": "visa",
            "visa_number": "VISA123",
            "visa_type": "tourist",
            "nationality": "FR",
            "given_names": "Storage",
            "surname": "Test",
            "date_of_birth": "1990-01-01",
            "date_of_issue": "2023-01-01",
            "date_of_expiry": "2024-01-01",
            "issuing_authority": "Embassy",
            "destination_country": "USA"
        })
        credentials.append(('visa', visa))
        
        print(f"\n CREDENTIAL STORAGE EFFICIENCY")
        print(f"{'Type':<15} {'Attributs':<10} {'Taille sig':<12} {'Efficacité':<12}")
        print("-" * 55)
        
        for cred_type, credential in credentials:
            attr_count = len(credential.attributes)
            sig_size = len(credential.signature.to_bytes())
            efficiency = attr_count / sig_size  # Attributs par byte
            
            print(f"{cred_type:<15} {attr_count:<10} {sig_size:<12} {efficiency:<12.4f}")
            
            # Stocker et mesurer
            holder.store_credential(credential)
            
        # Mesurer taille totale du wallet
        total_credentials = len(holder.credentials)
        
        print(f"\n💼 Wallet Summary:")
        print(f"  Total credentials: {total_credentials}")
        print(f"  Storage efficient: {total_credentials * 80} bytes pour signatures")
        
        self.assertGreater(total_credentials, 0)
        
        print(" Tests efficacité stockage terminés")


if __name__ == '__main__':
    # Configuration pour tests de performance
    print("🚀 STARTING BBS-DTC PERFORMANCE TESTS")
    print("="*60)
    
    # Réduire verbosité pour se concentrer sur les métriques
    unittest.main(verbosity=1, buffer=False)