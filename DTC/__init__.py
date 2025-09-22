"""
DTC Package - Digital Travel Credentials with BBS Signatures

This package implements a complete privacy-preserving digital credential system for travel
documents using BBS (Boneh-Boyen-Shacham) signatures. The system demonstrates how BBS
enables selective disclosure and unlinkable presentations for digital identity.

BBS Integration Architecture:
┌─────────────┐    BBS.Sign     ┌──────────────┐    BBS.ProofGen    ┌─────────────┐
│ DTCIssuer   │ ────────────► │ DTCHolder    │ ─────────────────► │ DTCVerifier │
│ (Govt/Org)  │  signs attrs   │ (Traveler)   │  selective proof   │ (Border)    │
└─────────────┘  as messages   └──────────────┘  only reveal some  └─────────────┘
                                                                           │
                               ┌─────────────────────────────────────────┘
                               │ BBS.ProofVerify
                               ▼
                         Valid credential
                         Only disclosed attributes revealed
                         Hidden attributes remain private
                         Unlinkable between presentations

Key Benefits:
- Selective Disclosure: Reveal only necessary attributes (e.g., age ≥ 18, not exact DOB)
- Unlinkability: Multiple presentations cannot be correlated
- Privacy: Sensitive data remains cryptographically hidden
- Efficiency: Constant-size proofs regardless of hidden attributes

Components:
- DTCCredential: Base credential structure with BBS message conversion
- DTCIssuer: Signs credential attributes using BBS scheme
- DTCHolder: Generates ZK proofs for selective disclosure
- DTCVerifier: Verifies presentations using BBS proof verification
"""

# Core credential structures and types
from DTC.dtc import (
    DTCCredential,
    DocumentType,
    AttributeType,
    CredentialAttribute,
    CredentialSchema,
    PassportCredential,
    VisaCredential, 
    VaccinationCredential,
    PASSPORT_SCHEMA,
    VISA_SCHEMA,
    VACCINATION_SCHEMA,
    create_passport_credential,
    create_visa_credential,
    create_vaccination_credential
)

# BBS-enabled actors in the DTC ecosystem
from DTC.DTCIssuer import DTCIssuer, create_test_issuer
from DTC.DTCHolder import DTCHolder, create_test_holder  
from DTC.DTCVerifier import DTCVerifier, create_test_verifier

# Unified BBS cryptographic interface
from DTC import bbs_core

__version__ = "1.0.0"
__author__ = "BBS Educational Implementation"
__description__ = "Digital Travel Credentials with BBS Signatures"

# Public API for BBS-based digital credentials
__all__ = [
    # Core credential structures
    'DTCCredential',
    'DocumentType', 
    'AttributeType',
    'CredentialAttribute',
    'CredentialSchema',
    
    # Specialized travel credentials
    'PassportCredential',
    'VisaCredential',
    'VaccinationCredential',
    
    # Predefined schemas
    'PASSPORT_SCHEMA',
    'VISA_SCHEMA', 
    'VACCINATION_SCHEMA',
    
    # BBS-enabled actors
    'DTCIssuer',     # Signs credentials with BBS
    'DTCHolder',     # Creates selective disclosure proofs
    'DTCVerifier',   # Verifies BBS presentations
    
    # Convenience functions
    'create_passport_credential',
    'create_visa_credential',
    'create_vaccination_credential',
    'create_test_issuer',
    'create_test_holder',
    'create_test_verifier',
    
    # BBS cryptographic core
    'bbs_core'
]

def get_version():
    """Get package version"""
    return __version__

def get_info():
    """Get package information"""
    return {
        'name': 'DTC',
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'components': len(__all__)
    }

# Initialize logging for the package
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

def create_demo_scenario():
    """
    Create a complete BBS-based DTC ecosystem demonstration
    
    This function sets up all the actors and trust relationships needed to
    demonstrate the full BBS selective disclosure workflow:
    1. Trusted issuers with BBS keypairs
    2. Traveler with digital wallet
    3. Verifiers with trusted issuer public keys
    """
    
    # Create trusted issuers with BBS signing capabilities
    french_gov = DTCIssuer("FR_GOV_001")         # Passport issuer
    us_embassy = DTCIssuer("US_EMBASSY_FR")      # Visa issuer
    health_ministry = DTCIssuer("FR_HEALTH_MIN") # Vaccination certificate issuer
    
    # Create traveler with BBS proof generation capabilities
    alice = DTCHolder("alice_dubois")
    
    # Create verifiers with BBS proof verification capabilities
    border_control = DTCVerifier("BORDER_CONTROL")
    airline = DTCVerifier("AIRLINE_CHECKIN")
    
    # Establish trust relationships: verifiers trust issuer public keys
    # This enables BBS proof verification against known issuer signatures
    border_control.add_trusted_issuer("FR_GOV_001", french_gov.public_key)
    border_control.add_trusted_issuer("US_EMBASSY_FR", us_embassy.public_key)
    border_control.add_trusted_issuer("FR_HEALTH_MIN", health_ministry.public_key)
    
    # Airline has more restricted trust (only passport/visa, not health)
    airline.add_trusted_issuer("FR_GOV_001", french_gov.public_key)
    airline.add_trusted_issuer("US_EMBASSY_FR", us_embassy.public_key)
    
    return {
        'issuers': {
            'french_gov': french_gov,
            'us_embassy': us_embassy,
            'health_ministry': health_ministry
        },
        'holders': {
            'alice': alice
        },
        'verifiers': {
            'border_control': border_control,
            'airline': airline
        }
    }