#!/usr/bin/env python3
"""
Demo/interactive_disclosure.py - Demonstration interactive de divulgation selective

Cette demo permet a l'utilisateur de choisir interactivement quels attributs
il souhaite reveler ou cacher lors de differents scenarios de verification.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

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
from benchmark.data.manager import DataManager


class InteractiveDisclosureDemo:
    
    def __init__(self):
        self.data_manager = DataManager()
        self.credential = None
        self.keys = None
        
    def print_header(self, title: str):
        line = "=" * 60
        print(f"\n{line}\n{title:^60}\n{line}\n")
    
    def load_or_create_credential(self) -> Dict[str, Any]:
        print("Selection du profil utilisateur :")
        
        available_profiles = []
        profile_files = [
            ("ellen_kampire_dtc.json", "Ellen Kampire (Rwandaise, 32 ans, défaut)"),
            ("Berissa_kawaya_dtc.json", "Berissa Kawaya (Ivoirienne, 28 ans, business)"),
            ("benoit_koleu_dtc.json", "Benoit Koleu (Japonais, 58 ans, executive)"),
            ("stephane_nzuri_dtc.json", "Stephane Nzuri (Belge, 15 ans, mineur)"),
        ]
        
        # Afficher les profils disponibles
        for i, (filename, description) in enumerate(profile_files, 1):
            print(f"{i}. {description}")
            available_profiles.append(filename)
        
        print(f"{len(profile_files) + 1}. Profil personnalisé")
        
        try:
            choice = input(f"\nChoisissez un profil (1-{len(profile_files) + 1}) [1]: ").strip() or "1"
        except KeyboardInterrupt:
            print("\nAu revoir !")
            sys.exit(0)
        
        choice_idx = int(choice) - 1
        
        if 0 <= choice_idx < len(profile_files):
            filename = available_profiles[choice_idx]
            return self._load_json_profile(filename)
        elif choice_idx == len(profile_files):
            return self._create_custom_profile()
        else:
            print("Choix invalide, utilisation d'Ellen Kampire par défaut")
            return self._load_json_profile("ellen_kampire_dtc.json")

    def _load_json_profile(self, filename: str) -> Dict[str, Any]:
        """Charger un profil depuis un fichier JSON"""
        try:
            # Essayer différents chemins
            possible_paths = [
                Path(__file__).parent.parent / "benchmark" / "data" / "custom" / filename,
                Path(__file__).parent.parent / "data" / "custom" / filename,
                Path(__file__).parent / "data" / "custom" / filename,
                Path(filename)
            ]
            
            profile_data = None
            for path in possible_paths:
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                    print(f"Profil chargé depuis: {path}")
                    break
            
            if not profile_data:
                print(f"Fichier {filename} non trouvé, utilisation profil par défaut")
                return self._load_business_profile()
            
            # Convertir le format JSON vers le format attendu
            attributes = {}
            for attr_name in profile_data.get('attributes', []):
                metadata = profile_data.get('attribute_metadata', {})
                if attr_name in metadata:
                    attributes[attr_name] = metadata[attr_name].get('example_value', f"value_{attr_name}")
                else:
                    attributes[attr_name] = f"example_{attr_name}"
            
            # Identifier les attributs sensibles
            sensitive_attributes = []
            for attr_name, meta in profile_data.get('attribute_metadata', {}).items():
                if meta.get('sensitive', False):
                    sensitive_attributes.append(attr_name)
            
            return {
                'name': profile_data.get('credential_holder', {}).get('full_name', 'Unknown'),
                'description': profile_data.get('description', ''),
                'attributes': attributes,
                'sensitive_attributes': sensitive_attributes
            }
            
        except Exception as e:
            print(f"Erreur lors du chargement de {filename}: {e}")
            print("Utilisation du profil business par défaut")
            return self._load_business_profile()
    
    def _load_business_profile(self) -> Dict[str, Any]:
        return {
            'name': 'Ellen Kampire',
            'description': 'Businesswoman rwandaise en deplacement',
            'attributes': {
                'full_name': 'Ellen Kampire',
                'nationality': 'Rwandaise', 
                'birth_date': '1996-03-15',
                'passport_number': 'RW2024789456',
                'visa_status': 'Valid Business B1',
                'sponsor_company': 'TechKigali Innovation',
                'purpose_of_visit': 'Business meetings and training',
                'accommodation_address': 'Hotel des Milles Collines, Kigali',
                'expiry_date': '2029-03-14',
                'biometric_hash': 'sha256:a1b2c3d4e5f6'
            },
            'sensitive_attributes': ['passport_number', 'birth_date', 'biometric_hash', 'accommodation_address']
        }
    
    def _load_student_profile(self) -> Dict[str, Any]:
        return {
            'name': 'Ellen Kampire',
            'description': 'Etudiante rwandaise en voyage scolaire',
            'attributes': {
                'full_name': 'Ellen Kampire',
                'nationality': 'Rwandaise',
                'birth_date': '2006-07-22',
                'passport_number': 'RW2023654789',
                'guardian_name': 'Marie Kampire',
                'school_name': 'College Saint-Michel, Kigali',
                'trip_supervisor': 'Prof. Jean Uwimana',
                'group_reference': 'VOYAGE-2024-PARIS-GRP7',
                'return_date': '2024-08-25',
                'emergency_contact': '+250 788 123 456'
            },
            'sensitive_attributes': ['passport_number', 'birth_date', 'guardian_name', 'emergency_contact']
        }
    
    def _load_executive_profile(self) -> Dict[str, Any]:
        return {
            'name': 'Ellen Kampire',
            'description': 'Executive rwandaise en mission',
            'attributes': {
                'full_name': 'Ellen Kampire',
                'nationality': 'Rwandaise',
                'birth_date': '1986-04-12',
                'passport_number': 'RW20241234567',
                'company_name': 'Rwanda Development Board',
                'job_title': 'Senior Investment Director',
                'business_purpose': 'Strategic partnership negotiations',
                'meeting_companies': 'African Development Bank, World Bank',
                'frequent_traveler_number': 'EXEC-TRAVELER-RW-58947',
                'accommodation_hotel': 'Hotel des Milles Collines'
            },
            'sensitive_attributes': ['passport_number', 'birth_date', 'frequent_traveler_number']
        }
    
    def _create_custom_profile(self) -> Dict[str, Any]:
        print("\nCreation d'un profil personnalise :")
        
        try:
            name = input("Nom complet : ").strip()
            nationality = input("Nationalite : ").strip()
            birth_date = input("Date de naissance (YYYY-MM-DD) : ").strip()
            
            custom_profile = {
                'name': name,
                'description': 'Profil personnalise',
                'attributes': {
                    'full_name': name,
                    'nationality': nationality,
                    'birth_date': birth_date,
                    'passport_number': f"XX{birth_date.replace('-', '')}",
                    'document_type': 'Passport',
                    'issuing_country': nationality
                },
                'sensitive_attributes': ['passport_number', 'birth_date']
            }
            
            print("\nAjouter des attributs supplementaires ? (o/n)")
            if input().lower().startswith('o'):
                while True:
                    attr_name = input("Nom de l'attribut (ou ENTER pour terminer): ").strip()
                    if not attr_name:
                        break
                    attr_value = input(f"Valeur pour {attr_name}: ").strip()
                    custom_profile['attributes'][attr_name] = attr_value
                    
                    is_sensitive = input("Cet attribut est-il sensible ? (o/n): ").lower().startswith('o')
                    if is_sensitive:
                        custom_profile['sensitive_attributes'].append(attr_name)
            
            return custom_profile
            
        except KeyboardInterrupt:
            print("\nRetour au menu principal")
            return self._load_business_profile()
    
    def setup_credential(self, profile: Dict[str, Any]):
        print(f"Configuration du credential pour {profile['name']}")
        
        sk, pk = BBSKeyGen.generate_keypair()
        
        #  Utiliser BBSWithProofs au lieu de BBSSignatureScheme seul
        max_messages = len(profile['attributes'])
        bbs_scheme = BBSWithProofs(max_messages=max_messages)
        
        self.keys = {'private': sk, 'public': pk}
        
        messages = []
        attr_list = list(profile['attributes'].keys())
        for attr in attr_list:
            value = str(profile['attributes'][attr])
            messages.append(value.encode('utf-8'))
        
        header = b"interactive_demo_credential"
        
        #  Utiliser la méthode sign de BBSWithProofs
        signature = bbs_scheme.sign(sk, messages, header)
        
        self.credential = {
            'profile': profile,
            'attributes': attr_list,
            'messages': messages,
            'signature': signature,
            'bbs_scheme': bbs_scheme,  # Maintenant BBSWithProofs
            'header': header
        }
        
        print("Credential signé avec succès")
        return True
    
    def choose_disclosure_interactive(self, scenario: str) -> Dict[str, List[str]]:
        self.print_header(f"SCENARIO : {scenario}")
        
        profile = self.credential['profile']
        attributes = self.credential['attributes']
        sensitive = profile['sensitive_attributes']
        
        print(f"Profil : {profile['name']}")
        print(f"{profile['description']}")
        print("\nAttributs disponibles :")
        
        for i, attr in enumerate(attributes, 1):
            value = profile['attributes'][attr]
            is_sensitive = attr in sensitive
            sensitive_mark = " [SENSIBLE]" if is_sensitive else ""
            print(f"   {i:2d}. {attr}: {value}{sensitive_mark}")
        
        print(f"\nChoisissez les attributs a REVELER pour ce scenario")
        print("Entrez les numeros separes par des virgules (ex: 1,3,5)")
        print("Ou 'all' pour tout reveler, 'none' pour tout cacher")
        
        suggestions = self._get_scenario_suggestions(scenario, attributes, sensitive)
        if suggestions:
            suggestion_indices = [str(i+1) for i, attr in enumerate(attributes) if attr in suggestions]
            print(f"\nSuggestion pour '{scenario}': {', '.join(suggestion_indices)}")
        
        try:
            choice = input("\nVotre choix : ").strip()
        except KeyboardInterrupt:
            print("\nArret de la demonstration")
            sys.exit(0)
        
        disclosed = []
        hidden = []
        
        if choice.lower() == 'all':
            disclosed = attributes[:]
        elif choice.lower() == 'none':
            hidden = attributes[:]
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',') if x.strip()]
                disclosed = [attributes[i] for i in indices if 0 <= i < len(attributes)]
                hidden = [attr for attr in attributes if attr not in disclosed]
            except ValueError:
                print("Format invalide, utilisation des suggestions")
                disclosed = suggestions or [attributes[0]]
                hidden = [attr for attr in attributes if attr not in disclosed]
        
        if not disclosed:
            print("Au moins un attribut doit etre divulgue")
            disclosed = [attributes[0]]
            hidden = [attr for attr in attributes if attr not in disclosed]
        
        return {'disclosed': disclosed, 'hidden': hidden}
    
    def _get_scenario_suggestions(self, scenario: str, attributes: List[str], sensitive: List[str]) -> List[str]:
        scenario_lower = scenario.lower()
        
        if 'hotel' in scenario_lower:
            return [attr for attr in ['full_name', 'nationality'] if attr in attributes]
        
        elif 'frontiere' in scenario_lower or 'border' in scenario_lower:
            return [attr for attr in ['full_name', 'nationality', 'visa_status', 'document_type'] if attr in attributes]
        
        elif 'douane' in scenario_lower or 'customs' in scenario_lower:
            return [attr for attr in ['full_name', 'nationality', 'purpose_of_visit', 'return_date'] if attr in attributes]
        
        elif 'age' in scenario_lower:
            return [attr for attr in ['full_name', 'birth_date'] if attr in attributes]
        
        elif 'business' in scenario_lower or 'travail' in scenario_lower:
            return [attr for attr in ['full_name', 'company_name', 'job_title', 'business_purpose'] if attr in attributes]
        
        elif 'ecole' in scenario_lower or 'school' in scenario_lower:
            return [attr for attr in ['full_name', 'school_name', 'trip_supervisor', 'group_reference'] if attr in attributes]
        
        else:
            return [attr for attr in attributes if attr not in sensitive][:3]
    
    def demonstrate_proof(self, disclosure: Dict[str, List[str]], scenario: str):
        print(f"\nGénération de preuve pour '{scenario}'")
        
        disclosed = disclosure['disclosed']
        hidden = disclosure['hidden']
        
        print(f"\nAttributs RÉVÉLÉS ({len(disclosed)}):")
        for attr in disclosed:
            value = self.credential['profile']['attributes'][attr]
            print(f"   {attr}: {value}")
        
        print(f"\nAttributs CACHÉS ({len(hidden)}):")
        for attr in hidden:
            print(f"   {attr}: <preuve zero-knowledge>")
        
        disclosed_indices = [self.credential['attributes'].index(attr) for attr in disclosed]
        
        try:
            #  Utiliser generate_proof au lieu de core_proof_gen
            presentation_header = f"{scenario}_presentation".encode('utf-8')
            
            proof = self.credential['bbs_scheme'].generate_proof(
                pk=self.keys['public'],
                signature=self.credential['signature'],
                header=self.credential['header'],
                messages=self.credential['messages'],
                disclosed_indexes=disclosed_indices,
                presentation_header=presentation_header
            )
            
            disclosed_messages = [self.credential['messages'][i] for i in disclosed_indices]
            
            #  Utiliser verify_proof au lieu de core_proof_verify
            is_valid = self.credential['bbs_scheme'].verify_proof(
                pk=self.keys['public'],
                proof=proof,
                header=self.credential['header'],
                disclosed_messages=disclosed_messages,
                disclosed_indexes=disclosed_indices,
                presentation_header=presentation_header
            )
            
            if is_valid:
                print("Preuve générée et vérifiée avec succès")
                
                privacy_score = len(hidden) / len(self.credential['attributes']) * 100
                print(f"Score de privacy: {privacy_score:.1f}% ({len(hidden)}/{len(self.credential['attributes'])} attributs cachés)")
                
                return True
            else:
                print("✗ Preuve invalide")
                return False
                
        except Exception as e:
            print(f"Erreur lors de la génération/vérification de preuve: {e}")
            return False
    
    def run_scenarios(self):
        scenarios = [
            "Check-in hotel",
            "Controle frontiere", 
            "Verification douaniere",
            "Verification d'age (bar/discotheque)",
            "Controle business (bureau)",
            "Urgence medicale",
            "Scenario personnalise"
        ]
        
        while True:
            self.print_header("CHOIX DU SCENARIO DE VERIFICATION")
            
            print("Scenarios disponibles :")
            for i, scenario in enumerate(scenarios, 1):
                print(f"   {i}. {scenario}")
            print("   0. Terminer")
            
            try:
                choice = input("\nChoisissez un scenario (0-7) : ").strip()
            except KeyboardInterrupt:
                print("\nAu revoir !")
                break
            
            if choice == '0':
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(scenarios):
                    if idx == len(scenarios) - 1:
                        scenario = input("Nom du scenario personnalise : ").strip()
                    else:
                        scenario = scenarios[idx]
                    
                    disclosure = self.choose_disclosure_interactive(scenario)
                    success = self.demonstrate_proof(disclosure, scenario)
                    
                    if success:
                        print("\nScenario termine avec succes !")
                        
                        try:
                            continue_choice = input("\nTester un autre scenario ? (o/n) [o]: ").strip().lower()
                            if continue_choice.startswith('n'):
                                break
                        except KeyboardInterrupt:
                            break
                    else:
                        print("\nEchec du scenario")
                        
                else:
                    print("Choix invalide")
                    
            except ValueError:
                print("Veuillez entrer un numero")
    
    def run_interactive_demo(self):
        self.print_header("DEMONSTRATION INTERACTIVE - DIVULGATION SELECTIVE")
        
        print("Cette demonstration vous permet de :")
        print("   • Choisir votre profil utilisateur")  
        print("   • Selectionner interactivement quels attributs reveler")
        print("   • Tester differents scenarios de verification")
        print("   • Voir l'impact sur votre privacy")
        
        profile = self.load_or_create_credential()
        
        if not self.setup_credential(profile):
            print("Erreur de configuration")
            return False
        
        self.run_scenarios()
        
        self.print_header("DEMONSTRATION INTERACTIVE TERMINEE")
        
        print("Vous avez experimente :")
        print("   • La divulgation selective personnalisee")
        print("   • Differents niveaux de privacy")
        print("   • L'adaptation aux contextes de verification")
        print("   • La preservation des donnees sensibles")
        
        return True

def main():
    print("Demonstration Interactive BBS - Divulgation Selective")
    print("Choisissez vos attributs, testez vos scenarios !")
    
    demo = InteractiveDisclosureDemo()
    success = demo.run_interactive_demo()
    
    if success:
        print("\nDemonstration interactive reussie !")
        sys.exit(0)
    else:
        print("\nDemonstration interactive echouee !")
        sys.exit(1)

if __name__ == "__main__":
    main()