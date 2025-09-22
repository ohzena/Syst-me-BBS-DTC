"""
bbs_core.py - Unified BBS Interface

Provides a unified interface to all BBS components
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from BBSCore.Setup import (
    BBSPrivateKey, BBSPublicKey, BBSKeyPair, BBSSystemSetup, BBSGenerators,
    CURVE_ORDER, DST_KEYGEN, calculate_domain, hash_to_scalar
)

from BBSCore.KeyGen import BBSKeyGen
from BBSCore.bbsSign import BBSSignatureScheme, BBSSignature
from BBSCore.ZKProof import BBSProof, BBSProofScheme, BBSWithProofs

# All BBS components are required - no fallbacks
BBS_AVAILABLE = True

def generate_keypair(ikm: bytes = None) -> tuple:
    """Generate BBS keypair"""
    keypair = BBSKeyGen.keygen(ikm)
    return keypair.secret_key, keypair.public_key

def create_signature_scheme(max_messages: int = 10) -> BBSSignatureScheme:
    """Create BBS signature scheme"""
    return BBSSignatureScheme(max_messages=max_messages)

def create_proof_scheme(max_messages: int = 10) -> BBSProofScheme:
    """Create BBS proof scheme"""
    return BBSProofScheme(max_messages=max_messages)

# Export all BBS components
__all__ = [
    'BBSPrivateKey', 'BBSPublicKey', 'BBSKeyPair', 'BBSSystemSetup', 'BBSGenerators',
    'BBSKeyGen', 'BBSSignatureScheme', 'BBSSignature', 'BBSProof', 'BBSProofScheme', 'BBSWithProofs',
    'CURVE_ORDER', 'DST_KEYGEN', 'calculate_domain', 'hash_to_scalar',
    'generate_keypair', 'create_signature_scheme', 'create_proof_scheme',
    'BBS_AVAILABLE'
]