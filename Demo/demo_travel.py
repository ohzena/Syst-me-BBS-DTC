#!/usr/bin/env python3
"""
demo_travel.py - Travel Demonstration with BBS-based DTC

Demonstrates complete international travel journey using BBS signatures for
privacy-preserving credential verification. Shows how different travel contexts
require different attribute disclosures while maintaining unlinkability.

Key BBS Integration Features:
- Profile-based credential generation from JSON configurations
- Context-specific selective disclosure patterns
- Unlinkability demonstration across multiple checkpoints
- Privacy scoring based on hidden vs revealed attributes

The demo simulates:
1. Credential issuance with BBS signatures over attribute messages
2. Multiple verification checkpoints with varying disclosure requirements
3. Privacy analysis showing unlinkability between presentations
4. Travel scenario adaptation based on traveler profile
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pathlib import Path

from DTC.bbs_core import BBSKeyGen, BBSWithProofs, BBSProofScheme, BBSSignatureScheme
from DTC.DTCIssuer import DTCIssuer
from DTC.DTCHolder import DTCHolder
from DTC.DTCVerifier import DTCVerifier
from benchmark.data.manager import DataManager
from benchmark.data.data_personalized import ProfileAdapter

class TravelDemo:
    """Travel demonstration with BBS-based selective disclosure"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.traveler_profile = None
        self.travel_scenario = None
        self.credentials = {}
        self.verifications = []
    
    def load_traveler_profile(self, json_file: Optional[str] = None) -> Dict[str, Any]:
        """Load traveler profile from custom profiles or use Ellen Kampire default"""
        
        if json_file:
            try:
                # Use ProfileAdapter directly to get original JSON structure
                adapter = ProfileAdapter()
                profile_data = adapter.load_profile(json_file)
                print(f"Profile loaded: {profile_data.get('name', json_file)}")
                return profile_data
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
                print("Using Ellen Kampire default profile")
        
        # Try to load Ellen Kampire from custom profiles
        if not json_file:
            try:
                adapter = ProfileAdapter()
                profile_data = adapter.load_profile("ellen_kampire_dtc")
                print(f"Profile loaded: Ellen KAMPIRE (default)")
                return profile_data
            except Exception as e:
                print(f"Could not load Ellen Kampire profile: {e}")
        
        # Fallback to Ellen Kampire hardcoded profile
        ellen_profile = {
            "name": "Ellen KAMPIRE - Default Digital Travel Credential",
            "description": "Default credential for benchmarks and demos",
            "credential_holder": {
                "full_name": "Ellen KAMPIRE",
                "age": 32,
                "nationality": "Rwandan",
                "gender": "F"
            },
            "attributes": {
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
            "travel_itinerary": [
                {"country": "Rwanda", "city": "Kigali", "type": "departure"},
                {"country": "France", "city": "Paris", "type": "tourism"},
                {"country": "Rwanda", "city": "Kigali", "type": "return"}
            ]
        }
        
        print("Using Ellen KAMPIRE fallback profile")
        return ellen_profile
    
    
    def adapt_travel_scenario(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt travel scenario based on traveler profile"""
        
        holder = profile.get('credential_holder', {})
        attributes = profile.get('attributes', [])  # This is a list
        attribute_metadata = profile.get('attribute_metadata', {})
        
        # Analyze traveler type
        age = holder.get('age', 30)
        nationality = holder.get('nationality', 'French')
        
        # Get purpose of visit from metadata
        purpose_of_visit = ""
        if 'purpose_of_visit' in attribute_metadata:
            purpose_of_visit = attribute_metadata['purpose_of_visit'].get('example_value', '').lower()
        
        # Scenario adaptation based on profile
        if age < 18:
            # Minor travel with supervision requirements
            scenario = {
                "type": "supervised_minor_travel",
                "destinations": ["France", "Belgium", "Netherlands"],
                "supervision_required": True,
                "guardian_contact_needed": True,
                "restrictions": ["no_solo_travel", "limited_activities"]
            }
        elif "business" in purpose_of_visit:
            # Business travel scenario
            scenario = {
                "type": "business_travel", 
                "destinations": ["France", "Germany", "USA"],
                "fast_track_eligible": True,
                "corporate_guarantees": True,
                "meeting_verification_needed": True
            }
        elif "executive" in profile.get('description', '').lower():
            # Executive travel with VIP services
            scenario = {
                "type": "executive_travel",
                "destinations": ["Japan", "Germany", "USA"],
                "vip_services": True,
                "diplomatic_courtesies": False,
                "security_clearance": "business"
            }
        else:
            # Standard leisure travel
            scenario = {
                "type": "standard_travel",
                "destinations": ["France", "Spain", "Italy"],
                "tourist_activities": True,
                "budget_accommodations": True
            }
        
        scenario["traveler_profile"] = profile
        return scenario

    def setup_credentials(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Setup BBS-signed travel credentials from traveler profile"""
        
        print("Setting up BBS-signed travel credentials...")
        print(f"[DEBUG] Profile structure: {profile}")
        print(f"[DEBUG] Profile keys: {list(profile.keys()) if profile else 'None'}")
        
        # Handle different profile structures
        if 'attributes' in profile:
            print(f"[DEBUG] 'attributes' found in profile")
            print(f"[DEBUG] attributes type: {type(profile['attributes'])}")
            print(f"[DEBUG] attributes content: {profile['attributes']}")
            
            if isinstance(profile['attributes'], dict):
                # Format: {"attributes": {"key": "value", ...}}
                print("[DEBUG] Using dict format for attributes")
                attributes = list(profile['attributes'].keys())
                attribute_values = profile['attributes']
            elif isinstance(profile['attributes'], list):
                # Format: {"attributes": ["key1", "key2"], "attribute_metadata": {"key1": {"example_value": "value1"}}}
                print("[DEBUG] Using list format for attributes")
                attributes = profile['attributes']
                
                # Extract values from profile structure
                attribute_values = {}
                credential_holder = profile.get('credential_holder', {})
                attribute_metadata = profile.get('attribute_metadata', {})
                
                print(f"[DEBUG] credential_holder: {credential_holder}")
                print(f"[DEBUG] attribute_metadata: {attribute_metadata}")
                
                # Use example_value from metadata or credential_holder data
                for attr in attributes:
                    if attr in credential_holder:
                        attribute_values[attr] = credential_holder[attr]
                        print(f"[DEBUG] Using credential_holder for {attr}: {credential_holder[attr]}")
                    elif attr in attribute_metadata and 'example_value' in attribute_metadata[attr]:
                        attribute_values[attr] = attribute_metadata[attr]['example_value']
                        print(f"[DEBUG] Using example_value for {attr}: {attribute_metadata[attr]['example_value']}")
                    else:
                        # Fallback to profile's attribute_values if exists
                        fallback_values = profile.get('attribute_values', {
                            'full_name': 'Ellen KAMPIRE', 
                            'nationality': 'Rwandan', 
                            'passport_number': 'RW123456'
                        })
                        attribute_values[attr] = fallback_values.get(attr, f"value_{attr}")
                        print(f"[DEBUG] Using fallback for {attr}: {attribute_values[attr]}")
            else:
                # Fallback
                print("[DEBUG] attributes is neither dict nor list, using fallback")
                attributes = ['full_name', 'nationality', 'passport_number']
                attribute_values = {'full_name': 'Ellen KAMPIRE', 'nationality': 'Rwandan', 'passport_number': 'RW123456'}
        else:
            # No attributes found, use fallback
            print("[DEBUG] No 'attributes' key found in profile, using fallback")
            attributes = ['full_name', 'nationality', 'passport_number'] 
            attribute_values = {'full_name': 'Ellen KAMPIRE', 'nationality': 'Rwandan', 'passport_number': 'RW123456'}
        
        print(f"Attributes found: {len(attributes)}")
        for attr in attributes:
            value = attribute_values.get(attr, f"value_{attr}")
            print(f"   {attr}: {value}")
        
        # Generate BBS keypair for issuing authority
        gov_sk, gov_pk = BBSKeyGen.generate_keypair()
        
        # Use BBSWithProofs for complete BBS functionality
        bbs_scheme = BBSWithProofs(max_messages=len(attributes))

        # Prepare attribute messages for BBS signing
        messages = []
        for attr in attributes:
            value = attribute_values.get(attr, f"value_{attr}")
            messages.append(str(value).encode('utf-8'))
        
        # Sign credential with BBS
        header = b"travel_credential_demo"
        signature = bbs_scheme.sign(gov_sk, messages, header)
        
        credentials = {
            'profile': {'attributes': attribute_values},
            'attributes': attributes,
            'messages': messages,
            'signature': signature,
            'bbs_scheme': bbs_scheme,
            'header': header,
            'issuer_keys': {'private': gov_sk, 'public': gov_pk}
        }
        
        print("BBS credentials generated successfully")
        return credentials    

    def demonstrate_verification(self, context: str, required_attrs: List[str], 
                               optional_attrs: List[str] = None) -> Dict[str, Any]:
        """Demonstrate BBS proof verification in specific context"""
        
        if not self.credentials:
            return {'success': False, 'error': 'No credentials'}
        
        optional_attrs = optional_attrs or []
        profile = self.credentials['profile']
        
        print(f"\nVerification required for: {context}")
        
        # Determine which attributes to reveal through selective disclosure
        available_attrs = set(self.credentials['attributes'])
        disclosed = []
        
        # Add required attributes that are available
        for attr in required_attrs:
            if attr in available_attrs:
                disclosed.append(attr)
            else:
                print(f"Required attribute '{attr}' not available")
        
        # Add some optional attributes for context
        for attr in optional_attrs:
            if attr in available_attrs and len(disclosed) < len(available_attrs) * 0.6:
                disclosed.append(attr)
        
        hidden = [attr for attr in self.credentials['attributes'] if attr not in disclosed]
        
        # Display disclosure pattern
        print(f"REVEALED attributes for {context} ({len(disclosed)}):")
        for attr in disclosed:
            value = profile['attributes'][attr]
            print(f"   {attr}: {value}")
        
        print(f"HIDDEN attributes (zero-knowledge) ({len(hidden)}):")
        for attr in hidden:
            print(f"   {attr}: <cryptographically hidden>")
        
        # Generate and verify BBS proof
        disclosed_indices = [self.credentials['attributes'].index(attr) for attr in disclosed]
        
        # Use BBSWithProofs high-level methods
        presentation_header = f"{context}_presentation".encode('utf-8')
        
        # Generate BBS proof for selective disclosure
        proof = self.credentials['bbs_scheme'].generate_proof(
            pk=self.credentials['issuer_keys']['public'],
            signature=self.credentials['signature'],
            header=self.credentials['header'],
            messages=self.credentials['messages'],
            disclosed_indexes=disclosed_indices,
            presentation_header=presentation_header
        )
        
        # Verify BBS proof
        disclosed_messages = [self.credentials['messages'][i] for i in disclosed_indices]
        is_valid = self.credentials['bbs_scheme'].verify_proof(
            pk=self.credentials['issuer_keys']['public'],
            proof=proof,
            header=self.credentials['header'],
            disclosed_messages=disclosed_messages,
            disclosed_indexes=disclosed_indices,
            presentation_header=presentation_header
        )
        
        if is_valid:
            print(f"Verification {context} SUCCESSFUL")
            privacy_score = len(hidden) / len(self.credentials['attributes']) * 100
            print(f"Privacy preserved: {privacy_score:.0f}%")
        else:
            print(f"✗ Verification {context} FAILED")
            return {'success': False, 'context': context}
        
        privacy_score = len(hidden) / len(self.credentials['attributes']) * 100
        
        verification_result = {
            'success': is_valid,
            'context': context,
            'disclosed_attributes': disclosed,
            'hidden_attributes': hidden,
            'privacy_score': privacy_score,
            'timestamp': datetime.now().isoformat()
        }
        
        self.verifications.append(verification_result)
        return verification_result
    
    def demonstrate_unlinkability(self):
        """Demonstrate unlinkability between BBS presentations"""
        
        print("\n=== UNLINKABILITY DEMONSTRATION ===")
        
        if len(self.verifications) < 2:
            print("Not enough verifications to demonstrate unlinkability")
            return 50.0
        
        print("Analyzing correlation between verifications...")
        
        print(f"Verifications performed: {len(self.verifications)}")
        
        for i, verif in enumerate(self.verifications, 1):
            print(f"   {i}. {verif['context']}: {len(verif['disclosed_attributes'])} attributes revealed")
        
        # Analyze disclosure patterns for unlinkability
        all_disclosed = set()
        context_patterns = {}
        
        for verif in self.verifications:
            context = verif['context']
            disclosed = set(verif['disclosed_attributes'])
            all_disclosed.update(disclosed)
            context_patterns[context] = disclosed
        
        # Calculate unlinkability score
        unique_combinations = len(set(tuple(sorted(pattern)) for pattern in context_patterns.values()))
        total_verifications = len(self.verifications)
        
        unlinkability_score = (unique_combinations / total_verifications) * 100
        
        print(f"\nUnlinkability analysis:")
        print(f"   - Unique disclosure patterns: {unique_combinations}")
        print(f"   - Total verifications: {total_verifications}")
        print(f"   - Unlinkability score: {unlinkability_score:.0f}%")
        
        if unlinkability_score >= 80:
            print("EXCELLENT unlinkability - Correlation very difficult")
        elif unlinkability_score >= 60:
            print("GOOD unlinkability - Correlation complicated")
        else:
            print(" Limited unlinkability - Correlation possible")
        
        # Technical demonstration
        print("\nBBS technical properties:")
        print("   - Each proof uses fresh randomization")
        print("   - Proofs are zero-knowledge")
        print("   - Correlation impossible without disclosed attributes")
        print("   - Original signature remains hidden")
        
        return unlinkability_score
    
    def run_travel_journey(self, profile: Dict[str, Any]):
        """Simulate complete travel journey with BBS verifications"""
        
        traveler_name = profile.get('credential_holder', {}).get('full_name', 'Unknown Traveler')
        print(f"\n=== TRAVEL JOURNEY: {traveler_name} ===")
        
        # Adapt scenario based on profile
        scenario = self.adapt_travel_scenario(profile)
        
        print(f"Travel type: {scenario['type']}")
        print(f"Destinations: {', '.join(scenario['destinations'])}")
        
        # Define journey steps based on scenario type
        journey_steps = []
        
        if scenario['type'] == 'supervised_minor_travel':
            journey_steps = [
                ("School verification", ["full_name"], ["nationality"]),
                ("Minor border control", ["full_name", "nationality", "birth_date"], []),
                ("Group accommodation check-in", ["full_name"], ["entry_date"]),
                ("Return verification", ["full_name"], ["expiry_date"])
            ]
        
        elif scenario['type'] == 'business_travel':
            journey_steps = [
                ("Business flight check-in", ["full_name"], ["purpose_of_visit"]),
                ("Business border control", ["full_name", "nationality", "visa_status"], []),
                ("Business hotel verification", ["full_name"], ["document_type"]),
                ("Customs control", ["full_name", "purpose_of_visit"], []),
                ("Corporate security check", ["full_name", "purpose_of_visit"], [])
            ]
        
        elif scenario['type'] == 'executive_travel':
            journey_steps = [
                ("Executive fast track", ["full_name"], []),
                ("VIP border control", ["full_name", "nationality"], []),
                ("Premium hotel check-in", ["full_name"], ["document_type"]),
                ("Business meeting", ["full_name"], ["purpose_of_visit"]),
                ("Express departure", ["full_name"], [])
            ]
        
        else:  # standard_travel
            journey_steps = [
                ("Flight registration", ["full_name", "nationality"], []),
                ("Border control", ["full_name", "nationality", "visa_status"], ["purpose_of_visit"]),
                ("Hotel check-in", ["full_name"], ["entry_date"]),
                ("Return customs control", ["full_name", "nationality"], [])
            ]
        
        # Execute each step with BBS verification
        for i, (step_name, required, optional) in enumerate(journey_steps, 1):
            print(f"\n--- STEP {i}: {step_name} ---")
            
            verification = self.demonstrate_verification(step_name, required, optional)
            
            if verification['success']:
                print(f"Step {step_name} validated successfully")
            else:
                print(f"✗ Problem at step {step_name}")
                return False
        
        return True
    
    def generate_journey_report(self):
        """Generate travel report with privacy metrics"""
        
        print("\n=== TRAVEL REPORT ===")
        
        if not self.verifications:
            print("No verifications to analyze")
            return {}
        
        # General statistics
        total_verifications = len(self.verifications)
        successful_verifications = sum(1 for v in self.verifications if v['success'])
        avg_privacy = sum(v['privacy_score'] for v in self.verifications) / total_verifications
        
        print(f"Travel statistics:")
        print(f"   - Total verifications: {total_verifications}")
        print(f"   - Successful verifications: {successful_verifications}")
        print(f"   - Success rate: {(successful_verifications/total_verifications)*100:.0f}%")
        print(f"   - Average privacy: {avg_privacy:.0f}%")
        
        # Attribute analysis
        all_disclosed = set()
        disclosure_frequency = {}
        
        for verif in self.verifications:
            for attr in verif['disclosed_attributes']:
                all_disclosed.add(attr)
                disclosure_frequency[attr] = disclosure_frequency.get(attr, 0) + 1
        
        print(f"\nDisclosure analysis:")
        print(f"   - Unique attributes disclosed: {len(all_disclosed)}")
        print(f"   - Total available attributes: {len(self.credentials['attributes'])}")
        
        # Most frequently requested attributes
        sorted_attrs = sorted(disclosure_frequency.items(), key=lambda x: x[1], reverse=True)
        print(f"\nMost requested attributes:")
        for attr, count in sorted_attrs[:5]:
            percentage = (count / total_verifications) * 100
            print(f"   - {attr}: {count} times ({percentage:.0f}%)")
        
        # Privacy evaluation
        if avg_privacy >= 70:
            print("EXCELLENT privacy protection")
        elif avg_privacy >= 50:
            print("GOOD privacy protection")
        else:
            print("Privacy protection could be improved")
        
        return {
            'total_verifications': total_verifications,
            'success_rate': (successful_verifications/total_verifications)*100,
            'avg_privacy_score': avg_privacy,
            'unique_attributes_disclosed': len(all_disclosed),
            'most_requested_attributes': sorted_attrs[:5]
        }
    
    def run_complete_travel_demo(self, json_file: Optional[str] = None):
        """Run complete travel demonstration with BBS"""
        
        print("=== DIGITAL TRAVEL CREDENTIALS TRAVEL DEMONSTRATION ===")
        print(f"[DEBUG] json_file parameter: {json_file}")
        
        # Load traveler profile
        profile = self.load_traveler_profile(json_file)
        print(f"[DEBUG] Profile loaded from load_traveler_profile: {profile}")
        self.traveler_profile = profile
        
        # Setup BBS credentials
        self.credentials = self.setup_credentials(profile)
        
        # Simulate travel journey
        success = self.run_travel_journey(profile)
        
        if not success:
            print("Travel interrupted")
            return False
        
        # Demonstrate unlinkability
        unlinkability_score = self.demonstrate_unlinkability()
        
        # Generate report
        report = self.generate_journey_report()
        
        if not report:
            return False
        
        # Final summary
        print("\n=== TRAVEL COMPLETED SUCCESSFULLY ===")
        
        traveler_name = profile.get('credential_holder', {}).get('full_name', 'Unknown Traveler')
        print(f"Travel by {traveler_name} completed")
        print(f"Privacy preserved: {report['avg_privacy_score']:.0f}% on average")
        print(f"Unlinkability: {unlinkability_score:.0f}%")
        print(f"Successful verifications: {report['success_rate']:.0f}%")
        
        print(f"\nDemonstrated benefits:")
        print("   - Selective disclosure by context")
        print("   - Unlinkability between verifications")
        print("   - Privacy by design")
        print("   - Ease of use for traveler")
        
        return True

def main():
    """Main entry point"""
    
    print("Travel Demonstration with Digital Travel Credentials")
    print("Realistic simulation with BBS-based selective disclosure\n")
    
    # Check arguments
    json_file = None
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        print(f"Using profile: {json_file}")
    else:
        print("Using Ellen KAMPIRE default profile")
        print("   Usage: python demo_travel.py [profile.json]")
        print("   Examples:")
        print("     python demo_travel.py ellen_kampire_dtc")
        print("     python demo_travel.py custom_profile")
    
    # Run demonstration
    demo = TravelDemo()
    success = demo.run_complete_travel_demo(json_file)
    
    if success:
        print("\nTravel demonstration successful!")
        sys.exit(0)
    else:
        print("\n❌ Travel demonstration failed!")
        sys.exit(1)

def run_with_profile(profile_path: str = None):
    """Entry point for benchmark runner with explicit profile path"""
    
    print("Travel Demonstration with Digital Travel Credentials")
    print("Realistic simulation with BBS-based selective disclosure\n")
    
    if profile_path:
        print(f"Using profile: {profile_path}")
    else:
        print("Using Ellen KAMPIRE default profile")
    
    # Run demonstration
    demo = TravelDemo()
    success = demo.run_complete_travel_demo(profile_path)
    
    return success

# Standalone functions for main.py compatibility
def demo_complete_travel_flow(json_file: Optional[str] = None) -> bool:
    """Standalone function for main.py to run complete travel demo with Ellen Kampire default"""
    demo = TravelDemo()
    return demo.run_complete_travel_demo(json_file or "ellen_kampire_dtc")

def demo_selective_disclosure_comparison() -> bool:
    """Demonstrate selective disclosure comparison using Ellen Kampire profile"""
    demo = TravelDemo()
    
    print("\nSELECTIVE DISCLOSURE COMPARISON")
    print("Demonstration with different disclosure levels using Ellen KAMPIRE profile\n")
    
    # Load Ellen Kampire profile first
    demo.traveler_profile = demo.load_traveler_profile("ellen_kampire_dtc")
    demo.credentials = demo.setup_credentials(demo.traveler_profile)
    
    # Test different disclosure levels
    scenarios = [
        ("Minimal verification", ["full_name"]),
        ("Standard verification", ["full_name", "nationality"]),
        ("Complete verification", ["full_name", "nationality", "birth_date", "visa_status"])
    ]
    
    success = True
    for scenario_name, required_attrs in scenarios:
        print(f"{scenario_name}:")
        try:
            verification = demo.demonstrate_verification(scenario_name, required_attrs, [])
            if verification['success']:
                privacy_score = verification['privacy_score']
                print(f"   Success - Privacy: {privacy_score}%")
            else:
                print(f"   ❌ Failed")
                success = False
        except Exception as e:
            print(f"   ⚠️ Simulation error: {str(e)}")
            success = False
    
    return success

if __name__ == "__main__":
    main()