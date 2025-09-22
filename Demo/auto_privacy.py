#!/usr/bin/env python3
"""
Demo/auto_privacy.py - Protection automatique de la privacy

Démontre la protection automatique des attributs selon des règles 
prédéfinies de privacy et de conformité réglementaire.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent.parent))

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    class Fore:
        RED = GREEN = YELLOW = CYAN = BLUE = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = ""

from DTC.bbs_core import BBSKeyGen, BBSWithProofs

class PrivacyLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"

class DataCategory(Enum):
    IDENTITY = "identity"
    BIOMETRIC = "biometric"
    LOCATION = "location"
    FINANCIAL = "financial"
    HEALTH = "health"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"

@dataclass
class AttributePolicy:
    name: str
    privacy_level: PrivacyLevel
    data_category: DataCategory
    auto_hide_contexts: Set[str]
    min_age_reveal: Optional[int] = None
    requires_consent: bool = False
    gdpr_special: bool = False

class AutoPrivacyEngine:
    
    def __init__(self):
        self.policies = self._initialize_policies()
        
    def _initialize_policies(self) -> Dict[str, AttributePolicy]:
        policies = {}
        
        policies['full_name'] = AttributePolicy(
            'full_name', PrivacyLevel.PUBLIC, DataCategory.IDENTITY, set()
        )
        
        policies['nationality'] = AttributePolicy(
            'nationality', PrivacyLevel.PUBLIC, DataCategory.IDENTITY,
            {'medical', 'social_services'}
        )
        
        policies['birth_date'] = AttributePolicy(
            'birth_date', PrivacyLevel.CONFIDENTIAL, DataCategory.IDENTITY,
            {'hotel', 'restaurant', 'shopping', 'entertainment'},
            min_age_reveal=16
        )
        
        policies['passport_number'] = AttributePolicy(
            'passport_number', PrivacyLevel.SECRET, DataCategory.IDENTITY,
            {'hotel', 'restaurant', 'entertainment', 'medical'},
            requires_consent=True
        )
        
        policies['photo_hash'] = AttributePolicy(
            'photo_hash', PrivacyLevel.SECRET, DataCategory.BIOMETRIC,
            {'hotel', 'restaurant', 'entertainment'},
            gdpr_special=True
        )
        
        policies['biometric_hash'] = AttributePolicy(
            'biometric_hash', PrivacyLevel.TOP_SECRET, DataCategory.BIOMETRIC,
            {'hotel', 'restaurant', 'entertainment', 'business'},
            gdpr_special=True
        )
        
        policies['address'] = AttributePolicy(
            'address', PrivacyLevel.CONFIDENTIAL, DataCategory.LOCATION,
            {'border', 'customs', 'business'}
        )
        
        policies['company_name'] = AttributePolicy(
            'company_name', PrivacyLevel.INTERNAL, DataCategory.FINANCIAL,
            {'medical', 'personal'}
        )
        
        policies['medical_info_hash'] = AttributePolicy(
            'medical_info_hash', PrivacyLevel.TOP_SECRET, DataCategory.HEALTH,
            {'border', 'customs', 'business', 'hotel'},
            gdpr_special=True
        )
        
        return policies
    
    def apply_auto_privacy(self, attributes: List[str], context: str, 
                          user_age: Optional[int] = None) -> Dict[str, List[str]]:
        disclosed = []
        hidden = []
        auto_hidden = []
        
        for attr in attributes:
            policy = self.policies.get(attr)
            
            if not policy:
                disclosed.append(attr)
                continue
            
            should_hide = False
            reason = ""
            
            if context.lower() in policy.auto_hide_contexts:
                should_hide = True
                reason = f"contexte '{context}'"
                auto_hidden.append((attr, reason))
            
            elif policy.min_age_reveal and user_age and user_age < policy.min_age_reveal:
                should_hide = True
                reason = f"age minimum ({policy.min_age_reveal} ans)"
                auto_hidden.append((attr, reason))
            
            elif policy.privacy_level in [PrivacyLevel.SECRET, PrivacyLevel.TOP_SECRET]:
                if context.lower() not in ['emergency', 'law_enforcement']:
                    should_hide = True
                    reason = f"niveau {policy.privacy_level.value}"
                    auto_hidden.append((attr, reason))
            
            elif policy.gdpr_special and context.lower() not in ['medical', 'emergency']:
                should_hide = True
                reason = "donnees speciales RGPD"
                auto_hidden.append((attr, reason))
            
            if should_hide:
                hidden.append(attr)
            else:
                disclosed.append(attr)
        
        return {
            'disclosed': disclosed,
            'hidden': hidden,
            'auto_hidden': auto_hidden
        }

class AutoPrivacyDemo:
    
    def __init__(self):
        self.privacy_engine = AutoPrivacyEngine()
        
    def print_header(self, title: str):
        line = "=" * 60
        print(f"\n{line}\n{title:^60}\n{line}\n")
    
    def demo_gdpr_compliance(self):
        self.print_header("CONFORMITE RGPD AUTOMATIQUE")
        
        profile = {
            'name': 'Ellen Kampire',
            'age': 28,
            'attributes': {
                'full_name': 'Ellen Kampire',
                'birth_date': '1996-03-15',
                'nationality': 'Rwandaise',
                'passport_number': 'RW789456123',
                'photo_hash': 'sha256:photo_ellen_123',
                'address': '45 Boulevard de la Paix, Kigali',
                'medical_info_hash': 'sha256:medical_ellen_789',
                'company_name': 'TechKigali SARL',
                'biometric_hash': 'sha256:bio_ellen_456'
            }
        }
        
        contexts = [
            ('hotel', 'Enregistrement hotelier'),
            ('medical', 'Consultation medicale'),
            ('border', 'Controle frontiere'),
            ('business', 'Reunion affaires')
        ]
        
        print(f"Profil test : {profile['name']} ({profile['age']} ans)")
        
        for context, description in contexts:
            print(f"\nContexte : {description}")
            
            result = self.privacy_engine.apply_auto_privacy(
                list(profile['attributes'].keys()),
                context,
                profile['age']
            )
            
            print(f"Attributs révélés ({len(result['disclosed'])}):")
            for attr in result['disclosed']:
                value = profile['attributes'][attr]
                print(f"  {attr}: {value}")
            
            if result['auto_hidden']:
                print(f"Attributs cachés automatiquement ({len(result['auto_hidden'])}):")
                for attr, reason in result['auto_hidden']:
                    print(f"  {attr}: masque ({reason})")
            
            total_attrs = len(profile['attributes'])
            hidden_count = len(result['hidden'])
            privacy_score = (hidden_count / total_attrs) * 100
            print(f"Score privacy: {privacy_score:.0f}%")
        
        return True
    
    def demo_bbs_with_auto_privacy(self):
        self.print_header("INTEGRATION BBS + PROTECTION AUTOMATIQUE")
        
        profile = {
            'name': 'Ellen Kampire',
            'age': 28,
            'attributes': {
                'full_name': 'Ellen Kampire',
                'nationality': 'Rwandaise',
                'birth_date': '1996-03-15',
                'passport_number': 'RW2024789456',
                'visa_status': 'Valid Business',
                'company_name': 'TechKigali Innovation',
                'purpose_of_visit': 'Tech conference',
                'photo_hash': 'sha256:photo_ellen_123',
                'biometric_hash': 'sha256:bio_ellen_456'
            }
        }
        
        context = 'hotel'
        
        result = self.privacy_engine.apply_auto_privacy(
            list(profile['attributes'].keys()),
            context,
            profile['age']
        )
        
        print(f"Protection automatique appliquée :")
        print(f"  Révélés: {len(result['disclosed'])} attributs")
        print(f"  Cachés: {len(result['hidden'])} attributs")
        
        try:

            sk, pk = BBSKeyGen.generate_keypair()
            bbs_scheme = BBSWithProofs(max_messages=len(profile['attributes']))
            
            all_messages = [str(profile['attributes'][attr]).encode('utf-8') 
                        for attr in profile['attributes'].keys()]
            
            header = b"auto_privacy_demo"
            

            signature = bbs_scheme.sign(sk, all_messages, header)
            
            disclosed_indices = [list(profile['attributes'].keys()).index(attr) 
                            for attr in result['disclosed']]
            
            presentation_header = f"{context}_auto_privacy".encode('utf-8')
            
            proof = bbs_scheme.generate_proof(
                pk=pk,
                signature=signature,
                header=header,
                messages=all_messages,
                disclosed_indexes=disclosed_indices,
                presentation_header=presentation_header
            )
            
            disclosed_messages = [all_messages[i] for i in disclosed_indices]
            
            is_valid = bbs_scheme.verify_proof(
                pk=pk,
                proof=proof,
                header=header,
                disclosed_messages=disclosed_messages,
                disclosed_indexes=disclosed_indices,
                presentation_header=presentation_header
            )
            
            if is_valid:
                print("Preuve BBS avec protection automatique VALIDE")
                
                privacy_efficiency = len(result['hidden']) / len(profile['attributes']) * 100
                print(f"Efficacité privacy: {privacy_efficiency:.0f}%")
                
                print(f"\nRésultat pour le vérificateur ({context}):")
                for attr in result['disclosed']:
                    value = profile['attributes'][attr]
                    print(f"  {attr}: {value}")
                
                print(f"\nDonnées automatiquement protégées:")
                for attr, reason in result['auto_hidden']:
                    print(f"  {attr}: protégé ({reason})")
                
                return True
            else:
                print("✗ Erreur de vérification BBS")
                return False
                
        except Exception as e:
            print(f"Erreur BBS: {e}")
            return False
    def run_all_demos(self):
        self.print_header("DEMONSTRATIONS PROTECTION AUTOMATIQUE PRIVACY")
        
        demos = [
            ("RGPD", self.demo_gdpr_compliance),
            ("BBS", self.demo_bbs_with_auto_privacy)
        ]
        
        results = []
        
        for name, demo_func in demos:
            try:
                success = demo_func()
                results.append(success)
                
                if success:
                    print(f"Demo {name} terminee avec succes")
                else:
                    print(f"Demo {name} echouee")
            
            except Exception as e:
                print(f"Erreur demo {name}: {e}")
                results.append(False)
        
        success_count = sum(results)
        total_count = len(results)
        
        if success_count == total_count:
            print(f"\nToutes les demos reussies ({success_count}/{total_count})")
            return True
        else:
            print(f"Quelques demos ont echoue ({success_count}/{total_count})")
            return False

def main():
    demo = AutoPrivacyDemo()
    success = demo.run_all_demos()
    
    if success:
        print("\nToutes les demonstrations reussies !")
        sys.exit(0)
    else:
        print("\nCertaines demonstrations ont echoue !")
        sys.exit(1)

if __name__ == "__main__":
    main()