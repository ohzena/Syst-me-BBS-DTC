"""
BBSCore - Core BBS Signature Scheme Implementation

This module provides the core BBS (Boneh-Boyen-Shacham) signature scheme
implementation for privacy-preserving digital signatures with selective disclosure.
"""

# Core BBS classes and functions
from BBSCore.Setup import BBSPublicKey, BBSPrivateKey, BBSKeyPair, BBSSystemSetup, BBSGenerators
from BBSCore.KeyGen import BBSKeyGen
from BBSCore.bbsSign import BBSSignature, BBSSignatureScheme
from BBSCore.BlindSign import BlindCommitment, BBSBlindSigner, BlindSignatureProtocol
from BBSCore.ZKProof import BBSProof, BBSProofScheme

__all__ = [
    # Key management
    'BBSPublicKey',
    'BBSPrivateKey', 
    'BBSKeyPair',
    'BBSKeyGen',
    'BBSGenerators',
    'BBSSystemSetup',

    
    # Signature schemes
    'BBSSignature',
    'BBSSignatureScheme',
    'BlindCommitment', 
    'CommitmentProof',
    'BlindSignerClient',
    'BBSBlindSigner',
    'BlindSignatureProtocol',
    
    # Zero-knowledge proofs
    'ProofInitResult',
    'BBSProof',
    'BBSProofScheme',
    'BBSWithProofs'
]