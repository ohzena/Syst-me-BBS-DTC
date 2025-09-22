#!/usr/bin/env python3
"""
generate_from_csv.py - Generateur simplifie de graphiques depuis CSV

Lit les CSV et genere directement les graphiques sans complexite
"""

import sys
from pathlib import Path
import pandas as pd
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmark.visualization.graphs import SimpleGraphGenerator
from benchmark.visualization.extra_graphs import SimpleExtraGraphGenerator

def main():
    """Genere tous les graphiques depuis les CSV"""
    
    parser = argparse.ArgumentParser(description="Genere les graphiques depuis les CSV")
    parser.add_argument('--input', '-i', default='metrics', help='Repertoire des CSV')
    parser.add_argument('--basic-only', action='store_true', help='Graphiques de base seulement')
    args = parser.parse_args()
    
    csv_dir = Path(args.input) / "csv"
    
    if not csv_dir.exists():
        print(f"Repertoire CSV non trouve: {csv_dir}")
        return 1
    
    print(f"\nGENERATION DES GRAPHIQUES DEPUIS: {csv_dir}")
    print("="*50)
    
    print("\n[1/2] Graphiques de base...")
    basic_gen = SimpleGraphGenerator(output_dir=args.input)
    basic_gen.generate_all_graphs()
    
    if not args.basic_only:
        print("\n[2/2] Graphiques avances...")
        extra_gen = SimpleExtraGraphGenerator(output_dir=args.input)
        extra_gen.generate_all_graphs()
    
    print(f"\nGraphiques generes dans: {Path(args.input) / 'graphs'}")
    return 0

if __name__ == "__main__":
    sys.exit(main())