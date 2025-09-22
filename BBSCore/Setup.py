"""
Setup.py - BBS System Setup and Key Structures
Following IETF BBS Signatures specification 
"""

import hashlib
import secrets
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass
import base58

from py_ecc.optimized_bls12_381 import (
    G1, G2, multiply, add, neg, pairing, final_exponentiate,
    FQ12, curve_order, field_modulus, normalize, Z1, Z2
)

from py_ecc.bls.hash_to_curve import hash_to_G1, hash_to_G2
from py_ecc.bls.g2_primitives import (G1_to_pubkey, G2_to_signature, signature_to_G2, pubkey_to_G1)
from py_ecc.optimized_bls12_381.optimized_pairing import normalize1
from BBSCore.utils import points_equal

# BLS12-381 constants from py_ecc
CURVE_ORDER = curve_order
FIELD_MODULUS = field_modulus

# Domain Separation Tags as per Core.tex Section 4.1
DST_KEYGEN = b"BBS_BLS12381G1_XMD:SHA-256_SSWU_RO_KEYGEN_DST_"
DST_H2S = b"BBS_BLS12381G1_XMD:SHA-256_SSWU_RO_H2S_"
DST_H2C = b"BBS_BLS12381G1_XMD:SHA-256_SSWU_RO_H2C_DST_"
DST_GENERATORS = b"BBS_BLS12381G1_XMD:SHA-256_SSWU_RO_MESSAGE_GENERATOR_DST_"

# Sizes per Core.tex specification
SCALAR_SIZE = 32
G1_COMPRESSED_SIZE = 48
G2_COMPRESSED_SIZE = 96

# Type hints for py_ecc points
G1Point = Tuple[int, int]
G2Point = Tuple[Tuple[int, int], Tuple[int, int]]
G1PointProjective = Tuple[int, int, int]

def to_projective(pt):
    """Convert affine (x,y) to projective (x,y,1)"""
    if pt is None:
        return None
    try:
        if len(pt) == 2:
            x, y = pt
            return (x, y, 1)
    except Exception:
        pass
    return pt

def ensure_affine(pt):
    """Ensure point is in affine representation (x,y)"""
    if pt is None:
        return None
    try:
        if len(pt) == 3:
            return normalize(pt)
    except Exception:
        pass
    return pt

def hash_to_scalar(data: bytes, dst: bytes) -> int:
    """
    Hash data to scalar in Zr using SHA-256
    Per Core.tex hash_to_scalar operation
    """
    hasher = hashlib.sha256()
    hasher.update(data)
    hasher.update(dst)
    hash_bytes = hasher.digest()
    
    # Convert to scalar modulo curve_order
    scalar = int.from_bytes(hash_bytes, 'big') % CURVE_ORDER
    return scalar

def point_to_bytes_g1(P: tuple) -> bytes:
    """Serialize G1 point to 48 bytes per Core.tex"""
    return G1_to_pubkey(normalize1(P))

def point_from_bytes_g1(data):
    """Deserialize G1 point from 48 bytes per Core.tex"""
    if data == b'\x00' * 48:
        return None
    return pubkey_to_G1(data)

def point_to_bytes_g2(point) -> bytes:
    """Serialize G2 point to 96 bytes per Core.tex"""
    if point is None:
        return b'\x00' * 96
    return G2_to_signature(normalize1(point))

def point_from_bytes_g2(data):
    """Deserialize G2 point from 96 bytes per Core.tex"""
    if data == b'\x00' * 96:
        return None
    return signature_to_G2(data)

def verify_pairing_equation(left_g1: G1Point, left_g2: G2Point, 
                           right_g1: G1Point, right_g2: G2Point) -> bool:
    """
    Verify pairing equation: e(left_g1, left_g2) = e(right_g1, right_g2)
    Core.tex uses pairing verification in CoreVerify and CoreProofVerify
    """
    # Calculate pairings with py_ecc order (G2 first)
    p1 = pairing(left_g2, left_g1)
    p2 = pairing(right_g2, right_g1)
    
    # Use negation for efficient verification
    neg_right_g2 = neg(right_g2)
    p2_neg = pairing(neg_right_g2, right_g1)
    product = p1 * p2_neg
    
    return final_exponentiate(product) == FQ12.one()

@dataclass
class BBSPrivateKey:
    """
    BBS Secret Key - scalar in Zr per Core.tex
    Used in CoreSign operation
    """
    x: int
    
    def to_bytes(self) -> bytes:
        """Serialize to 32 bytes"""
        return self.x.to_bytes(32, 'big')
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'BBSPrivateKey':
        """Deserialize from bytes"""
        if len(data) != 32:
            raise ValueError(f"Invalid secret key size: {len(data)}")
        return cls(x=int.from_bytes(data, 'big'))
    
    def to_base58(self) -> str:
        """Encode to base58"""
        return base58.b58encode(self.to_bytes()).decode('ascii')
    
    def to_pk(self) -> 'BBSPublicKey':
        """
        Calculate corresponding public key W = x * G2
        Per Core.tex KeyGen operation
        """
        W = multiply(G2, self.x)
        return BBSPublicKey(W=W)

@dataclass 
class BBSPublicKey:
    """
    BBS Public Key - point in G2 per Core.tex
    Used in CoreVerify and CoreProofVerify operations
    """
    W: tuple

    def to_bytes(self) -> bytes:
        """Serialize key to 96 bytes using point compression"""
        return G2_to_signature(normalize1(self.W))

    @classmethod
    def from_bytes(cls, data: bytes) -> 'BBSPublicKey':
        """Deserialize key from bytes"""
        if len(data) != 96:
            raise ValueError(f"Invalid public key size: {len(data)}")
        return cls(W=signature_to_G2(data))

    def __eq__(self, other):
        """Compare public keys using point equality"""   
        if not isinstance(other, BBSPublicKey):
            return NotImplemented
        return points_equal(self.W, other.W)
    
    def to_base58(self) -> str:
        """Encode to base58"""
        return base58.b58encode(self.to_bytes()).decode('ascii')
    
    @classmethod
    def from_base58(cls, data: str) -> 'BBSPublicKey':
        """Decode from base58"""
        bytes_data = base58.b58decode(data)
        return cls.from_bytes(bytes_data)

@dataclass
class BBSKeyPair:
    """BBS Key Pair per Core.tex KeyGen operation"""
    secret_key: BBSPrivateKey
    public_key: BBSPublicKey

class BBSGenerators:
    """
    Generator creation following Core.tex Section 4.1.1
    Creates Q_1 (domain generator) and H_1, ..., H_L (message generators)
    """
    
    @staticmethod
    def hash_to_g1(data: bytes, dst: bytes) -> G1Point:
        """
        Hash-to-G1 using py_ecc
        Implements hash_to_curve operation from Core.tex
        """
        try:
            point = hash_to_G1(data, dst, hash_function=hashlib.sha256)
            return point
        except Exception as e:
            raise ValueError(f"hash_to_g1 failed: {e}")
    
    @staticmethod
    def create_generators(count: int, api_id: bytes = b"") -> List[G1Point]:
        """
        Create L+1 generators: Q_1, H_1, ..., H_L
        Per Core.tex Section 4.1.1.1 generator creation requirements
        """
        generators = []

        # Generate Q_1 (domain generator) per Core.tex
        q1_seed = DST_GENERATORS + b"Q_1_" + api_id
        Q_1 = BBSGenerators.hash_to_g1(q1_seed, DST_GENERATORS)
        
        if Q_1 is None:
            raise ValueError("Q_1 generation failed")
        generators.append(Q_1)

        # Generate H_1, ..., H_count (message generators)
        for i in range(1, count + 1):
            h_seed = DST_GENERATORS + b"H_" + i.to_bytes(4, 'big') + api_id
            H_i = BBSGenerators.hash_to_g1(h_seed, DST_GENERATORS)
            
            if H_i is None:
                raise ValueError(f"H_{i} generation failed")
            generators.append(H_i)

        return generators

def calculate_domain(
    PK: bytes,
    Q_1: tuple,
    H_generators: list,
    header: bytes,
    api_id: bytes
) -> int:
    """
    Calculate domain value per Core.tex calculate_domain operation
    Used in CoreSign, CoreVerify, CoreProofGen, and CoreProofVerify
    """
    data = b""
    data += PK  # Public key bytes
    data += point_to_bytes_g1(Q_1)
    for H in H_generators:
        data += point_to_bytes_g1(H)
    data += len(header).to_bytes(8, 'big') + header
    data += api_id

    # Hash to scalar
    dst = api_id + b"H2S_"
    return hash_to_scalar(data, dst)

class BBSSystemSetup:
    """
    BBS System Setup per Core.tex specifications
    Handles generator creation and key pair generation
    """
    
    def __init__(self, max_messages: int = 50, api_id: bytes = b""):
        """
        Initialize BBS system
        Creates generators Q_1, H_1, ..., H_max_messages per Core.tex
        """
        self.max_messages = max_messages
        self.api_id = api_id
        
        # Create generators per Core.tex Section 4.1.1
        self.generators = BBSGenerators.create_generators(max_messages, api_id)
        
        # Separate Q_1 and H generators for easy access
        self.Q_1 = self.generators[0]
        self.H_generators = self.generators[1:]
    
    def create_key_pair(self, ikm: Optional[bytes] = None) -> BBSKeyPair:
        """
        Create new BBS key pair per Core.tex KeyGen operation
        """
        if ikm is None:
            # Generate random private key
            sk_int = secrets.randbelow(CURVE_ORDER)
        else:
            # Derive key from input keying material
            sk_int = hash_to_scalar(ikm, DST_KEYGEN) % CURVE_ORDER
        
        # Create private key
        private_key = BBSPrivateKey(x=sk_int)
        
        # Derive public key: W = sk * G2 per Core.tex
        public_key_point = multiply(G2, sk_int)
        public_key = BBSPublicKey(W=public_key_point)
        
        return BBSKeyPair(secret_key=private_key, public_key=public_key)
    
    def get_generators(self) -> List[G1Point]:
        """Get all generators (Q_1, H_1, ..., H_L)"""
        return self.generators.copy()
    
    def get_message_generators(self) -> List[G1Point]:
        """Get message generators (H_1, ..., H_L)"""
        return self.H_generators.copy()
    
    def get_domain_generator(self) -> G1Point:
        """Get domain generator (Q_1)"""
        return self.Q_1

def ensure_g1_point(point: Union[G1Point, None]) -> Optional[G1Point]:
    """Ensure point is in py_ecc G1 format"""
    if point is None:
        return None
    if isinstance(point, tuple) and len(point) == 2:
        return point
    raise ValueError("Invalid G1 point format")

def ensure_g2_point(point: Union[G2Point, None]) -> Optional[G2Point]:
    """Ensure point is in py_ecc G2 format"""
    if point is None:
        return None
    if isinstance(point, tuple) and len(point) == 2:
        return point
    raise ValueError("Invalid G2 point format")