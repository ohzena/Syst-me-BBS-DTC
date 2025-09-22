"""
benchmark/visualization/extra_graphs.py - Graphiques avancés

3 graphiques avancés:
1. Scalabilité vs Taille de lot (efficacité de traitement) 
2. Distribution du temps par opération (stacked bar)
3. Analyse des bottlenecks (heatmap)
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

class ExtraGraphGenerator:
    """Générateur de graphiques avancés"""

    def __init__(self, output_dir: str = "benchmark/metrics"):
        self.output_dir = Path(output_dir)
        self.graphs_dir = self.output_dir / "graphs" / "advanced"
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration matplotlib
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 11
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 10
        plt.rcParams['figure.titlesize'] = 16        
        
        # Configuration des couleurs
        self.COLORS = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'warning': '#F18F01',
            'success': '#27A300',
            'info': '#17A2B8',
            'danger': '#DC3545',
            'dark': '#343A40',
            'light': '#F8F9FA',
            'key_generation': '#7B68EE',
            'signature': '#2E86AB',
            'verification': '#A23B72',
            'proof_generation': '#F18F01',
            'proof_verification': '#27A300'
        }

        self.STYLES = {
            'line_width': 2.5,
            'marker_size': 10,
            'grid_alpha': 0.3,
            'annotation_size': 10,
            'label_size': 12,
            'title_size': 14
        }    
    
    def load_csv(self, filename: str) -> pd.DataFrame:
        """Charge un fichier CSV"""
        csv_path = self.output_dir / "csv" / filename
        if csv_path.exists():
            return pd.read_csv(csv_path)
        else:
            print(f"CSV not found: {csv_path}")
            return pd.DataFrame()
    
    def graph1_scalability_batch_size(self) -> plt.Figure:
        """Graphique 1: Scalabilité vs Batch Size"""
        df = self.load_csv("batch_performance.csv")
        
        if df.empty:
            raise ValueError("batch_performance.csv not found or empty. Run benchmarks first.")
        
        batch_sizes = df['batch_size'].tolist()
        # Utiliser la bonne colonne selon le collector
        if 'avg_time_per_op_ms' in df.columns:
            avg_times = df['avg_time_per_op_ms'].tolist()
        elif 'total_sign_time_ms' in df.columns:
            avg_times = df['total_sign_time_ms'].tolist()
        else:
            raise ValueError("Invalid CSV format: missing expected time columns")

        fig, ax = plt.subplots(figsize=(12, 7))
        bars = ax.bar(range(len(batch_sizes)), avg_times,
                     color=self.COLORS['secondary'], edgecolor='black', linewidth=1.5)
        
        ax.set_xlabel('Taille de lot', fontsize=self.STYLES['label_size'])
        ax.set_ylabel('Temps moyen par opération (ms)', fontsize=self.STYLES['label_size'])
        ax.set_title('Efficacité de Traitement par Lots BBS', fontsize=self.STYLES['title_size'], fontweight='bold')
        ax.set_xticks(range(len(batch_sizes)))
        ax.set_xticklabels([str(b) for b in batch_sizes])
        ax.grid(True, alpha=self.STYLES['grid_alpha'])

        # Annotation des valeurs
        for bar, val in zip(bars, avg_times):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(avg_times)*0.01,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=9)
        
        # Ligne de tendance
        z = np.polyfit(range(len(batch_sizes)), avg_times, 2)
        p = np.poly1d(z)
        ax.plot(range(len(batch_sizes)), p(range(len(batch_sizes))), 
                "o-", alpha=0.8, color=self.COLORS['warning'], linewidth=2)
        
        plt.tight_layout()
        return fig

    def graph2_time_distribution_operations(self) -> plt.Figure:
        """Graphique 2: Distribution du Temps par Opération (Cumulative Plot)"""
        df = self.load_csv("scalability.csv")
        
        if df.empty:
            raise ValueError("scalability.csv not found or empty. Run benchmarks first.")
        
        attr_counts = df['attribute_count'].tolist()
        operations_data = {
            'key_generation': df['key_gen_time_ms'].tolist(),
            'signature': df['sign_time_ms'].tolist(),
            'verification': df['verify_time_ms'].tolist(), 
            'proof_generation': df['proof_gen_time_ms'].tolist(),
            'proof_verification': df['proof_verify_time_ms'].tolist()
        }

        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Convertir en arrays numpy pour faciliter les calculs
        x = np.array(attr_counts)
        cumulative_bottom = np.zeros(len(attr_counts))
        
        # Couleurs et ordre des opérations (du plus bas au plus haut)
        operations_order = [
            ('key_generation', self.COLORS['key_generation'], 'Key Generation'),
            ('signature', self.COLORS['signature'], 'Signature'),
            ('verification', self.COLORS['verification'], 'Verification'),
            ('proof_verification', self.COLORS['proof_verification'], 'Proof Verification'),
            ('proof_generation', self.COLORS['proof_generation'], 'Proof Generation')  # Plus lourd en dernier
        ]
        
        # Créer le graphique cumulatif avec fill_between
        for op_key, color, label in operations_order:
            times = np.array(operations_data[op_key])
            cumulative_top = cumulative_bottom + times
            
            # fill_between pour l'aire cumulée
            ax.fill_between(x, cumulative_bottom, cumulative_top,
                           alpha=0.8, color=color, label=label,
                           edgecolor='white', linewidth=1)
            
            # Ligne de contour pour chaque section
            ax.plot(x, cumulative_top, color=color, linewidth=2, alpha=0.9)
            
            cumulative_bottom = cumulative_top

        # Configuration des axes
        ax.set_xlabel('Nombre d\'Attributs', fontsize=self.STYLES['label_size'])
        ax.set_ylabel('Temps Cumulé (ms)', fontsize=self.STYLES['label_size'])
        ax.set_title('Distribution Cumulative des Temps par Opération BBS', 
                    fontsize=self.STYLES['title_size'], fontweight='bold')
        
        # Échelle logarithmique pour les attributs
        ax.set_xscale('log', base=2)
        ax.set_xticks([1, 2, 4, 8, 16, 32, 64, 128])
        ax.set_xticklabels(['1', '2', '4', '8', '16', '32', '64', '128'])
        
        # Grille et légende
        ax.grid(True, alpha=self.STYLES['grid_alpha'], axis='y')
        ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
        
        # Annotations pour les valeurs totales aux points clés
        total_times = cumulative_bottom
        for i, (attr_count, total_time) in enumerate(zip(attr_counts, total_times)):
            if attr_count in [8, 32]:  # Annoter quelques points clés
                ax.annotate(f'{total_time:.1f}ms', 
                           xy=(attr_count, total_time), 
                           xytext=(10, 10), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                           arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                           fontsize=9)

        plt.tight_layout()
        return fig
    
    
    def graph3_bottleneck_analysis(self) -> plt.Figure:
        """Graphique 3: Analyse des Bottlenecks (Heatmap)"""
        df = self.load_csv("scalability.csv")
        
        if df.empty:
            raise ValueError("scalability.csv not found or empty. Run benchmarks first.")
        
        attr_counts = df['attribute_count'].tolist()
        time_matrix = []
        for _, row in df.iterrows():
            time_row = [
                row['key_gen_time_ms'],
                row['sign_time_ms'],
                row['verify_time_ms'],  
                row['proof_gen_time_ms'],
                row['proof_verify_time_ms']
            ]
            time_matrix.append(time_row)

        fig, ax = plt.subplots(figsize=(14, 8))
        
        all_operations = ['Key Generation', 'Signature', 'Verification', 
                         'Proof Generation', 'Proof Verification']

        im = ax.imshow(time_matrix, aspect='auto', cmap='YlOrRd', interpolation='nearest')
        
        # Configuration des axes
        ax.set_xticks(range(len(all_operations)))
        ax.set_xticklabels(all_operations, rotation=45, ha='right')
        ax.set_yticks(range(len(attr_counts)))
        ax.set_yticklabels([f'{count} attrs' for count in attr_counts])
        ax.set_xlabel('Opérations BBS', fontsize=self.STYLES['label_size'])
        ax.set_ylabel('Nombre d\'Attributs', fontsize=self.STYLES['label_size'])
        ax.set_title('Heatmap des Temps d\'Opération BBS (ms)', fontsize=self.STYLES['title_size'], fontweight='bold')

        # Annotations avec les valeurs
        for i in range(len(attr_counts)):
            for j in range(len(all_operations)):
                text = ax.text(j, i, f'{time_matrix[i][j]:.1f}', 
                             ha="center", va="center", color="black", fontsize=8)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Temps (ms)', rotation=270, labelpad=15)

        # Identification des bottlenecks (encadrement rouge)
        for i, times in enumerate(time_matrix):
            max_time_idx = times.index(max(times))
            # Encadrer le bottleneck en rouge
            rect = plt.Rectangle((max_time_idx-0.45, i-0.45), 0.9, 0.9, 
                               fill=False, edgecolor='red', linewidth=3)
            ax.add_patch(rect)

        plt.tight_layout()
        return fig

    def generate_all_graphs(self):
        """Génère et sauvegarde tous les graphiques avancés"""
        graphs = {
            'scalability_batch_size': self.graph1_scalability_batch_size(),
            'time_distribution_operations': self.graph2_time_distribution_operations(),
            'bottleneck_analysis': self.graph3_bottleneck_analysis()
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
    generator = ExtraGraphGenerator()
    graphs = generator.generate_all_graphs()
    print(f"\n Generated {len(graphs)} advanced graphs successfully!")