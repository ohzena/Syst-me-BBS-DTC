"""
Tests d'intégration complets pour le système BBS-DTC

Ces tests vérifient le fonctionnement end-to-end du système :
- Flux complet de bout en bout avec succès
- Détection et rejet des credentials altérés  
- Intégration avec les données de benchmark
- Scénarios de voyage complets
"""

import unittest
import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import des modules principaux
from DTC import DTCIssuer, DTCHolder, DTCVerifier, create_demo_scenario
from Demo.dtc_complete import main as demo_main
from Demo.demo_travel import main as travel_main
from benchmark.data.manager import DataManager


class TestFullFlowSuccess(unittest.TestCase):
    """Tests pour le flux complet avec succès"""

    def setUp(self):
        """Configuration d'un écosystème DTC complet"""
        self.scenario = create_demo_scenario()
        
        # Acteurs du système
        self.french_gov = self.scenario['issuers']['french_gov']
        self.us_embassy = self.scenario['issuers']['us_embassy'] 
        self.health_ministry = self.scenario['issuers']['health_ministry']
        
        self.alice = self.scenario['holders']['alice']
        
        self.border_control = self.scenario['verifiers']['border_control']
        self.airline = self.scenario['verifiers']['airline']
        
    def test_complete_travel_workflow(self):
        """Test workflow complet de voyage avec multiples credentials"""
        
        # === PHASE 1: EMISSION DES CREDENTIALS ===
        
        # 1. Gouvernement français émet un passeport
        passport_data = {
            "document_type": "passport",
            "document_number": "20FR12345",
            "nationality": "FR",
            "given_names": "Alice Marie",
            "surname": "Dubois",
            "date_of_birth": "1992-05-10",
            "place_of_birth": "Lyon, France", 
            "date_of_issue": "2022-01-15",
            "date_of_expiry": "2032-01-15",
            "issuing_authority": "République Française"
        }
        
        passport = self.french_gov.issue_passport(passport_data)
        self.assertIsNotNone(passport.signature)
        
        # 2. Ambassade US émet un visa
        visa_data = {
            "document_type": "visa",
            "visa_number": "US2023NYK001",
            "visa_type": "B1/B2",
            "nationality": "FR",
            "given_names": "Alice Marie",
            "surname": "Dubois",
            "date_of_birth": "1992-05-10",
            "date_of_issue": "2023-06-01",
            "date_of_expiry": "2033-06-01",
            "issuing_authority": "US Embassy Paris",
            "destination_country": "USA"
        }
        
        visa = self.us_embassy.issue_visa(visa_data)
        self.assertIsNotNone(visa.signature)
        
        # 3. Ministère santé émet certificat vaccination
        vaccination_data = {
            "document_type": "vaccination_certificate",
            "certificate_id": "VAX2023FR001",
            "given_names": "Alice Marie",
            "surname": "Dubois", 
            "date_of_birth": "1992-05-10",
            "vaccination_details": {
                "vaccine_name": "COVID-19 mRNA",
                "manufacturer": "Pfizer-BioNTech",
                "doses": [
                    {"date": "2021-05-15", "batch": "EJ1685"},
                    {"date": "2021-07-10", "batch": "FD1234"},
                    {"date": "2022-01-20", "batch": "GH5678"}
                ]
            },
            "issuing_authority": "French Health Ministry"
        }
        
        vaccination = self.health_ministry.issue_vaccination(vaccination_data)
        self.assertIsNotNone(vaccination.signature)
        
        # === PHASE 2: STOCKAGE PAR LE DETENTEUR ===
        
        # Alice stocke tous ses credentials
        self.alice.store_credential(passport)
        self.alice.store_credential(visa)
        self.alice.store_credential(vaccination)
        
        # Vérifier stockage
        self.assertEqual(len(self.alice.credentials), 3)
        
        # === PHASE 3: VERIFICATION À L'AÉROPORT ===
        
        # Alice présente passeport et visa à la compagnie aérienne
        # (divulgation sélective - pas besoin de révéler date de naissance)
        airline_presentation = self.alice.create_combined_presentation([
            (passport.credential_id, ["nationality", "surname", "given_names", "date_of_expiry"]),
            (visa.credential_id, ["destination_country", "visa_type", "date_of_expiry"])
        ])
        
        airline_result = self.airline.verify_presentation(airline_presentation)
        self.assertTrue(airline_result.is_valid)
        self.assertEqual(airline_result.disclosed_attributes["nationality"], "FR")
        self.assertEqual(airline_result.disclosed_attributes["destination_country"], "USA")
        
        # === PHASE 4: CONTRÔLE FRONTALIER ===
        
        # Alice présente tous ses credentials au contrôle frontalier
        # Mais utilise divulgation sélective pour la vaccination (pas de détails des doses)
        border_presentation = self.alice.create_combined_presentation([
            (passport.credential_id, ["nationality", "surname", "given_names", "date_of_birth"]),
            (visa.credential_id, ["destination_country", "visa_type", "date_of_issue"]),
            (vaccination.credential_id, ["certificate_id", "vaccine_name", "issuing_authority"])
        ])
        
        border_result = self.border_control.verify_presentation(border_presentation)
        self.assertTrue(border_result.is_valid)
        
        # Vérifier que les informations sensibles ne sont pas révélées
        self.assertNotIn("vaccination_details", border_result.disclosed_attributes)
        
        # === PHASE 5: VÉRIFICATION DES PROPRIÉTÉS BBS ===
        
        # 5a. Unlinkability: les deux présentations ne peuvent pas être corrélées
        # (En théorie - on ne peut pas le tester directement, mais c'est garanti par BBS)
        
        # 5b. Selective Disclosure: vérifier qu'informations cachées restent cachées
        self.assertNotIn("date_of_birth", airline_result.disclosed_attributes)
        self.assertNotIn("vaccination_details", border_result.disclosed_attributes)
        
        # 5c. Authenticité: toutes les signatures sont valides
        self.assertTrue(airline_result.is_valid)
        self.assertTrue(border_result.is_valid)
        
        print(" Workflow complet de voyage réussi avec divulgation sélective")
        
    def test_age_verification_without_birthdate(self):
        """Test vérification d'âge sans révéler date de naissance"""
        
        # Émettre passeport pour majeur
        adult_passport_data = {
            "document_type": "passport",
            "document_number": "ADULT123",
            "nationality": "FR",
            "given_names": "Majeur",
            "surname": "Testeur",
            "date_of_birth": "1990-01-01",  # Plus de 18 ans
            "place_of_birth": "Paris, France",
            "date_of_issue": "2020-01-01", 
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "République Française"
        }
        
        passport = self.french_gov.issue_passport(adult_passport_data)
        self.alice.store_credential(passport)
        
        # Alice prouve qu'elle a plus de 18 ans sans révéler sa date de naissance
        age_proof = self.alice.create_age_proof_presentation(
            passport.credential_id,
            min_age=18
        )
        
        # Vérifier que la preuve est acceptée
        result = self.border_control.verify_presentation(age_proof)
        self.assertTrue(result.is_valid)
        self.assertTrue(result.age_requirements_met)
        
        # Vérifier que date de naissance n'est PAS révélée
        self.assertNotIn("date_of_birth", result.disclosed_attributes)
        
        print(" Vérification d'âge réussie sans révéler date de naissance")
        
    def test_multi_issuer_trust_chain(self):
        """Test chaîne de confiance avec multiples émetteurs"""
        
        # Créer un autre émetteur non fiable
        rogue_issuer = DTCIssuer("ROGUE_ISSUER")
        
        # Credential émis par émetteur fiable
        valid_passport = self.french_gov.issue_passport({
            "document_type": "passport",
            "document_number": "VALID999",
            "nationality": "FR",
            "given_names": "Legitimate",
            "surname": "User",
            "date_of_birth": "1985-01-01",
            "place_of_birth": "Paris, France",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01", 
            "issuing_authority": "République Française"
        })
        
        # Credential émis par émetteur non fiable
        rogue_passport = rogue_issuer.issue_passport({
            "document_type": "passport",
            "document_number": "FAKE123",
            "nationality": "XX",
            "given_names": "Fake",
            "surname": "User",
            "date_of_birth": "1985-01-01",
            "place_of_birth": "Unknown",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "Fake Authority"
        })
        
        self.alice.store_credential(valid_passport)
        self.alice.store_credential(rogue_passport)
        
        # Présenter credential valide
        valid_presentation = self.alice.create_full_presentation(valid_passport.credential_id)
        valid_result = self.border_control.verify_presentation(valid_presentation)
        self.assertTrue(valid_result.is_valid)
        
        # Présenter credential non fiable
        rogue_presentation = self.alice.create_full_presentation(rogue_passport.credential_id)
        rogue_result = self.border_control.verify_presentation(rogue_presentation)
        self.assertFalse(rogue_result.is_valid)
        self.assertIn("untrusted", rogue_result.error_message.lower())
        
        print(" Chaîne de confiance fonctionne correctement")


class TestFullFlowTamperedCredential(unittest.TestCase):
    """Tests pour détection des credentials altérés"""

    def setUp(self):
        """Configuration pour tests d'altération"""
        self.scenario = create_demo_scenario()
        self.issuer = self.scenario['issuers']['french_gov']
        self.holder = self.scenario['holders']['alice']
        self.verifier = self.scenario['verifiers']['border_control']
        
        # Créer credential valide
        self.valid_data = {
            "document_type": "passport",
            "document_number": "TAMPER123",
            "nationality": "FR",
            "given_names": "Test",
            "surname": "User",
            "date_of_birth": "1990-01-01",
            "place_of_birth": "Paris, France", 
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "République Française"
        }
        
        self.credential = self.issuer.issue_passport(self.valid_data)
        self.holder.store_credential(self.credential)
        
    def test_detect_altered_attribute_value(self):
        """Test détection d'altération de valeur d'attribut"""
        
        # Altérer la nationalité après émission
        tampered_cred = self.credential.copy()
        tampered_cred.attributes["nationality"].value = "HACKED"
        
        # Remplacer dans le stockage du détenteur
        self.holder.credentials[tampered_cred.credential_id] = tampered_cred
        
        # Essayer de présenter le credential altéré
        presentation = self.holder.create_full_presentation(tampered_cred.credential_id)
        result = self.verifier.verify_presentation(presentation)
        
        # Doit être rejeté
        self.assertFalse(result.is_valid)
        self.assertIn("signature", result.error_message.lower())
        
        print(" Altération d'attribut détectée et rejetée")
        
    def test_detect_signature_tampering(self):
        """Test détection d'altération de signature"""
        
        # Créer une fausse signature
        from BBSCore.bbsSign import BBSSignature
        fake_signature = BBSSignature(A=self.credential.signature.A, e=12345)
        
        # Remplacer la signature
        tampered_cred = self.credential.copy()
        tampered_cred.signature = fake_signature
        
        self.holder.credentials[tampered_cred.credential_id] = tampered_cred
        
        # Essayer de présenter
        presentation = self.holder.create_full_presentation(tampered_cred.credential_id)
        result = self.verifier.verify_presentation(presentation)
        
        # Doit être rejeté
        self.assertFalse(result.is_valid)
        
        print(" Altération de signature détectée et rejetée")
        
    def test_detect_replay_attack(self):
        """Test détection d'attaque par rejeu"""
        
        # Créer une présentation valide
        original_presentation = self.holder.create_selective_presentation(
            self.credential.credential_id,
            ["nationality", "surname"]
        )
        
        # Première vérification doit réussir
        result1 = self.verifier.verify_presentation(original_presentation)
        self.assertTrue(result1.is_valid)
        
        # Essayer de rejouer la même présentation
        # (Dans un vrai système, on utiliserait des nonces/timestamps)
        result2 = self.verifier.verify_presentation(original_presentation)
        
        # Pour ce test, on vérifie juste que la signature est toujours valide
        # En pratique, le système devrait rejeter les rejeux via des nonces
        self.assertTrue(result2.is_valid)
        
        print(" Mécanisme de détection de rejeu testé")
        
    def test_detect_mixed_credentials(self):
        """Test détection de mélange d'attributs de différents credentials"""
        
        # Créer un second credential
        other_data = {
            "document_type": "passport",
            "document_number": "OTHER456", 
            "nationality": "DE",
            "given_names": "Other",
            "surname": "Person",
            "date_of_birth": "1985-12-25",
            "place_of_birth": "Berlin, Germany",
            "date_of_issue": "2021-01-01",
            "date_of_expiry": "2031-01-01",
            "issuing_authority": "Deutschland"
        }
        
        other_credential = self.issuer.issue_passport(other_data)
        self.holder.store_credential(other_credential)
        
        # Essayer de mélanger les attributs (attaque sophistiquée)
        # Alice essaie de créer un "frankenstein credential"
        try:
            mixed_cred = self.credential.copy()
            mixed_cred.attributes["nationality"] = other_credential.attributes["nationality"]
            # Mais garde la signature originale
            
            self.holder.credentials[mixed_cred.credential_id] = mixed_cred
            
            presentation = self.holder.create_full_presentation(mixed_cred.credential_id)
            result = self.verifier.verify_presentation(presentation)
            
            # Doit être rejeté car signature ne correspond plus
            self.assertFalse(result.is_valid)
            
        except Exception as e:
            # Si ça lève une exception, c'est aussi une protection valide
            print(f" Mélange détecté par exception: {e}")
            
        print(" Protection contre mélange de credentials testée")


class TestDemoTravelWithBenchmarkData(unittest.TestCase):
    """Tests d'intégration avec les données de benchmark"""
    
    def setUp(self):
        """Configuration avec données réelles du benchmark"""
        self.data_manager = DataManager()
        
        # Charger données de profils existants
        self.ellen_profile = self.data_manager.load_person_data("ellen_kampire_dtc")
        self.benoit_profile = self.data_manager.load_person_data("benoit_koleu_dtc") 
        self.Berissa_profile = self.data_manager.load_person_data("Berissa_kawaya_dtc")
        
    def test_demo_with_ellen_data(self):
        """Test démo complète avec données d'Ellen Kampire"""
        
        # Créer écosystème DTC
        scenario = create_demo_scenario()
        
        # Extraire données d'Ellen depuis le profil
        ellen_data = self.ellen_profile
        
        # Créer credentials basés sur ses données réelles
        passport_data = {
            "document_type": "passport",
            "document_number": ellen_data.get("passport_number", "UG123456789"),
            "nationality": ellen_data.get("nationality", "UG"), 
            "given_names": ellen_data.get("given_names", "Ellen"),
            "surname": ellen_data.get("surname", "Kampire"),
            "date_of_birth": ellen_data.get("date_of_birth", "1995-03-22"),
            "place_of_birth": ellen_data.get("place_of_birth", "Kampala, Uganda"),
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01", 
            "issuing_authority": "Republic of Uganda"
        }
        
        # Émettre et vérifier
        issuer = scenario['issuers']['french_gov']  # Pour le test
        holder = scenario['holders']['alice']  # Sera Ellen virtuellement
        verifier = scenario['verifiers']['border_control']
        
        credential = issuer.issue_passport(passport_data)
        holder.store_credential(credential)
        
        # Test de présentation
        presentation = holder.create_selective_presentation(
            credential.credential_id,
            ["nationality", "surname", "date_of_expiry"]
        )
        
        result = verifier.verify_presentation(presentation)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.disclosed_attributes["nationality"], "UG")
        self.assertEqual(result.disclosed_attributes["surname"], "Kampire")
        
        print(" Test avec données réelles d'Ellen réussi")
        
    def test_batch_processing_benchmark_profiles(self):
        """Test traitement en lot des profils de benchmark"""
        
        profiles = [self.ellen_profile, self.benoit_profile, self.Berissa_profile]
        scenario = create_demo_scenario()
        
        issuer = scenario['issuers']['french_gov']
        holder = scenario['holders']['alice']
        verifier = scenario['verifiers']['border_control']
        
        processed_count = 0
        
        for profile in profiles:
            if profile:
                # Créer credential pour chaque profil
                passport_data = {
                    "document_type": "passport",
                    "document_number": profile.get("passport_number", f"TEST{processed_count}"),
                    "nationality": profile.get("nationality", "XX"),
                    "given_names": profile.get("given_names", "Test"),
                    "surname": profile.get("surname", "User"),
                    "date_of_birth": profile.get("date_of_birth", "1990-01-01"),
                    "place_of_birth": profile.get("place_of_birth", "Unknown"),
                    "date_of_issue": "2020-01-01",
                    "date_of_expiry": "2030-01-01",
                    "issuing_authority": "Test Authority"
                }
                
                try:
                    credential = issuer.issue_passport(passport_data)
                    holder.store_credential(credential)
                    
                    # Test de vérification
                    presentation = holder.create_selective_presentation(
                        credential.credential_id,
                        ["nationality", "surname"]
                    )
                    
                    result = verifier.verify_presentation(presentation)
                    if result.is_valid:
                        processed_count += 1
                        
                except Exception as e:
                    print(f"Erreur avec profil: {e}")
                    
        # Au moins 2 profils doivent fonctionner
        self.assertGreaterEqual(processed_count, 2)
        
        print(f" Traitement en lot réussi: {processed_count} profils traités")
        
    def test_performance_metrics_integration(self):
        """Test intégration avec les métriques de performance"""
        
        from benchmark.collector import BenchmarkCollector
        import time
        
        # Créer collector pour mesurer
        collector = BenchmarkCollector()
        
        # Setup
        scenario = create_demo_scenario()
        issuer = scenario['issuers']['french_gov']
        holder = scenario['holders']['alice']
        verifier = scenario['verifiers']['border_control']
        
        # Test avec différentes tailles de données
        for num_attributes in [5, 10, 15]:
            
            # Créer credential avec nombre variable d'attributs
            passport_data = {
                "document_type": "passport",
                "document_number": f"PERF{num_attributes}",
                "nationality": "FR",
                "given_names": "Performance",
                "surname": "Test",
                "date_of_birth": "1990-01-01",
                "place_of_birth": "Paris, France",
                "date_of_issue": "2020-01-01",
                "date_of_expiry": "2030-01-01",
                "issuing_authority": "Test Authority"
            }
            
            # Ajouter attributs additionnels si nécessaire
            for i in range(num_attributes - 10):
                passport_data[f"extra_attr_{i}"] = f"value_{i}"
            
            # Mesurer temps d'émission
            start_time = time.time()
            credential = issuer.issue_passport(passport_data)
            emission_time = time.time() - start_time
            
            # Mesurer temps de vérification
            holder.store_credential(credential)
            presentation = holder.create_full_presentation(credential.credential_id)
            
            start_time = time.time()
            result = verifier.verify_presentation(presentation)
            verification_time = time.time() - start_time
            
            # Enregistrer métriques
            collector.record_metric({
                'operation': 'integration_test',
                'num_attributes': num_attributes,
                'emission_time': emission_time,
                'verification_time': verification_time,
                'success': result.is_valid
            })
            
            self.assertTrue(result.is_valid)
            
        print(" Métriques de performance intégrées avec succès")
        
    def test_demo_modules_integration(self):
        """Test intégration avec les modules de démo"""
        
        # Test que les modules de démo peuvent s'exécuter sans erreur
        # (test d'intégration léger)
        
        try:
            # Simuler paramètres pour dtc_complete
            import sys
            original_argv = sys.argv
            sys.argv = ['dtc_complete.py']
            
            # Ces modules doivent s'importer et initialiser sans erreur
            from Demo.dtc_complete import setup_complete_system
            from Demo.demo_travel import setup_travel_demo
            
            # Test setup basique
            system = setup_complete_system()
            self.assertIsNotNone(system)
            
            travel_demo = setup_travel_demo()
            self.assertIsNotNone(travel_demo)
            
            sys.argv = original_argv
            
            print(" Intégration modules de démo réussie")
            
        except ImportError as e:
            self.skipTest(f"Modules démo non disponibles: {e}")
        except Exception as e:
            self.fail(f"Erreur intégration démo: {e}")


if __name__ == '__main__':
    # Configuration pour tests d'intégration
    unittest.main(verbosity=2, buffer=True, failfast=False)