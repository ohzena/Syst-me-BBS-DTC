"""
DTCHolder.py - Digital Trust Certificate Holder Implementation

The DTCHolder represents travelers who possess digital credentials and need to present
them for verification while preserving privacy. This component demonstrates the core
value proposition of BBS signatures: selective disclosure and unlinkable presentations.

Key BBS Integration:
- Stores BBS-signed credentials from trusted issuers
- Generates zero-knowledge proofs for selective attribute disclosure
- Creates unlinkable presentations that hide sensitive information
- Maintains credential wallet with multiple document types

The holder creates presentations using BBS proof generation:
proof = BBS.ProofGen(public_key, signature, header, messages, disclosed_indices)

This allows proving possession of a valid credential while revealing only specific
attributes (e.g., nationality but not date of birth), ensuring privacy and preventing
correlation between different presentations.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
import json
import logging

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from DTC.bbs_core import (
    BBSSignatureScheme, BBSPrivateKey, BBSPublicKey, BBSSignature,
    BBSProofScheme, BBSProof, BBSWithProofs
)
BBS_AVAILABLE = True

from DTC.dtc import DTCCredential, DocumentType, AttributeType, DTC_VERSION, DTC_CONTEXT

logger = logging.getLogger(__name__)


class DTCHolder:
    """
    Digital Travel Credential Holder - Creates selective disclosure presentations
    
    This class implements the holder role in the BBS-based DTC system. It manages
    a digital wallet of BBS-signed credentials and generates zero-knowledge proofs
    for selective disclosure, enabling privacy-preserving verification.
    """
    
    def __init__(self, holder_id: str):
        """Initialize holder with BBS proof generation capabilities"""
        self.holder_id = holder_id
        self.credentials: Dict[str, DTCCredential] = {}
        
        # Initialize BBS proof generation for selective disclosure
        self.bbs = BBSWithProofs(max_messages=30)
        
        logger.info(f"Holder {holder_id} initialized")
    
    def store_credential(self, credential_id: str, credential: DTCCredential):
        """
        Store a BBS-signed credential in the holder's digital wallet
        
        Validates that the credential contains a proper BBS signature before storage.
        The signature will later be used to generate zero-knowledge proofs.
        """
        if not isinstance(credential, DTCCredential):
            raise ValueError("credential must be a DTCCredential instance")
        
        self.credentials[credential_id] = credential
        
        # Verify BBS signature format if present
        if credential.signature_bytes:
            assert len(credential.signature_bytes) >= 80, \
                f"Invalid BBS signature size: {len(credential.signature_bytes)} < 80"
        
        logger.info(f"Stored {credential.document_type.value} credential: {credential_id}")
    
    def create_presentation(self,
                           credential_id: str,
                           issuer_pk: Any,  # BBSPublicKey
                           attributes_to_reveal: List[str],
                           presentation_header: bytes = b"",
                           issuer_id: str = None) -> Tuple[Any, List[bytes], List[int]]:
        """
        Create a selective disclosure presentation using BBS zero-knowledge proofs
        
        This is the core privacy-preserving functionality: the holder can prove possession
        of a valid credential while revealing only specific attributes. The BBS proof
        ensures that unrevealed attributes remain completely hidden.
        
        Args:
            credential_id: ID of credential to present from wallet
            issuer_pk: Issuer's BBS public key for proof verification
            attributes_to_reveal: Names of attributes to disclose (e.g., ["nationality"])
            presentation_header: Context-specific header for domain separation
            
        Returns:
            Tuple of (bbs_proof, disclosed_messages, disclosed_indices)
        """
        if credential_id not in self.credentials:
            raise ValueError(f"Credential {credential_id} not found in wallet")
        
        credential = self.credentials[credential_id]
        
        # Get the issuer ID (use provided one or extract from credential)
        actual_issuer_id = issuer_id or credential.issuer_id
        
        # Initialize BBS with the same API_ID as used during signing
        bbs_with_issuer_context = BBSWithProofs(max_messages=30, api_id=actual_issuer_id.encode())
        
        # Convert credential to BBS message vector (same as issuer used for signing)
        messages = credential.to_message_list()
        indices_map = credential.get_attribute_indices_map()
        
        # Determine which message indices to disclose in the proof
        disclosed_indices = []
        # Always reveal credential type and issuer for verification context
        disclosed_indices.extend([1, 2])
        
        # Add specifically requested attributes for selective disclosure
        for attr_name in attributes_to_reveal:
            if attr_name in indices_map:
                disclosed_indices.append(indices_map[attr_name])
            else:
                logger.warning(f"Attribute '{attr_name}' not found in credential")
        
        disclosed_indices = sorted(list(set(disclosed_indices)))
        
        # Extract only the messages that will be revealed
        disclosed_messages = [messages[i] for i in disclosed_indices]
        
        # Create context header for proof generation
        header = f"{credential.document_type.value}:{actual_issuer_id}".encode()
        logger.info(f"DTCHolder proof generation header: {header}")
        
        # Generate BBS zero-knowledge proof for selective disclosure
        # Deserialize the BBS signature from storage
        signature = BBSSignature.from_bytes(credential.signature_bytes)
        
        # VERIFICATION: Check if the signature itself is valid before generating proof
        logger.info(f"DTCHolder verification - signature bytes length: {len(credential.signature_bytes)}")
        logger.info(f"DTCHolder verification - messages count: {len(messages)}")
        for i, msg in enumerate(messages):
            try:
                decoded = msg.decode('utf-8')
                logger.info(f"  [{i}] {decoded}")
            except:
                logger.info(f"  [{i}] <binary data: {len(msg)} bytes>")
                
        signature_valid = bbs_with_issuer_context.verify(issuer_pk, signature, messages, header)
        logger.info(f"Signature validation before proof generation: {signature_valid}")
        
        if not signature_valid:
            logger.error("Signature is invalid! Cannot generate valid proof.")
            # Test with the original signature object
            if hasattr(credential, 'signature') and credential.signature is not None:
                direct_valid = bbs_with_issuer_context.verify(issuer_pk, credential.signature, messages, header)
                logger.info(f"Direct signature validation (no serialization): {direct_valid}")
        
        # Generate ZK proof: proves knowledge of valid signature while
        # only revealing selected attributes
        proof = bbs_with_issuer_context.generate_proof(
            pk=issuer_pk,
            signature=signature,
            header=header,
            messages=messages,
            disclosed_indexes=disclosed_indices,
            presentation_header=presentation_header
        )
        
        logger.info(f"Created ZK presentation revealing {len(disclosed_indices)} of {len(messages)} attributes")
        
        return proof, disclosed_messages, disclosed_indices
    
    def list_credentials(self) -> List[DTCCredential]:
        """List all credentials in the holder's wallet"""
        return list(self.credentials.values())
    
    def get_credential(self, credential_id: str) -> Optional[DTCCredential]:
        """Get a specific credential by ID"""
        return self.credentials.get(credential_id)
    
    def get_credentials_by_type(self, doc_type: DocumentType) -> List[DTCCredential]:
        """Get all credentials of a specific document type"""
        return [cred for cred in self.credentials.values() 
                if cred.document_type == doc_type]
    
    def remove_credential(self, credential_id: str) -> bool:
        """Remove a credential from the wallet"""
        if credential_id in self.credentials:
            del self.credentials[credential_id]
            logger.info(f"Removed credential {credential_id}")
            return True
        return False
    
    def get_wallet_stats(self) -> Dict[str, Any]:
        """Get statistics about the credential wallet"""
        stats = {
            "total_credentials": len(self.credentials),
            "by_type": {},
            "valid_count": 0,
            "expired_count": 0,
            "revoked_count": 0
        }
        
        for cred in self.credentials.values():
            # Count by document type
            doc_type = cred.document_type.value
            stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1
            
            # Count by validity status
            if cred.revoked:
                stats["revoked_count"] += 1
            elif cred.is_valid():
                stats["valid_count"] += 1
            else:
                stats["expired_count"] += 1
        
        return stats
    
    def export_credentials_json(self) -> str:
        """Export all credentials to JSON format for backup/transfer"""
        export_data = {
            "holder_id": self.holder_id,
            "export_timestamp": datetime.now().isoformat(),
            "credentials": {}
        }
        
        for cred_id, cred in self.credentials.items():
            try:
                export_data["credentials"][cred_id] = json.loads(cred.to_json())
            except Exception as e:
                logger.error(f"Failed to export credential {cred_id}: {e}")
        
        return json.dumps(export_data, indent=2)
    
    def import_credentials_json(self, json_str: str) -> int:
        """Import credentials from JSON format"""
        try:
            data = json.loads(json_str)
            imported_count = 0
            
            for cred_id, cred_data in data.get("credentials", {}).items():
                # Reconstruct credential with BBS signature from JSON
                cred_json = json.dumps(cred_data)
                credential = DTCCredential.from_json(cred_json)
                
                # Store in wallet
                self.store_credential(cred_id, credential)
                imported_count += 1
            
            logger.info(f"Imported {imported_count} credentials")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import credentials: {e}")
            return 0
    
    def validate_credential_integrity(self, credential_id: str) -> Dict[str, Any]:
        """Validate the integrity of a stored credential"""
        if credential_id not in self.credentials:
            return {"valid": False, "error": "Credential not found"}
        
        credential = self.credentials[credential_id]
        results = {
            "valid": True,
            "checks": {}
        }
        
        # Check schema compliance
        schema_valid = credential.schema.validate_attributes(credential.attributes)
        results["checks"]["schema"] = schema_valid
        if not schema_valid:
            results["valid"] = False
        
        # Check expiry status
        not_expired = credential.is_valid()
        results["checks"]["not_expired"] = not_expired
        if not not_expired:
            results["valid"] = False
        
        # Check BBS signature presence
        has_signature = credential.signature_bytes is not None
        results["checks"]["has_signature"] = has_signature
        if not has_signature:
            results["valid"] = False
        
        return results
    
    def get_presentation_capabilities(self, credential_id: str) -> Dict[str, Any]:
        """
        Analyze what attributes can be selectively disclosed from a credential
        
        This helps understand the privacy options available for a given credential.
        """
        if credential_id not in self.credentials:
            return {"error": "Credential not found"}
        
        credential = self.credentials[credential_id]
        
        capabilities = {
            "credential_type": credential.document_type.value,
            "total_attributes": len(credential.attributes),
            "revealable_attributes": [],
            "hidden_attributes": [],
            "always_revealed": ["document_type", "issuer_id"]  # For verification context
        }
        
        # Categorize attributes by visibility options
        for name, attr in credential.attributes.items():
            if attr.hidden:
                capabilities["hidden_attributes"].append(name)
            else:
                capabilities["revealable_attributes"].append(name)
        
        return capabilities


def create_test_holder(holder_id: str = "test_holder") -> DTCHolder:
    """Create a DTCHolder for testing purposes"""
    return DTCHolder(holder_id)