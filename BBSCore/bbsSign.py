"""
bbsSign.py - BBS Signature Scheme Implementation
Following IETF BBS Signatures specification
"""

import secrets
import hashlib
from typing import List, Tuple, Optional
from dataclasses import dataclass

from py_ecc.optimized_bls12_381 import (
    G1, G2, multiply, add, neg, pairing, final_exponentiate, 
    FQ12, curve_order, normalize
)

from py_ecc.bls.g2_primitives import G1_to_pubkey, pubkey_to_G1
from py_ecc.optimized_bls12_381.optimized_pairing import normalize1

from BBSCore.Setup import (
    BBSPrivateKey, BBSPublicKey, BBSGenerators,
    CURVE_ORDER, hash_to_scalar, calculate_domain,
    point_to_bytes_g1, point_from_bytes_g1
)
from BBSCore.KeyGen import BBSKeyGen
from BBSCore.utils import points_equal

SIGNATURE_SIZE = 80  # A (48) + e (32) - per Core.tex specification
DST_H2S = b"BBS_BLS12381G1_XMD:SHA-256_SSWU_RO_H2S_DST_"

@dataclass
class BBSSignature:
    """BBS Signature following Core.tex: (A, e)"""
    A: tuple  # G1 point
    e: int    # Scalar
    
    def to_bytes(self) -> bytes:
        """Serialize to 80 bytes per Core.tex"""
        A_bytes = G1_to_pubkey(normalize1(self.A))
        e_bytes = self.e.to_bytes(32, 'big')
        return A_bytes + e_bytes
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'BBSSignature':
        """Deserialize from bytes"""
        if len(data) != 80:
            raise ValueError(f"Invalid signature size: {len(data)}")
        A = pubkey_to_G1(data[:48])
        e = int.from_bytes(data[48:80], 'big')
        return cls(A=A, e=e)
    
    def __eq__(self, other):
        if not isinstance(other, BBSSignature):
            return NotImplemented
        return points_equal(self.A, other.A) and self.e == other.e

class BBSSignatureScheme:
    """
    BBS Signature Scheme implementing Core.tex operations:
    - CoreSign (Section 3.6.1)
    - CoreVerify (Section 3.6.2)
    """
    
    def __init__(self, max_messages: int = 10, api_id: bytes = b"", generators: Optional[List[tuple]] = None):
        self.max_messages = max_messages
        self.api_id = api_id
        
        if generators:
            self.generators = generators
        else:
            self.generators = BBSGenerators.create_generators(self.max_messages, self.api_id)
        
        self.P1 = G1
        self.P2 = G2
    
    def core_sign(self, SK: BBSPrivateKey, header: bytes, messages: List[bytes]) -> BBSSignature:
        """
        CoreSign operation from Core.tex Section 3.6.1
        
        Procedure :
        1. domain = calculate_domain(PK, Q_1, (H_1, ..., H_L), header, api_id)
        2. e = hash_to_scalar(serialize((SK, msg_1, ..., msg_L, domain)), hash_to_scalar_dst)
        3. B = P1 + Q_1 * domain + H_1 * msg_1 + ... + H_L * msg_L
        4. A = B * (1 / (SK + e))
        5. return signature_to_octets((A, e))
        """
        L = len(messages)
        if L > self.max_messages:
            raise ValueError(f"Too many messages: {L} > {self.max_messages}")
        
        # Core.tex: Extract generators Q_1, H_1, ..., H_L
        Q_1 = self.generators[0]
        H_generators = self.generators[1:L+1]
        
        # Core.tex Step 1: Calculate domain
        pk = SK.to_pk()
        domain = calculate_domain(pk.to_bytes(), Q_1, H_generators, header, self.api_id)
        
        # Convert messages to scalars
        msg_scalars = [hash_to_scalar(m, self.api_id + DST_H2S) for m in messages]
        
        # Core.tex Step 2: Calculate e = H(SK || msg_1 || ... || msg_L || domain)
        e_data = SK.x.to_bytes(32, 'big')
        for msg_scalar in msg_scalars:
            e_data += msg_scalar.to_bytes(32, 'big')
        e_data += domain.to_bytes(32, 'big')
        hash_to_scalar_dst = self.api_id + b"H2S_"
        e = hash_to_scalar(e_data, hash_to_scalar_dst)
        
        # Core.tex Step 3: Calculate B = P1 + Q_1 * domain + sum(H_i * msg_i)
        B = self.P1
        if domain != 0:
            B = add(B, multiply(Q_1, domain))
        for i, msg_scalar in enumerate(msg_scalars):
            if msg_scalar != 0:
                B = add(B, multiply(H_generators[i], msg_scalar))
        
        # Core.tex Step 4: Calculate A = B * (1/(SK + e))
        sk_plus_e = (SK.x + e) % CURVE_ORDER
        if sk_plus_e == 0:
            raise ValueError("Invalid: SK + e = 0")
        
        inv = pow(sk_plus_e, CURVE_ORDER - 2, CURVE_ORDER)
        A = multiply(B, inv)
        
        # Core.tex Step 5: Return signature (A, e)
        return BBSSignature(A=A, e=e)
    
    def core_verify(self, PK: BBSPublicKey, signature: BBSSignature, 
                   header: bytes, messages: List[bytes]) -> bool:
        """
        CoreVerify operation from Core.tex Section 3.6.2
        
        Procedure :
        1. domain = calculate_domain(PK, Q_1, (H_1, ..., H_L), header, api_id)
        2. B = P1 + Q_1 * domain + H_1 * msg_1 + ... + H_L * msg_L
        3. if h(A, W) * h(A * e - B, BP2) != Identity_GT, return INVALID
        4. return VALID
        
        Note: Equation rearranged to h(A, W + e*P2) == h(B, P2)
        """
        L = len(messages)
        if L > self.max_messages:
            return False
        
        # Core.tex: Extract generators Q_1, H_1, ..., H_L
        Q_1 = self.generators[0]
        H_generators = self.generators[1:L+1]
        
        # Core.tex Step 1: Calculate domain
        domain = calculate_domain(PK.to_bytes(), Q_1, H_generators, header, self.api_id)
        
        # Convert messages to scalars
        msg_scalars = [hash_to_scalar(m, self.api_id + DST_H2S) for m in messages]
        
        # Core.tex Step 2: Calculate B = P1 + Q_1 * domain + sum(H_i * msg_i)
        B = self.P1
        if domain != 0:
            B = add(B, multiply(Q_1, domain))
        for i, msg_scalar in enumerate(msg_scalars):
            if msg_scalar != 0 and i < len(H_generators):
                B = add(B, multiply(H_generators[i], msg_scalar))
        
        # Core.tex Step 3: Verify pairing equation
        # Original: h(A, W) * h(A * e - B, P2) == Identity_GT
        # Rearranged: h(A, W + e*P2) == h(B, P2)
        W_plus_eP2 = add(PK.W, multiply(self.P2, signature.e))
        
        pairing_left = pairing(W_plus_eP2, signature.A)
        pairing_right = pairing(self.P2, B)
        
        return pairing_left == pairing_right
    
    def sign(self, sk: BBSPrivateKey, messages: List[bytes], header: bytes = b"") -> BBSSignature:
        """Sign multiple messages using CoreSign"""
        return self.core_sign(sk, header, messages)
    
    def verify(self, pk: BBSPublicKey, signature: BBSSignature, 
              messages: List[bytes], header: bytes = b"") -> bool:
        """Verify signature using CoreVerify"""
        return self.core_verify(pk, signature, header, messages)
    
    def sign_single(self, sk: BBSPrivateKey, message, header: bytes = b"") -> BBSSignature:
        """Sign a single message"""
        if isinstance(message, (list, tuple)):
            if len(message) == 0:
                raise ValueError("Empty message list")
            return self.core_sign(sk, header, list(message))
        return self.core_sign(sk, header, [message])
    
    def verify_single(self, pk: BBSPublicKey, signature: BBSSignature,
                     message, header: bytes = b"") -> bool:
        """Verify a single message signature"""
        if isinstance(message, (list, tuple)):
            if len(message) == 0:
                raise ValueError("Empty message list")
            return self.core_verify(pk, signature, header, list(message))
        return self.core_verify(pk, signature, header, [message])