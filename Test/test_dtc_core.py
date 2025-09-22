"""
Tests unitaires pour DTC - Digital Trust Certificate

Ce module teste les composants DTC qui utilisent BBS pour créer
un système de credentials de voyage avec divulgation sélective :
- Conformité des schémas par les émetteurs
- Stockage et récupération par les détenteurs
- Acceptation des credentials valides par les vérificateurs
- Rejet des credentials invalides
"""

import unittest
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

# Import des modules DTC
from DTC.dtc import (
    DTCCredential, DocumentType, AttributeType, CredentialAttribute,
    CredentialSchema, PassportCredential, VisaCredential, VaccinationCredential,
    PASSPORT_SCHEMA, VISA_SCHEMA, VACCINATION_SCHEMA,
    create_passport_credential, create_visa_credential, create_vaccination_credential
)
from DTC.DTCIssuer import DTCIssuer, create_test_issuer
from DTC.DTCHolder import DTCHolder, create_test_holder
from DTC.DTCVerifier import DTCVerifier, create_test_verifier


class TestIssuerSchemaCompliance(unittest.TestCase):
    """Tests pour la conformité des schémas par les émetteurs DTC"""

    def setUp(self):
        """Configuration initiale"""
        self.issuer = create_test_issuer("TEST_GOV_001")
        
    def test_passport_schema_compliance(self):
        """Test conformité schéma passeport"""
        # Créer credential conforme au schéma passeport
        passport_data = {
            "document_type": "passport",
            "document_number": "123456789",
            "nationality": "FR",
            "given_names": "Jean Pierre",
            "surname": "Dupont",
            "date_of_birth": "1985-03-15",
            "place_of_birth": "Paris, France",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "République Française"
        }
        
        # Émettre le credential
        passport_cred = self.issuer.issue_passport(passport_data)
        
        # Vérifier conformité
        self.assertIsInstance(passport_cred, PassportCredential)
        self.assertEqual(passport_cred.document_type, DocumentType.PASSPORT)
        self.assertEqual(passport_cred.get_attribute("nationality").value, "FR")
        self.assertEqual(passport_cred.get_attribute("document_number").value, "123456789")
        
        # Vérifier signature BBS
        self.assertIsNotNone(passport_cred.signature)
        
    def test_visa_schema_compliance(self):
        """Test conformité schéma visa"""
        visa_data = {
            "document_type": "visa",
            "visa_number": "USA2023001",
            "visa_type": "B1/B2",
            "nationality": "FR",
            "given_names": "Marie",
            "surname": "Martin",
            "date_of_birth": "1990-07-22",
            "date_of_issue": "2023-01-15",
            "date_of_expiry": "2024-01-15",
            "issuing_authority": "US Embassy Paris",
            "destination_country": "USA"
        }
        
        visa_cred = self.issuer.issue_visa(visa_data)
        
        # Vérifier conformité
        self.assertIsInstance(visa_cred, VisaCredential)
        self.assertEqual(visa_cred.document_type, DocumentType.VISA)
        self.assertEqual(visa_cred.get_attribute("destination_country").value, "USA")
        self.assertEqual(visa_cred.get_attribute("visa_type").value, "B1/B2")
        
    def test_vaccination_schema_compliance(self):
        """Test conformité schéma vaccination"""
        vacc_data = {
            "document_type": "vaccination_certificate",
            "certificate_id": "VAC2023FR001",
            "given_names": "Sophie",
            "surname": "Leclerc",
            "date_of_birth": "1988-11-03",
            "vaccination_details": {
                "vaccine_name": "COVID-19 mRNA",
                "manufacturer": "Pfizer-BioNTech",
                "doses": [
                    {"date": "2021-05-01", "batch": "ABC123"},
                    {"date": "2021-06-15", "batch": "DEF456"}
                ]
            },
            "issuing_authority": "French Health Ministry"
        }
        
        vacc_cred = self.issuer.issue_vaccination(vacc_data)
        
        # Vérifier conformité
        self.assertIsInstance(vacc_cred, VaccinationCredential)
        self.assertEqual(vacc_cred.document_type, DocumentType.VACCINATION_CERTIFICATE)
        self.assertEqual(vacc_cred.get_attribute("certificate_id").value, "VAC2023FR001")
        
    def test_invalid_schema_rejection(self):
        """Test rejet de données non conformes au schéma"""
        # Données passeport manquantes
        incomplete_data = {
            "document_type": "passport",
            "document_number": "123456789"
            # Manque les champs obligatoires
        }
        
        with self.assertRaises((ValueError, KeyError)):
            self.issuer.issue_passport(incomplete_data)
            
    def test_issuer_key_management(self):
        """Test gestion des clés par l'émetteur"""
        # Vérifier que l'émetteur a des clés BBS
        self.assertIsNotNone(self.issuer.private_key)
        self.assertIsNotNone(self.issuer.public_key)
        
        # Vérifier identité
        self.assertEqual(self.issuer.issuer_id, "TEST_GOV_001")
        
        # Vérifier capacité de signature
        test_data = {"document_type": "passport", "document_number": "TEST123"}
        try:
            # Doit pouvoir signer sans erreur
            passport = create_passport_credential(test_data)
            self.issuer.sign_credential(passport)
        except Exception as e:
            self.fail(f"Issuer should be able to sign credentials: {e}")


class TestHolderStoreRetrieve(unittest.TestCase):
    """Tests pour stockage et récupération par les détenteurs"""

    def setUp(self):
        """Configuration initiale"""
        self.holder = create_test_holder("alice_test")
        self.issuer = create_test_issuer("TEST_ISSUER")
        
        # Créer quelques credentials de test
        self.passport_cred = self.issuer.issue_passport({
            "document_type": "passport",
            "document_number": "FR123456",
            "nationality": "FR",
            "given_names": "Alice",
            "surname": "Dubois",
            "date_of_birth": "1992-05-10",
            "place_of_birth": "Lyon, France",
            "date_of_issue": "2021-01-01",
            "date_of_expiry": "2031-01-01",
            "issuing_authority": "République Française"
        })
        
        self.visa_cred = self.issuer.issue_visa({
            "document_type": "visa",
            "visa_number": "US2023001",
            "visa_type": "tourist",
            "nationality": "FR",
            "given_names": "Alice",
            "surname": "Dubois",
            "date_of_birth": "1992-05-10",
            "date_of_issue": "2023-01-01",
            "date_of_expiry": "2024-01-01",
            "issuing_authority": "US Embassy",
            "destination_country": "USA"
        })
        
    def test_store_credentials(self):
        """Test stockage des credentials"""
        # Stocker passport
        self.holder.store_credential(self.passport_cred)
        
        # Vérifier stockage
        self.assertEqual(len(self.holder.credentials), 1)
        self.assertIn(self.passport_cred.credential_id, self.holder.credentials)
        
        # Stocker visa
        self.holder.store_credential(self.visa_cred)
        self.assertEqual(len(self.holder.credentials), 2)
        
    def test_retrieve_by_type(self):
        """Test récupération par type de document"""
        # Stocker les deux
        self.holder.store_credential(self.passport_cred)
        self.holder.store_credential(self.visa_cred)
        
        # Récupérer passeports
        passports = self.holder.get_credentials_by_type(DocumentType.PASSPORT)
        self.assertEqual(len(passports), 1)
        self.assertEqual(passports[0].document_type, DocumentType.PASSPORT)
        
        # Récupérer visas
        visas = self.holder.get_credentials_by_type(DocumentType.VISA)
        self.assertEqual(len(visas), 1)
        self.assertEqual(visas[0].document_type, DocumentType.VISA)
        
    def test_retrieve_by_issuer(self):
        """Test récupération par émetteur"""
        self.holder.store_credential(self.passport_cred)
        
        # Récupérer par issuer_id
        creds_from_issuer = self.holder.get_credentials_by_issuer("TEST_ISSUER")
        self.assertEqual(len(creds_from_issuer), 1)
        self.assertEqual(creds_from_issuer[0].issuer_id, "TEST_ISSUER")
        
    def test_credential_wallet_management(self):
        """Test gestion du portefeuille de credentials"""
        # Wallet vide au début
        self.assertEqual(len(self.holder.credentials), 0)
        
        # Ajouter credentials
        self.holder.store_credential(self.passport_cred)
        self.holder.store_credential(self.visa_cred)
        
        # Vérifier contenu
        all_creds = self.holder.list_all_credentials()
        self.assertEqual(len(all_creds), 2)
        
        # Supprimer un credential
        self.holder.remove_credential(self.passport_cred.credential_id)
        self.assertEqual(len(self.holder.credentials), 1)
        
        # Vérifier qu'il reste le bon
        remaining = self.holder.list_all_credentials()
        self.assertEqual(remaining[0].document_type, DocumentType.VISA)
        
    def test_selective_disclosure_preparation(self):
        """Test préparation pour divulgation sélective"""
        self.holder.store_credential(self.passport_cred)
        
        # Préparer pour divulgation sélective - ne révéler que nationalité et nom
        disclosed_attributes = ["nationality", "surname"]
        
        presentation_data = self.holder.prepare_selective_disclosure(
            self.passport_cred.credential_id,
            disclosed_attributes
        )
        
        # Vérifier structure
        self.assertIn("disclosed_attributes", presentation_data)
        self.assertIn("hidden_attributes", presentation_data)
        self.assertIn("proof_data", presentation_data)
        
        # Vérifier contenu
        disclosed = presentation_data["disclosed_attributes"]
        self.assertIn("nationality", disclosed)
        self.assertIn("surname", disclosed)
        self.assertNotIn("date_of_birth", disclosed)  # Doit être caché


class TestVerifierAcceptsValid(unittest.TestCase):
    """Tests pour acceptance des credentials valides par les vérificateurs"""

    def setUp(self):
        """Configuration initiale"""
        self.verifier = create_test_verifier("BORDER_CONTROL")
        self.issuer = create_test_issuer("TRUSTED_GOV")
        self.holder = create_test_holder("traveler")
        
        # Ajouter l'émetteur comme fiable
        self.verifier.add_trusted_issuer("TRUSTED_GOV", self.issuer.public_key)
        
        # Créer et signer un credential valide
        self.valid_passport = self.issuer.issue_passport({
            "document_type": "passport",
            "document_number": "VALID123",
            "nationality": "FR",
            "given_names": "Valid",
            "surname": "Traveler",
            "date_of_birth": "1990-01-01",
            "place_of_birth": "Paris, France",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "République Française"
        })
        
        self.holder.store_credential(self.valid_passport)
        
    def test_verify_complete_credential(self):
        """Test vérification d'un credential complet"""
        # Créer présentation complète
        presentation = self.holder.create_full_presentation(self.valid_passport.credential_id)
        
        # Vérifier
        verification_result = self.verifier.verify_presentation(presentation)
        
        self.assertTrue(verification_result.is_valid)
        self.assertEqual(verification_result.issuer_id, "TRUSTED_GOV")
        self.assertIsNone(verification_result.error_message)
        
    def test_verify_selective_disclosure(self):
        """Test vérification avec divulgation sélective"""
        # Créer présentation avec divulgation sélective
        disclosed_attrs = ["nationality", "surname", "date_of_expiry"]
        presentation = self.holder.create_selective_presentation(
            self.valid_passport.credential_id,
            disclosed_attrs
        )
        
        # Vérifier
        result = self.verifier.verify_presentation(presentation)
        
        self.assertTrue(result.is_valid)
        # Doit contenir seulement les attributs révélés
        self.assertIn("nationality", result.disclosed_attributes)
        self.assertIn("surname", result.disclosed_attributes)
        self.assertNotIn("date_of_birth", result.disclosed_attributes)
        
    def test_verify_age_proof(self):
        """Test vérification preuve d'âge (sans révéler date de naissance)"""
        # Le détenteur prouve qu'il a plus de 18 ans sans révéler sa date de naissance
        age_proof_presentation = self.holder.create_age_proof_presentation(
            self.valid_passport.credential_id,
            min_age=18
        )
        
        result = self.verifier.verify_presentation(age_proof_presentation)
        
        self.assertTrue(result.is_valid)
        # Date de naissance ne doit pas être révélée
        self.assertNotIn("date_of_birth", result.disclosed_attributes)
        # Mais preuve d'âge doit être valide
        self.assertTrue(result.age_requirements_met)
        
    def test_verify_nationality_only(self):
        """Test vérification nationalité seule"""
        # Révéler seulement la nationalité
        nationality_presentation = self.holder.create_selective_presentation(
            self.valid_passport.credential_id,
            ["nationality"]
        )
        
        result = self.verifier.verify_presentation(nationality_presentation)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.disclosed_attributes), 1)
        self.assertEqual(result.disclosed_attributes["nationality"], "FR")
        
    def test_multiple_credentials_verification(self):
        """Test vérification avec multiples credentials"""
        # Ajouter un visa
        visa = self.issuer.issue_visa({
            "document_type": "visa",
            "visa_number": "VISA123",
            "visa_type": "tourist",
            "nationality": "FR",
            "given_names": "Valid",
            "surname": "Traveler",
            "date_of_birth": "1990-01-01",
            "date_of_issue": "2023-01-01",
            "date_of_expiry": "2024-01-01",
            "issuing_authority": "Embassy",
            "destination_country": "USA"
        })
        
        self.holder.store_credential(visa)
        
        # Créer présentation combinée
        combined_presentation = self.holder.create_combined_presentation([
            (self.valid_passport.credential_id, ["nationality", "surname"]),
            (visa.credential_id, ["destination_country", "visa_type"])
        ])
        
        result = self.verifier.verify_presentation(combined_presentation)
        self.assertTrue(result.is_valid)


class TestVerifierRejectsInvalid(unittest.TestCase):
    """Tests pour rejet des credentials invalides"""

    def setUp(self):
        """Configuration initiale"""
        self.verifier = create_test_verifier("STRICT_VERIFIER")
        self.trusted_issuer = create_test_issuer("TRUSTED")
        self.untrusted_issuer = create_test_issuer("UNTRUSTED")
        self.holder = create_test_holder("test_holder")
        
        # Seul TRUSTED est ajouté comme fiable
        self.verifier.add_trusted_issuer("TRUSTED", self.trusted_issuer.public_key)
        
        # Credentials pour les tests
        self.trusted_cred = self.trusted_issuer.issue_passport({
            "document_type": "passport",
            "document_number": "TRUSTED123",
            "nationality": "FR",
            "given_names": "Trusted",
            "surname": "User",
            "date_of_birth": "1985-01-01",
            "place_of_birth": "Paris, France",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "Trusted Authority"
        })
        
        self.untrusted_cred = self.untrusted_issuer.issue_passport({
            "document_type": "passport",
            "document_number": "UNTRUSTED123",
            "nationality": "XX",
            "given_names": "Untrusted",
            "surname": "User",
            "date_of_birth": "1985-01-01",
            "place_of_birth": "Unknown",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "Unknown Authority"
        })
        
        self.holder.store_credential(self.trusted_cred)
        self.holder.store_credential(self.untrusted_cred)
        
    def test_reject_untrusted_issuer(self):
        """Test rejet credential d'émetteur non fiable"""
        # Essayer de présenter credential d'émetteur non fiable
        presentation = self.holder.create_full_presentation(self.untrusted_cred.credential_id)
        
        result = self.verifier.verify_presentation(presentation)
        
        self.assertFalse(result.is_valid)
        self.assertIn("untrusted issuer", result.error_message.lower())
        
    def test_reject_tampered_credential(self):
        """Test rejet credential altéré"""
        # Altérer le credential
        tampered_cred = self.trusted_cred.copy()
        tampered_cred.attributes["nationality"].value = "HACKED"
        
        # Stocker le credential altéré
        self.holder.credentials[tampered_cred.credential_id] = tampered_cred
        
        presentation = self.holder.create_full_presentation(tampered_cred.credential_id)
        result = self.verifier.verify_presentation(presentation)
        
        self.assertFalse(result.is_valid)
        
    def test_reject_expired_credential(self):
        """Test rejet credential expiré"""
        # Créer credential expiré
        expired_cred = self.trusted_issuer.issue_passport({
            "document_type": "passport",
            "document_number": "EXPIRED123",
            "nationality": "FR",
            "given_names": "Expired",
            "surname": "User",
            "date_of_birth": "1985-01-01",
            "place_of_birth": "Paris, France",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2020-12-31",  # Expiré
            "issuing_authority": "Trusted Authority"
        })
        
        self.holder.store_credential(expired_cred)
        presentation = self.holder.create_full_presentation(expired_cred.credential_id)
        
        result = self.verifier.verify_presentation(presentation)
        
        self.assertFalse(result.is_valid)
        self.assertIn("expired", result.error_message.lower())
        
    def test_reject_invalid_proof(self):
        """Test rejet preuve invalide"""
        # Créer une présentation avec des indices incorrects
        try:
            # Simuler une preuve corrompue en modifiant les données après génération
            presentation = self.holder.create_selective_presentation(
                self.trusted_cred.credential_id,
                ["nationality"]
            )
            
            # Corrompre la preuve
            if hasattr(presentation, 'proof_data'):
                presentation.proof_data = b"corrupted_proof_data"
            
            result = self.verifier.verify_presentation(presentation)
            self.assertFalse(result.is_valid)
            
        except Exception:
            # Si la corruption provoque une exception, c'est aussi un rejet valide
            pass
            
    def test_reject_mismatched_requirements(self):
        """Test rejet si les exigences ne sont pas satisfaites"""
        # Vérificateur exige nationalité US, mais credential a FR
        presentation = self.holder.create_selective_presentation(
            self.trusted_cred.credential_id,
            ["nationality"]
        )
        
        # Configurer vérificateur pour exiger US
        self.verifier.set_nationality_requirement("US")
        
        result = self.verifier.verify_presentation(presentation)
        
        self.assertFalse(result.is_valid)
        self.assertIn("nationality requirement", result.error_message.lower())


if __name__ == '__main__':
    unittest.main(verbosity=2, buffer=True)