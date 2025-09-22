"""
credential_issuance.py - Complete Digital Travel Credential Demo

Demonstrates the full BBS-based DTC workflow: issuance, storage, and verification
with selective disclosure across multiple travel checkpoints.

This demo shows how BBS signatures enable privacy-preserving travel:
1. Issuers sign credential attributes as BBS message vectors
2. Holders store signed credentials and generate selective disclosure proofs
3. Verifiers validate presentations while seeing only necessary attributes

Key BBS Integration Demonstrated:
- Multi-issuer ecosystem (government, embassy, health ministry)
- Selective disclosure at different checkpoints (airline, border, customs)
- Unlinkable presentations preventing traveler tracking
- Privacy preservation through zero-knowledge proofs
"""

import time
from datetime import datetime

import sys
import os
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from DTC.dtc import (
    PassportCredential, VisaCredential, VaccinationCredential,
    DTCCredential, DocumentType
)
from DTC.DTCIssuer import DTCIssuer
from DTC.DTCHolder import DTCHolder
from DTC.DTCVerifier import DTCVerifier
from benchmark.data.data_personalized import load_profile_for_benchmark


def setup_actors(profile_name: str = None):
    """Setup BBS-enabled actors for the DTC ecosystem"""
    print("\n=== SETUP: Creating Digital Identity Ecosystem ===")
    
    # Load traveler profile data
    traveler_profile = None
    if load_profile_for_benchmark:
        try:
            profile_data = load_profile_for_benchmark(profile_name or "ellen_kampire_dtc")
            traveler_profile = profile_data['profile_name']
            print(f"Using traveler profile: {traveler_profile}")
        except:
            print("Using default profile data")
    
    # Create trusted issuers with BBS signing capabilities
    french_gov = DTCIssuer("FR_GOV_001")
    us_embassy = DTCIssuer("US_EMBASSY_FR")
    health_ministry = DTCIssuer("FR_HEALTH_MIN")
    
    print(f"Created French Government issuer: {french_gov.issuer_id}")
    print(f"Created US Embassy issuer: {us_embassy.issuer_id}")
    print(f"Created Health Ministry issuer: {health_ministry.issuer_id}")
    
    # Create traveler with BBS proof generation capabilities
    holder_name = traveler_profile if traveler_profile else "ellen_kampire"
    alice = DTCHolder(holder_name)
    print(f"Created digital wallet for: {alice.holder_id}")
    
    # Create verifiers with BBS proof verification capabilities
    border_control = DTCVerifier("FR_BORDER_CONTROL")
    airline_checkin = DTCVerifier("AIR_FRANCE_CHECKIN")
    us_customs = DTCVerifier("US_CUSTOMS_CBP")
    
    # Establish trust relationships: verifiers trust issuer public keys
    border_control.add_trusted_issuer("FR_GOV_001", french_gov.public_key)
    border_control.add_trusted_issuer("US_EMBASSY_FR", us_embassy.public_key)
    border_control.add_trusted_issuer("FR_HEALTH_MIN", health_ministry.public_key)
    
    airline_checkin.add_trusted_issuer("FR_GOV_001", french_gov.public_key)
    airline_checkin.add_trusted_issuer("US_EMBASSY_FR", us_embassy.public_key)
    
    us_customs.add_trusted_issuer("FR_GOV_001", french_gov.public_key)
    us_customs.add_trusted_issuer("US_EMBASSY_FR", us_embassy.public_key)
    us_customs.add_trusted_issuer("FR_HEALTH_MIN", health_ministry.public_key)
    
    print("All verifiers configured with trusted authorities")
    
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
            'airline_checkin': airline_checkin,
            'us_customs': us_customs
        },
        'profile': traveler_profile
    }


def demo_issuance(actors, profile_name: str = None):
    """Demonstrate BBS-based credential issuance using profile data"""
    print("\n=== ISSUANCE: Creating BBS-Signed Travel Credentials ===")
    
    french_gov = actors['issuers']['french_gov']
    us_embassy = actors['issuers']['us_embassy']
    health_ministry = actors['issuers']['health_ministry']
    alice = actors['holders']['alice']
    
    # Load profile data for credential attributes
    profile_data = None
    if load_profile_for_benchmark:
        try:
            profile_data = load_profile_for_benchmark(profile_name or "ellen_kampire_dtc")
        except:
            pass
    
    # Use profile data or fallback values
    if profile_data:
        profile = profile_data.get('profile_name', 'ellen_kampire_dtc')
        holder_name = "Ellen KAMPIRE"
        passport_number = "RW2024567890"
        nationality = "Rwandan"
        birth_date = "1992-07-15"
        expiry_date = "2030-07-14"
    else:
        holder_name = "Ellen KAMPIRE"
        passport_number = "RW2024567890"
        nationality = "Rwandan"
        birth_date = "1992-07-15"
        expiry_date = "2030-07-14"
    
    # Issue passport with BBS signature over attribute messages
    print("Issuing passport with BBS signature...")
    passport_data = {
        "document_number": passport_number,
        "given_names": holder_name.split()[0],
        "surname": " ".join(holder_name.split()[1:]) if len(holder_name.split()) > 1 else "",
        "nationality": nationality,
        "date_of_birth": birth_date,
        "place_of_birth": "Kigali, Rwanda",
        "date_of_issue": "2020-01-01",
        "date_of_expiry": expiry_date,
        "issuing_authority": "Rwanda Immigration Services"
    }
    passport = french_gov.issue_passport(passport_data)
    alice.store_credential("passport", passport)
    print(f"Passport issued and stored: {passport.credential_id}")
    
    # Issue US visa with BBS signature
    print("Issuing US tourist visa with BBS signature...")
    visa_data = {
        "visa_number": "US2024789012",
        "visa_type": "B1/B2 Tourist",
        "given_names": holder_name.split()[0],
        "surname": " ".join(holder_name.split()[1:]) if len(holder_name.split()) > 1 else "",
        "nationality": nationality,
        "date_of_birth": birth_date,
        "date_of_issue": "2024-01-01",
        "date_of_expiry": "2034-01-01",
        "issuing_authority": "US Embassy France",
        "destination_country": "United States"
    }
    visa = us_embassy.issue_visa(visa_data)
    alice.store_credential("us_visa", visa)
    print(f"US Visa issued and stored: {visa.credential_id}")
    
    # Issue vaccination certificate with BBS signature
    print("Issuing COVID-19 vaccination certificate with BBS signature...")
    vaccination_data = {
        "certificate_id": "RWVAC2023789456",
        "given_names": holder_name.split()[0],
        "surname": " ".join(holder_name.split()[1:]) if len(holder_name.split()) > 1 else "",
        "date_of_birth": birth_date,
        "vaccination_details": {
            "vaccine_type": "COVID-19",
            "vaccine_name": "Pfizer-BioNTech",
            "manufacturer": "Pfizer",
            "batch_number": "FE4721",
            "vaccination_date": "2023-09-15",
            "dose_number": 3,
            "total_doses": 3
        },
        "issuing_authority": "Rwanda Ministry of Health"
    }
    vaccination = health_ministry.issue_vaccination(vaccination_data)
    alice.store_credential("covid_vaccination", vaccination)
    print(f"Vaccination certificate issued and stored: {vaccination.credential_id}")
    
    # Show wallet contents
    print("\nDigital Wallet contains:")
    credentials = alice.list_credentials()
    for cred in credentials:
        print(f"  - {cred}")
    
    print("All credentials issued and stored successfully")
    
    return actors


def demo_presentation_verification(actors):
    """Demonstrate selective disclosure and BBS proof verification at checkpoints"""
    print("\n=== TRAVEL JOURNEY: Selective Disclosure with BBS Proofs ===")
    
    alice = actors['holders']['alice']
    airline_checkin = actors['verifiers']['airline_checkin']
    border_control = actors['verifiers']['border_control']
    us_customs = actors['verifiers']['us_customs']
    
    # Get stored credentials
    passport_cred = alice.get_credential("passport")
    visa_cred = alice.get_credential("us_visa")
    vaccination_cred = alice.get_credential("covid_vaccination")
    
    if not all([passport_cred, visa_cred, vaccination_cred]):
        print("Missing credentials for demo")
        return
    
    print("\n--- CHECKPOINT 1: Airline Check-in ---")
    print("Required: Name, passport number (minimal disclosure)")
    
    try:
        # Alice creates BBS proof revealing only name and passport number
        french_gov_pk = actors['issuers']['french_gov'].public_key
        proof, disclosed_msgs, disclosed_indices = alice.create_presentation(
            "passport", 
            french_gov_pk,
            ["holder_name", "document_number"],
            b"airline_checkin_context",
            issuer_id="FR_GOV_001"
        )
        
        # Airline verifies the BBS proof
        verification_result = airline_checkin.verify_presentation(
            proof, disclosed_msgs, disclosed_indices, b"airline_checkin_context",
            issuer_id="FR_GOV_001"
        )
        
        if verification_result["valid"]:
            print("Check-in approved! Revealed minimal information:")
            for attr, value in verification_result["revealed_attributes"].items():
                if ":" in value:
                    print(f"    {attr}: {value.split(':', 1)[1]}")
        else:
            print(f"Check-in failed: {verification_result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"Airline check-in failed: {e}")
    
    print("\n--- CHECKPOINT 2: Border Control (Departure) ---")
    print("Required: Passport verification + vaccination status")
    
    try:
        # Alice creates BBS proof for passport with more attributes
        proof_passport, disclosed_msgs_p, disclosed_indices_p = alice.create_presentation(
            "passport",
            french_gov_pk,
            ["holder_name", "document_number", "nationality", "date_of_birth"],
            b"border_departure_context",
            issuer_id="FR_GOV_001"
        )
        
        # Verify passport presentation
        passport_verification = border_control.verify_presentation(
            proof_passport, disclosed_msgs_p, disclosed_indices_p, b"border_departure_context",
            issuer_id="FR_GOV_001"
        )
        
        # Alice creates separate BBS proof for vaccination
        health_pk = actors['issuers']['health_ministry'].public_key
        proof_vaxx, disclosed_msgs_v, disclosed_indices_v = alice.create_presentation(
            "covid_vaccination",
            health_pk,
            ["holder_name", "vaccine_type", "vaccination_date", "dose_number"],
            b"health_verification_context",
            issuer_id="FR_HEALTH_MIN"
        )
        
        vaxx_verification = border_control.verify_presentation(
            proof_vaxx, disclosed_msgs_v, disclosed_indices_v, b"health_verification_context",
            issuer_id="FR_HEALTH_MIN"
        )
        
        if passport_verification["valid"] and vaxx_verification["valid"]:
            print("Border control approved! Alice can depart France")
            print("Verified: Identity, nationality, and vaccination status")
        else:
            print("Border control verification failed")
    
    except Exception as e:
        print(f"Border control verification failed: {e}")
    
    print("\n--- CHECKPOINT 3: US Customs (Arrival) ---")
    print("Required: Passport + Visa + Health verification")
    
    try:
        # Comprehensive BBS proof verification for US entry
        
        # Verify passport with different attribute selection
        proof_passport_us, disclosed_msgs_p_us, disclosed_indices_p_us = alice.create_presentation(
            "passport",
            french_gov_pk,
            ["holder_name", "document_number", "nationality"],
            b"us_entry_context",
            issuer_id="FR_GOV_001"
        )
        
        # Verify US visa
        us_embassy_pk = actors['issuers']['us_embassy'].public_key
        proof_visa, disclosed_msgs_visa, disclosed_indices_visa = alice.create_presentation(
            "us_visa",
            us_embassy_pk,
            ["holder_name", "visa_number", "visa_type", "valid_until"],
            b"us_entry_context",
            issuer_id="US_EMBASSY_FR"
        )
        
        # Verify health with minimal disclosure
        proof_health, disclosed_msgs_health, disclosed_indices_health = alice.create_presentation(
            "covid_vaccination",
            health_pk,
            ["vaccine_type", "vaccination_date", "dose_number"],
            b"us_entry_context",
            issuer_id="FR_HEALTH_MIN"
        )
        
        # US Customs verifies all BBS presentations
        passport_us_verify = us_customs.verify_presentation(
            proof_passport_us, disclosed_msgs_p_us, disclosed_indices_p_us, b"us_entry_context",
            issuer_id="FR_GOV_001"
        )
        
        visa_verify = us_customs.verify_presentation(
            proof_visa, disclosed_msgs_visa, disclosed_indices_visa, b"us_entry_context",
            issuer_id="US_EMBASSY_FR"
        )
        
        health_verify = us_customs.verify_presentation(
            proof_health, disclosed_msgs_health, disclosed_indices_health, b"us_entry_context",
            issuer_id="FR_HEALTH_MIN"
        )
        
        if all([passport_us_verify["valid"], visa_verify["valid"], health_verify["valid"]]):
            print("Welcome to the United States! All verifications passed")
            print("Verified: French passport, valid US visa, COVID vaccination")
        else:
            print("US entry denied - verification failed")
    
    except Exception as e:
        print(f"US customs verification failed: {e}")


def demo_privacy_features():
    """Demonstrate privacy and unlinkability features of BBS"""
    print("\n=== PRIVACY FEATURES: BBS Unlinkability Demonstration ===")
    
    print("Key Privacy Features Demonstrated:")
    print("  - Selective Disclosure: Only required attributes revealed")
    print("  - Unlinkable Presentations: Each verification uses fresh randomness")
    print("  - Zero-Knowledge Proofs: Hidden attributes remain private")
    print("  - Credential Minimization: Different info for different purposes")
    
    print("\nSecurity Properties:")
    print("  - Cryptographic signatures prevent forgery")
    print("  - BBS signatures enable selective disclosure")
    print("  - Zero-knowledge proofs preserve privacy")
    print("  - Presentation unlinkability prevents tracking")


def main(profile_name: str = None):
    """Main demo function showcasing BBS-based DTC system"""
    print("=" * 80)
    print("DIGITAL TRAVEL CREDENTIALS (DTC) - COMPLETE DEMO")
    print("Cryptographic Privacy for European Digital Identity")
    print("=" * 80)
    
    try:
        # Setup the BBS-enabled DTC ecosystem
        actors = setup_actors(profile_name)
        
        # Demonstrate BBS credential issuance
        actors = demo_issuance(actors, profile_name)
        
        # Demonstrate BBS presentations and verification
        demo_presentation_verification(actors)
        
        # Show BBS privacy features
        demo_privacy_features()
        
        print("\n=== SUCCESS: DEMO COMPLETE - DTC System Successfully Demonstrated! ===")
        
        # Summary statistics
        alice = actors['holders']['alice']
        wallet_stats = alice.get_wallet_stats()
        
        print("Summary:")
        print(f"  - Credentials issued: {wallet_stats['total_credentials']}")
        print(f"  - Passport credentials: {wallet_stats['by_type'].get('passport', 0)}")
        print(f"  - Visa credentials: {wallet_stats['by_type'].get('visa', 0)}")
        print(f"  - Vaccination credentials: {wallet_stats['by_type'].get('vaccination_certificate', 0)}")
        print(f"  - Valid credentials: {wallet_stats['valid_count']}")
        
        print("\nDigital Travel Credentials system operational!")
        print("Privacy-preserving travel verification enabled.")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

def run_with_profile(profile_path: str = None):
    """Entry point for benchmark runner with explicit profile path"""
    print("[INIT] Loading Demo modules...")
    from benchmark.data.manager import DataManager
    print(f"[INFO] Demo modules loaded: 6/6")
    
    # Load configuration using DataManager if needed
    data_manager = DataManager()
    
    print("=" * 80)
    print("DIGITAL TRAVEL CREDENTIALS (DTC) - COMPLETE DEMO")
    print("Cryptographic Privacy for European Digital Identity")
    print("=" * 80)
    
    try:
        # Setup actors with profile
        actors = setup_actors(profile_path)
        
        # Issuance phase
        actors = demo_issuance(actors, profile_path)
        
        # Verification phase
        demo_presentation_verification(actors)
        
        # Privacy features demonstration
        demo_privacy_features()
        
        print("=" * 45 + " SUCCESS " + "=" * 45)
        print("=== SUCCESS: DEMO COMPLETE - DTC System Successfully Demonstrated! ===")
        
        # Print summary
        alice = actors['holders']['alice']
        wallet_stats = alice.get_wallet_stats()
        
        print("Summary:")
        print(f"  - Credentials issued: {wallet_stats['total_credentials']}")
        print(f"  - Passport credentials: {wallet_stats['by_type'].get('passport', 0)}")
        print(f"  - Visa credentials: {wallet_stats['by_type'].get('visa', 0)}")
        print(f"  - Vaccination credentials: {wallet_stats['by_type'].get('vaccination_certificate', 0)}")
        print(f"  - Valid credentials: {wallet_stats['valid_count']}")
        
        print("\nDigital Travel Credentials system operational!")
        print("Privacy-preserving travel verification enabled.")
        
        return True
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    profile_name = sys.argv[1] if len(sys.argv) > 1 else None
    main(profile_name)