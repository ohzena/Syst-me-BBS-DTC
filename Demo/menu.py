#!/usr/bin/env python3
"""
Demo/menu.py - Menu principal des démonstrations BBS-DTC

Menu interactif pour lancer toutes les démonstrations disponibles.
"""

import sys
import subprocess
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

class DemoMenu:
    
    def __init__(self):
        self.demo_dir = Path(__file__).parent
        self.available_demos = self._discover_demos()
        self.json_profiles = self._discover_json_profiles()
    
    def _discover_demos(self) -> Dict[str, Dict[str, Any]]:
        demos = {
            'complete': {
                'file': 'dtc_complete.py',
                'title': 'Demonstration Complete BBS',
                'description': 'Processus complet etape par etape (Setup -> KeyGen -> Sign -> Verify -> Proof -> ProofVerify)',
                'duration': '5-10 min',
                'level': 'Debutant',
                'supports_json': True
            },
            
            'interactive': {
                'file': 'interactive_disclosure.py',
                'title': 'Divulgation Selective Interactive',
                'description': 'Choix interactif des attributs a reveler selon differents scenarios',
                'duration': '10-15 min',
                'level': 'Debutant',
                'supports_json': True
            },
            
            'travel': {
                'file': 'demo_travel.py',
                'title': 'Scenario de Voyage Complet',
                'description': 'Simulation complete d\'un voyage international avec DTC',
                'duration': '8-12 min',
                'level': 'Intermediaire',
                'supports_json': False
            },
            
            'credential_issuance': {
                'file': 'credential_issuance.py',
                'title': 'Emission de Credentials',
                'description': 'Processus d\'emission et de gestion des credentials DTC',
                'duration': '6-8 min',
                'level': 'Intermediaire',
                'supports_json': False
            },
            
            'blind': {
                'file': 'blind_signature.py',
                'title': 'Signatures Aveugles',
                'description': 'Demonstration des signatures aveugles pour la privacy renforcee',
                'duration': '3-5 min',
                'level': 'Intermediaire',
                'supports_json': False
            },
            
            'auto_privacy': {
                'file': 'auto_privacy.py',
                'title': 'Protection Automatique Privacy',
                'description': 'Demonstration de la protection automatique selon RGPD et contexte',
                'duration': '5-7 min',
                'level': 'Avance',
                'supports_json': False
            }
        }
        
        available = {}
        for key, demo in demos.items():
            demo_path = self.demo_dir / demo['file']
            if demo_path.exists():
                available[key] = demo
            else:
                print(f"Warning: {demo['file']} non trouve")
        
        return available
    
    def _discover_json_profiles(self) -> List[str]:
        json_dir = Path(__file__).parent.parent / "benchmark" / "data" / "custom"
        profiles = []
        
        if json_dir.exists():
            for json_file in json_dir.glob("*.json"):
                if json_file.name.endswith('_dtc.json'):
                    profiles.append(json_file.name)
        
        return sorted(profiles)
    
    def print_header(self, title: str):
        line = "=" * 80
        print(f"\n{line}\n{title:^80}\n{line}\n")
    
    def print_demo_info(self, key: str, demo: Dict[str, Any], index: int):
        print(f"{index:2d}. {demo['title']}")
        print(f"    {demo['description']}")
        print(f"    Niveau: {demo['level']} | Duree: {demo['duration']} | JSON: {'Oui' if demo['supports_json'] else 'Non'}")
        print()
    
    def show_main_menu(self):
        self.print_header("MENU PRINCIPAL - DEMONSTRATIONS BBS DIGITAL TRAVEL CREDENTIALS")
        
        print("Bienvenue dans les demonstrations interactives du systeme BBS-DTC !")
        print("Chaque demonstration illustre differents aspects des signatures BBS\n")
        
        categories = {
            'Debutant - Decouverte': ['complete', 'interactive'],
            'Intermediaire - Cas d\'usage': ['travel', 'credential_issuance', 'blind'],
            'Avance - Cryptographie': ['auto_privacy']
        }
        
        demo_index = 1
        for category, demo_keys in categories.items():
            print(f"{category}")
            print("-" * 40)
            
            for key in demo_keys:
                if key in self.available_demos:
                    self.print_demo_info(key, self.available_demos[key], demo_index)
                    demo_index += 1
        
        print("Options Avancees")
        print("-" * 40)
        print(f"{demo_index:2d}. Lancer TOUTES les demos (sequence complete)")
        print(f"{demo_index+1:2d}. Tests de performance et benchmarks")
        print(f"{demo_index+2:2d}. Informations systeme et dependances")
        print(" 0. Quitter\n")
        
        if self.json_profiles:
            print("Profils JSON DTC disponibles:")
            for profile in self.json_profiles:
                name = profile.replace('_dtc.json', '').replace('_', ' ').title()
                print(f"   • {name} ({profile})")
            print()
    
    def run_demo(self, demo_key: str, json_profile: Optional[str] = None):
        if demo_key not in self.available_demos:
            print(f"Demonstration '{demo_key}' non trouvee")
            return False
        
        demo = self.available_demos[demo_key]
        demo_path = self.demo_dir / demo['file']
        
        print(f"\nLancement: {demo['title']}")
        
        cmd = [sys.executable, str(demo_path)]
        
        if demo['supports_json'] and json_profile:
            cmd.append(json_profile)
            print(f"Utilisation du profil: {json_profile}")
        
        try:
            result = subprocess.run(cmd, cwd=self.demo_dir.parent)
            
            if result.returncode == 0:
                print("\nDemonstration terminee avec succes")
                return True
            else:
                print(f"\nDemonstration echouee (code: {result.returncode})")
                return False
                
        except FileNotFoundError:
            print(f"Impossible de lancer {demo_path}")
            return False
        except KeyboardInterrupt:
            print(f"\nDemonstration interrompue par l'utilisateur")
            return False
    
    def run_all_demos(self):
        self.print_header("SEQUENCE COMPLETE - TOUTES LES DEMONSTRATIONS")
        
        print("Cette sequence lance toutes les demonstrations dans l'ordre optimal")
        print("Duree estimee: 30-45 minutes\n")
        
        try:
            confirm = input("Continuer ? (o/n) [o]: ").strip().lower()
            if confirm.startswith('n'):
                return
        except KeyboardInterrupt:
            return
        
        demo_sequence = ['complete', 'interactive', 'travel', 'credential_issuance', 'blind', 'auto_privacy']
        
        results = []
        for i, demo_key in enumerate(demo_sequence, 1):
            if demo_key in self.available_demos:
                print(f"\n{'='*60}")
                print(f"DEMO {i}/{len(demo_sequence)}: {self.available_demos[demo_key]['title']}")
                print(f"{'='*60}")
                
                success = self.run_demo(demo_key)
                results.append((demo_key, success))
                
                if not success:
                    try:
                        cont = input(f"\nDemo {demo_key} echouee. Continuer ? (o/n) [o]: ").strip().lower()
                        if cont.startswith('n'):
                            break
                    except KeyboardInterrupt:
                        break
        
        self.print_header("RESUME DE LA SEQUENCE COMPLETE")
        
        success_count = sum(1 for _, success in results if success)
        total_count = len(results)
        
        print(f"Demonstrations executees: {total_count}")
        print(f"Reussites: {success_count}")
        print(f"Echecs: {total_count - success_count}")
        
        for demo_key, success in results:
            status = "SUCCES" if success else "ECHEC"
            title = self.available_demos[demo_key]['title']
            print(f"  {status} {title}")
        
        if success_count == total_count:
            print("\nToutes les demonstrations reussies !")
    
    def show_system_info(self):
        self.print_header("INFORMATIONS SYSTEME")
        
        print("Python:")
        print(f"  Version: {sys.version}")
        print(f"  Executable: {sys.executable}")
        
        print(f"\nRepertoire de travail:")
        print(f"  {Path.cwd()}")
        
        print(f"\nRepertoire des demos:")
        print(f"  {self.demo_dir}")
        
        print(f"\nDemonstrations disponibles: {len(self.available_demos)}")
        for key, demo in self.available_demos.items():
            print(f"  OK {demo['title']}")
        
        print(f"\nProfils JSON DTC: {len(self.json_profiles)}")
        for profile in self.json_profiles:
            print(f"  {profile}")
        
        print(f"\nDependances:")
        
        deps_to_test = [
            ('colorama', 'Interface coloree'),
            ('matplotlib', 'Graphiques'),
            ('numpy', 'Calculs numeriques'),
            ('pandas', 'Manipulation de donnees')
        ]
        
        for dep, desc in deps_to_test:
            try:
                __import__(dep)
                print(f"  OK {dep}: {desc}")
            except ImportError:
                print(f"  MANQUE {dep}: {desc}")
        
        print(f"\nModules BBS/DTC:")
        
        bbs_modules = [
            ('DTC.bbs_core', 'Interface BBS principale'),
            ('DTC.DTCIssuer', 'Emission de credentials'),
            ('DTC.DTCHolder', 'Gestion wallet'),
            ('DTC.DTCVerifier', 'Verification'),
            ('benchmark.data.manager', 'Gestion donnees JSON')
        ]
        
        for module, desc in bbs_modules:
            try:
                __import__(module)
                print(f"  OK {module}: {desc}")
            except ImportError:
                print(f"  MANQUE {module}: {desc}")
    
    def interactive_menu(self):
        while True:
            self.show_main_menu()
            
            try:
                choice = input("Votre choix (0 pour quitter): ").strip()
            except KeyboardInterrupt:
                print("\nAu revoir !")
                break
            
            if choice == '0':
                print("Au revoir !")
                break
            
            demo_keys = list(self.available_demos.keys())
            
            try:
                choice_int = int(choice)
                
                if 1 <= choice_int <= len(demo_keys):
                    demo_key = demo_keys[choice_int - 1]
                    
                    json_profile = None
                    demo = self.available_demos[demo_key]
                    
                    if demo['supports_json'] and self.json_profiles:
                        print(f"\nProfils JSON disponibles:")
                        print("  0. Utiliser le profil par defaut")
                        
                        for i, profile in enumerate(self.json_profiles, 1):
                            name = profile.replace('_dtc.json', '').replace('_', ' ').title()
                            print(f"  {i}. {name}")
                        
                        try:
                            profile_choice = input("Choisir un profil (0 pour defaut): ").strip()
                            profile_int = int(profile_choice)
                            
                            if 1 <= profile_int <= len(self.json_profiles):
                                json_profile = self.json_profiles[profile_int - 1]
                        except (ValueError, KeyboardInterrupt):
                            pass
                    
                    self.run_demo(demo_key, json_profile)
                
                elif choice_int == len(demo_keys) + 1:
                    self.run_all_demos()
                
                elif choice_int == len(demo_keys) + 2:
                    try:
                        benchmark_cmd = [sys.executable, "-m", "benchmark.runner", "--quick", "--visualize"]
                        print(f"\nLancement des benchmarks...")
                        subprocess.run(benchmark_cmd, cwd=self.demo_dir.parent)
                    except Exception as e:
                        print(f"Erreur lors des benchmarks: {e}")
                
                elif choice_int == len(demo_keys) + 3:
                    self.show_system_info()
                
                else:
                    print("Choix invalide")
            
            except ValueError:
                print("Veuillez entrer un numero")
            
            try:
                input("\nAppuyez sur ENTER pour continuer...")
            except KeyboardInterrupt:
                break

def main():
    print("Systeme de Demonstrations BBS Digital Travel Credentials")
    print("Menu interactif pour explorer toutes les fonctionnalites\n")
    
    menu = DemoMenu()
    
    if not menu.available_demos:
        print("Aucune demonstration trouvee !")
        print("Verifiez que les fichiers de demo sont presents dans le repertoire Demo/")
        sys.exit(1)
    
    try:
        menu.interactive_menu()
    except KeyboardInterrupt:
        print("\nMenu interrompu. Au revoir !")
    except Exception as e:
        print(f"\nErreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()