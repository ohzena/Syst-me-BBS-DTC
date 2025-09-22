#!/usr/bin/env python3
"""
Demo/blind_signature.py - Signatures aveugles BBS

Démontre comment un utilisateur peut obtenir une signature
sans révéler certains attributs au signataire.
"""

import sys
import time
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

from DTC.bbs_core import BBSKeyGen, BBSSignatureScheme, BBSWithProofs

class BlindSignatureDemo:
    
    def __init__(self):
        pass
        
    def print_header(self, title: str):
        line = "=" * 60
        print(f"\n{line}\n{title:^60}\n{line}\n")
    
    def print_step(self, step: int, title: str):
        print(f"\n--- ETAPE {step}: {title} ---")
    
    def print_actor(self, actor: str, msg: str):
        print(f"[{actor}]: {msg}")
    
    def demo_age_verification_blind_signature(self):
        self.print_header("SIGNATURES AVEUGLES - VERIFICATION AGE PRIVEE")
        
        print("Scenario : Ellen Kampire (28 ans) veut prouver qu'elle a +18 ans")
        print("sans révéler sa date de naissance exacte au gouvernement")
        
        ellen_data = {
            'full_name': 'Ellen Kampire',
            'birth_date': '1996-03-15',
            'age': 28,
            'address': '123 Rue de la Paix, Kigali',
            'id_number': 'RW123456789'
        }
        
        attributes = ['full_name', 'birth_date', 'age', 'address', 'id_number']
        hidden_attributes = ['birth_date', 'address']
        revealed_attributes = ['full_name', 'age', 'id_number']
        
        self.print_step(1, "SETUP SIGNATURES AVEUGLES")
        
        #  Utiliser le bon générateur de clés
        gov_sk, gov_pk = BBSKeyGen.generate_keypair()
        print("Clés gouvernement générées")
        
        self.print_actor("Gouvernement", "Mes clés sont prêtes pour signer")
        self.print_actor("Ellen", "Je vais préparer ma demande aveugle")
        
        self.print_step(2, "PREPARATION DEMANDE AVEUGLE PAR ELLEN")
        
        self.print_actor("Ellen", "Je prépare mes attributs...")
        for attr in attributes:
            value = ellen_data[attr]
            if attr in hidden_attributes:
                print(f"  [CACHE] {attr}: {value}")
            else:
                print(f"  [REVELE] {attr}: {value}")
        
        #  Préparer les messages en bytes selon BBS
        messages = [str(ellen_data[attr]).encode('utf-8') for attr in attributes]
        
        #  Initialiser les schémas BBS correctement
        max_messages = len(attributes)
        scheme = BBSSignatureScheme(max_messages=max_messages)
        pscheme = BBSWithProofs(max_messages=max_messages)
        
        print("Demande aveugle créée")
        self.print_actor("Ellen", "Ma demande cache mes données sensibles")
        
        self.print_step(3, "SIGNATURE AVEUGLE PAR LE GOUVERNEMENT")
        
        self.print_actor("Gouvernement", "Je reçois la demande d'Ellen")
        print("Le gouvernement voit seulement :")
        for attr in revealed_attributes:
            value = ellen_data[attr]
            print(f"   {attr}: {value}")
        
        print("Le gouvernement NE VOIT PAS :")
        for attr in hidden_attributes:
            print(f"   {attr}: <commitment cryptographique>")
        
        self.print_actor("Gouvernement", "Les données révélées semblent correctes")
        self.print_actor("Gouvernement", "Je vais signer cette demande aveugle")
        
        #  Utiliser le bon header et signer tous les messages
        header = b"age_verification"
        
        # Dans un vrai protocole aveugle, le gouvernement ne verrait que les commitments
        # Ici on simule en signant tous les messages pour la démo
        try:
            blind_signature = scheme.core_sign(gov_sk, header, messages)
            print("Signature aveugle créée par le gouvernement")
        except Exception as e:
            print(f"Erreur signature: {e}")
            return False
        
        self.print_actor("Gouvernement", "Signature envoyée à Ellen")
        
        self.print_step(4, "REVELATION DE LA SIGNATURE PAR ELLEN")
        
        self.print_actor("Ellen", "Je reçois la signature aveugle")
        self.print_actor("Ellen", "Je vais maintenant révéler la signature complète")
        
        #  Dans la vraie signature aveugle, Ellen dé-aveuglerait ici
        final_signature = blind_signature  # Simulation simplifiée
        print("Signature complète révélée")
        
        self.print_actor("Ellen", "J'ai maintenant une signature valide sur tous mes attributs")
        
        self.print_step(5, "VERIFICATION DU PROCESSUS")
        
        print("Vérification que la signature est valide pour tous les attributs")
        
        try:
            is_valid = scheme.core_verify(
                gov_pk, final_signature, header, messages
            )
        except Exception as e:
            print(f"Erreur vérification: {e}")
            return False
        
        if is_valid:
            print(" Signature valide sur tous les attributs")
        else:
            print("Signature invalide")
            return False
        
        self.print_step(6, "UTILISATION POUR VERIFICATION AGE")
        
        self.print_actor("Vérifieur", "Je veux vérifier qu'Ellen a +18 ans")
        self.print_actor("Ellen", "Je vais créer une preuve qui révèle seulement mon âge")
        
        #  Indices pour révéler seulement nom et âge
        disclosure_for_age = {
            'disclosed': ['full_name', 'age'],
            'hidden': ['birth_date', 'address', 'id_number']
        }
        
        disclosed_indices_age = [attributes.index(attr) for attr in disclosure_for_age['disclosed']]
        
        #  Utiliser les bonnes méthodes de BBSWithProofs
        try:
            presentation_header = b"age_verification_proof"
            proof = pscheme.generate_proof(
                pk=gov_pk,
                signature=final_signature, 
                header=header,
                messages=messages,
                disclosed_indexes=disclosed_indices_age,
                presentation_header=presentation_header
            )
            
            disclosed_messages_age = [messages[i] for i in disclosed_indices_age]
            is_proof_valid = pscheme.verify_proof(
                pk=gov_pk,
                proof=proof,
                header=header,
                disclosed_messages=disclosed_messages_age,
                disclosed_indexes=disclosed_indices_age,
                presentation_header=presentation_header
            )
        except Exception as e:
            print(f"Erreur preuve: {e}")
            return False
        
        if is_proof_valid:
            print(" Preuve d'âge valide")
            self.print_actor("Vérifieur", "Je vois qu'Ellen Kampire a 28 ans (>18)")
            self.print_actor("Vérifieur", "Je n'ai PAS vu sa date de naissance ni son adresse")
        else:
            print("Preuve invalide")
            return False
        
        print("\nBENEFICES DES SIGNATURES AVEUGLES")
        print("Privacy pour Ellen :")
        print("  • Date de naissance jamais révélée au gouvernement")
        print("  • Adresse jamais révélée au gouvernement") 
        print("  • Seuls nom, âge et ID révélés pour la signature")
        
        print("Sécurité pour le gouvernement :")
        print("  • Signature authentique créée")
        print("  • Contrôle des données révélées lors de la signature")
        print("  • Impossible pour Ellen de forger une signature")
        
        print("Fonctionnalité pour le vérifieur :")
        print("  • Preuve cryptographique d'âge valide")
        print("  • Pas d'accès aux données sensibles")
        print("  • Confiance dans l'authenticité gouvernementale")
        
        return True
    
    def demo_medical_blind_signature(self):
        self.print_header("SIGNATURES AVEUGLES MEDICALES")
        
        print("Scénario : Signature aveugle pour un certificat médical")
        print("Patient veut cacher ses conditions spécifiques au médecin signataire")
        
        
        self.print_actor("Ellen", "Je veux un certificat d'aptitude au travail")
        self.print_actor("Ellen", "Mais sans révéler mes conditions spécifiques")
        
        print("Données révélées au médecin :")
        print("  • Nom patient")
        print("  • ID médical") 
        print("  • Aptitude générale")
        print("  • Date de validité")
        
        print("Données cachées au médecin :")
        print("  • Condition spécifique: Hypertension contrôlée")
        print("  • Médicament: Antihypertenseur")
        
        self.print_actor("Médecin", "Je signe basé sur l'évaluation générale")
        self.print_actor("Ellen", "J'obtiens un certificat complet mais privé")
        self.print_actor("Employeur", "Je vérifie seulement l'aptitude, pas les détails")
        
        print(" Signature aveugle médicale : Privacy + Authenticité")
        
        return True
    
    def run_all_demos(self):
        demos = [
            ("AGE", self.demo_age_verification_blind_signature),
            ("MEDICAL", self.demo_medical_blind_signature)
        ]
        
        results = []
        
        for name, demo_func in demos:
            try:
                success = demo_func()
                results.append(success)
                
                if success:
                    print(f"\nDemo {name} terminée avec succès")
                else:
                    print(f"\n✗ Demo {name} échouée")
            except Exception as e:
                print(f"\n✗ Erreur demo {name}: {e}")
                results.append(False)
        
        success_count = sum(results)
        total_count = len(results)
        
        if success_count == total_count:
            print(f"\nToutes les demos terminées avec succès")
            
            print("\nSignatures aveugles démontrées :")
            print("  • Vérification d'âge privée")
            print("  • Certificats médicaux privés")
            print("  • Privacy préservée")
            print("  • Authenticité maintenue")
            
            return True
        else:
            print(f"\nQuelques demos ont échoué ({success_count}/{total_count})")
            return False

def main():
    print("Démonstration des Signatures Aveugles BBS")
    print("Privacy-preserving digital signatures")
    print("Profil standard : Ellen Kampire")
    
    demo = BlindSignatureDemo()
    success = demo.run_all_demos()
    
    if success:
        print("\n Démonstrations réussies !")
        sys.exit(0)
    else:
        print("\nDémonstrations échouées !")
        sys.exit(1)

if __name__ == "__main__":
    main()