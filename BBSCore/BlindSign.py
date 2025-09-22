# BlindSign.py

"""
BlindSign.py - BBS Blind Signature Protocols
Allows signing of hidden messages without revealing them to the signer
"""

import secrets
import hashlib
from typing import List, Tuple, Optional
from dataclasses import dataclass
import base58

# Import py_ecc pour BLS12-381 optimisé
from py_ecc.optimized_bls12_381 import (
    G1, G2,
    multiply,
    add,
    neg,
    pairing,
    final_exponentiate,
    FQ12,
    curve_order,
    Z1, Z2,
)

from py_ecc.bls.g2_primitives import G1_to_pubkey
from py_ecc.optimized_bls12_381.optimized_pairing import normalize1
# Import des classes refactorisées
from BBSCore.Setup import (
    BBSPrivateKey, BBSPublicKey, BBSGenerators, G1Point,
    CURVE_ORDER, hash_to_scalar, calculate_domain,
    point_to_bytes_g1, point_from_bytes_g1
)
from BBSCore.bbsSign import BBSSignature, BBSSignatureScheme
from BBSCore.KeyGen import BBSKeyGen

def affine_to_bytes(p: tuple) -> bytes:
    """
    Sérialise un point G1 de py_ecc en 48 octets.
    """
    if not isinstance(p, tuple):
        raise TypeError(f"Un tuple de point est attendu, mais a reçu {type(p)}")
    return G1_to_pubkey(normalize1(p))

@dataclass
class BlindCommitment:
    """
    Commitment produit par l'utilisateur (à envoyer au signataire)
    """
    C: G1Point
    blinding: int
    hidden_count: int

    def to_bytes(self) -> bytes:
        return affine_to_bytes(self.C) + self.blinding.to_bytes(32, 'big')

@dataclass
class CommitmentProof:
    """
    Preuve de connaissance Schnorr de l'ouverture du commitment
    """
    challenge: int
    responses: List[int]
    R: G1Point

    def to_bytes(self) -> bytes:
        out = self.challenge.to_bytes(32, 'big')
        out += len(self.responses).to_bytes(4, 'big')
        for s in self.responses:
            out += s.to_bytes(32, 'big')
        out += affine_to_bytes(self.R)
        return out

    def verify(self, commitment: BlindCommitment, H_gens: List[G1Point], api_id: bytes) -> bool:
        """
        Vérifie la preuve Schnorr multi-scalaire avec py_ecc
        """
        if len(H_gens) < len(self.responses):
            return False
        
        lhs_terms = []
        for i, si in enumerate(self.responses):
            if i < len(H_gens):
                lhs_terms.append(multiply(H_gens[i], si % CURVE_ORDER))

        lhs = lhs_terms[0]
        for term in lhs_terms[1:]:
            lhs = add(lhs, term)

        if lhs is None:
            return False
        
        rhs = multiply(commitment.C, self.challenge % CURVE_ORDER)
        
        neg_rhs = neg(rhs) if rhs is not None else None
        R_prime = add(lhs, neg_rhs) if neg_rhs is not None else lhs
        
        data = affine_to_bytes(commitment.C) + affine_to_bytes(R_prime) + api_id
        c_check = hash_to_scalar(data, api_id + b"H2S_")
        
        return c_check == self.challenge

class BBSBlindSigner:
    """
    Côté signataire : vérifie PoK et émet une signature sur le hash du commitment
    """
    def __init__(self, bbs_scheme: BBSSignatureScheme, api_id: bytes = b""):
        self.bbs = bbs_scheme
        self.api_id = api_id
        self.generators = self.bbs.generators
        self.P1 = self.bbs.P1
        self.P2 = self.bbs.P2

    def blind_sign(self, sk: BBSPrivateKey, commitment: BlindCommitment, known_messages: List[bytes], proof: CommitmentProof, header: bytes = b"") -> BBSSignature:
        """
        Le signataire vérifie la preuve et signe le hash du commitment comme un message.
        """
        # 1. Le nombre total de messages qui seront signés est 1 (pour le commit) + le nombre de messages connus.
        total_messages = 1 + len(known_messages)
        # On a besoin des générateurs correspondants H_1, ..., H_{total_messages}
        # Dans la notation BBS, ce sont les générateurs d'index 1 à total_messages.
        # Le premier message (le commitment) utilisera H_1, le premier message connu utilisera H_2, etc.
        # L'index 0 des générateurs est Q_1.
        H_gens_for_pok = self.generators[1:2 + commitment.hidden_count] # H_1 (pour blinding) et H_2.. (pour messages)
        
        # Le premier message utilise H_1 pour le blinding, les suivants H_2, etc. pour les messages cachés.
        # Donc pour la PoK, on a besoin de `1 + hidden_count` générateurs à partir de H_1.
        pok_gens = self.generators[1 : 1 + 1 + commitment.hidden_count]

        if not proof.verify(commitment, pok_gens, self.api_id):
             raise ValueError("Échec vérification preuve commitment")

        # 2. Le "premier message" signé est le hash du point de commitment C.
        # Les messages suivants sont les messages connus.
        commitment_hash_message = hashlib.sha256(affine_to_bytes(commitment.C)).digest()

        all_messages_to_sign = [commitment_hash_message] + known_messages
        
        # 3. On utilise la fonction de signature standard avec cette nouvelle liste de messages.
        return self.bbs.core_sign(sk, header, all_messages_to_sign)

class BlindSignerClient:
    """
    Côté client : crée commitment et preuve de connaissance de l'ouverture
    """
    def __init__(self, bbs_scheme: BBSSignatureScheme, api_id: bytes = b""):
        self.bbs = bbs_scheme
        self.api_id = api_id
        self.generators = self.bbs.generators

    def create_commitment(self, hidden_messages: List[bytes], blinding: Optional[int] = None) -> Tuple[BlindCommitment, CommitmentProof]:
        """
        Commitment: C = r*H1 + sum_j m_j*H_{j+2}
        """
        H_gens = self.generators[1:] # H1, H2, ...
        U = len(hidden_messages)
        # On a besoin de H1 (blinding) + U générateurs pour les messages
        if len(H_gens) < (1 + U):
            raise ValueError(f"Pas assez de générateurs H. Besoin {1+U}, dispo {len(H_gens)}")

        r = blinding if blinding is not None else secrets.randbelow(CURVE_ORDER)
        
        # H_gens[0] est H_1, H_gens[1] est H_2 etc.
        # C = r * H_1 + m1*H_2 + m2*H_3 ...
        C = multiply(H_gens[0], r)
        msg_scalars = [hash_to_scalar(m, self.api_id + b"H2S_") for m in hidden_messages]
        
        pok_gens = [H_gens[0]] # H_1 pour le blinding
        for i, s in enumerate(msg_scalars):
            # Le message i utilise le générateur H_{i+2} (index i+1 dans H_gens)
            H_i_plus_1 = H_gens[i + 1]
            pok_gens.append(H_i_plus_1)
            C = add(C, multiply(H_i_plus_1, s))
        
        commit = BlindCommitment(C=C, blinding=r, hidden_count=U)

        # Créer preuve Schnorr
        randomness = [secrets.randbelow(CURVE_ORDER) for _ in range(1 + U)] # pour r et chaque message
        
        R_terms = []
        for i, t in enumerate(randomness):
            R_terms.append(multiply(pok_gens[i], t))
        
        R = R_terms[0]
        for term in R_terms[1:]:
            R = add(R, term)

        data = affine_to_bytes(C) + affine_to_bytes(R) + self.api_id
        c = hash_to_scalar(data, self.api_id + b"H2S_")

        # s_i = t_i + c * secret_i
        secrets_list = [r] + msg_scalars
        responses = [(t + c * s) % CURVE_ORDER for t, s in zip(randomness, secrets_list)]

        proof = CommitmentProof(challenge=c, responses=responses, R=R)
        return commit, proof

    def unblind_signature(self, signature: BBSSignature) -> BBSSignature:
        return signature

class BlindSignatureProtocol:
    """
    API haut niveau pour exécuter l'émission aveugle
    """
    def __init__(self, api_id: bytes = b""):
        self.api_id = api_id
        # Injecter l'api_id dans le BBSSignatureScheme interne.
        self.bbs = BBSSignatureScheme(api_id=self.api_id)
        self.client = BlindSignerClient(self.bbs, api_id=self.api_id)
        self.signer = BBSBlindSigner(self.bbs, api_id=self.api_id)

    def execute_blind_signing(self, sk: BBSPrivateKey, hidden_messages: List[bytes], known_messages: List[bytes], blinding: Optional[int] = None) -> Tuple[BBSSignature, BlindCommitment]:
        commit, proof = self.client.create_commitment(hidden_messages, blinding=blinding)
        
        # Le signataire ne voit que le commit et les messages connus.
        # Il ne connaît pas `hidden_messages`.
        sig = self.signer.blind_sign(sk, commit, known_messages, proof, header=b"")

        final_sig = self.client.unblind_signature(sig)
        return final_sig, commit

    def verify_blind_signature(self, pk: BBSPublicKey, signature: BBSSignature, commit: BlindCommitment, known_messages: List[bytes], header: bytes = b"") -> bool:
        # Le vérificateur reconstruit la liste de messages qui a été signée.
        # Le premier message est le hash du point de commitment.
        commitment_hash_message = hashlib.sha256(affine_to_bytes(commit.C)).digest()
        
        msgs_that_were_signed = [commitment_hash_message] + known_messages
        
        return self.bbs.core_verify(pk, signature, header, msgs_that_were_signed)