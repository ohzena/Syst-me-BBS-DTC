"""
Tests unitaires pour BBSCore - BBS Signature Scheme

Ce module teste toutes les fonctionnalités core du système BBS :
- Génération de clés
- Signature et vérification
- Signatures aveugles
- Preuves zero-knowledge
- Utilitaires de sécurité
"""

import unittest
import secrets
import hashlib
from typing import List

# Import des modules BBSCore
from BBSCore.Setup import (
    BBSPrivateKey, BBSPublicKey, BBSKeyPair, BBSSystemSetup, BBSGenerators,
    hash_to_scalar, calculate_domain, point_to_bytes_g1, point_from_bytes_g1,
    CURVE_ORDER, DST_H2S, DST_KEYGEN
)
from BBSCore.KeyGen import BBSKeyGen, generate_bbs_keypair, validate_public_key
from BBSCore.bbsSign import BBSSignature, BBSSignatureScheme
from BBSCore.BlindSign import BlindCommitment, BBSBlindSigner, BlindSignatureProtocol
from BBSCore.ZKProof import BBSProof, BBSProofScheme
from BBSCore.utils import points_equal

class TestKeyGenValidity(unittest.TestCase):
    """Tests pour la génération de clés BBS"""

    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.keygen = BBSKeyGen()
        
    def test_keygen_basic(self):
        """Test génération de clé de base"""
        keypair = self.keygen.keygen()
        
        # Vérifier que les clés sont générées
        self.assertIsInstance(keypair, BBSKeyPair)
        self.assertIsInstance(keypair.secret_key, BBSPrivateKey)
        self.assertIsInstance(keypair.public_key, BBSPublicKey)
        
        # Vérifier que la clé privée est dans la bonne plage
        self.assertGreater(keypair.secret_key.x, 0)
        self.assertLess(keypair.secret_key.x, CURVE_ORDER)
        
    def test_keygen_deterministic(self):
        """Test génération déterministe avec seed"""
        ikm = b"test_seed_32_bytes_deterministic"
        
        keypair1 = self.keygen.keygen(ikm)
        keypair2 = self.keygen.keygen(ikm)
        
        # Même seed = mêmes clés
        self.assertEqual(keypair1.secret_key.x, keypair2.secret_key.x)
        self.assertTrue(points_equal(keypair1.public_key.W, keypair2.public_key.W))
        
    def test_keygen_different_seeds(self):
        """Test que des seeds différents donnent des clés différentes"""
        ikm1 = b"seed_one_32_bytes_for_testing_12"
        ikm2 = b"seed_two_32_bytes_for_testing_34"
        
        keypair1 = self.keygen.keygen(ikm1)
        keypair2 = self.keygen.keygen(ikm2)
        
        # Clés différentes
        self.assertNotEqual(keypair1.secret_key.x, keypair2.secret_key.x)
        self.assertFalse(points_equal(keypair1.public_key.W, keypair2.public_key.W))
        
    def test_sk_to_pk_conversion(self):
        """Test conversion clé privée vers publique"""
        keypair = self.keygen.keygen()
        pk_converted = self.keygen.sk_to_pk(keypair.secret_key)
        
        # La clé publique convertie doit correspondre
        self.assertTrue(points_equal(pk_converted.W, keypair.public_key.W))
        
    def test_generate_bbs_keypair_base58(self):
        """Test génération avec encodage base58"""
        sk_b58, pk_b58 = generate_bbs_keypair("test_seed")
        
        # Vérifier format base58
        self.assertIsInstance(sk_b58, str)
        self.assertIsInstance(pk_b58, str)
        self.assertGreater(len(sk_b58), 40)  # Base58 de 32 bytes
        self.assertGreater(len(pk_b58), 120) # Base58 de 96 bytes
        
    def test_validate_public_key(self):
        """Test validation de clé publique"""
        _, pk_b58 = generate_bbs_keypair()
        
        # Clé valide
        self.assertTrue(validate_public_key(pk_b58))
        
        # Clé invalide
        self.assertFalse(validate_public_key("invalid_key"))
        self.assertFalse(validate_public_key(""))


class TestBBSSignatureValid(unittest.TestCase):
    """Tests pour la signature et vérification BBS valides"""

    def setUp(self):
        """Configuration initiale"""
        self.bbs = BBSSignatureScheme(max_messages=5)
        self.keypair = BBSKeyGen.keygen()
        self.messages = [b"message1", b"message2", b"message3"]
        self.header = b"test_header"
        
    def test_single_message_signature(self):
        """Test signature d'un seul message"""
        message = b"single_message"
        
        signature = self.bbs.sign_single(self.keypair.secret_key, message, self.header)
        
        # Vérifier signature
        self.assertIsInstance(signature, BBSSignature)
        
        # Vérifier validation
        is_valid = self.bbs.verify_single(
            self.keypair.public_key, signature, message, self.header
        )
        self.assertTrue(is_valid)
        
    def test_multiple_messages_signature(self):
        """Test signature de plusieurs messages"""
        signature = self.bbs.sign(self.keypair.secret_key, self.messages, self.header)
        
        # Vérifier signature
        self.assertIsInstance(signature, BBSSignature)
        
        # Vérifier validation
        is_valid = self.bbs.verify(
            self.keypair.public_key, signature, self.messages, self.header
        )
        self.assertTrue(is_valid)
        
    def test_empty_header(self):
        """Test avec header vide"""
        signature = self.bbs.sign(self.keypair.secret_key, self.messages)
        is_valid = self.bbs.verify(self.keypair.public_key, signature, self.messages)
        self.assertTrue(is_valid)
        
    def test_signature_serialization(self):
        """Test sérialisation/désérialisation signature"""
        signature = self.bbs.sign(self.keypair.secret_key, self.messages, self.header)
        
        # Sérialiser
        sig_bytes = signature.to_bytes()
        self.assertEqual(len(sig_bytes), 80)  # 48 + 32 bytes
        
        # Désérialiser
        signature_restored = BBSSignature.from_bytes(sig_bytes)
        
        # Vérifier égalité
        self.assertEqual(signature, signature_restored)
        
        # Vérifier que ça marche encore
        is_valid = self.bbs.verify(
            self.keypair.public_key, signature_restored, self.messages, self.header
        )
        self.assertTrue(is_valid)


class TestBBSSignatureInvalid(unittest.TestCase):
    """Tests pour rejeter les signatures invalides"""

    def setUp(self):
        """Configuration initiale"""
        self.bbs = BBSSignatureScheme(max_messages=5)
        self.keypair = BBSKeyGen.keygen()
        self.messages = [b"message1", b"message2"]
        self.header = b"test_header"
        self.signature = self.bbs.sign(self.keypair.secret_key, self.messages, self.header)
        
    def test_wrong_public_key(self):
        """Test signature avec mauvaise clé publique"""
        wrong_keypair = BBSKeyGen.keygen()
        
        is_valid = self.bbs.verify(
            wrong_keypair.public_key, self.signature, self.messages, self.header
        )
        self.assertFalse(is_valid)
        
    def test_wrong_messages(self):
        """Test signature avec mauvais messages"""
        wrong_messages = [b"wrong1", b"wrong2"]
        
        is_valid = self.bbs.verify(
            self.keypair.public_key, self.signature, wrong_messages, self.header
        )
        self.assertFalse(is_valid)
        
    def test_wrong_header(self):
        """Test signature avec mauvais header"""
        wrong_header = b"wrong_header"
        
        is_valid = self.bbs.verify(
            self.keypair.public_key, self.signature, self.messages, wrong_header
        )
        self.assertFalse(is_valid)
        
    def test_tampered_signature(self):
        """Test signature altérée"""
        # Altérer la signature
        tampered_sig = BBSSignature(
            A=self.signature.A,
            e=(self.signature.e + 1) % CURVE_ORDER
        )
        
        is_valid = self.bbs.verify(
            self.keypair.public_key, tampered_sig, self.messages, self.header
        )
        self.assertFalse(is_valid)
        
    def test_too_many_messages(self):
        """Test avec trop de messages"""
        too_many_messages = [f"msg{i}".encode() for i in range(10)]
        
        with self.assertRaises(ValueError):
            self.bbs.sign(self.keypair.secret_key, too_many_messages, self.header)


class TestBlindSignCycle(unittest.TestCase):
    """Tests pour les signatures aveugles"""

    def setUp(self):
        """Configuration initiale"""
        self.max_messages = 5
        self.setup = BBSSystemSetup(self.max_messages)
        self.keypair = self.setup.create_key_pair()
        self.signer = BBSBlindSigner(self.keypair.secret_key, self.setup.generators)
        
    def test_blind_signature_protocol(self):
        """Test protocole complet de signature aveugle"""
        messages = [b"public1", b"public2"]
        hidden_messages = [b"hidden1", b"hidden2"]
        header = b"blind_header"
        
        # Créer le protocole
        protocol = BlindSignatureProtocol(
            self.keypair.public_key,
            self.setup.generators,
            messages,
            hidden_messages,
            header
        )
        
        # Phase 1: Engagement aveugle
        commitment_result = protocol.create_commitment()
        self.assertIsInstance(commitment_result, BlindCommitment)
        
        # Phase 2: Signature aveugle
        blind_signature = self.signer.blind_sign(
            commitment_result,
            messages,
            header
        )
        
        # Phase 3: Déblindage
        unblinded_sig = protocol.unblind_signature(blind_signature)
        
        # Vérifier que la signature déblindée est valide
        all_messages = messages + hidden_messages
        bbs_scheme = BBSSignatureScheme(self.max_messages, generators=self.setup.generators)
        
        is_valid = bbs_scheme.verify(
            self.keypair.public_key,
            unblinded_sig,
            all_messages,
            header
        )
        self.assertTrue(is_valid)
        
    def test_commitment_properties(self):
        """Test propriétés des engagements"""
        messages = [b"msg1"]
        hidden_messages = [b"hidden1", b"hidden2"]
        
        protocol = BlindSignatureProtocol(
            self.keypair.public_key,
            self.setup.generators,
            messages,
            hidden_messages
        )
        
        commitment = protocol.create_commitment()
        
        # Vérifier structure de l'engagement
        self.assertIsNotNone(commitment.commitment_point)
        self.assertIsNotNone(commitment.proof)
        self.assertEqual(len(commitment.blinding_factors), len(hidden_messages))


class TestZKProofValidity(unittest.TestCase):
    """Tests pour les preuves zero-knowledge"""

    def setUp(self):
        """Configuration initiale"""
        self.max_messages = 5
        self.bbs_scheme = BBSSignatureScheme(self.max_messages)
        self.proof_scheme = BBSProofScheme(self.max_messages)
        self.keypair = BBSKeyGen.keygen()
        
        self.messages = [b"msg1", b"msg2", b"msg3", b"msg4"]
        self.header = b"proof_header"
        self.signature = self.bbs_scheme.sign(
            self.keypair.secret_key, self.messages, self.header
        )
        
    def test_selective_disclosure_proof(self):
        """Test preuve de divulgation sélective"""
        # Révéler seulement les messages 0 et 2
        disclosed_indices = [0, 2]
        disclosed_messages = [self.messages[i] for i in disclosed_indices]
        
        # Générer la preuve
        proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            self.signature,
            self.header,
            self.messages,
            disclosed_indices
        )
        
        self.assertIsInstance(proof, BBSProof)
        
        # Vérifier la preuve
        is_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            proof,
            self.header,
            disclosed_messages,
            disclosed_indices
        )
        self.assertTrue(is_valid)
        
    def test_full_disclosure_proof(self):
        """Test preuve avec tous les messages révélés"""
        disclosed_indices = list(range(len(self.messages)))
        
        proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            self.signature,
            self.header,
            self.messages,
            disclosed_indices
        )
        
        is_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            proof,
            self.header,
            self.messages,
            disclosed_indices
        )
        self.assertTrue(is_valid)
        
    def test_no_disclosure_proof(self):
        """Test preuve sans révélation (tous cachés)"""
        disclosed_indices = []
        disclosed_messages = []
        
        proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            self.signature,
            self.header,
            self.messages,
            disclosed_indices
        )
        
        is_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            proof,
            self.header,
            disclosed_messages,
            disclosed_indices
        )
        self.assertTrue(is_valid)
        
    def test_proof_serialization(self):
        """Test sérialisation des preuves"""
        disclosed_indices = [1, 3]
        disclosed_messages = [self.messages[i] for i in disclosed_indices]
        
        proof = self.proof_scheme.proof_gen(
            self.keypair.public_key,
            self.signature,
            self.header,
            self.messages,
            disclosed_indices
        )
        
        # Sérialiser
        proof_bytes = proof.to_bytes()
        
        # Désérialiser
        proof_restored = BBSProof.from_bytes(proof_bytes)
        
        # Vérifier que ça marche encore
        is_valid = self.proof_scheme.proof_verify(
            self.keypair.public_key,
            proof_restored,
            self.header,
            disclosed_messages,
            disclosed_indices
        )
        self.assertTrue(is_valid)


class TestSecurityUtilsHash(unittest.TestCase):
    """Tests pour les utilitaires de sécurité et hachage"""

    def test_hash_to_scalar_deterministic(self):
        """Test que hash_to_scalar est déterministe"""
        data = b"test_data_for_hashing"
        dst = DST_H2S
        
        hash1 = hash_to_scalar(data, dst)
        hash2 = hash_to_scalar(data, dst)
        
        self.assertEqual(hash1, hash2)
        self.assertGreaterEqual(hash1, 0)
        self.assertLess(hash1, CURVE_ORDER)
        
    def test_hash_to_scalar_different_inputs(self):
        """Test que des entrées différentes donnent des hashes différents"""
        data1 = b"input_one"
        data2 = b"input_two"
        dst = DST_H2S
        
        hash1 = hash_to_scalar(data1, dst)
        hash2 = hash_to_scalar(data2, dst)
        
        self.assertNotEqual(hash1, hash2)
        
    def test_calculate_domain(self):
        """Test calcul du domaine"""
        setup = BBSSystemSetup(3)
        pk_bytes = setup.create_key_pair().public_key.to_bytes()
        Q_1 = setup.Q_1
        H_gens = setup.H_generators[:2]
        header = b"domain_header"
        api_id = b"test_api"
        
        domain1 = calculate_domain(pk_bytes, Q_1, H_gens, header, api_id)
        domain2 = calculate_domain(pk_bytes, Q_1, H_gens, header, api_id)
        
        # Déterministe
        self.assertEqual(domain1, domain2)
        self.assertGreaterEqual(domain1, 0)
        self.assertLess(domain1, CURVE_ORDER)
        
        # Différent avec header différent
        domain3 = calculate_domain(pk_bytes, Q_1, H_gens, b"different", api_id)
        self.assertNotEqual(domain1, domain3)
        
    def test_point_serialization_g1(self):
        """Test sérialisation des points G1"""
        setup = BBSSystemSetup(1)
        point = setup.Q_1
        
        # Sérialiser
        point_bytes = point_to_bytes_g1(point)
        self.assertEqual(len(point_bytes), 48)
        
        # Désérialiser
        point_restored = point_from_bytes_g1(point_bytes)
        
        # Vérifier égalité
        self.assertTrue(points_equal(point, point_restored))
        
    def test_generators_creation(self):
        """Test création de générateurs"""
        count = 5
        api_id = b"test_generators"
        
        generators = BBSGenerators.create_generators(count, api_id)
        
        # Vérifier nombre correct
        self.assertEqual(len(generators), count + 1)  # Q_1 + H_1...H_count
        
        # Vérifier que tous les générateurs sont différents
        for i in range(len(generators)):
            for j in range(i + 1, len(generators)):
                self.assertFalse(points_equal(generators[i], generators[j]))
                
    def test_points_equal_utility(self):
        """Test utilitaire points_equal"""
        setup = BBSSystemSetup(2)
        point1 = setup.Q_1
        point2 = setup.H_generators[0]
        
        # Même point
        self.assertTrue(points_equal(point1, point1))
        
        # Points différents
        self.assertFalse(points_equal(point1, point2))
        
        # Sérialisation/désérialisation
        point1_bytes = point_to_bytes_g1(point1)
        point1_restored = point_from_bytes_g1(point1_bytes)
        self.assertTrue(points_equal(point1, point1_restored))


if __name__ == '__main__':
    # Configuration des tests
    unittest.main(verbosity=2, buffer=True)