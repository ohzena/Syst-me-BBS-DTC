"""
Digital Trust Certificate (DTC) Verifier Implementation
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
import json
import logging

import sys
import os
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from DTC.bbs_core import (
    BBSSignatureScheme, BBSPrivateKey, BBSPublicKey, BBSSignature,
    BBSProofScheme, BBSProof, BBSWithProofs
)
BBS_AVAILABLE = True

from DTC.dtc import DTCCredential, DocumentType, AttributeType, DTC_VERSION, DTC_CONTEXT

logger = logging.getLogger(__name__)


class DTCVerifier:
    """Digital Trust Certificate Verifier"""
    
    def __init__(self, verifier_id: str):
        """Initialize verifier with BBS proof verification capabilities"""
        self.verifier_id = verifier_id
        self.trusted_issuers: Dict[str, Dict[str, Any]] = {}
        
        self.bbs = BBSWithProofs(max_messages=30)
        logger.info(f"BBS verification enabled for {verifier_id}")
        
        logger.info(f"Verifier {verifier_id} initialized")
    
    def add_trusted_issuer(self, issuer_id: str, public_key: Any, 
                          document_types: Optional[List[DocumentType]] = None):
        """Add a trusted issuer to the verifier"""
        self.trusted_issuers[issuer_id] = {
            "public_key": public_key,
            "document_types": document_types or list(DocumentType),
            "added_at": datetime.now()
        }
        
        logger.info(f"Added trusted issuer: {issuer_id}")
    
    def verify_presentation(self,
                           proof: Any,
                           disclosed_messages: List[bytes],
                           disclosed_indices: List[int],
                           presentation_header: bytes = b"",
                           issuer_id: str = None) -> Dict[str, Any]:
        """Verify presentation using zero-knowledge proof verification"""
        try:
            #  Validation plus robuste des paramètres d'entrée
            if not disclosed_messages or not disclosed_indices:
                return {
                    "valid": False,
                    "error": "Empty disclosed messages or indices"
                }
            
            if len(disclosed_messages) != len(disclosed_indices):
                return {
                    "valid": False,
                    "error": "Mismatch between messages and indices count"
                }
            
            # Recherche de l'issuer dans les messages révélés  
            extracted_issuer_id = None
            doc_type = None
            
            #  Méthode plus robuste pour extraire l'issuer
            for i, idx in enumerate(disclosed_indices):
                if i < len(disclosed_messages):
                    try:
                        msg = disclosed_messages[i].decode('utf-8')
                        
                        # Format: "attribute:value" ou juste "value"
                        if ':' in msg:
                            key, value = msg.split(':', 1)
                            if 'issuer' in key.lower():
                                extracted_issuer_id = value
                            elif 'document_type' in key.lower() or 'doc_type' in key.lower():
                                doc_type = value
                        else:
                            # Si c'est l'index 2, c'est probablement l'issuer par convention
                            if idx == 2 or 'issuer' in str(idx):
                                extracted_issuer_id = msg
                            elif idx == 1 or 'doc' in str(idx):
                                doc_type = msg
                                
                    except Exception as e:
                        logger.warning(f"Failed to parse message {i}: {e}")
                        continue
            
            # Use provided issuer_id or extract from messages
            final_issuer_id = issuer_id or extracted_issuer_id
            
            # Si on n'a pas trouvé l'issuer, chercher avec des heuristiques
            if not final_issuer_id:
                # Chercher un format connu d'issuer (contient souvent des underscores ou codes)
                for i, msg_bytes in enumerate(disclosed_messages):
                    try:
                        msg = msg_bytes.decode('utf-8')
                        if '_' in msg and msg.isupper():  # Format comme "FR_GOV_001"
                            final_issuer_id = msg
                            break
                    except:
                        continue
            
            if not final_issuer_id:
                return {
                    "valid": False,
                    "error": "Issuer information not found in disclosed messages"
                }
            
            # Vérifier que l'issuer est de confiance
            if final_issuer_id not in self.trusted_issuers:
                return {
                    "valid": False,
                    "error": f"Unknown or untrusted issuer: {final_issuer_id}"
                }
            
            issuer_info = self.trusted_issuers[final_issuer_id]
            issuer_pk = issuer_info["public_key"]
            
            # Initialize BBS with the same API_ID as used during signing and proof generation
            bbs_with_issuer_context = BBSWithProofs(max_messages=30, api_id=final_issuer_id.encode())
            
            #  Construire le header correctement
            if doc_type:
                header = f"{doc_type}:{final_issuer_id}".encode('utf-8')
            else:
                header = final_issuer_id.encode('utf-8')
            
            #  Vérification de la preuve BBS avec les bons paramètres
            try:
                logger.info(f"Verification attempt - Issuer: {final_issuer_id}")
                logger.info(f"Header: {header}")
                logger.info(f"Disclosed messages count: {len(disclosed_messages)}")
                logger.info(f"Disclosed indices: {disclosed_indices}")
                logger.info(f"Presentation header: {presentation_header}")
                
                # Vérifier la structure de la preuve
                logger.info(f"Proof type: {type(proof)}")
                if hasattr(proof, 'Abar'):
                    logger.info(f"Proof has Abar: {proof.Abar is not None}")
                if hasattr(proof, 'Bbar'):
                    logger.info(f"Proof has Bbar: {proof.Bbar is not None}")
                if hasattr(proof, 'D'):
                    logger.info(f"Proof has D: {proof.D is not None}")
                if hasattr(proof, 'e_hat'):
                    logger.info(f"Proof e_hat: {proof.e_hat}")
                
                # S'assurer que les attributs de proof ne sont pas None
                if hasattr(proof, 'e_hat') and proof.e_hat is None:
                    proof.e_hat = 1
                if hasattr(proof, 'r1_hat') and proof.r1_hat is None:
                    proof.r1_hat = 1  
                if hasattr(proof, 'r3_hat') and proof.r3_hat is None:
                    proof.r3_hat = 1
                if hasattr(proof, 'cp') and proof.cp is None:
                    proof.cp = 1
                if not hasattr(proof, 'commitments'):
                    proof.commitments = []
                
                is_valid = bbs_with_issuer_context.verify_proof(
                    pk=issuer_pk, 
                    proof=proof, 
                    header=header,
                    disclosed_messages=disclosed_messages, 
                    disclosed_indexes=disclosed_indices,
                    presentation_header=presentation_header
                )
                
                logger.info(f"BBS proof verification result: {is_valid}")
                    
            except Exception as e:
                logger.error(f"Proof verification failed: {e}")
                return {
                    "valid": False,
                    "error": f"Proof verification error: {e}"
                }
            
            if not is_valid:
                return {
                    "valid": False,
                    "error": "Zero-knowledge proof verification failed"
                }
            
            #  Extraction améliorée des attributs révélés
            revealed_attributes = {}
            for i, idx in enumerate(disclosed_indices):
                if i < len(disclosed_messages):
                    try:
                        msg = disclosed_messages[i].decode('utf-8')
                        if ':' in msg:
                            key, value = msg.split(':', 1)
                            # Nettoyer la clé si elle contient des préfixes
                            if ':' in key:
                                key = key.split(':')[-1]  # Prendre la dernière partie
                            revealed_attributes[key.strip()] = value.strip()
                        else:
                            # Utiliser un nom d'attribut basé sur l'index
                            revealed_attributes[f"attribute_{idx}"] = msg
                    except Exception as e:
                        logger.warning(f"Failed to parse message {i}: {e}")
                        revealed_attributes[f"raw_message_{i}"] = str(disclosed_messages[i])
            
            logger.info(f"Successfully verified presentation from {issuer_id}")
            
            return {
                "valid": True,
                "issuer": issuer_id,
                "document_type": doc_type,
                "revealed_attributes": revealed_attributes,
                "disclosed_count": len(disclosed_indices),
                "verification_timestamp": datetime.now().isoformat(),
                "verifier_id": self.verifier_id
            }
            
        except Exception as e:
            logger.error(f"Presentation verification failed: {e}")
            return {
                "valid": False,
                "error": f"Verification error: {e}",
                "verifier_id": self.verifier_id
            }
    
    def remove_trusted_issuer(self, issuer_id: str) -> bool:
        """Remove a trusted issuer"""
        if issuer_id in self.trusted_issuers:
            del self.trusted_issuers[issuer_id]
            logger.info(f"Removed trusted issuer: {issuer_id}")
            return True
        return False
    
    def get_trusted_issuers(self) -> List[str]:
        """Get list of all trusted issuer IDs"""
        return list(self.trusted_issuers.keys())
    
    def is_issuer_trusted(self, issuer_id: str, document_type: DocumentType = None) -> bool:
        """Check if an issuer is trusted for a specific document type"""
        if issuer_id not in self.trusted_issuers:
            return False
        
        if document_type is None:
            return True
        
        trusted_types = self.trusted_issuers[issuer_id]["document_types"]
        return document_type in trusted_types
    
    def validate_requirements(self, requirements: List[str], 
                            revealed_attributes: Dict[str, Any]) -> Dict[str, bool]:
        """Validate that revealed attributes meet specific requirements"""
        results = {}
        for req in requirements:
            #  Validation plus flexible des exigences
            found = False
            for attr_name in revealed_attributes.keys():
                if req.lower() in attr_name.lower() or attr_name.lower() in req.lower():
                    found = True
                    break
            results[req] = found
        
        return results
    
    def verify_with_policy(self, 
                          proof: Any,
                          disclosed_messages: List[bytes],
                          disclosed_indices: List[int],
                          policy: Dict[str, Any],
                          presentation_header: bytes = b"") -> Dict[str, Any]:
        """Verify presentation against a specific policy"""
        basic_result = self.verify_presentation(
            proof, disclosed_messages, disclosed_indices, presentation_header
        )
        
        if not basic_result["valid"]:
            return basic_result
        
        policy_results = {
            "basic_verification": True,
            "policy_compliance": True,
            "policy_checks": {}
        }
        
        revealed_attrs = basic_result.get("revealed_attributes", {})
        issuer = basic_result.get("issuer")
        doc_type = basic_result.get("document_type")
        
        #  Validation des attributs requis
        required_attrs = policy.get("required_attributes", [])
        if required_attrs:
            attr_check = self.validate_requirements(required_attrs, revealed_attrs)
            policy_results["policy_checks"]["required_attributes"] = attr_check
            
            if not all(attr_check.values()):
                policy_results["policy_compliance"] = False
        
        allowed_issuers = policy.get("allowed_issuers", [])
        if allowed_issuers and issuer not in allowed_issuers:
            policy_results["policy_checks"]["allowed_issuer"] = False
            policy_results["policy_compliance"] = False
        else:
            policy_results["policy_checks"]["allowed_issuer"] = True
        
        allowed_doc_types = policy.get("allowed_document_types", [])
        if allowed_doc_types and doc_type and doc_type not in allowed_doc_types:
            policy_results["policy_checks"]["allowed_document_type"] = False
            policy_results["policy_compliance"] = False
        else:
            policy_results["policy_checks"]["allowed_document_type"] = True
        
        # Combiner les résultats
        result = {**basic_result, **policy_results}
        result["valid"] = basic_result["valid"] and policy_results["policy_compliance"]
        
        return result
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get statistics about verifications performed"""
        return {
            "verifier_id": self.verifier_id,
            "trusted_issuers_count": len(self.trusted_issuers),
            "trusted_issuers": list(self.trusted_issuers.keys()),
            "bbs_available": BBS_AVAILABLE,
            "bbs_enabled": self.bbs is not None
        }
    
    def export_trusted_issuers(self) -> str:
        """Export trusted issuers configuration to JSON"""
        export_data = {
            "verifier_id": self.verifier_id,
            "export_timestamp": datetime.now().isoformat(),
            "trusted_issuers": {}
        }
        
        for issuer_id, data in self.trusted_issuers.items():
            pk_data = data["public_key"].to_base58()
            
            export_data["trusted_issuers"][issuer_id] = {
                "public_key": pk_data,
                "document_types": [dt.value for dt in data["document_types"]],
                "added_at": data["added_at"].isoformat()
            }
        
        return json.dumps(export_data, indent=2)
    
    def import_trusted_issuers(self, json_str: str) -> int:
        """Import trusted issuers from JSON configuration"""
        try:
            data = json.loads(json_str)
            imported_count = 0
            
            for issuer_id, issuer_data in data.get("trusted_issuers", {}).items():
                # Create public key from stored data
                pk_data = issuer_data.get("public_key")
                public_key = BBSPublicKey.from_base58(pk_data) if pk_data else None
                
                # Parse document types
                doc_types = []
                for dt in issuer_data.get("document_types", []):
                    if isinstance(dt, str):
                        doc_types.append(DocumentType(dt))
                    else:
                        doc_types.append(dt)
                
                self.add_trusted_issuer(issuer_id, public_key, doc_types)
                imported_count += 1
            
            logger.info(f"Imported {imported_count} trusted issuers")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import trusted issuers: {e}")
            return 0


def create_test_verifier(verifier_id: str = "test_verifier") -> DTCVerifier:
    """Create a DTCVerifier for testing purposes"""
    return DTCVerifier(verifier_id)

def create_border_control_verifier():
    """Create a verifier configured for border control use case"""
    verifier = DTCVerifier("Border Control Authority")
    return verifier

def create_airline_verifier():
    """Create a verifier configured for airline check-in use case"""
    verifier = DTCVerifier("Airline Check-in System")
    return verifier

def create_customs_verifier():
    """Create a verifier configured for customs control use case"""
    verifier = DTCVerifier("Customs Control Authority")
    return verifier

def create_hotel_verifier():
    """Create a verifier configured for hotel check-in use case"""
    verifier = DTCVerifier("Hotel Check-in System")
    return verifier