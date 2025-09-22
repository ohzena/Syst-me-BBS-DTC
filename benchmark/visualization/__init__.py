"""
benchmark.visualization - Génération de graphiques et rapports pour benchmarks BBS-DTC

Ce module fournit les outils pour:
- Générer 4 graphiques de base (performance/taille vs attributs/divulgation)
- Créer 3 graphiques avancés (scalabilité, mémoire, bottlenecks)
- Exporter dans multiple formats (PNG, PDF, SVG)
- Générer des rapports HTML interactifs

Modules:
- graphs: Graphiques de base (4 graphiques principaux)
- extra_graphs: Graphiques avancés (3 graphiques supplémentaires)
- export: Export multi-format et génération de rapports
"""

__version__ = "1.0.0"
__description__ = "Visualization tools for BBS-DTC benchmarks"

# Imports principaux
import matplotlib.pyplot as plt
import seaborn as sns

from .graphs import GraphGenerator
from .extra_graphs import ExtraGraphGenerator  
try:
    from .export import ResultExporter
except ImportError:
    # ResultExporter is optional
    ResultExporter = None

# Exposition des classes principales
__all__ = [
    # Générateurs de graphiques
    'GraphGenerator',
    'ExtraGraphGenerator',
    'ResultExporter',
    
    # Utilitaires
    'create_basic_graphs',
    'create_advanced_graphs', 
    'export_all_formats',
    'generate_html_report',
    'get_supported_formats'
]

# Configuration des graphiques par défaut
DEFAULT_GRAPH_CONFIG = {
    'style': 'seaborn-v0_8',
    'dpi': 300,
    'formats': ['png', 'pdf'],
    'colors': {
        'primary': '#2E86AB',
        'secondary': '#A23B72',
        'success': '#F18F01', 
        'warning': '#C73E1D',
        'info': '#6A994E'
    }
}

# Liste des graphiques disponibles
AVAILABLE_GRAPHS = {
    'basic': [
        'performance_vs_attributes',
        'proof_size_vs_attributes', 
        'performance_vs_disclosure',
        'proof_size_vs_disclosure'
    ],
    'advanced': [
        'scalability_vs_batch_size',
        'memory_usage_vs_attributes',
        'bottleneck_analysis'
    ]
}

def create_basic_graphs(results_data, config=None):
    """
    Crée tous les graphiques de base
    
    Args:
        results_data (dict): Données de résultats
        config: Configuration des graphiques
        
    Returns:
        dict: Graphiques générés {nom: figure}
    """
    if config is None:
        from ..config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG
    
    generator = GraphGenerator(config)
    return generator.generate_all_graphs(results_data)

def create_advanced_graphs(advanced_data, config=None):
    """
    Crée tous les graphiques avancés
    
    Args:
        advanced_data (dict): Données avancées
        config: Configuration des graphiques
        
    Returns:
        dict: Graphiques avancés générés {nom: figure}
    """
    if config is None:
        from ..config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG
    
    generator = ExtraGraphGenerator(config)
    return generator.generate_all_graphs(advanced_data)

def export_all_formats(graphs_dict, output_dir="metrics/graphs", formats=['png']):
    """
    Exporte tous les graphiques dans les formats demandés
    
    Args:
        graphs_dict (dict): Dictionnaire {nom: figure}
        output_dir (str): Répertoire de sortie
        formats (list): Liste des formats ['png', 'pdf', 'svg']
        
    Returns:
        list: Chemins des fichiers exportés
    """
    from pathlib import Path
    exported_files = []
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for graph_name, fig in graphs_dict.items():
        for fmt in formats:
            try:
                # Déterminer le sous-répertoire
                subdir = "advanced" if any(kw in graph_name for kw in ['scalability', 'memory', 'bottleneck']) else "basic"
                file_path = output_path / subdir / f"{graph_name}.{fmt}"
                file_path.parent.mkdir(exist_ok=True)
                
                # Sauvegarder
                fig.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white')
                exported_files.append(str(file_path))
                
            except Exception as e:
                print(f"Erreur export {graph_name}.{fmt}: {e}")
    
    return exported_files

def generate_html_report(core_results, advanced_results=None, graphs=None):
    """
    Génère un rapport HTML complet
    
    Args:
        core_results (dict): Résultats principaux
        advanced_results (dict): Résultats avancés
        graphs (dict): Graphiques générés
        
    Returns:
        str: Chemin du rapport HTML généré
    """
    if ResultExporter is None:
        print("Warning: ResultExporter not available, generating basic report")
        return "report_not_available.html"
    
    from ..config import DEFAULT_CONFIG
    exporter = ResultExporter(DEFAULT_CONFIG)
    return exporter.generate_html_report(core_results, advanced_results, graphs)

def get_supported_formats():
    """
    Retourne les formats d'export supportés
    
    Returns:
        dict: Formats supportés par type
    """
    return {
        'image': ['png', 'jpg', 'svg', 'eps'],
        'document': ['pdf'],
        'web': ['html']
    }

def setup_matplotlib_style(style='seaborn-v0_8'):
    """
    Configure le style matplotlib par défaut
    
    Args:
        style (str): Style à appliquer
    """
    try:
        plt.style.use(style)
        # Configuration personnalisée
        plt.rcParams.update({
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'savefig.facecolor': 'white',
            'font.size': 10,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'legend.fontsize': 10
        })
    except Exception as e:
        print(f"Warning: Impossible d'appliquer le style {style}: {e}")

def quick_visualization(results, output_dir="metrics", formats=['png']):
    """
    Fonction utilitaire pour créer rapidement tous les graphiques
    
    Args:
        results (dict): Résultats de benchmark complets
        output_dir (str): Répertoire de sortie
        formats (list): Formats d'export
        
    Returns:
        dict: Informations sur les fichiers générés
    """
    from ..config import DEFAULT_CONFIG
    
    # Extraire les données
    core_data = {k: v for k, v in results.items() 
                if k in ['performance_vs_attributes', 'proof_size_vs_attributes', 
                        'performance_vs_disclosure', 'proof_size_vs_disclosure']}
    
    advanced_data = {k: v for k, v in results.items()
                    if k in ['scalability_vs_batch', 'memory_vs_attributes', 'bottleneck_analysis']}
    
    # Générer les graphiques
    basic_graphs = create_basic_graphs(core_data, DEFAULT_CONFIG)
    advanced_graphs = create_advanced_graphs(advanced_data, DEFAULT_CONFIG) if advanced_data else {}
    
    # Exporter
    all_graphs = {**basic_graphs, **advanced_graphs}
    exported_files = export_all_formats(all_graphs, output_dir, formats)
    
    # Rapport HTML
    html_report = generate_html_report(core_data, advanced_data, all_graphs)
    
    return {
        'graphs_generated': len(all_graphs),
        'files_exported': len(exported_files),
        'formats': formats,
        'html_report': html_report,
        'output_directory': output_dir
    }

# Initialisation automatique du style
setup_matplotlib_style()

# Métadonnées du sous-package
PACKAGE_INFO = {
    'name': 'benchmark.visualization',
    'version': __version__,
    'description': __description__,
    'dependencies': ['matplotlib', 'seaborn', 'pandas'],
    'graph_types': AVAILABLE_GRAPHS,
    'supported_formats': get_supported_formats(),
    'default_style': DEFAULT_GRAPH_CONFIG['style']
}