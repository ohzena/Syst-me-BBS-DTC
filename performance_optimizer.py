# performance_optimizer.py - Version Améliorée
"""
Performance Optimization Module for BBS Signature Scheme
Implements advanced caching, memoization, and parallel processing
Optimized for the BBS DTC (Digital Trust Certificate) system
"""

import hashlib
import pickle
import time
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from functools import lru_cache, wraps
from typing import List, Dict, Any, Optional, Callable, Tuple, Union
import multiprocessing as mp
from dataclasses import dataclass, field
import numpy as np
import weakref
from collections import OrderedDict
import logging
import platform
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration avancée pour les optimisations de performance - Optimisée pour M1"""
    enable_generator_cache: bool = True
    enable_pairing_cache: bool = True
    enable_parallel_processing: bool = True
    enable_precomputation: bool = True
    enable_memory_pooling: bool = True
    
    # Tailles de cache optimisées pour 8GB RAM M1
    max_generator_cache_size: int = 64   # Réduit pour M1 8GB
    max_pairing_cache_size: int = 128    # Conservateur pour la mémoire
    max_point_cache_size: int = 256      # Adapté à la mémoire limitée
    
    # Parallélisation optimisée pour M1 (4P+4E cores)
    max_workers: Optional[int] = None  # Auto-détection M1
    batch_size_threshold: int = 3      # Plus agressif sur M1
    prefer_threads_over_processes: bool = True  # M1 préfère les threads
    
    # Précomputation adaptée pour M1
    precompute_common_generators: bool = True
    precompute_window_size: int = 3    # Plus petit pour M1
    max_precompute_parallel: int = 2   # Limité pour économiser la mémoire
    
    # Monitoring léger pour M1
    enable_detailed_timing: bool = True
    enable_memory_monitoring: bool = True
    performance_log_interval: int = 50  # Plus fréquent sur M1
    memory_warning_threshold: float = 0.85  # Alerte à 85% RAM


class M1OptimizationDetector:
    """Détecte et optimise spécifiquement pour les puces Apple M1/M2"""
    
    @staticmethod
    def is_apple_silicon():
        """Détecte si on est sur Apple Silicon (M1/M2)"""
        try:
            return (platform.system() == 'Darwin' and 
                    platform.machine() in ['arm64', 'aarch64'])
        except:
            return False
    
    @staticmethod
    def get_optimal_worker_count():
        """Calcule le nombre optimal de workers pour M1"""
        if not M1OptimizationDetector.is_apple_silicon():
            return mp.cpu_count()
        
        # Sur M1: 4 cores de performance + 4 cores d'efficacité
        # Pour les opérations crypto, privilégier les cores de performance
        cpu_count = mp.cpu_count()
        
        if cpu_count == 8:  # M1 standard
            # Utiliser 6 workers: 4 P-cores + 2 E-cores pour éviter la saturation
            return 6
        elif cpu_count >= 10:  # M1 Pro/Max/Ultra
            # Utiliser 75% des cores pour laisser de la place au système
            return max(6, int(cpu_count * 0.75))
        else:
            # Fallback conservateur
            return max(2, cpu_count - 2)
    
    @staticmethod
    def get_memory_optimized_cache_sizes():
        """Calcule les tailles de cache optimales pour la mémoire disponible"""
        try:
            # Essai de détecter la RAM avec psutil
            import psutil
            total_ram_gb = psutil.virtual_memory().total / (1024**3)
            
            if total_ram_gb <= 8:  # 8GB RAM (MacBook Air M1)
                return {
                    'generator_cache': 32,
                    'pairing_cache': 64,
                    'point_cache': 128
                }
            elif total_ram_gb <= 16:  # 16GB RAM
                return {
                    'generator_cache': 64,
                    'pairing_cache': 128,
                    'point_cache': 256
                }
            else:  # 32GB+ RAM
                return {
                    'generator_cache': 128,
                    'pairing_cache': 256,
                    'point_cache': 512
                }
        except ImportError:
            # Fallback conservateur si psutil n'est pas disponible
            return {
                'generator_cache': 32,
                'pairing_cache': 64,
                'point_cache': 128
            }
    
    @staticmethod
    def create_m1_optimized_config() -> OptimizationConfig:
        """Crée une configuration optimisée pour M1"""
        cache_sizes = M1OptimizationDetector.get_memory_optimized_cache_sizes()
        
        return OptimizationConfig(
            # Caches optimisés pour la mémoire
            max_generator_cache_size=cache_sizes['generator_cache'],
            max_pairing_cache_size=cache_sizes['pairing_cache'],
            max_point_cache_size=cache_sizes['point_cache'],
            
            # Workers optimisés pour M1
            max_workers=M1OptimizationDetector.get_optimal_worker_count(),
            batch_size_threshold=3,  # Plus agressif sur M1
            prefer_threads_over_processes=True,
            
            # Précomputation adaptée
            precompute_window_size=3,
            max_precompute_parallel=2,
            
            # Monitoring adapté
            performance_log_interval=50,
            memory_warning_threshold=0.85,
            
            # Activations standard
            enable_generator_cache=True,
            enable_pairing_cache=True,
            enable_parallel_processing=True,
            enable_precomputation=True,
            enable_memory_pooling=True,
            enable_detailed_timing=True,
            enable_memory_monitoring=True
        )


class AdvancedPerformanceMonitor:
    """Monitoring avancé des performances avec statistiques détaillées"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.metrics = {}
        self.memory_usage = {}
        self.operation_count = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def record_operation(self, operation: str, duration: float, memory_delta: int = 0):
        """Enregistre une opération avec timing et usage mémoire"""
        with self.lock:
            if operation not in self.metrics:
                self.metrics[operation] = {
                    'times': [],
                    'memory_deltas': [],
                    'count': 0,
                    'total_time': 0,
                    'last_recorded': time.time()
                }
            
            self.metrics[operation]['times'].append(duration)
            self.metrics[operation]['memory_deltas'].append(memory_delta)
            self.metrics[operation]['count'] += 1
            self.metrics[operation]['total_time'] += duration
            self.metrics[operation]['last_recorded'] = time.time()
            
            self.operation_count += 1
            
            # Vérification mémoire spéciale pour M1 8GB
            if (self.config.enable_memory_monitoring and 
                hasattr(self.config, 'memory_warning_threshold')):
                self._check_memory_pressure()
            
            # Log périodique si activé
            if (self.config.enable_detailed_timing and 
                self.operation_count % self.config.performance_log_interval == 0):
                self._log_summary()
    
    def _check_memory_pressure(self):
        """Vérifie la pression mémoire (important sur M1 8GB)"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100.0
            
            if memory_usage > self.config.memory_warning_threshold:
                logger.warning(f"[WARNING] Utilisation mémoire élevée: {memory_usage:.1%} "
                             f"(seuil: {self.config.memory_warning_threshold:.1%})")
                logger.info(f"[INFO] Considérez réduire les tailles de cache ou vider les caches")
        except ImportError:
            pass
    
    def _log_summary(self):
        """Log un résumé des performances"""
        uptime = time.time() - self.start_time
        logger.info(f"[PERF] Performance Summary (uptime: {uptime:.1f}s, ops: {self.operation_count})")
        
        for op, data in sorted(self.metrics.items(), key=lambda x: x[1]['total_time'], reverse=True):
            if data['count'] > 0:
                avg_time = data['total_time'] / data['count']
                logger.info(f"  {op}: {avg_time:.2f}ms avg ({data['count']} ops)")
    
    def get_detailed_stats(self, operation: str) -> Dict[str, Any]:
        """Obtient des statistiques détaillées pour une opération"""
        with self.lock:
            if operation not in self.metrics:
                return {}
            
            data = self.metrics[operation]
            times = data['times']
            
            if not times:
                return {}
            
            return {
                'count': len(times),
                'total_time': sum(times),
                'mean': np.mean(times),
                'median': np.median(times),
                'std': np.std(times),
                'min': min(times),
                'max': max(times),
                'p95': np.percentile(times, 95),
                'p99': np.percentile(times, 99),
                'ops_per_second': len(times) / (time.time() - self.start_time),
                'memory_impact': np.mean(data['memory_deltas']) if data['memory_deltas'] else 0
            }
    
    def generate_performance_report(self) -> str:
        """Génère un rapport complet de performance"""
        uptime = time.time() - self.start_time
        report = [
            "[RAPPORT] PERFORMANCE BBS DTC",
            "=" * 50,
            f"Temps de fonctionnement: {uptime:.1f}s",
            f"Opérations totales: {self.operation_count}",
            f"Taux global: {self.operation_count/uptime:.1f} ops/sec",
            "",
            "Détail par opération:"
        ]
        
        for operation in sorted(self.metrics.keys()):
            stats = self.get_detailed_stats(operation)
            if stats:
                report.append(f"  {operation}:")
                report.append(f"    Moyenne: {stats['mean']:.2f}ms")
                report.append(f"    Médiane: {stats['median']:.2f}ms")
                report.append(f"    P95: {stats['p95']:.2f}ms")
                report.append(f"    Count: {stats['count']}")
                report.append(f"    Taux: {stats['ops_per_second']:.1f} ops/sec")
                if stats['memory_impact'] != 0:
                    report.append(f"    Mémoire: {stats['memory_impact']:+.1f}MB")
                report.append("")
        
        return "\n".join(report)


def timed_operation(operation_name: str, monitor: Optional[AdvancedPerformanceMonitor] = None):
    """Décorateur avancé pour mesurer les opérations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            # Mesure mémoire si disponible
            memory_before = 0
            if monitor and monitor.config.enable_memory_monitoring:
                try:
                    import psutil
                    process = psutil.Process()
                    memory_before = process.memory_info().rss / 1024 / 1024  # MB
                except ImportError:
                    pass
            
            try:
                result = func(*args, **kwargs)
                
                # Calcul timing
                duration = (time.perf_counter() - start_time) * 1000  # ms
                
                # Calcul delta mémoire
                memory_delta = 0
                if monitor and monitor.config.enable_memory_monitoring and memory_before > 0:
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_after = process.memory_info().rss / 1024 / 1024
                        memory_delta = memory_after - memory_before
                    except ImportError:
                        pass
                
                # Enregistrement
                if monitor:
                    monitor.record_operation(operation_name, duration, memory_delta)
                
                return result
                
            except Exception as e:
                duration = (time.perf_counter() - start_time) * 1000
                if monitor:
                    monitor.record_operation(f"{operation_name}_ERROR", duration)
                raise
        
        return wrapper
    return decorator


class SmartGeneratorCache:
    """Cache intelligent des générateurs BBS avec prédiction et préchargement"""
    
    def __init__(self, config: OptimizationConfig, monitor: AdvancedPerformanceMonitor):
        self.config = config
        self.monitor = monitor
        self._cache = OrderedDict()  # LRU avec OrderedDict
        self._access_patterns = {}  # Analyse des patterns d'accès
        self._lock = threading.RLock()
        self._precomputed = set()
        
        # Précomputation des tailles communes si activée
        if config.precompute_common_generators:
            self._precompute_common_sizes()
    
    def _precompute_common_sizes(self):
        """Précompute les générateurs pour les tailles communes (optimisé M1)"""
        # Tailles communes pour DTC, mais moins sur M1 pour économiser la mémoire
        if M1OptimizationDetector.is_apple_silicon():
            common_sizes = [3, 5, 8, 10, 12]  # Plus conservateur sur M1
        else:
            common_sizes = [3, 5, 8, 10, 12, 16, 20, 32]  # Standard
        
        logger.info(f"[SETUP] Précomputation M1-optimisée des générateurs pour {common_sizes}")
        
        for size in common_sizes:
            try:
                # Cette fonction sera fournie lors de l'initialisation
                if hasattr(self, '_compute_func'):
                    self.get_generators(size, self._compute_func)
                    self._precomputed.add(size)
            except Exception as e:
                logger.warning(f"Échec précomputation pour taille {size}: {e}")
    
    @timed_operation("generator_cache_access")
    def get_generators(self, count: int, compute_func: Optional[Callable] = None) -> Any:
        """Récupère les générateurs avec cache intelligent"""
        with self._lock:
            # Mise à jour pattern d'accès
            self._access_patterns[count] = self._access_patterns.get(count, 0) + 1
            
            # Cache hit
            if count in self._cache:
                # Déplacer vers la fin (LRU)
                value = self._cache.pop(count)
                self._cache[count] = value
                return value
            
            # Cache miss - calcul nécessaire
            if not compute_func:
                return None
            
            # Éviction LRU si nécessaire
            if len(self._cache) >= self.config.max_generator_cache_size:
                # Éviction du moins récemment utilisé
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug(f"Éviction cache générateur: taille {evicted_key}")
            
            # Calcul et stockage
            try:
                generators = compute_func(count)
                self._cache[count] = generators
                
                # Prédiction: précharger les tailles voisines populaires
                self._predictive_preload(count, compute_func)
                
                return generators
                
            except Exception as e:
                logger.error(f"Erreur calcul générateurs taille {count}: {e}")
                raise
    
    def _predictive_preload(self, current_count: int, compute_func: Callable):
        """Précharge de manière prédictive les tailles voisines"""
        if not self.config.precompute_common_generators:
            return
            
        # Prédiction basée sur les patterns
        neighbors = [current_count + 1, current_count + 2, current_count * 2]
        for neighbor in neighbors:
            if (neighbor <= 128 and  # Limite raisonnable
                neighbor not in self._cache and
                len(self._cache) < self.config.max_generator_cache_size - 5):  # Garde de la place
                try:
                    threading.Thread(
                        target=lambda: self.get_generators(neighbor, compute_func),
                        daemon=True
                    ).start()
                except Exception:
                    pass  # Préchargement optionnel
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Statistiques du cache"""
        with self._lock:
            total_accesses = sum(self._access_patterns.values())
            return {
                'cache_size': len(self._cache),
                'max_size': self.config.max_generator_cache_size,
                'access_patterns': dict(sorted(self._access_patterns.items(), 
                                             key=lambda x: x[1], reverse=True)),
                'total_accesses': total_accesses,
                'precomputed_sizes': list(self._precomputed),
                'hit_rate': len(self._cache) / max(total_accesses, 1)
            }
    
    def clear_cache(self):
        """Vide le cache"""
        with self._lock:
            self._cache.clear()
            self._access_patterns.clear()
            logger.info("Cache générateurs vidé")


class AdvancedPairingCache:
    """Cache avancé pour les opérations de pairing avec compression"""
    
    def __init__(self, config: OptimizationConfig, monitor: AdvancedPerformanceMonitor):
        self.config = config
        self.monitor = monitor
        self._cache = weakref.WeakValueDictionary()
        self._strong_refs = OrderedDict()  # Références fortes LRU
        self._lock = threading.RLock()
        self._hit_count = 0
        self._miss_count = 0
    
    def _compute_cache_key(self, g1_point: Any, g2_point: Any) -> str:
        """Calcule une clé de cache optimisée"""
        try:
            # Utilise la représentation compressée des points
            g1_bytes = self._point_to_compressed_bytes(g1_point)
            g2_bytes = self._point_to_compressed_bytes(g2_point)
            
            # Hash rapide avec blake2b (plus rapide que SHA-256)
            import hashlib
            hasher = hashlib.blake2b(digest_size=16)  # 128-bit hash
            hasher.update(g1_bytes)
            hasher.update(g2_bytes)
            return hasher.hexdigest()
            
        except Exception as e:
            # Fallback vers string representation
            logger.warning(f"Fallback cache key computation: {e}")
            key_data = f"{g1_point}_{g2_point}"
            return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def _point_to_compressed_bytes(self, point: Any) -> bytes:
        """Convertit un point en représentation compressée"""
        try:
            # Si le point a une méthode to_affine(), l'utiliser
            if hasattr(point, 'to_affine'):
                point = point.to_affine()
            
            # Si le point supporte bytes(), l'utiliser
            if hasattr(point, '__bytes__'):
                return bytes(point)
            
            # Fallback vers string
            return str(point).encode()
            
        except Exception:
            return str(point).encode()
    
    @timed_operation("pairing_cache_access")
    def get_or_compute_pairing(self, g1_point: Any, g2_point: Any, 
                              compute_func: Callable) -> Any:
        """Récupère ou calcule un pairing avec cache"""
        key = self._compute_cache_key(g1_point, g2_point)
        
        with self._lock:
            # Cache hit
            if key in self._cache:
                self._hit_count += 1
                # Marquer comme récemment utilisé
                if key in self._strong_refs:
                    value = self._strong_refs.pop(key)
                    self._strong_refs[key] = value
                return self._cache[key]
            
            # Cache miss
            self._miss_count += 1
            
            # Calcul du pairing
            try:
                result = compute_func(g1_point, g2_point)
                
                # Stockage dans le cache
                self._cache[key] = result
                
                # Gestion des références fortes (LRU)
                self._strong_refs[key] = result
                if len(self._strong_refs) > self.config.max_pairing_cache_size // 2:
                    # Éviction LRU
                    self._strong_refs.popitem(last=False)
                
                return result
                
            except Exception as e:
                logger.error(f"Erreur calcul pairing: {e}")
                raise
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Statistiques du cache de pairing"""
        with self._lock:
            total = self._hit_count + self._miss_count
            return {
                'cache_entries': len(self._cache),
                'strong_refs': len(self._strong_refs),
                'hits': self._hit_count,
                'misses': self._miss_count,
                'hit_rate': self._hit_count / max(total, 1),
                'total_requests': total
            }


class ParallelBBSProcessor:
    """Processeur parallèle optimisé pour les opérations BBS - Spécialement optimisé M1"""
    
    def __init__(self, config: OptimizationConfig, monitor: AdvancedPerformanceMonitor):
        self.config = config
        self.monitor = monitor
        
        # Configuration optimisée pour M1
        if config.max_workers is None:
            self.max_workers = M1OptimizationDetector.get_optimal_worker_count()
        else:
            self.max_workers = config.max_workers
        
        self.is_m1 = M1OptimizationDetector.is_apple_silicon()
        
        # Sur M1, privilégier les threads pour les opérations crypto
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = None  # Créé uniquement si nécessaire
        
        logger.info(f"[INIT] Processeur parallèle M1-optimisé initialisé:")
        logger.info(f"   - Workers: {self.max_workers}")
        logger.info(f"   - Architecture: {'Apple M1' if self.is_m1 else 'Standard'}")
        logger.info(f"   - Préférence: {'Threads' if config.prefer_threads_over_processes else 'Processus'}")
    
    @timed_operation("parallel_batch_operation")
    def execute_batch_operation(self, operation_func: Callable, 
                               operation_args: List[Tuple],
                               use_processes: bool = False,
                               timeout: float = 30.0) -> List[Any]:
        """Exécute une opération en batch avec parallélisation intelligente (M1-optimisée)"""
        
        # Décision automatique: paralléliser seulement si ça en vaut la peine
        if len(operation_args) < self.config.batch_size_threshold:
            logger.debug(f"Batch trop petit ({len(operation_args)}), exécution séquentielle")
            return [operation_func(*args) for args in operation_args]
        
        # Sur M1, privilégier les threads sauf demande explicite
        if self.is_m1 and hasattr(self.config, 'prefer_threads_over_processes'):
            use_processes = use_processes and not self.config.prefer_threads_over_processes
        
        # Sélection du pool
        if use_processes:
            if self.process_pool is None:
                # Créer avec moins de workers pour M1 8GB
                process_workers = max(2, self.max_workers // 2) if self.is_m1 else self.max_workers
                self.process_pool = ProcessPoolExecutor(max_workers=process_workers)
                logger.info(f"[PROCESS] Process pool créé avec {process_workers} workers")
            executor = self.process_pool
        else:
            executor = self.thread_pool
        
        logger.debug(f"Exécution parallèle M1 de {len(operation_args)} opérations "
                    f"({'processus' if use_processes else 'threads'})")
        
        # Soumission des tâches avec gestion de la charge M1
        futures = []
        for args in operation_args:
            future = executor.submit(operation_func, *args)
            futures.append(future)
        
        # Collecte des résultats avec gestion d'erreurs
        results = []
        successful = 0
        failed = 0
        
        for i, future in enumerate(futures):
            try:
                # Timeout plus court sur M1 pour détecter les blocages
                actual_timeout = timeout * 0.8 if self.is_m1 else timeout
                result = future.result(timeout=actual_timeout)
                results.append(result)
                successful += 1
            except Exception as e:
                logger.error(f"Erreur tâche {i}: {e}")
                results.append(None)
                failed += 1
        
        logger.info(f"Batch M1 terminé: {successful} succès, {failed} échecs")
        return results
    
    def shutdown(self):
        """Arrêt propre des pools"""
        logger.info("[PROCESS] Arrêt des pools de threads...")
        self.thread_pool.shutdown(wait=True)
        if self.process_pool:
            self.process_pool.shutdown(wait=True)


class OptimizedBBSInterface:
    """Interface BBS optimisée - wrapper transparent"""
    
    def __init__(self, base_bbs_class, max_messages: int = 30, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.monitor = AdvancedPerformanceMonitor(self.config)
        
        # Composants d'optimisation
        self.generator_cache = SmartGeneratorCache(self.config, self.monitor)
        self.pairing_cache = AdvancedPairingCache(self.config, self.monitor)
        self.parallel_processor = ParallelBBSProcessor(self.config, self.monitor)
        
        # Instance BBS de base
        self.base_bbs = base_bbs_class(max_messages=max_messages)
        
        # Injection des optimisations dans l'instance de base
        self._inject_optimizations()
        
        logger.info(f"[READY] BBS optimisé initialisé (max_messages={max_messages})")
    
    def _inject_optimizations(self):
        """Injecte les optimisations dans l'instance BBS de base"""
        # Cette méthode sera adaptée selon votre implémentation BBS
        if hasattr(self.base_bbs, '_generator_cache'):
            self.base_bbs._generator_cache = self.generator_cache
        if hasattr(self.base_bbs, '_pairing_cache'):
            self.base_bbs._pairing_cache = self.pairing_cache
    
    @timed_operation("optimized_bbs_sign")
    def sign(self, *args, **kwargs):
        """Signature optimisée"""
        return self.base_bbs.sign(*args, **kwargs)
    
    @timed_operation("optimized_bbs_verify")
    def verify(self, *args, **kwargs):
        """Vérification optimisée"""
        return self.base_bbs.verify(*args, **kwargs)
    
    def batch_sign(self, sk, message_batches: List[List[bytes]], 
                   header: bytes = b"") -> List[Any]:
        """Signature en batch parallélisée"""
        operation_args = [(sk, messages, header) for messages in message_batches]
        return self.parallel_processor.execute_batch_operation(
            self.base_bbs.sign, operation_args
        )
    
    def batch_verify(self, pk, sig_msg_pairs: List[Tuple], 
                     header: bytes = b"") -> List[bool]:
        """Vérification en batch parallélisée"""
        operation_args = [(pk, sig, messages, header) for sig, messages in sig_msg_pairs]
        return self.parallel_processor.execute_batch_operation(
            self.base_bbs.verify, operation_args
        )
    
    def get_performance_report(self) -> str:
        """Rapport de performance détaillé"""
        report = [self.monitor.generate_performance_report()]
        
        # Statistiques des caches
        report.append("\n[CACHES] STATISTIQUES DES CACHES")
        report.append("-" * 30)
        
        gen_stats = self.generator_cache.get_cache_stats()
        report.append(f"Générateurs - Taille: {gen_stats['cache_size']}/{gen_stats['max_size']}")
        report.append(f"Générateurs - Taux de hit: {gen_stats['hit_rate']:.2%}")
        
        pair_stats = self.pairing_cache.get_cache_stats()
        report.append(f"Pairings - Entrées: {pair_stats['cache_entries']}")
        report.append(f"Pairings - Taux de hit: {pair_stats['hit_rate']:.2%}")
        
        return "\n".join(report)
    
    def clear_caches(self):
        """Vide tous les caches"""
        self.generator_cache.clear_cache()
        # Les caches de pairing utilisent weak references, pas besoin de vider explicitement
        logger.info("[CLEANUP] Tous les caches vidés")
    
    def __getattr__(self, name):
        """Délègue tous les autres attributs à l'instance BBS de base"""
        return getattr(self.base_bbs, name)


# Interface globale simplifiée
class BBSPerformanceManager:
    """Gestionnaire global des optimisations BBS"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.config = OptimizationConfig()
            self.optimized_instances = weakref.WeakSet()
            self._initialized = True
    
    def enable_optimizations(self, config: OptimizationConfig = None):
        """Active les optimisations globalement"""
        if config:
            self.config = config
        
        logger.info("[GLOBAL] Optimisations BBS activées globalement")
        logger.info(f"   - Cache générateurs: {self.config.enable_generator_cache}")
        logger.info(f"   - Cache pairings: {self.config.enable_pairing_cache}")
        logger.info(f"   - Parallélisation: {self.config.enable_parallel_processing}")
        logger.info(f"   - Workers max: {self.config.max_workers or mp.cpu_count()}")
    
    def create_optimized_bbs(self, base_bbs_class, max_messages: int = 30):
        """Crée une instance BBS optimisée"""
        optimized = OptimizedBBSInterface(base_bbs_class, max_messages, self.config)
        self.optimized_instances.add(optimized)
        return optimized
    
    def get_global_performance_report(self) -> str:
        """Rapport de performance global"""
        report = ["[GLOBAL] RAPPORT DE PERFORMANCE GLOBAL", "=" * 40]
        
        active_instances = len(self.optimized_instances)
        report.append(f"Instances BBS optimisées actives: {active_instances}")
        
        if active_instances > 0:
            report.append("\nRapports individuels:")
            for i, instance in enumerate(self.optimized_instances):
                try:
                    report.append(f"\n--- Instance {i+1} ---")
                    report.append(instance.get_performance_report())
                except Exception as e:
                    report.append(f"Erreur rapport instance {i+1}: {e}")
        
        return "\n".join(report)
    
    def clear_all_caches(self):
        """Vide tous les caches de toutes les instances"""
        for instance in self.optimized_instances:
            try:
                instance.clear_caches()
            except Exception as e:
                logger.error(f"Erreur vidage cache: {e}")


# Interface de convenance
def enable_bbs_optimizations(config: OptimizationConfig = None):
    """Active les optimisations BBS - interface simple avec détection M1"""
    manager = BBSPerformanceManager()
    
    # Auto-détection et optimisation pour M1
    if config is None and M1OptimizationDetector.is_apple_silicon():
        logger.info("[APPLE] Apple M1 détecté - utilisation de la configuration optimisée")
        config = M1OptimizationDetector.create_m1_optimized_config()
    elif config is None:
        config = OptimizationConfig()
    
    manager.enable_optimizations(config)
    return manager

def create_optimized_bbs(base_bbs_class, max_messages: int = 30):
    """Crée une instance BBS optimisée - interface simple"""
    manager = BBSPerformanceManager()
    return manager.create_optimized_bbs(base_bbs_class, max_messages)


if __name__ == "__main__":
    # Test de démonstration avec détection M1
    print("[TEST] Test du module d'optimisation BBS")
    
    # Détection de l'architecture
    is_m1 = M1OptimizationDetector.is_apple_silicon()
    if is_m1:
        print("[APPLE] Apple M1 détecté - Configuration spécialisée activée")
        
        # Affichage des optimisations M1
        optimal_workers = M1OptimizationDetector.get_optimal_worker_count()
        cache_sizes = M1OptimizationDetector.get_memory_optimized_cache_sizes()
        
        print(f"   Workers optimaux: {optimal_workers}")
        print(f"   Cache générateurs: {cache_sizes['generator_cache']}")
        print(f"   Cache pairings: {cache_sizes['pairing_cache']}")
        
        # Configuration M1
        config = M1OptimizationDetector.create_m1_optimized_config()
    else:
        print("[ARCH] Architecture standard détectée")
        config = OptimizationConfig(
            enable_generator_cache=True,
            enable_pairing_cache=True,
            enable_parallel_processing=True,
            max_workers=4
        )
    
    # Activation
    manager = enable_bbs_optimizations(config)
    
    print("[SUCCESS] Optimisations activées avec succès")
    if is_m1:
        print("[M1] Performances optimisées pour votre MacBook Air M1 8GB")
        print("[MONITORING] Surveillance automatique de la mémoire activée")
    print("[INFO] Utilisez create_optimized_bbs() pour créer des instances optimisées")