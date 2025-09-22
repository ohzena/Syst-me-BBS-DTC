"""
DTCIssuer.py - Digital Trust Certificate Issuer Implementation

The DTCIssuer represents trusted authorities (governments, health organizations) that issue
verifiable travel credentials using BBS signatures. This component demonstrates how BBS 
enables privacy-preserving digital credentials through selective disclosure.

Key BBS Integration:
- Uses BBS signature scheme to sign credential attributes as separate messages
- Each credential attribute becomes a BBS message, enabling selective disclosure
- Issues credentials that holders can later present with zero-knowledge proofs
- Maintains cryptographic keys for BBS signature generation

The issuer signs a vector of messages representing credential attributes:
messages = [credential_id, document_type, issuer_id, issued_at, attr1, attr2, ...]
signature = BBS.Sign(secret_key, messages, header)

This allows holders to later prove possession of valid credentials while revealing
only specific attributes through BBS proof generation.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import logging

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from BBSCore.KeyGen import BBSKeyGen
from BBSCore.Setup import BBSPrivateKey, BBSPublicKey, BBSKeyPair
from BBSCore.bbsSign import BBSSignatureScheme, BBSSignature
from BBSCore.ZKProof import BBSProofScheme, BBSWithProofs

from DTC.dtc import (
    DTCCredential, DocumentType, AttributeType, CredentialAttribute,
    PASSPORT_SCHEMA, VISA_SCHEMA, VACCINATION_SCHEMA,
    PassportCredential, VisaCredential, VaccinationCredential
)

logger = logging.getLogger(__name__)


class DTCIssuer:
    """
    Digital Trust Certificate Issuer - Signs credentials using BBS signatures
    
    This class implements the issuer role in the BBS-based DTC system. It generates
    BBS keypairs and signs credential attributes as message vectors, enabling later
    selective disclosure by credential holders.
    """
    
    def __init__(self, issuer_id: str, max_messages: int = 30):
        """Initialize DTC Issuer with BBS signing capabilities"""
        self.issuer_id = issuer_id
        self.max_messages = max_messages
        
        # Generate BBS keypair for credential signing
        logger.info(f"Generating BBS keys for issuer: {issuer_id}")
        keypair = BBSKeyGen.keygen()
        self.secret_key = keypair.secret_key
        self.public_key = keypair.public_key
        
        # Initialize BBS with ZK proof support for issuing signatures
        self.bbs = BBSWithProofs(max_messages=max_messages, api_id=issuer_id.encode())
        
        logger.info(f"Initialized BBS issuer {issuer_id} with {max_messages} max messages")
    
    def sign_credential(self, credential: DTCCredential, holder_id: str, 
                       document_type: DocumentType) -> DTCCredential:
        """
        Sign a credential using BBS signatures
        
        This converts the credential attributes to BBS messages and signs them,
        enabling later selective disclosure by the holder.
        """
        # Use the credential's own message generation method for consistency
        messages = credential.to_message_list()
        
        # Create signing context header
        header = f"{document_type.value}:{self.issuer_id}".encode()
        
        logger.info(f"DTCIssuer signing with header: {header}")
        logger.info(f"DTCIssuer signing {len(messages)} messages")
        for i, msg in enumerate(messages):
            try:
                decoded = msg.decode('utf-8')
                logger.info(f"  [{i}] {decoded}")
            except:
                logger.info(f"  [{i}] <binary data: {len(msg)} bytes>")
        
        # Generate BBS signature over the message vector
        signature = self.bbs.sign(self.secret_key, messages, header)
        logger.info(f"DTCIssuer generated signature: {signature}")
        
        # VERIFICATION: Test signature immediately after creation
        signature_check = self.bbs.verify(self.public_key, signature, messages, header)
        logger.info(f"DTCIssuer signature immediate verification: {signature_check}")
        
        credential.signature = signature
        credential.signature_bytes = signature.to_bytes()  # Standard 80-byte BBS signature
        
        logger.info(f"Issued {document_type.value} credential for {holder_id}")
        
        return credential
    
    def issue_passport(self, passport_data: Dict[str, Any]) -> PassportCredential:
        """Issue a passport credential with BBS signature"""
        
        # Extract holder information
        holder_name = f"{passport_data.get('given_names', '')} {passport_data.get('surname', '')}"
        holder_id = passport_data.get('holder_id', holder_name.lower().replace(" ", "_") + "@passport.holder")
        
        # Create passport credential from data
        # Map input data to schema attribute names
        full_name = f"{passport_data['given_names']} {passport_data['surname']}".strip()
        
        passport = PassportCredential(
            issuer_id=self.issuer_id,
            holder_id=holder_id,
            document_number=passport_data["document_number"],
            holder_name=full_name,
            nationality=passport_data["nationality"],
            date_of_birth=passport_data["date_of_birth"],
            place_of_birth=passport_data["place_of_birth"],
            date_of_issue=passport_data["date_of_issue"],
            date_of_expiry=passport_data["date_of_expiry"],
            issuing_authority=passport_data["issuing_authority"]
        )
        
        # Sign the passport credential using BBS
        self.sign_credential(passport, holder_id, DocumentType.PASSPORT)
        
        logger.info(f"Issued passport credential for {holder_name}")
        return passport
    
    def issue_visa(self, visa_data: Dict[str, Any]) -> VisaCredential:
        """Issue a visa credential with BBS signature"""
        
        # Extract holder information
        holder_name = f"{visa_data.get('given_names', '')} {visa_data.get('surname', '')}"
        holder_id = visa_data.get('holder_id', holder_name.lower().replace(" ", "_") + "@visa.holder")
        
        # Map input data to schema attribute names
        full_name = f"{visa_data['given_names']} {visa_data['surname']}".strip()
        
        # Create visa credential  
        visa = VisaCredential(
            issuer_id=self.issuer_id,
            holder_id=holder_id,
            visa_number=visa_data["visa_number"],
            visa_type=visa_data["visa_type"],
            holder_name=full_name,
            country_of_issue=visa_data["issuing_authority"], 
            valid_from=visa_data["date_of_issue"],
            valid_until=visa_data["date_of_expiry"],
            entries_allowed="Multiple",
            duration_of_stay=90
        )
        
        # Sign the visa credential using BBS
        self.sign_credential(visa, holder_id, DocumentType.VISA)
        
        logger.info(f"Issued visa credential for {holder_name}")
        return visa
    
    def issue_vaccination(self, vaccination_data: Dict[str, Any]) -> VaccinationCredential:
        """Issue a vaccination certificate with BBS signature"""
        
        # Extract holder information  
        holder_name = f"{vaccination_data.get('given_names', '')} {vaccination_data.get('surname', '')}"
        holder_id = vaccination_data.get('holder_id', holder_name.lower().replace(" ", "_") + "@vaccination.holder")
        
        # Extract vaccination details if provided as a dictionary
        vaccination_details = vaccination_data.get("vaccination_details", {})
        
        # Create vaccination credential with proper attribute mapping
        vaccination = VaccinationCredential(
            issuer_id=self.issuer_id,
            holder_id=holder_id,
            certificate_id=vaccination_data["certificate_id"],
            holder_name=holder_name,  # Map to schema expected name
            given_names=vaccination_data["given_names"], 
            surname=vaccination_data["surname"],
            date_of_birth=vaccination_data["date_of_birth"],
            # Map vaccination_details to individual schema attributes
            vaccine_type=vaccination_details.get("vaccine_type", "COVID-19"),
            vaccine_name=vaccination_details.get("vaccine_name", "Unknown"),
            manufacturer=vaccination_details.get("manufacturer", "Unknown"),
            batch_number=vaccination_details.get("batch_number", "Unknown"),
            vaccination_date=vaccination_details.get("vaccination_date", vaccination_data.get("date_of_birth")),
            vaccination_center=vaccination_details.get("vaccination_center", "Unknown Center"),
            country_of_vaccination=vaccination_details.get("country_of_vaccination", "Unknown"),
            dose_number=vaccination_details.get("dose_number", 1),
            total_doses=vaccination_details.get("total_doses", 2),
            next_dose_date=vaccination_details.get("next_dose_date"),
            issuing_authority=vaccination_data["issuing_authority"]
        )
        
        # Sign the vaccination credential using BBS
        self.sign_credential(vaccination, holder_id, DocumentType.VACCINATION)
        
        logger.info(f"Issued vaccination certificate for {holder_name}")
        return vaccination
    
    def get_public_key_bytes(self) -> bytes:
        """Get issuer's BBS public key in bytes format (96 bytes for G2 point)"""
        return self.public_key.to_bytes()
        
    def get_public_key_base58(self) -> str:
        """Get issuer's BBS public key in base58 format for sharing"""
        return self.public_key.to_base58()
        
    def get_issuer_info(self) -> Dict[str, Any]:
        """Get issuer information including BBS public key"""
        return {
            "issuer_id": self.issuer_id,
            "max_messages": self.max_messages,
            "public_key_base58": self.get_public_key_base58(),
            "supported_documents": [doc.value for doc in DocumentType]
        }


def create_test_issuer(issuer_id: str = "test_issuer") -> DTCIssuer:
    """Create a DTCIssuer for testing purposes"""
    return DTCIssuer(issuer_id)