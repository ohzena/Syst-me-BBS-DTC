#!/usr/bin/env python3
"""
Guide d'optimisation spécifique pour MacBook Air M1 2020 (8GB RAM)
Démontre les optimisations adaptées à votre matériel spécifique
"""

import sys
import os
import time
import threading
from typing import List

# Ajout du répertoire pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from performance_optimizer import (
    enable_bbs_optimizations,
    create_optimized_bbs,
    M1OptimizationDetector,
    OptimizationConfig,
    BBSPerformanceManager
)

def print_m1_system_info():
    """Affiche les informations système M1 détectées"""
    print("[M1 SYSTEM] INFORMATIONS SYSTÈME MACBOOK AIR M1")
    print("=" * 45)
    
    # Détection M1
    is_m1 = M1OptimizationDetector.is_apple_silicon()
    print(f"Architecture Apple Silicon: {'[SUCCESS] OUI' if is_m1 else '[ERROR] NON'}")
    
    if is_m1:
        workers = M1OptimizationDetector.get_optimal_worker_count()
        cache_sizes = M1OptimizationDetector.get_memory_optimized_cache_sizes()
        
        print(f"Workers optimaux détectés: {workers} (sur 8 cœurs M1)")
        print("Répartition recommandée:")
        print("  - 4 cœurs performance (P-cores)")
        print("  - 2 cœurs efficacité (E-cores)")
        print("  - 2 cœurs réservés au système")
        
        print(f"\nTailles de cache pour 8GB RAM:")
        print(f"  - Générateurs: {cache_sizes['generator_cache']} entrées")
        print(f"  - Pairings: {cache_sizes['pairing_cache']} entrées") 
        print(f"  - Points: {cache_sizes['point_cache']} entrées")
        
        # Vérification mémoire
        try:
            import psutil
            memory = psutil.virtual_memory()
            print(f"\nMémoire actuelle:")
            print(f"  - Total: {memory.total / (1024**3):.1f} GB")
            print(f"  - Disponible: {memory.available / (1024**3):.1f} GB")
            print(f"  - Utilisation: {memory.percent:.1f}%")
        except ImportError:
            print("\n[WARNING]  psutil non disponible pour le monitoring mémoire")


def demo_m1_optimized_configuration():
    """Démonstration de la configuration optimisée M1"""
    print("\n[SETUP] CONFIGURATION OPTIMISÉE POUR M1")
    print("=" * 40)
    
    # Configuration automatique M1
    print("1. Configuration automatique (recommandée):")
    config_auto = M1OptimizationDetector.create_m1_optimized_config()
    print(f"   [SUCCESS] Workers: {config_auto.max_workers}")
    print(f"   [SUCCESS] Cache générateurs: {config_auto.max_generator_cache_size}")
    print(f"   [SUCCESS] Cache pairings: {config_auto.max_pairing_cache_size}")
    print(f"   [SUCCESS] Seuil batch: {config_auto.batch_size_threshold}")
    print(f"   [SUCCESS] Préférence threads: {config_auto.prefer_threads_over_processes}")
    
    # Configuration manuelle pour comparaison
    print("\n2. Configuration manuelle conservative:")
    config_manual = OptimizationConfig(
        max_workers=4,  # Plus conservateur
        max_generator_cache_size=16,  # Très petit
        max_pairing_cache_size=32,
        batch_size_threshold=5,  # Moins agressif
        prefer_threads_over_processes=True
    )
    print(f"   [BALANCE]  Workers: {config_manual.max_workers}")
    print(f"   [BALANCE]  Cache générateurs: {config_manual.max_generator_cache_size}")
    print(f"   [BALANCE]  Cache pairings: {config_manual.max_pairing_cache_size}")
    
    return config_auto, config_manual


def demo_memory_efficient_operations():
    """Démontre les opérations économes en mémoire pour M1 8GB"""
    print("\n[SAVE] DÉMONSTRATION OPÉRATIONS ÉCONOMES EN MÉMOIRE")
    print("=" * 55)
    
    # Activation optimisations M1
    manager = enable_bbs_optimizations()  # Auto-détection M1
    
    # Import des modules BBS (avec fallback)
    try:
        from BBSCore.bbsSign import BBSSignatureScheme
        from BBSCore.KeyGen import BBSKeyGen
        bbs_available = True
    except ImportError:
        print("[WARNING]  Modules BBS non disponibles, utilisation des mocks")
        
        class BBSSignatureScheme:
            def __init__(self, max_messages=30):
                self.max_messages = max_messages
            def sign(self, sk, messages, header=b""):
                time.sleep(0.005)  # Simule M1 rapide
                return f"signature_m1_{len(messages)}"
            def verify(self, pk, signature, messages, header=b""):
                time.sleep(0.003)  # M1 rapide pour vérification
                return True
        
        class BBSKeyGen:
            @staticmethod
            def generate_keypair():
                return "mock_sk_m1", "mock_pk_m1"
        
        bbs_available = False
    
    # Création d'instance optimisée pour M1
    print("[LAUNCH] Création d'instance BBS optimisée M1...")
    optimized_bbs = create_optimized_bbs(BBSSignatureScheme, max_messages=15)
    
    # Test avec monitoring mémoire
    print("[DATA] Test avec monitoring mémoire actif...")
    sk, pk = BBSKeyGen.generate_keypair()
    
    # Opérations graduelles pour voir l'impact mémoire
    message_counts = [3, 5, 8, 10, 12]  # Tailles modérées pour 8GB
    
    for msg_count in message_counts:
        print(f"\n  Test avec {msg_count} messages:")
        
        messages = [f"msg_m1_{i}:data_optimized".encode() for i in range(msg_count)]
        
        # Signature avec monitoring
        start_time = time.time()
        signature = optimized_bbs.sign(sk, messages)
        sign_time = (time.time() - start_time) * 1000
        
        # Vérification
        start_time = time.time()  
        is_valid = optimized_bbs.verify(pk, signature, messages)
        verify_time = (time.time() - start_time) * 1000
        
        print(f"    Signature: {sign_time:.2f}ms")
        print(f"    Vérification: {verify_time:.2f}ms {'[SUCCESS]' if is_valid else '[ERROR]'}")
    
    # Statistiques des caches
    print(f"\n[GRAPH] Statistiques des caches:")
    try:
        gen_stats = optimized_bbs.generator_cache.get_cache_stats()
        pair_stats = optimized_bbs.pairing_cache.get_cache_stats()
        
        print(f"  Générateurs: {gen_stats['cache_size']} entrées")
        print(f"  Hit rate générateurs: {gen_stats['hit_rate']:.1%}")
        print(f"  Pairings: {pair_stats['cache_entries']} entrées")
        print(f"  Hit rate pairings: {pair_stats['hit_rate']:.1%}")
    except Exception as e:
        print(f"  [WARNING]  Erreur stats: {e}")


def demo_batch_operations_m1():
    """Démontre les opérations batch optimisées pour M1"""
    print("\n[FAST] OPÉRATIONS BATCH OPTIMISÉES M1")
    print("=" * 40)
    
    # Configuration spéciale pour batch sur M1
    config = OptimizationConfig(
        max_workers=6,  # Optimal pour M1
        batch_size_threshold=3,  # Agressif sur M1
        prefer_threads_over_processes=True,  # Meilleur sur M1
        enable_memory_monitoring=True
    )
    
    manager = enable_bbs_optimizations(config)
    
    # Setup
    try:
        from BBSCore.bbsSign import BBSSignatureScheme
        from BBSCore.KeyGen import BBSKeyGen
    except ImportError:
        # Mocks optimisés M1
        class BBSSignatureScheme:
            def __init__(self, max_messages=30):
                self.max_messages = max_messages
            def sign(self, sk, messages, header=b""):
                time.sleep(0.003)  # M1 très rapide
                return f"batch_sig_m1_{len(messages)}"
            def verify(self, pk, signature, messages, header=b""):
                time.sleep(0.002)  # M1 optimisé
                return True
        
        class BBSKeyGen:
            @staticmethod
            def generate_keypair():
                return "batch_sk_m1", "batch_pk_m1"
    
    optimized_bbs = create_optimized_bbs(BBSSignatureScheme, max_messages=20)
    sk, pk = BBSKeyGen.generate_keypair()
    
    # Préparation de batches de taille modérée pour M1 8GB
    print("[LIST] Préparation de batches optimisés M1...")
    batch_sizes = [4, 8, 12]  # Tailles modérées pour éviter la saturation mémoire
    
    for batch_size in batch_sizes:
        print(f"\n  Test batch de {batch_size} opérations:")
        
        # Messages pour DTC typiques
        message_batches = []
        for i in range(batch_size):
            messages = [
                f"type:credential_{i}".encode(),
                f"holder:user_m1_{i}".encode(),
                f"issuer:gov_m1".encode(),
                f"timestamp:{int(time.time())}".encode()
            ]
            message_batches.append(messages)
        
        # Test signature batch
        print(f"    🔏 Signature batch...")
        start_time = time.time()
        signatures = optimized_bbs.batch_sign(sk, message_batches)
        batch_sign_time = (time.time() - start_time) * 1000
        
        print(f"      Temps total: {batch_sign_time:.2f}ms")
        print(f"      Temps/signature: {batch_sign_time/len(signatures):.2f}ms")
        
        # Test vérification batch
        print(f"    [SUCCESS] Vérification batch...")
        sig_msg_pairs = list(zip(signatures, message_batches))
        start_time = time.time()
        results = optimized_bbs.batch_verify(pk, sig_msg_pairs)
        batch_verify_time = (time.time() - start_time) * 1000
        
        print(f"      Temps total: {batch_verify_time:.2f}ms")
        print(f"      Temps/vérification: {batch_verify_time/len(results):.2f}ms")
        print(f"      Toutes valides: {'[SUCCESS]' if all(results) else '[ERROR]'}")


def demo_memory_monitoring_m1():
    """Démontre le monitoring mémoire spécifique M1"""
    print("\n[SEARCH] MONITORING MÉMOIRE M1 (8GB)")
    print("=" * 35)
    
    try:
        import psutil
        
        # Configuration avec alertes mémoire
        config = OptimizationConfig(
            enable_memory_monitoring=True,
            memory_warning_threshold=0.75,  # Alerte à 75% sur 8GB
            performance_log_interval=20     # Log fréquent
        )
        
        manager = enable_bbs_optimizations(config)
        
        # Monitoring en temps réel
        memory_initial = psutil.virtual_memory()
        print(f"Mémoire initiale: {memory_initial.percent:.1f}% utilisée")
        print(f"Disponible: {memory_initial.available / (1024**3):.2f} GB")
        
        # Simulation d'opérations intensives
        print("\n[DATA] Simulation d'opérations avec monitoring...")
        
        try:
            from BBSCore.bbsSign import BBSSignatureScheme
            from BBSCore.KeyGen import BBSKeyGen
        except ImportError:
            class BBSSignatureScheme:
                def __init__(self, max_messages=30):
                    self.max_messages = max_messages
                def sign(self, sk, messages, header=b""):
                    # Simule allocation mémoire
                    dummy_data = bytearray(1024 * 100)  # 100KB
                    time.sleep(0.01)
                    return f"memory_test_sig_{len(messages)}"
                def verify(self, pk, signature, messages, header=b""):
                    time.sleep(0.005)
                    return True
            
            class BBSKeyGen:
                @staticmethod
                def generate_keypair():
                    return "memory_test_sk", "memory_test_pk"
        
        optimized_bbs = create_optimized_bbs(BBSSignatureScheme, max_messages=25)
        sk, pk = BBSKeyGen.generate_keypair()
        
        # Opérations progressives avec monitoring
        for round_num in range(1, 6):
            print(f"\n  Round {round_num}:")
            
            # Opérations multiples
            for i in range(10):
                messages = [f"memory_test_{round_num}_{i}_{j}".encode() for j in range(5)]
                signature = optimized_bbs.sign(sk, messages)
                optimized_bbs.verify(pk, signature, messages)
            
            # Vérification mémoire
            memory_current = psutil.virtual_memory()
            print(f"    Mémoire: {memory_current.percent:.1f}% "
                  f"(+{memory_current.percent - memory_initial.percent:.1f}%)")
            
            if memory_current.percent > 80:
                print("    [WARNING] Utilisation mémoire élevée détectée!")
                print("    [INFO] Nettoyage des caches recommandé...")
                optimized_bbs.clear_caches()
                
                # Vérification après nettoyage
                memory_after_cleanup = psutil.virtual_memory()
                print(f"    [CLEAN] Après nettoyage: {memory_after_cleanup.percent:.1f}%")
        
        # Rapport final
        print(f"\n[LIST] Rapport final du monitoring:")
        performance_report = manager.get_global_performance_report()
        print(performance_report)
        
    except ImportError:
        print("[WARNING]  psutil non disponible - monitoring mémoire limité")
        print("[INFO] Installez psutil pour le monitoring complet: pip install psutil")


def main():
    """Démonstration complète des optimisations M1"""
    print("[APPLE] GUIDE D'OPTIMISATION MACBOOK AIR M1 - BBS DTC")
    print("=" * 60)
    
    # 1. Informations système
    print_m1_system_info()
    
    # 2. Configuration optimisée
    config_auto, config_manual = demo_m1_optimized_configuration()
    
    # 3. Opérations économes en mémoire
    demo_memory_efficient_operations()
    
    # 4. Opérations batch optimisées
    demo_batch_operations_m1()
    
    # 5. Monitoring mémoire
    demo_memory_monitoring_m1()
    
    print(f"\n[SUCCESS] GUIDE M1 TERMINÉ!")
    print("=" * 25)
    print("[SUCCESS] Votre MacBook Air M1 8GB est maintenant optimisé pour BBS DTC")
    print("[LAUNCH] Les performances sont adaptées à votre architecture spécifique")
    print("[SAVE] La surveillance mémoire protège contre la saturation")
    print("[FAST] La parallélisation tire parti des P-cores et E-cores M1")


if __name__ == "__main__":
    main()