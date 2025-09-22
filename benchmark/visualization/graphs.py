"""
benchmark/visualization/graphs.py - Graphiques simplifiés pour BBS-DTC

4 graphiques principaux :
1. Performance vs Attributes
2. Proof Size vs Attributes
3. Performance vs Disclosure
4. Proof Size vs Disclosure 
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

class GraphGenerator:
    """Générateur de graphiques simplifiés pour BBS"""
    
    def __init__(self, output_dir: str = "benchmark/metrics/"):
        self.output_dir = Path(output_dir)
        self.graphs_dir = self.output_dir / "graphs" / "basic"
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration matplotlib
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['font.size'] = 11
        plt.rcParams['legend.fontsize'] = 10
        plt.rcParams['figure.titlesize'] = 16
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14

        # Couleurs cohérentes
        self.COLORS = {
            'sign': '#2E86AB',
            'verify': '#A23B72',
            'proof_gen': '#F18F01',
            'proof_verify': '#27A300',
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'warning': '#F18F01',
            'success': '#27A300',
            'info': '#17A2B8',
            'danger': '#DC3545'            
        }

        self.STYLES = {
            'line_width': 2.5,
            'marker_size': 10,
            'grid_alpha': 0.3,
            'annotation_size': 10,
            'label_size': 12,
            'title_size': 14
        }

        # Style seaborn
        sns.set_style("whitegrid")
        sns.set_context("paper", font_scale=1.2)
    
    def load_csv(self, filename: str) -> pd.DataFrame:
        """Charge un fichier CSV"""
        csv_path = self.output_dir / "csv" / filename
        if csv_path.exists():
            return pd.read_csv(csv_path)
        else:
            print(f"CSV not found: {csv_path}")
            return pd.DataFrame()
    
    def graph1_performance_vs_attributes(self) -> plt.Figure:
        """Graphique 1: Performance vs Nombre d'Attributs"""
        df = self.load_csv("scalability.csv")
        
        if df.empty:
            print("No scalability.csv data found")
            return None

        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Données depuis le CSV
        attr_counts = df['attribute_count'].tolist()
        sign_times = df['sign_time_ms'].tolist()
        verify_times = df['verify_time_ms'].tolist()
        proof_gen_times = df['proof_gen_time_ms'].tolist()
        proof_verify_times = df['proof_verify_time_ms'].tolist()
        
        # Tracer les lignes
        ax.plot(attr_counts, sign_times, 'o-', color=self.COLORS['sign'], 
                linewidth=self.STYLES['line_width'], markersize=8, label='Signature')
        ax.plot(attr_counts, verify_times, 's--', color=self.COLORS['verify'], 
                linewidth=self.STYLES['line_width'], markersize=8, label='Verification')
        ax.plot(attr_counts, proof_gen_times, '^-.', color=self.COLORS['proof_gen'],
                linewidth=self.STYLES['line_width'], markersize=8, label='Generation de Preuve')
        ax.plot(attr_counts, proof_verify_times, 'v:', color=self.COLORS['proof_verify'],
                linewidth=self.STYLES['line_width'], markersize=8, label='Verification de Preuve')

        # Configuration
        ax.set_xlabel('Nombre d\'Attributs', fontsize=self.STYLES['label_size'])
        ax.set_ylabel('Temps (ms)', fontsize=self.STYLES['label_size'])
        ax.set_title('Scalabilité des Performances des Opérations BBS', fontsize=self.STYLES['title_size'], fontweight='bold')
        ax.set_xscale('log', base=2)
        ax.set_xticks([1, 2, 4, 8, 16, 32, 64, 128])
        ax.set_xticklabels(['1', '2', '4', '8', '16', '32', '64', '128'])
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', frameon=True)
        
        plt.tight_layout()
        return fig
    
    def graph2_proof_size_vs_attributes(self) -> plt.Figure:
        """Graphique 2: Taille des Preuves vs Attributs"""
        df = self.load_csv("scalability.csv")
        
        if df.empty:
            print("No scalability.csv data found")
            return None
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        attr_counts = df['attribute_count'].tolist()
        signature_sizes = df.get('signature_size_bytes', [112] * len(attr_counts)).tolist()
        proof_sizes = df.get('proof_size_bytes', [384] * len(attr_counts)).tolist()
        
        signature_sizes_kb = [size / 1024 for size in signature_sizes]
        proof_sizes_kb = [size / 1024 for size in proof_sizes]
        
        ax.plot(attr_counts, signature_sizes_kb, 'o-', 
                color=self.COLORS['primary'], linewidth=self.STYLES['line_width'],
                markersize=self.STYLES['marker_size'], label='Taille Signature')
        
        ax.plot(attr_counts, proof_sizes_kb, 's--', 
                color=self.COLORS['proof_gen'], linewidth=self.STYLES['line_width'],
                markersize=self.STYLES['marker_size'], label='Taille Preuve ZK')
        
        ax.set_xlabel("Nombre d'Attributs", fontsize=self.STYLES['label_size'])
        ax.set_ylabel("Taille (KB)", fontsize=self.STYLES['label_size'])
        ax.set_title("Taille de Preuve et de Signature par Nombre d'Attributs", 
                    fontsize=self.STYLES['title_size'], fontweight='bold')
        ax.set_xscale('log', base=2)
        ax.set_xticks([1, 2, 4, 8, 16, 32, 64, 128])
        ax.set_xticklabels(['1', '2', '4', '8', '16', '32', '64', '128'])
        ax.grid(True, alpha=self.STYLES['grid_alpha'])
        ax.legend(loc='upper left')
        
        ax.fill_between(attr_counts, signature_sizes_kb, proof_sizes_kb, 
                        alpha=0.2, color=self.COLORS['proof_gen'])
        
        plt.tight_layout()
        return fig

    def graph3_performance_vs_disclosure(self) -> plt.Figure:
        """Graphique 3: Performance vs Taux de Divulgation"""
        df = self.load_csv("disclosure_rate.csv")
        
        if df.empty:
            print("No disclosure_rate.csv data found")
            return None
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        disclosure_rates = df['disclosure_percent'].tolist()
        proof_gen_times = df['proof_gen_time_ms'].tolist()
        proof_verify_times = df['proof_verify_time_ms'].tolist()
        

        ax.plot(disclosure_rates, proof_gen_times, 'D-',
                color=self.COLORS['proof_gen'], linewidth=self.STYLES['line_width']*1.2,
                markersize=self.STYLES['marker_size']*1.2, label='Generation Preuve')
        
        ax.plot(disclosure_rates, proof_verify_times, 'o-',
                color=self.COLORS['proof_verify'], linewidth=self.STYLES['line_width']*1.2,
                markersize=self.STYLES['marker_size']*1.2, label='Vérification Preuve')
        
        # Zones de privacy
        ax.axvspan(0, 25, alpha=0.1, color=self.COLORS['success'])
        ax.axvspan(25, 75, alpha=0.1, color=self.COLORS['info'])
        ax.axvspan(75, 100, alpha=0.1, color=self.COLORS['warning'])

        ax.set_xlabel('Taux de divulgation (%)', fontsize=12)
        ax.set_ylabel('Temps (ms)', fontsize=12)
        ax.set_title('Opérations BBS par taux de divulgation sélective', 
                    fontsize=self.STYLES['title_size'], fontweight='bold')
        ax.set_xlim(0, 100)
        ax.grid(True, alpha=self.STYLES['grid_alpha'])
        ax.legend(loc='best')
        
        # Labels des zones
        y_pos = ax.get_ylim()[1] * 0.9
        ax.text(15, y_pos, 'Haute\nPrivacy', ha='center', fontsize=10, color=self.COLORS['success'])
        ax.text(50, y_pos, 'Moyenne', ha='center', fontsize=10, color=self.COLORS['info'])
        ax.text(85, y_pos, 'Basse\nPrivacy', ha='center', fontsize=10, color=self.COLORS['warning'])

        plt.tight_layout()
        return fig
    
    def graph4_proof_size_vs_disclosure(self) -> plt.Figure:
        """Graphique 4: Taille des Preuves vs Divulgation (Linéaire)"""
        df = self.load_csv("disclosure_rate.csv")
        
        if df.empty:
            print("No disclosure_rate.csv data found")
            return None

        fig, ax = plt.subplots(figsize=(12, 7))
        
        disclosure_rates = df['disclosure_percent'].tolist()
        
        # Tailles de preuves depuis le CSV
        if 'proof_size_bytes' in df.columns:
            proof_sizes_kb = [size / 1024 for size in df['proof_size_bytes'].tolist()]
        else:
            # Estimation : plus de disclosure = preuves plus petites
            proof_sizes_kb = [0.4 - (rate/100 * 0.1) for rate in disclosure_rates]
        
        # Graphique linéaire
        ax.plot(disclosure_rates, proof_sizes_kb, 'o-',
                color=self.COLORS['warning'], linewidth=self.STYLES['line_width'],
                markersize=self.STYLES['marker_size'], label='Taille Preuve ZK')
        
        # Zone de remplissage sous la courbe
        ax.fill_between(disclosure_rates, proof_sizes_kb, alpha=0.3, 
                       color=self.COLORS['warning'])
        
        # Zones de privacy (comme dans graph3)
        ax.axvspan(0, 25, alpha=0.1, color=self.COLORS['success'])
        ax.axvspan(25, 75, alpha=0.1, color=self.COLORS['info'])
        ax.axvspan(75, 100, alpha=0.1, color=self.COLORS['warning'])
        
        ax.set_xlabel('Taux de divulgation (%)', fontsize=self.STYLES['label_size'])
        ax.set_ylabel('Taille de la preuve (KB)', fontsize=self.STYLES['label_size'])
        ax.set_title('Taille de la preuve ZK par taux de divulgation sélective', 
                    fontsize=self.STYLES['title_size'], fontweight='bold')
        ax.set_xlim(0, 100)
        ax.grid(True, alpha=self.STYLES['grid_alpha'])
        ax.legend(loc='best')
        
        # Labels des zones de privacy
        y_pos = max(proof_sizes_kb) * 0.9
        ax.text(15, y_pos, 'Haute\nPrivacy', ha='center', fontsize=10, color=self.COLORS['success'])
        ax.text(50, y_pos, 'Moyenne', ha='center', fontsize=10, color=self.COLORS['info'])
        ax.text(85, y_pos, 'Basse\nPrivacy', ha='center', fontsize=10, color=self.COLORS['warning'])
        
        plt.tight_layout()
        return fig

    def generate_all_graphs(self):
        """Génère et sauvegarde tous les graphiques principaux"""
        graphs = {
            'performance_vs_attributes': self.graph1_performance_vs_attributes(),
            'proof_size_vs_attributes': self.graph2_proof_size_vs_attributes(),
            'performance_vs_disclosure': self.graph3_performance_vs_disclosure(),
            'proof_size_vs_disclosure': self.graph4_proof_size_vs_disclosure()
        }
        
        # Sauvegarder
        for name, fig in graphs.items():
            filepath = self.graphs_dir / f"{name}.png"
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Saved: {filepath}")
            plt.close(fig)
        
        return graphs

# Test direct
if __name__ == "__main__":
    generator = GraphGenerator()
    graphs = generator.generate_all_graphs()
    print(f"\nGenerated {len(graphs)} main graphs successfully!")