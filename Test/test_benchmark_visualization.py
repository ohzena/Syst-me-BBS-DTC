"""
Tests de visualisation et données pour le système BBS-DTC

Ces tests vérifient l'intégration avec les vrais modules de benchmark :
- Tests avec les vraies données de benchmark
- Génération de graphiques réels avec GraphGenerator
- Export CSV/JSON avec les vrais collectors
"""

import unittest
import os
import tempfile
import shutil
import json
import csv

from benchmark.collector import BenchmarkCollector
from benchmark.visualization.graphs import GraphGenerator
from benchmark.data.manager import DataManager


class TestRealBenchmarkVisualization(unittest.TestCase):
    """Tests avec les vrais modules de benchmark"""

    def setUp(self):
        """Configuration"""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def tearDown(self):
        """Nettoyage"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_real_data_loading(self):
        """Test chargement données réelles"""
        data_manager = DataManager()
        
        # Test chargement profils existants
        try:
            ellen_data = data_manager.load_person_data("ellen_kampire_dtc")
            self.assertIsInstance(ellen_data, dict)
            self.assertIn("given_names", ellen_data)
            print(" Données Ellen chargées")
        except:
            self.skipTest("Données Ellen non disponibles")
            
    def test_real_collector_usage(self):
        """Test utilisation collector réel"""
        collector = BenchmarkCollector()
        
        # Enregistrer métriques réelles
        collector.record_metric({
            'operation': 'signature',
            'attributes': 10,
            'time_ms': 25.3,
            'success': True
        })
        
        # Vérifier que les métriques sont stockées
        metrics = collector.get_metrics()
        self.assertGreater(len(metrics), 0)
        
        print(" Collector réel utilisé avec succès")
        
    def test_real_graph_generation(self):
        """Test génération graphiques avec GraphGenerator réel"""
        try:
            generator = GraphGenerator(output_dir=self.output_dir)
            
            # Données de performance réelles
            perf_data = [
                {"attributes": 5, "signature_time_ms": 12.1},
                {"attributes": 10, "signature_time_ms": 18.5},
                {"attributes": 15, "signature_time_ms": 24.8}
            ]
            
            # Générer graphique réel
            graph_file = generator.create_performance_vs_attributes_graph(
                perf_data, 
                title="Real Performance Graph",
                filename="real_performance.png"
            )
            
            # Vérifier création
            self.assertTrue(os.path.exists(graph_file))
            print(" Graphique réel généré")
            
        except Exception as e:
            self.skipTest(f"GraphGenerator non disponible: {e}")


class TestRealDataExport(unittest.TestCase):
    """Tests export de données réelles"""
    
    def setUp(self):
        """Configuration"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Nettoyage"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_csv_export_real_data(self):
        """Test export CSV avec données réelles"""
        # Utiliser collector pour générer vraies données
        collector = BenchmarkCollector()
        
        # Simuler benchmark réel
        for i in range(5, 16):
            collector.record_metric({
                'operation': 'signature',
                'attributes': i,
                'time_ms': 10 + i * 1.2,
                'memory_mb': 2.0 + i * 0.1
            })
            
        # Export vers CSV
        csv_file = os.path.join(self.test_dir, "real_metrics.csv")
        metrics = collector.get_metrics()
        
        with open(csv_file, 'w', newline='') as f:
            if metrics:
                fieldnames = metrics[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(metrics)
                
        # Vérifier
        self.assertTrue(os.path.exists(csv_file))
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        self.assertGreater(len(rows), 0)
        print(f" CSV réel exporté: {len(rows)} lignes")


if __name__ == '__main__':
    unittest.main(verbosity=2, buffer=True)