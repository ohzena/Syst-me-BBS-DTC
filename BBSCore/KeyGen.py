"""
KeyGen.py - BBS Key Generation using py_ecc BLS12-381 implementation
Following IETF BBS Signatures specification (Core.tex)
"""

import secrets
from typing import List, Tuple, Optional
import hashlib

from py_ecc.optimized_bls12_381 import (
    G2, multiply, curve_order
)

def hash_to_int(msg: bytes, hash_function=hashlib.sha256) -> int:
    """Hash to integer modulo curve order"""
    digest = hash_function(msg).digest()
    return int.from_bytes(digest, 'big') % curve_order

from BBSCore.Setup import (
    BBSPrivateKey, BBSPublicKey, BBSKeyPair, 
    CURVE_ORDER, DST_KEYGEN, SCALAR_SIZE, G2_COMPRESSED_SIZE,
    hash_to_scalar
)

class BBSKeyGen:
    """
    BBS Key Generation implementing Core.tex KeyGen operation
    Uses py_ecc for optimized BLS12-381 operations
    """
    
    @staticmethod
    def keygen(ikm: bytes = None, key_info: bytes = b"") -> BBSKeyPair:
        """
        Generate BBS key pair following Core.tex KeyGen procedure
        
        Core.tex KeyGen:
        1. Generate or derive secret key SK in Zr  
        2. Compute public key PK = SK * G2
        
        Args:
            ikm: Input key material (32+ bytes)
            key_info: Optional key information
            
        Returns:
            BBSKeyPair with py_ecc points
        """
        if ikm is None:
            ikm = secrets.token_bytes(32)
        
        # Derive secret key using hash_to_scalar per Core.tex
        salt = DST_KEYGEN + key_info
        sk_data = ikm + salt
        sk_val = hash_to_scalar(sk_data, DST_KEYGEN)
        
        # Ensure key is in valid range [1, r-1]
        if sk_val == 0:
            sk_val = 1
        
        sk = BBSPrivateKey(x=sk_val)
        
        # Core.tex: Compute public key W = sk * G2
        W = multiply(G2, sk.x)
        pk = BBSPublicKey(W=W)
        
        return BBSKeyPair(secret_key=sk, public_key=pk)
    
    @staticmethod
    def sk_to_pk(sk: BBSPrivateKey) -> BBSPublicKey:
        """
        Convert secret key to public key per Core.tex
        PK = SK * G2
        """
        W = multiply(G2, sk.x)
        return BBSPublicKey(W=W)
    
    @staticmethod
    def generate_keypair(seed: bytes = None) -> Tuple[BBSPrivateKey, BBSPublicKey]:
        """
        Generate BBS key pair - convenience function
        """
        keypair = BBSKeyGen.keygen(ikm=seed)
        return keypair.secret_key, keypair.public_key

def generate_bbs_keypair(seed: Optional[str] = None) -> Tuple[str, str]:
    """
    Generate BBS key pair and return as base58 strings
    
    Args:
        seed: Optional seed string
        
    Returns:
        Tuple of (secret_key_base58, public_key_base58)
    """
    ikm = None
    if seed:
        ikm = hashlib.sha256(seed.encode()).digest()
    
    sk, pk = BBSKeyGen.generate_keypair(ikm)
    return sk.to_base58(), pk.to_base58()

def validate_public_key(pk_base58: str) -> bool:
    """
    Validate base58-encoded public key
    
    Args:
        pk_base58: Public key in base58
        
    Returns:
        True if valid
    """
    try:
        pk = BBSPublicKey.from_base58(pk_base58)
        
        # Basic validation: check point is not None (infinity)
        if pk.W is None:
            return False
            
        # Validate py_ecc tuple format
        if not isinstance(pk.W, tuple) or len(pk.W) != 2:
            return False
            
        # Validate G2 components: each component is tuple (x, y) in Fq2
        (x_part, y_part) = pk.W
        if not isinstance(x_part, tuple) or len(x_part) != 2:
            return False
        if not isinstance(y_part, tuple) or len(y_part) != 2:
            return False
            
        return True
    except Exception:
        return False

def batch_generate_keypairs(count: int, base_seed: str = None) -> List[Tuple[str, str]]:
    """
    Generate multiple key pairs efficiently
    
    Args:
        count: Number of pairs to generate
        base_seed: Optional base seed
        
    Returns:
        List of tuples (sk_base58, pk_base58)
    """
    keypairs = []
    
    for i in range(count):
        # Create unique seed for each key
        if base_seed:
            seed = f"{base_seed}_{i}"
        else:
            seed = None
            
        sk_b58, pk_b58 = generate_bbs_keypair(seed)
        keypairs.append((sk_b58, pk_b58))
    
    return keypairs