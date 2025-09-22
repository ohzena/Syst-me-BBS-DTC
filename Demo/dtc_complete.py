#!/usr/bin/env python3
"""
dtc_complete.py - Complete Digital Travel Credentials Demonstration

Step-by-step demonstration of the complete BBS process for DTC:

1. Setup - System configuration
2. Key Generation - BBS keypair generation
3. Signature - Multi-message signing of attributes
4. Verification - Signature verification
5. Proof Generation - Zero-knowledge proof creation
6. Proof Verification - ZK proof validation

Uses Ellen Kampire profile by default, supports custom profiles from benchmark/data/custom/
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import BBS and DTC components
from DTC.bbs_core import BBSKeyGen, BBSSignatureScheme, BBSProofScheme, BBSWithProofs
from DTC.DTCIssuer import DTCIssuer
from DTC.DTCHolder import DTCHolder
from DTC.DTCVerifier import DTCVerifier

# Import benchmark data components
from benchmark.data.manager import DataManager
from benchmark.data.data_personalized import load_profile_for_benchmark

class StepByStepBBSDemo:
    """Step-by-step demonstration of the BBS process"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.current_scenario = None
        self.keys = None
        self.signature = None
        self.messages = None
        self.bbs_scheme = None
    
    def print_section(self, title: str):
        """Print section header"""
        line = "=" * 70
        print(f"\n{line}")
        print(f"{title:^70}")
        print(f"{line}\n")
    
    def print_step(self, step: int, title: str):
        """Print step header"""
        print(f"\n{'-' * 15} STEP {step}: {title} {'-' * 15}")
    
    def load_dtc_scenario(self, json_file: Optional[str] = None) -> Dict[str, Any]:
        """Load DTC scenario from custom profiles or use Ellen Kampire default"""
        
        if json_file:
            profile_data = load_profile_for_benchmark(json_file)
            scenario = self._convert_profile_to_scenario(profile_data)
            print(f"Scenario loaded from {json_file}")
            self.current_scenario = scenario
            return scenario
        
        # Try to load Ellen Kampire from custom profiles
        if not json_file:
            profile_data = load_profile_for_benchmark("ellen_kampire_dtc")
            scenario = self._convert_profile_to_scenario(profile_data)
            print("Ellen Kampire profile loaded from custom data")
            self.current_scenario = scenario
            return scenario
        
        # Fallback to Ellen Kampire hardcoded scenario
        default_scenario = {
            "name": "Ellen KAMPIRE - Default Travel Demo",
            "description": "Default credential demonstration with Ellen Kampire",
            "credential_holder": {
                "full_name": "Ellen KAMPIRE",
                "age": 32,
                "nationality": "Rwandan"
            },
            "attributes": [
                "passport_number", "full_name", "nationality", "birth_date",
                "expiry_date", "issuing_country", "document_type", "visa_status",
                "entry_date", "purpose_of_visit"
            ],
            "attribute_values": {
                "passport_number": "RW2024567890",
                "full_name": "Ellen KAMPIRE",
                "nationality": "Rwandan",
                "birth_date": "1992-07-15",
                "expiry_date": "2030-07-14",
                "issuing_country": "Rwanda",
                "document_type": "Passport",
                "visa_status": "Valid",
                "entry_date": "2024-09-01",
                "purpose_of_visit": "Tourism"
            },
            "disclosure_patterns": [
                {
                    "name": "Standard Border Control",
                    "disclosed": ["full_name", "nationality", "document_type", "visa_status", "purpose_of_visit"],
                    "hidden": ["passport_number", "birth_date", "expiry_date", "issuing_country", "entry_date"]
                }
            ]
        }
        
        print("Using Ellen KAMPIRE fallback scenario")
        #  Assigner self.current_scenario
        self.current_scenario = default_scenario
        return default_scenario

    
    def _convert_profile_to_scenario(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert benchmark profile format to demo scenario format"""
        
        #  Gérer les différents formats de profil
        if 'attributes' in profile_data and isinstance(profile_data['attributes'], list):
            # Format JSON avec liste d'attributs et metadata
            attributes = profile_data['attributes']
            attribute_metadata = profile_data.get('attribute_metadata', {})
            
            attribute_values = {}
            for attr in attributes:
                if attr in attribute_metadata:
                    attribute_values[attr] = attribute_metadata[attr].get('example_value', f"value_{attr}")
                else:
                    attribute_values[attr] = f"example_{attr}"
        
        elif 'base_messages' in profile_data:
            # Format benchmark avec base_messages
            base_messages = profile_data.get('base_messages', [])
            attributes = []
            attribute_values = {}
            
            for msg in base_messages:
                try:
                    msg_str = msg.decode('utf-8') if isinstance(msg, bytes) else str(msg)
                    if ':' in msg_str:
                        key, value = msg_str.split(':', 1)
                        attributes.append(key)
                        attribute_values[key] = value
                    else:
                        attributes.append(msg_str)
                        attribute_values[msg_str] = f"value_{msg_str}"
                except:
                    continue
        
        else:
            # Format inconnu, utiliser fallback
            attributes = ["full_name", "nationality", "document_type"]
            attribute_values = {
                "full_name": "Unknown User",
                "nationality": "Unknown",
                "document_type": "Passport"
            }
        
        # Get disclosure patterns
        disclosure_patterns = profile_data.get('disclosure_patterns', [])
        if not disclosure_patterns:
            # Create default pattern revealing 50%
            mid_point = len(attributes) // 2
            disclosure_patterns = [{
                "name": "Default 50% Disclosure",
                "disclosed": attributes[:mid_point],
                "hidden": attributes[mid_point:]
            }]
        
        #  Ajouter les infos du credential_holder
        credential_holder = profile_data.get('credential_holder', {})
        if not credential_holder and 'full_name' in attribute_values:
            credential_holder = {
                "full_name": attribute_values['full_name'],
                "nationality": attribute_values.get('nationality', 'Unknown')
            }
        
        return {
            "name": profile_data.get('name', 'Custom Profile'),
            "description": profile_data.get('description', 'Profile loaded from benchmark data'),
            "credential_holder": credential_holder,
            "attributes": attributes,
            "attribute_values": attribute_values,
            "disclosure_patterns": disclosure_patterns
        }

    def step_1_setup(self, scenario: Dict[str, Any]):
        """STEP 1: BBS System Setup"""
        
        self.print_step(1, "BBS SYSTEM SETUP")
        
        print("Configuring BBS signature system...")
        print("  Elliptic curve: BLS12-381 (128-bit security)")
        print("  Generators: G1, G2 and pairing e: G1 x G2 -> GT")
        
        max_messages = len(scenario['attributes'])
        
        self.bbs_scheme = BBSWithProofs(max_messages=max_messages)
        print(f"  BBSWithProofs initialized for {max_messages} messages maximum")
        
        # Display attributes that will be signed
        print("Credential attributes:")
        for i, attr in enumerate(scenario['attributes'], 1):
            value = scenario.get('attribute_values', {}).get(attr, f"<value_{i}>")
            print(f"   {i:2d}. {attr}: {value}")
        
        print("System setup completed")
        return True
    
    def step_2_keygen(self):
        """STEP 2: Key Generation"""
        
        self.print_step(2, "KEY GENERATION")
        
        print("Generating BBS keypair...")
        print("  Private key: x <- Zq (random scalar)")
        print("  Public key: X2 = g2^x (point on G2)")
        
        sk, pk = BBSKeyGen.generate_keypair()
        self.keys = {'private': sk, 'public': pk}
        print("Keypair generated successfully")
        print(f"  Private key: <BBSPrivateKey>")
        print(f"  Public key: <BBSPublicKey>")
        
        print("Key generation completed")
        return True
    
    def step_4_verification(self):
        """STEP 4: Signature Verification"""
        
        self.print_step(4, "SIGNATURE VERIFICATION")
        
        if not self.signature or not self.messages or not self.keys:
            print("Signature, messages or keys missing")
            return False
        
        header = b"DTC_credential_header"
        
        print("Verifying signature authenticity...")
        print("BBS verification:")
        print("  1. Recalculate C = g1 * ∏(hi^mi)")
        print("  2. Verify: e(A, X2 * g2^e) = e(C, g2)")
        
        start_time = time.time()
        is_valid = self.bbs_scheme.core_verify(
            self.keys['public'],
            self.signature,
            header,
            self.messages
        )
        verify_time = (time.time() - start_time) * 1000
        
        if is_valid:
            print(f"Signature VALID (verified in {verify_time:.2f}ms)")
            print("  Pairing verification: signature authentic")
        else:
            print("Signature INVALID")
            return False
        
        if is_valid:
            print("Verification completed successfully")
            return True
        return False
    

    def step_3_signature(self):
        """STEP 3: Message Signing"""
        
        self.print_step(3, "MESSAGE SIGNING")
        
        #  Vérifier les bonnes conditions
        if not self.current_scenario:
            print("Scenario missing")
            return False
            
        if not self.keys:
            print("Keys missing")
            return False
            
        if not self.bbs_scheme:
            print("BBS scheme not initialized")
            return False
        
        print("Preparing messages for BBS signing...")
        
        #  Préparer les messages depuis le scénario
        attributes = self.current_scenario.get('attributes', [])
        attribute_values = self.current_scenario.get('attribute_values', {})
        
        if not attributes:
            print("No attributes found in scenario")
            return False
        
        # Préparer les messages en bytes
        messages = []
        for attr in attributes:
            value = attribute_values.get(attr, f"default_value_{attr}")
            messages.append(str(value).encode('utf-8'))
        
        self.messages = messages
        
        print(f"Messages prepared: {len(messages)} attributes")
        print("BBS multi-message signing:")
        print("  1. Domain calculation: domain = H(PK, generators, header)")
        print("  2. Randomness: e <- Zq")
        print("  3. Commitment: B = g1 * Q1^domain * Π(Hi^mi)")
        print("  4. Signature: A = B^(1/(x+e))")
        
        header = b"DTC_credential_demo"
        
        # Use BBS scheme to sign messages
        start_time = time.time()
        
        # Try with BBSWithProofs first
        if hasattr(self.bbs_scheme, 'sign'):
            signature = self.bbs_scheme.sign(
                self.keys['private'], 
                messages, 
                header
            )
        # Fallback to BBSSignatureScheme
        elif hasattr(self.bbs_scheme, 'core_sign'):
            signature = self.bbs_scheme.core_sign(
                self.keys['private'], 
                header, 
                messages
            )
        else:
            raise AttributeError("No signing method available")
        
        sign_time = (time.time() - start_time) * 1000
        
        print(f"Signature generated in {sign_time:.2f}ms")
        print(f"  Signature: {type(signature).__name__}")
        
        # Signature size
        if hasattr(signature, 'to_bytes'):
            sig_bytes = signature.to_bytes()
            print(f"  Signature size: {len(sig_bytes)} bytes")
        
        self.signature = signature
        
        print("Message signing completed")
        return True

    #  Aussi corriger step_4_verification pour gérer les différents types
    def step_4_verification(self):
        """STEP 4: Signature Verification"""
        
        self.print_step(4, "SIGNATURE VERIFICATION")
        
        if not self.signature or not self.messages or not self.keys:
            print("Signature, messages, or keys missing")
            return False
        
        print("Verifying BBS signature...")
        print("BBS verification process:")
        print("  1. Recalculate C = g1 * Π(hi^mi)")
        print("  2. Verify: e(A, X2 * g2^e) = e(C, g2)")
        
        header = b"DTC_credential_demo"
        
        start_time = time.time()
        
        # Try with BBSWithProofs first
        if hasattr(self.bbs_scheme, 'verify'):
            is_valid = self.bbs_scheme.verify(
                self.keys['public'],
                self.signature,
                self.messages,
                header
            )
        # Fallback to BBSSignatureScheme
        elif hasattr(self.bbs_scheme, 'core_verify'):
            is_valid = self.bbs_scheme.core_verify(
                self.keys['public'],
                self.signature,
                header,
                self.messages
            )
        else:
            raise AttributeError("No verification method available")
        
        verify_time = (time.time() - start_time) * 1000
        
        if is_valid:
            print(f" Signature VALID (verified in {verify_time:.2f}ms)")
            print("  Pairing verification: signature authentic")
        else:
            print("✗ Signature INVALID")
            return False
        
        if is_valid:
            print("Verification completed successfully")
            return True
        return False

    def step_5_proof_generation(self):
        """STEP 5: Zero-Knowledge Proof Generation"""
        
        self.print_step(5, "ZERO-KNOWLEDGE PROOF GENERATION")
        
        if not self.current_scenario or not self.signature:
            print("Scenario or signature missing")
            return False
        
        disclosure_patterns = self.current_scenario.get('disclosure_patterns', [])
        
        if not disclosure_patterns:
            # Créer un pattern par défaut si aucun n'existe
            attributes = self.current_scenario.get('attributes', [])
            mid_point = len(attributes) // 2
            disclosure_pattern = {
                "name": "Default 50% Disclosure",
                "disclosed": attributes[:mid_point],
                "hidden": attributes[mid_point:]
            }
            print("Using default disclosure pattern (50% disclosure)")
        else:
            # Utiliser le premier pattern disponible
            disclosure_pattern = disclosure_patterns[0]
        
        disclosed_attrs = disclosure_pattern.get('disclosed', [])
        hidden_attrs = disclosure_pattern.get('hidden', [])
        
        # Si les listes sont vides, créer un pattern par défaut
        if not disclosed_attrs and not hidden_attrs:
            attributes = self.current_scenario.get('attributes', [])
            if attributes:
                mid_point = len(attributes) // 2
                disclosed_attrs = attributes[:mid_point]
                hidden_attrs = attributes[mid_point:]
                print("Generated default disclosure pattern from available attributes")
            else:
                print("No attributes available for disclosure")
                return False
        
        print(f"Disclosure pattern: {disclosure_pattern.get('name', 'Generated Pattern')}")
        print(f"Disclosed attributes ({len(disclosed_attrs)}): {', '.join(disclosed_attrs)}")
        print(f"Hidden attributes ({len(hidden_attrs)}): {', '.join(hidden_attrs)}")
        
        # Calculate indices of disclosed attributes
        disclosed_indices = []
        available_attributes = self.current_scenario.get('attributes', [])
        
        for attr in disclosed_attrs:
            if attr in available_attributes:
                idx = available_attributes.index(attr)
                disclosed_indices.append(idx)
            else:
                print(f"Warning: Disclosed attribute '{attr}' not found in available attributes")
        
        if not disclosed_indices:
            print("No valid disclosed attributes found")
            return False
        
        print("Zero-knowledge proof generation:")
        print("  1. Signature randomization")
        print("  2. Creating commitments for hidden attributes")
        print("  3. Generating proofs of knowledge")
        
        #  Utiliser les mêmes headers que step_3 et step_4
        header = b"DTC_credential_demo"
        presentation_header = b"presentation_to_verifier"
        
        #  Stocker les paramètres pour la vérification
        self.proof_header = header
        self.proof_presentation_header = presentation_header
        
        start_time = time.time()
        proof = self.bbs_scheme.generate_proof(
            pk=self.keys['public'],
            signature=self.signature,
            header=header,
            messages=self.messages,
            disclosed_indexes=disclosed_indices,
            presentation_header=presentation_header
        )
        proof_time = (time.time() - start_time) * 1000
        
        print(f" ZK proof generated in {proof_time:.2f}ms")
        print(f"  Proof: {type(proof).__name__}")
        
        # Proof size
        if hasattr(proof, 'to_bytes'):
            proof_bytes = proof.to_bytes()
            print(f"  Proof size: {len(proof_bytes)} bytes")
        
        self.proof = proof
        self.disclosed_indices = disclosed_indices
        
        print("Proof generation completed")
        return True

    #  step_6_proof_verification avec les mêmes paramètres
    def step_6_proof_verification(self):
        """STEP 6: Proof Verification"""
        
        self.print_step(6, "PROOF VERIFICATION")
        
        if not hasattr(self, 'proof') or not hasattr(self, 'disclosed_indices'):
            print("Proof or indices missing")
            return False
        
        # Prepare disclosed messages
        disclosed_messages = [self.messages[i] for i in self.disclosed_indices]
        
        print("Verifying proof by verifier...")
        print("ZK proof verification:")
        print("  1. Verifying cryptographic pairings")
        print("  2. Validating commitments")
        print("  3. Checking integrity of disclosed attributes")
        
        #  Utiliser les mêmes headers que step_5
        header = getattr(self, 'proof_header', b"DTC_credential_demo")
        presentation_header = getattr(self, 'proof_presentation_header', b"presentation_to_verifier")
        
        start_time = time.time()
        
        is_proof_valid = self.bbs_scheme.verify_proof(
            pk=self.keys['public'],
            proof=self.proof,
            header=header,
            disclosed_messages=disclosed_messages,
            disclosed_indexes=self.disclosed_indices,
            presentation_header=presentation_header
        )
        
        verify_time = (time.time() - start_time) * 1000
        
        if is_proof_valid:
            print(f"Proof VALID (verified in {verify_time:.2f}ms)")
            print("   Cryptographic integrity confirmed")
            print("   Disclosed attributes authenticated")
            print("   Hidden attributes remain private")
        else:
            print("Proof INVALID")
            print("  Debug info:")
            print(f"    Header: {header}")
            print(f"    Presentation header: {presentation_header}")
            print(f"    Disclosed indices: {self.disclosed_indices}")
            print(f"    Disclosed messages count: {len(disclosed_messages)}")
            return False
        
        if is_proof_valid:
            print(" Proof verification completed successfully")
            
            #  Final summary plus robuste
            print("\n TRANSACTION SUMMARY:")
            
            disclosure_patterns = self.current_scenario.get('disclosure_patterns', [])
            if disclosure_patterns:
                pattern = disclosure_patterns[0]
                disclosed_attrs = pattern.get('disclosed', [])
                hidden_attrs = pattern.get('hidden', [])
                
                print(f" Pattern used: {pattern.get('name', 'Unknown')}")
                print(f"  Disclosed attributes ({len(disclosed_attrs)}):")
                for attr in disclosed_attrs:
                    value = self.current_scenario.get('attribute_values', {}).get(attr, '<value>')
                    print(f"      {attr} = {value}")
                
                print(f" Hidden attributes ({len(hidden_attrs)}):")
                for attr in hidden_attrs:
                    print(f"      {attr} = <zero-knowledge proof only>")
                
                total_attrs = len(self.current_scenario.get('attributes', []))
                privacy_score = len(hidden_attrs) / total_attrs * 100 if total_attrs > 0 else 0
                print(f"\n  Privacy score: {privacy_score:.1f}% of attributes hidden")
                
                # Afficher les détails techniques
                print(f"\n Technical details:")
                print(f"     Total attributes: {total_attrs}")
                print(f"     Messages signed: {len(self.messages) if self.messages else 0}")
                print(f"     Disclosed indices: {self.disclosed_indices}")
            
            return True
        return False




    def run_complete_demo(self, json_file: Optional[str] = None):
        """Run complete demonstration"""
        
        self.print_section("COMPLETE BBS DIGITAL TRAVEL CREDENTIALS DEMONSTRATION")
        
        print("This demo shows each step of the BBS process:")
        print("   1. System setup")
        print("   2. Key generation")
        print("   3. Attribute signing")
        print("   4. Signature verification")
        print("   5. Zero-knowledge proof generation")
        print("   6. Proof verification")
        
        #  Load scenario et l'assigner
        scenario = self.load_dtc_scenario(json_file)
        if not scenario:
            print("Failed to load scenario")
            return False
        
        # Execute each step
        try:
            #  Passer scenario à step_1_setup
            if not self.step_1_setup(scenario):
                return False
            
            if not self.step_2_keygen():
                return False
            
            if not self.step_3_signature():
                return False
            
            if not self.step_4_verification():
                return False
            
            if not self.step_5_proof_generation():
                return False
            
            if not self.step_6_proof_verification():
                return False
            
            # Final success
            self.print_section("DEMONSTRATION COMPLETED SUCCESSFULLY")
            
            print("All BBS steps have been validated")
            print("DTC system functioning correctly")
            print("Selective disclosure operational")
            
            #  Afficher le résumé final
            holder_name = self.current_scenario.get('credential_holder', {}).get('full_name', 'Unknown')
            total_attrs = len(self.current_scenario.get('attributes', []))
            print(f"\n Demonstration completed for {holder_name}")
            print(f" Processed {total_attrs} attributes with BBS signatures")
            print(f" Privacy-preserving selective disclosure demonstrated")
            
            return True
            
        except Exception as e:
            print(f"Error during demonstration: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main entry point"""
    
    print("BBS Digital Travel Credentials Step-by-Step Demonstration")
    print("Uses Ellen Kampire profile by default, supports custom profiles from benchmark/data/custom/")
    
    # Check arguments
    import sys
    json_file = None
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        print(f"Using profile: {json_file}")
    else:
        print("Using Ellen KAMPIRE default profile")
        print("   Usage: python dtc_complete.py [profile.json]")
        print("   Examples:")
        print("     python dtc_complete.py ellen_kampire_dtc")
        print("     python dtc_complete.py custom_profile")
    
    # Run demonstration
    demo = StepByStepBBSDemo()
    success = demo.run_complete_demo(json_file)
    
    if success:
        print("\nDemonstration successful!")
        sys.exit(0)
    else:
        print("\nDemonstration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()