#!/usr/bin/env python3
"""
BBS Digital Trust Certificate - Main Entry Point
Main entry point with performance optimizations and command delegation
"""

import sys
import argparse
import time

try:
    from performance_optimizer import (
        enable_bbs_optimizations,
        M1OptimizationDetector,
        BBSPerformanceManager
    )
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False

DEFAULT_USER = "Ellen Kampire"

def print_banner():
    """Display project banner"""
    print("\nBBS Digital Trust Certificate (DTC)")
    print("Privacy-Preserving Travel Credentials")
    print("-" * 50)

def setup_optimizations(args):
    """Configure and enable performance optimizations with architecture detection"""
    if not OPTIMIZATION_AVAILABLE or args.no_optimization:
        if args.no_optimization:
            print("Performance optimizations disabled")
        return None
        
    print("Configuring performance optimizations...")
    
    # Automatic M1 architecture detection
    if M1OptimizationDetector.is_apple_silicon():
        print("Apple Silicon detected - applying optimized configuration")
        config = M1OptimizationDetector.create_m1_optimized_config()
    else:
        print("Standard architecture detected - using default configuration")
        from performance_optimizer import OptimizationConfig
        config = OptimizationConfig()

    # Enable optimizations
    manager = enable_bbs_optimizations(config)
    print(f"Optimizations enabled - Workers: {config.max_workers}")
    
    return manager


def run_benchmark_with_ellen(args, perf_manager):
    """Execute benchmarks with default scenario"""
    print("Starting benchmarks...")
    try:
        from benchmark.runner import BenchmarkRunner
        
        # CORRECTION: Créer le runner sans custom_file
        runner = BenchmarkRunner(
            config_name='standard',
            perf_manager=perf_manager
        )
        
        # CORRECTION: Passer custom_file en paramètre si nécessaire
        profile_name = args.custom_user if args.custom_user else "ellen_kampire_dtc"
        
        # Appeler run_default_benchmarks avec le bon profil
        if hasattr(runner, 'run_default_benchmarks'):
            if args.custom_user:
                # Si un profil personnalisé est spécifié
                runner.run_default_benchmarks(profile_name=profile_name)
            else:
                # Utiliser le profil par défaut
                runner.run_default_benchmarks()
        else:
            # Fallback vers d'autres méthodes disponibles
            if hasattr(runner, 'run_benchmarks'):
                runner.run_benchmarks()
            elif hasattr(runner, 'run'):
                runner.run()
            else:
                print("No suitable benchmark method found")
                return False
        
        if args.visualize:
            print("Generating visualization graphs...")
            try:
                if hasattr(runner, 'graphs_dir'):
                    print(f"Graphs generated in {runner.graphs_dir}")
                elif hasattr(runner, 'generate_graphs'):
                    runner.generate_graphs()
                    print("Graphs generated successfully")
                else:
                    print("Visualization not available")
            except Exception as viz_error:
                print(f"Visualization error (non-critical): {viz_error}")
        
        return True
        
    except ImportError as e:
        print(f"Benchmark module not available: {e}")
        return False
    except Exception as e:
        print(f"Error executing benchmarks: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        
        try:
            print("Trying fallback benchmark execution...")
            import subprocess
            cmd = [sys.executable, "-m", "benchmark.runner"]
            if args.custom_user:
                cmd.extend(["--profile", args.custom_user])
            if args.visualize:
                cmd.append("--visualize")
            
            result = subprocess.run(cmd, capture_output=False)
            return result.returncode == 0
            
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
            return False

def run_demo(args, perf_manager):
    """Execute demonstration scenarios"""
    print("Running BBS-DTC demonstration...")
    try:
        # CORRECTION: Importer et exécuter la fonction main directement
        sys.argv = ['dtc_complete.py']
        if args.custom_user:
            sys.argv.append(args.custom_user)
        
        from Demo.dtc_complete import main as demo_main
        demo_main()
        return True
    except ImportError:
        print("Demo module not available")
        return False
    except Exception as e:
        print(f"Error running demo: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False

def run_travel_demo(args, perf_manager):
    """Execute travel demonstration"""
    print("Running travel demonstration...")
    try:
        # CORRECTION: Configurer sys.argv pour le module
        sys.argv = ['demo_travel.py']
        if args.custom_user:
            sys.argv.append(args.custom_user)
            
        from Demo.demo_travel import main as travel_main
        travel_main()
        return True
    except ImportError:
        print("Travel demo module not available")
        return False
    except Exception as e:
        print(f"Error running travel demo: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False

def run_credential_issuance(args, perf_manager):
    """Execute credential issuance demonstration"""
    print("Running credential issuance demonstration...")
    try:
        from Demo.credential_issuance import main as credential_main
        credential_main()
        return True
    except ImportError:
        print("Credential issuance demo module not available")
        return False
    except Exception as e:
        print(f"Error running credential issuance demo: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False

def run_auto_privacy(args, perf_manager):
    """Execute automatic privacy protection demonstration"""
    print("Running automatic privacy protection demonstration...")
    try:
        from Demo.auto_privacy import main as privacy_main
        privacy_main()
        return True
    except ImportError:
        print("Auto privacy demo module not available")
        return False
    except Exception as e:
        print(f"Error running auto privacy demo: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False

def run_blind_signature(args, perf_manager):
    """Execute blind signature demonstration"""
    print("Running blind signature demonstration...")
    try:
        from Demo.blind_signature import main as blind_main
        blind_main()
        return True
    except ImportError:
        print("Blind signature demo module not available")
        return False
    except Exception as e:
        print(f"Error running blind signature demo: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False

def run_interactive_disclosure(args, perf_manager):
    """Execute interactive disclosure demonstration"""
    print("Running interactive disclosure demonstration...")
    try:
        from Demo.interactive_disclosure import main as interactive_main
        interactive_main()
        return True
    except ImportError:
        print("Interactive disclosure demo module not available")
        return False
    except Exception as e:
        print(f"Error running interactive disclosure demo: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False

def run_all_commands(args, perf_manager):
    """Execute all available commands"""
    print("Running complete BBS-DTC suite...")
    
    commands = [
        ("demo", run_demo),
        ("travel", run_travel_demo),
        ("credential", run_credential_issuance),
        ("privacy", run_auto_privacy),
        ("blind", run_blind_signature),
        ("interactive", run_interactive_disclosure),
        ("benchmark", run_benchmark_with_ellen)
    ]
    
    results = {}
    for name, func in commands:
        print(f"\n--- Executing {name} ---")
        try:
            results[name] = func(args, perf_manager)
        except Exception as e:
            print(f"Failed to execute {name}: {e}")
            results[name] = False
    
    # Summary
    print("\n--- Execution Summary ---")
    for name, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{name}: {status}")
    
    return all(results.values())

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="BBS-DTC Demo & Benchmark Suite")
    parser.add_argument("command", 
                       choices=["demo", "travel", "credential", "privacy", 
                               "blind", "interactive", "benchmark", "all"], 
                       help="Command to execute")
    parser.add_argument("--verbose", "-v", 
                       action="store_true", 
                       help="Enable verbose output")
    parser.add_argument("--no-optimization", 
                       action="store_true", 
                       help="Disable performance optimizations")
    parser.add_argument("--visualize", 
                       action="store_true", 
                       help="Generate visualization graphs for benchmarks")
    parser.add_argument("--custom-user", "-u", 
                       type=str, 
                       help=f"Use custom JSON file instead of {DEFAULT_USER}")
    
    args = parser.parse_args()

    # Setup performance optimizations
    perf_manager = setup_optimizations(args)

    try:
        success = False
        
        if args.command == "demo":
            success = run_demo(args, perf_manager)
        elif args.command == "travel":
            success = run_travel_demo(args, perf_manager)
        elif args.command == "credential":
            success = run_credential_issuance(args, perf_manager)
        elif args.command == "privacy":
            success = run_auto_privacy(args, perf_manager)
        elif args.command == "blind":
            success = run_blind_signature(args, perf_manager)
        elif args.command == "interactive":
            success = run_interactive_disclosure(args, perf_manager)
        elif args.command == "benchmark":
            success = run_benchmark_with_ellen(args, perf_manager)
        elif args.command == "all":
            success = run_all_commands(args, perf_manager)
        
        if success:
            print("\nExecution completed successfully")
        else:
            print("\nExecution completed with errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nExecution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup optimizations
        if perf_manager:
            if args.verbose:
                print("Cleaning up optimizations...")
                final_report = perf_manager.get_global_performance_report()
                print(final_report)

if __name__ == "__main__":
    main()