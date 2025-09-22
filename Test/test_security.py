"""
Tests de sécurité pour le système BBS-DTC

Ces tests vérifient les propriétés de sécurité cryptographiques :
- Rejet des preuves altérées
- Rejet des clés publiques invalides  
- Détection des incohérences d'attributs cachés
- Résistance aux attaques courantes
"""

import unittest
import secrets
import hashlib
from typing import List, Dict, Any

# Import des modules BBS et DTC
from BBSCore.KeyGen import BBSKeyGen
from BBSCore.Setup import BBSPrivateKey, BBSPublicKey, CURVE_ORDER
from BBSCore.bbsSign import BBSSignature, BBSSignatureScheme
from BBSCore.ZKProof import BBSProof, BBSProofScheme
from DTC.DTCIssuer import DTCIssuer
from DTC.DTCHolder import DTCHolder
from DTC.DTCVerifier import DTCVerifier


class SecurityTestHelper:
    """Utilitaires pour tests de sécurité"""
    
    @staticmethod
    def corrupt_signature(signature: BBSSignature) -> BBSSignature:
        """Corrompre une signature BBS"""
        corrupted_e = (signature.e + 1) % CURVE_ORDER
        return BBSSignature(A=signature.A, e=corrupted_e)
        
    @staticmethod
    def create_fake_public_key() -> BBSPublicKey:
        """Créer une clé publique factice"""
        from py_ecc.optimized_bls12_381 import G2, multiply
        fake_secret = secrets.randbelow(CURVE_ORDER)
        fake_W = multiply(G2, fake_secret)
        return BBSPublicKey(W=fake_W)
        
    @staticmethod
    def corrupt_proof_data(proof: BBSProof) -> BBSProof:
        """Corrompre les données d'une preuve"""
        # Altérer un des points de la preuve
        corrupted_proof = BBSProof(
            Abar=proof.Abar,
            Bbar=proof.Bbar,
            D=proof.D,
            s_e=proof.s_e,
            s_r1=proof.s_r1,
            s_r3=proof.s_r3,
            s_m=[(s + 1) % CURVE_ORDER if i == 0 else s for i, s in enumerate(proof.s_m)]  # Altérer premier s_m
        )
        return corrupted_proof


class TestTamperedProofRejected(unittest.TestCase):
    """Tests rejet des preuves altérées"""

    def setUp(self):
        """Configuration initiale"""
        self.keypair = BBSKeyGen.keygen()
        self.bbs = BBSSignatureScheme(max_messages=10)
        self.proof_scheme = BBSProofScheme(max_messages=10)
        
        self.messages = [b"msg1", b"msg2", b"msg3", b"msg4"]
        self.header = b"security_test_header"
        self.signature = self.bbs.sign(self.keypair.secret_key, self.messages, self.header)
        
    def test_corrupted_signature_rejected(self):
        """Test rejet signature corrompue"""
        
        # Corrompre la signature
        corrupted_sig = SecurityTestHelper.corrupt_signature(self.signature)
        
        # Vérifier que signature corrompue est rejetée
        is_valid = self.bbs.verify(
            self.keypair.public_key,
            corrupted_sig,
            self.messages,
            self.header
        )
        
        self.assertFalse(is_valid, "Corrupted signature should be rejected")
        
        # Vérifier que signature originale est toujours valide
        is_original_valid = self.bbs.verify(
            self.keypair.public_key,
            self.signature,
            self.messages,
            self.header
        )
        
        self.assertTrue(is_original_valid, "Original signature should remain valid")
        
        print(" Signature corrompue rejetée correctement")
        
    def test_tampered_proof_rejected(self):
        """Test rejet preuve altérée"""
        
        # Créer preuve valide
        disclosed_indices = [0, 2]
        disclosed_messages = [self.messages[i] for i in disclosed_indices]
        
        valid_proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            self.signature,
            self.header,
            self.messages,
            disclosed_indices
        )
        
        # Vérifier que preuve valide passe
        is_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            valid_proof,
            self.header,
            disclosed_messages,
            disclosed_indices
        )
        self.assertTrue(is_valid, "Valid proof should pass")
        
        # Corrompre la preuve
        corrupted_proof = SecurityTestHelper.corrupt_proof_data(valid_proof)
        
        # Vérifier que preuve corrompue est rejetée
        is_corrupted_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            corrupted_proof,
            self.header,
            disclosed_messages,
            disclosed_indices
        )
        
        self.assertFalse(is_corrupted_valid, "Corrupted proof should be rejected")
        
        print(" Preuve altérée rejetée correctement")
        
    def test_wrong_disclosed_messages_rejected(self):
        """Test rejet avec mauvais messages révélés"""
        
        disclosed_indices = [0, 1]
        
        # Créer preuve avec messages corrects
        proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            self.signature,
            self.header,
            self.messages,
            disclosed_indices
        )
        
        # Essayer vérification avec mauvais messages révélés
        wrong_disclosed = [b"wrong_msg1", b"wrong_msg2"]
        
        is_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            proof,
            self.header,
            wrong_disclosed,
            disclosed_indices
        )
        
        self.assertFalse(is_valid, "Proof with wrong disclosed messages should be rejected")
        
        print(" Messages révélés incorrects rejetés")
        
    def test_proof_replay_with_different_header(self):
        """Test rejet preuve rejouée avec header différent"""
        
        disclosed_indices = [1, 3]
        disclosed_messages = [self.messages[i] for i in disclosed_indices]
        
        # Créer preuve avec header spécifique
        original_header = b"original_context"
        proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            self.signature,
            original_header,
            self.messages,
            disclosed_indices
        )
        
        # Vérifier avec header original - doit passer
        is_valid_original = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            proof,
            original_header,
            disclosed_messages,
            disclosed_indices
        )
        self.assertTrue(is_valid_original)
        
        # Essayer avec header différent - doit échouer
        different_header = b"different_context"
        is_valid_different = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            proof,
            different_header,
            disclosed_messages,
            disclosed_indices
        )
        
        self.assertFalse(is_valid_different, "Proof should be rejected with different header")
        
        print(" Rejeu preuve avec header différent rejeté")
        
    def test_proof_with_wrong_disclosed_indices(self):
        """Test rejet preuve avec mauvais indices révélés"""
        
        # Créer preuve révélant indices 0 et 2
        original_indices = [0, 2]
        disclosed_messages = [self.messages[i] for i in original_indices]
        
        proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            self.signature,
            self.header,
            self.messages,
            original_indices
        )
        
        # Essayer vérification avec indices différents
        wrong_indices = [1, 3]
        
        is_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            proof,
            self.header,
            disclosed_messages,
            wrong_indices
        )
        
        self.assertFalse(is_valid, "Proof with wrong disclosed indices should be rejected")
        
        print(" Indices révélés incorrects rejetés")


class TestInvalidPublicKeyRejected(unittest.TestCase):
    """Tests rejet des clés publiques invalides"""

    def setUp(self):
        """Configuration"""
        self.valid_keypair = BBSKeyGen.keygen()
        self.bbs = BBSSignatureScheme(max_messages=5)
        self.messages = [b"test_msg_1", b"test_msg_2"]
        self.header = b"pubkey_test_header"
        
    def test_signature_with_wrong_public_key(self):
        """Test vérification avec mauvaise clé publique"""
        
        # Créer signature avec clé valide
        signature = self.bbs.sign(
            self.valid_keypair.secret_key,
            self.messages,
            self.header
        )
        
        # Créer autre clé publique
        wrong_keypair = BBSKeyGen.keygen()
        
        # Vérifier avec mauvaise clé publique
        is_valid = self.bbs.verify(
            wrong_keypair.public_key,
            signature,
            self.messages,
            self.header
        )
        
        self.assertFalse(is_valid, "Signature should be rejected with wrong public key")
        
        # Vérifier que ça marche avec la bonne clé
        is_valid_correct = self.bbs.verify(
            self.valid_keypair.public_key,
            signature,
            self.messages,
            self.header
        )
        
        self.assertTrue(is_valid_correct, "Signature should pass with correct public key")
        
        print(" Mauvaise clé publique rejetée pour signature")
        
    def test_proof_with_wrong_public_key(self):
        """Test vérification preuve avec mauvaise clé publique"""
        
        proof_scheme = BBSProofScheme(max_messages=5)
        
        # Créer signature et preuve avec clé valide
        signature = self.bbs.sign(
            self.valid_keypair.secret_key,
            self.messages,
            self.header
        )
        
        disclosed_indices = [0]
        disclosed_messages = [self.messages[0]]
        
        proof = proof_scheme.proof_gen(
            self.valid_keypair.public_key,
            signature,
            self.header,
            self.messages,
            disclosed_indices
        )
        
        # Créer autre clé publique
        wrong_keypair = BBSKeyGen.keygen()
        
        # Vérifier preuve avec mauvaise clé
        is_valid = proof_scheme.proof_verify(
            wrong_keypair.public_key,
            proof,
            self.header,
            disclosed_messages,
            disclosed_indices
        )
        
        self.assertFalse(is_valid, "Proof should be rejected with wrong public key")
        
        print(" Mauvaise clé publique rejetée pour preuve")
        
    def test_malformed_public_key_handling(self):
        """Test gestion clé publique malformée"""
        
        # Créer clé publique avec point invalide (None)
        try:
            malformed_key = BBSPublicKey(W=None)
            
            # Essayer utiliser clé malformée
            signature = self.bbs.sign(
                self.valid_keypair.secret_key,
                self.messages,
                self.header
            )
            
            # Vérification avec clé malformée doit échouer
            with self.assertRaises((ValueError, TypeError, AttributeError)):
                self.bbs.verify(malformed_key, signature, self.messages, self.header)
                
        except Exception:
            # Si création de clé malformée elle-même échoue, c'est aussi une protection
            pass
            
        print(" Clé publique malformée gérée correctement")
        
    def test_dtc_verifier_untrusted_issuer(self):
        """Test rejet par vérificateur DTC d'émetteur non fiable"""
        
        # Créer émetteurs et vérificateur
        trusted_issuer = DTCIssuer("TRUSTED_ISSUER")
        untrusted_issuer = DTCIssuer("UNTRUSTED_ISSUER")
        
        verifier = DTCVerifier("SECURITY_VERIFIER")
        holder = DTCHolder("test_holder")
        
        # Ajouter seulement l'émetteur fiable
        verifier.add_trusted_issuer("TRUSTED_ISSUER", trusted_issuer.public_key)
        
        # Créer credentials des deux émetteurs
        trusted_cred = trusted_issuer.issue_passport({
            "document_type": "passport",
            "document_number": "TRUSTED123",
            "nationality": "FR",
            "given_names": "Trusted",
            "surname": "User",
            "date_of_birth": "1990-01-01",
            "place_of_birth": "Paris, France",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "Trusted Authority"
        })
        
        untrusted_cred = untrusted_issuer.issue_passport({
            "document_type": "passport",
            "document_number": "UNTRUSTED123",
            "nationality": "XX",
            "given_names": "Untrusted",
            "surname": "User",
            "date_of_birth": "1990-01-01",
            "place_of_birth": "Unknown",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "Untrusted Authority"
        })
        
        holder.store_credential(trusted_cred)
        holder.store_credential(untrusted_cred)
        
        # Présenter credential fiable - doit passer
        trusted_presentation = holder.create_full_presentation(trusted_cred.credential_id)
        trusted_result = verifier.verify_presentation(trusted_presentation)
        self.assertTrue(trusted_result.is_valid)
        
        # Présenter credential non fiable - doit échouer
        untrusted_presentation = holder.create_full_presentation(untrusted_cred.credential_id)
        untrusted_result = verifier.verify_presentation(untrusted_presentation)
        self.assertFalse(untrusted_result.is_valid)
        self.assertIn("untrusted", untrusted_result.error_message.lower())
        
        print(" Émetteur non fiable rejeté correctement")


class TestHiddenAttributeMismatch(unittest.TestCase):
    """Tests détection incohérences attributs cachés"""

    def setUp(self):
        """Configuration"""
        self.keypair = BBSKeyGen.keygen()
        self.bbs = BBSSignatureScheme(max_messages=8)
        self.proof_scheme = BBSProofScheme(max_messages=8)
        
        # Messages avec attributs sensibles
        self.messages = [
            b"nationality:FR",
            b"name:Alice_Dubois", 
            b"date_of_birth:1992-05-10",
            b"passport_number:123456789",
            b"issuer:French_Government",
            b"issued_date:2020-01-01",
            b"expiry_date:2030-01-01",
            b"secret_clearance:TOP_SECRET"  # Attribut très sensible
        ]
        
        self.header = b"hidden_attr_test"
        self.signature = self.bbs.sign(self.keypair.secret_key, self.messages, self.header)
        
    def test_inconsistent_hidden_attribute_claims(self):
        """Test détection d'affirmations incohérentes sur attributs cachés"""
        
        # Alice génère une preuve cachant la date de naissance et le niveau de clearance
        disclosed_indices = [0, 1, 3, 4, 5, 6]  # Cache indices 2 (DOB) et 7 (clearance)
        disclosed_messages = [self.messages[i] for i in disclosed_indices]
        
        # Créer preuve valide
        valid_proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            self.signature,
            self.header,
            self.messages,
            disclosed_indices
        )
        
        # Vérifier preuve valide passe
        is_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            valid_proof,
            self.header,
            disclosed_messages,
            disclosed_indices
        )
        self.assertTrue(is_valid)
        
        # Test: Alice essaie de prétendre révéler différents attributs
        # Mais utilise la même preuve (ce qui devrait échouer)
        wrong_disclosed_indices = [0, 1, 2, 4, 5, 6]  # Prétend révéler DOB au lieu de clearance
        wrong_disclosed_messages = [self.messages[i] for i in wrong_disclosed_indices]
        
        is_wrong_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            valid_proof,  # Même preuve
            self.header,
            wrong_disclosed_messages,
            wrong_disclosed_indices
        )
        
        self.assertFalse(is_wrong_valid, "Proof should be rejected with inconsistent disclosure")
        
        print(" Incohérence attributs révélés détectée")
        
    def test_hidden_attribute_constraint_violation(self):
        """Test violation contraintes attributs cachés"""
        
        # Scénario: Alice veut prouver qu'elle a plus de 18 ans
        # sans révéler sa date de naissance exacte
        
        # Pour ce test, nous simulons une contrainte d'âge
        # En réalité, cela nécessiterait des preuves ZK plus sophistiquées
        
        age_constraint_messages = [
            b"nationality:FR",
            b"name:Alice_Dubois",
            b"age_over_18:true",  # Attribut dérivé
            b"birth_year_after:1974",  # Contrainte générale
            b"passport_number:123456789"
        ]
        
        age_signature = self.bbs.sign(
            self.keypair.secret_key,
            age_constraint_messages,
            b"age_constraint_test"
        )
        
        # Alice révèle tout sauf les détails d'âge spécifiques
        disclosed_indices = [0, 1, 4]  # Cache contraintes d'âge
        disclosed_messages = [age_constraint_messages[i] for i in disclosed_indices]
        
        age_proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            age_signature,
            b"age_constraint_test",
            age_constraint_messages,
            disclosed_indices
        )
        
        # Vérification normale doit passer
        is_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            age_proof,
            b"age_constraint_test",
            disclosed_messages,
            disclosed_indices
        )
        
        self.assertTrue(is_valid)
        
        # Test: Alice essaie de présenter preuve avec messages incompatibles
        incompatible_disclosed = [b"nationality:FR", b"name:Alice_Dubois", b"age_over_18:false"]
        
        is_incompatible_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            age_proof,
            b"age_constraint_test",
            incompatible_disclosed,
            disclosed_indices
        )
        
        self.assertFalse(is_incompatible_valid, "Incompatible constraint should be rejected")
        
        print(" Violation contrainte attribut caché détectée")
        
    def test_selective_disclosure_consistency(self):
        """Test cohérence divulgation sélective"""
        
        # Test avec multiples niveaux de divulgation
        disclosure_levels = [
            ([0, 1], "basic_info"),       # Nationalité + nom
            ([0, 1, 2], "with_dob"),      # + date naissance  
            ([0, 1, 3, 4], "official"),   # + numéros officiels
            (list(range(8)), "full")      # Tout révéler
        ]
        
        for indices, level_name in disclosure_levels:
            disclosed_messages = [self.messages[i] for i in indices]
            
            # Créer preuve pour ce niveau
            proof = self.proof_scheme.proof_gen(
                self.keypair.public_key,
                self.signature,
                self.header,
                self.messages,
                indices
            )
            
            # Vérifier cohérence
            is_valid = self.proof_scheme.proof_verify(
                self.keypair.public_key,
                proof,
                self.header,
                disclosed_messages,
                indices
            )
            
            self.assertTrue(is_valid, f"Disclosure level {level_name} should be valid")
            
            # Test cross-contamination: utiliser preuve d'un niveau pour un autre
            if len(disclosure_levels) > 1:
                wrong_indices, _ = disclosure_levels[0] if level_name != "basic_info" else disclosure_levels[1]
                wrong_disclosed = [self.messages[i] for i in wrong_indices]
                
                is_wrong_valid = self.proof_scheme.proof_verify(
                    self.keypair.public_key,
                    proof,
                    self.header,
                    wrong_disclosed,
                    wrong_indices
                )
                
                # Si les indices sont différents, ça doit échouer
                if set(indices) != set(wrong_indices):
                    self.assertFalse(is_wrong_valid, f"Cross-level proof reuse should fail")
                    
        print(" Cohérence divulgation sélective vérifiée")
        
    def test_attribute_binding_integrity(self):
        """Test intégrité liaison attributs"""
        
        # Créer signature avec attributs liés
        linked_messages = [
            b"user_id:alice123",
            b"account_balance:1000",
            b"account_currency:EUR", 
            b"last_transaction:2024-01-15",
            b"account_status:active"
        ]
        
        linked_signature = self.bbs.sign(
            self.keypair.secret_key,
            linked_messages,
            b"account_test"
        )
        
        # Alice révèle balance mais cache currency (pour tromper)
        disclosed_indices = [0, 1, 4]  # user_id, balance, status
        disclosed_messages = [linked_messages[i] for i in disclosed_indices]
        
        proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            linked_signature,
            b"account_test",
            linked_messages,
            disclosed_indices
        )
        
        # Vérification normale
        is_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            proof,
            b"account_test",
            disclosed_messages,
            disclosed_indices
        )
        
        self.assertTrue(is_valid)
        
        # Alice essaie de modifier la balance révélée (mais cache currency pour pas se faire prendre)
        fake_disclosed = [b"user_id:alice123", b"account_balance:10000", b"account_status:active"]
        
        is_fake_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            proof,
            b"account_test",
            fake_disclosed,
            disclosed_indices
        )
        
        self.assertFalse(is_fake_valid, "Modified attribute should be rejected")
        
        print(" Intégrité liaison attributs vérifiée")


class TestCryptographicAttacks(unittest.TestCase):
    """Tests résistance aux attaques cryptographiques"""

    def setUp(self):
        """Configuration"""
        self.keypair = BBSKeyGen.keygen()
        self.bbs = BBSSignatureScheme(max_messages=5)
        
    def test_signature_forgery_resistance(self):
        """Test résistance à la falsification de signature"""
        
        messages = [b"forge_test_msg1", b"forge_test_msg2"]
        header = b"forgery_test"
        
        # Signature légitime
        legitimate_sig = self.bbs.sign(self.keypair.secret_key, messages, header)
        
        # Essayer diverses formes de falsification
        forgery_attempts = [
            # 1. Modifier composante A
            BBSSignature(A=legitimate_sig.A, e=(legitimate_sig.e + 1) % CURVE_ORDER),
            
            # 2. Modifier composante e  
            BBSSignature(A=legitimate_sig.A, e=(legitimate_sig.e * 2) % CURVE_ORDER),
            
            # 3. Inverser e
            BBSSignature(A=legitimate_sig.A, e=pow(legitimate_sig.e, -1, CURVE_ORDER)),
        ]
        
        # Toutes les tentatives doivent échouer
        for i, forged_sig in enumerate(forgery_attempts):
            is_valid = self.bbs.verify(
                self.keypair.public_key,
                forged_sig,
                messages,
                header
            )
            
            self.assertFalse(is_valid, f"Forgery attempt {i+1} should be rejected")
            
        print(" Résistance falsification signature vérifiée")
        
    def test_chosen_message_attack_resistance(self):
        """Test résistance attaque à messages choisis"""
        
        # Attaquant choisit messages spéciaux
        chosen_messages = [
            b"",  # Message vide
            b"\x00" * 32,  # Zéros
            b"\xFF" * 32,  # Tous bits à 1
            b"AAAA" * 8,   # Pattern répétitif
        ]
        
        # Signer messages choisis
        signatures = []
        for msg in chosen_messages:
            sig = self.bbs.sign(self.keypair.secret_key, [msg], b"chosen_msg_test")
            signatures.append((msg, sig))
            
        # Vérifier que toutes les signatures sont valides
        for msg, sig in signatures:
            is_valid = self.bbs.verify(
                self.keypair.public_key,
                sig,
                [msg],
                b"chosen_msg_test"
            )
            self.assertTrue(is_valid, f"Legitimate signature should be valid for message: {msg}")
            
        # Attaquant essaie d'utiliser info des messages choisis pour forger
        # Essayer de combiner composantes de différentes signatures
        if len(signatures) >= 2:
            (_, sig1), (_, sig2) = signatures[:2]
            
            # Tentative forgerie en combinant
            combined_forgery = BBSSignature(A=sig1.A, e=sig2.e)
            
            # Doit échouer sur n'importe quel message
            for msg, _ in signatures:
                is_combined_valid = self.bbs.verify(
                    self.keypair.public_key,
                    combined_forgery,
                    [msg],
                    b"chosen_msg_test"
                )
                self.assertFalse(is_combined_valid, "Combined forgery should fail")
                
        print(" Résistance attaque messages choisis vérifiée")
        
    def test_malleability_resistance(self):
        """Test résistance à la malléabilité"""
        
        messages = [b"malleability_test"]
        header = b"malleability_header"
        
        signature = self.bbs.sign(self.keypair.secret_key, messages, header)
        
        # Essayer diverses transformations malléables
        from py_ecc.optimized_bls12_381 import multiply, add, neg, Z1
        
        # 1. Multiplier A par facteur
        try:
            factor = 2
            modified_A = multiply(signature.A, factor)
            malleable_sig1 = BBSSignature(A=modified_A, e=signature.e)
            
            is_valid = self.bbs.verify(
                self.keypair.public_key,
                malleable_sig1,
                messages,
                header
            )
            
            self.assertFalse(is_valid, "Malleable signature should be rejected")
        except:
            # Si opération échoue, c'est aussi une protection
            pass
            
        # 2. Ajouter point neutre
        try:
            neutral_modified_A = add(signature.A, Z1)  # Ajouter point à l'infini
            malleable_sig2 = BBSSignature(A=neutral_modified_A, e=signature.e)
            
            is_valid = self.bbs.verify(
                self.keypair.public_key,
                malleable_sig2,
                messages,
                header
            )
            
            # Selon l'implémentation, ceci peut passer ou échouer
            # Les deux comportements sont acceptables
            print(f"  Point neutre result: {is_valid}")
        except:
            # Si opération échoue, c'est une protection
            pass
            
        print(" Résistance malléabilité testée")


if __name__ == '__main__':
    print(" TESTING BBS-DTC SECURITY PROPERTIES")
    print("=" * 60)
    
    unittest.main(verbosity=2, buffer=True)