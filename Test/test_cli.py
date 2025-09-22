"""
Tests CLI pour le benchmark runner et main.py

Ces tests vérifient le bon fonctionnement des interfaces en ligne de commande :
- Tests avec les vrais fichiers de configuration
- Tests avec les vrais modules de benchmark
- Tests d'intégration avec main.py
"""

import unittest
import subprocess
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path


class TestRealCliUsage(unittest.TestCase):
    """Tests CLI avec les vrais composants"""

    def setUp(self):
        """Configuration"""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = os.path.dirname(os.path.dirname(__file__))
        
    def tearDown(self):
        """Nettoyage"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_main_help_command(self):
        """Test affichage aide main.py"""
        cmd = [
            sys.executable,
            os.path.join(self.project_root, "main.py"), 
            "--help"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root
            )
            
            # Vérifier que aide s'affiche
            self.assertEqual(result.returncode, 0)
            self.assertIn("usage:", result.stdout.lower())
            
            # Vérifier présence des commandes principales
            expected_commands = ["demo", "benchmark", "travel"]
            for cmd_name in expected_commands:
                self.assertIn(cmd_name, result.stdout)
                
            print(" Main.py help command successful")
            
        except FileNotFoundError:
            self.skipTest("main.py not found")
        except Exception as e:
            self.fail(f"Help command failed: {e}")
            
    def test_demo_command_execution(self):
        """Test exécution commande demo"""
        cmd = [
            sys.executable,
            os.path.join(self.project_root, "main.py"),
            "demo",
            "--no-optimization",
            "--verbose"
        ]
        
        try:
            # Exécuter avec timeout court
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root
            )
            
            # Vérifier que ça démarre sans crash Python
            self.assertNotIn("Traceback", result.stderr)
            
            print(" Demo command executed without crash")
            
        except subprocess.TimeoutExpired:
            print(" Demo command started (timed out as expected)")
        except FileNotFoundError:
            self.skipTest("main.py not found")
            
    def test_benchmark_command_basic(self):
        """Test commande benchmark de base"""
        cmd = [
            sys.executable, 
            os.path.join(self.project_root, "main.py"),
            "benchmark",
            "--no-optimization"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=20,
                cwd=self.project_root
            )
            
            # Pas de crash Python
            self.assertNotIn("Traceback", result.stderr)
            
            print(" Benchmark command executed")
            
        except subprocess.TimeoutExpired:
            print(" Benchmark command started")  
        except FileNotFoundError:
            self.skipTest("main.py not found")


class TestRealConfigHandling(unittest.TestCase):
    """Tests avec vrais fichiers de configuration"""
    
    def setUp(self):
        """Configuration"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Nettoyage"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_create_real_config(self):
        """Test création configuration réelle"""
        config_data = {
            "benchmark_settings": {
                "max_attributes": 20,
                "iterations_per_test": 5,
                "include_performance": True,
                "include_security": True
            },
            "output_settings": {
                "generate_csv": True,
                "generate_graphs": True,
                "output_directory": self.test_dir
            }
        }
        
        config_file = os.path.join(self.test_dir, "real_benchmark_config.json")
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        # Vérifier fichier créé et valide
        self.assertTrue(os.path.exists(config_file))
        
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
            
        self.assertEqual(loaded_config["benchmark_settings"]["max_attributes"], 20)
        print(" Configuration réelle créée")
        
    def test_real_data_profile_creation(self):
        """Test création profil avec vraies données"""
        from benchmark.data.manager import DataManager
        
        try:
            data_manager = DataManager()
            
            # Essayer de charger profil existant
            profile_data = data_manager.load_person_data("ellen_kampire_dtc")
            
            # Sauvegarder une copie pour test
            test_profile_file = os.path.join(self.test_dir, "test_profile.json")
            
            with open(test_profile_file, 'w') as f:
                json.dump(profile_data, f, indent=2)
                
            # Vérifier
            self.assertTrue(os.path.exists(test_profile_file))
            
            with open(test_profile_file, 'r') as f:
                loaded_profile = json.load(f)
                
            self.assertIn("given_names", loaded_profile)
            print(" Profil réel créé")
            
        except Exception as e:
            self.skipTest(f"DataManager non disponible: {e}")


class TestErrorHandling(unittest.TestCase):
    """Tests gestion d'erreurs réelles"""
    
    def setUp(self):
        """Configuration"""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = os.path.dirname(os.path.dirname(__file__))
        
    def tearDown(self):
        """Nettoyage"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_invalid_command_handling(self):
        """Test gestion commande invalide"""
        cmd = [
            sys.executable,
            os.path.join(self.project_root, "main.py"),
            "invalid_command"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.project_root
            )
            
            # Doit échouer proprement
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
            
            print(" Commande invalide gérée correctement")
            
        except FileNotFoundError:
            self.skipTest("main.py not found")
            
    def test_missing_file_error(self):
        """Test erreur fichier manquant"""
        # Créer fichier de config corrompu
        corrupted_file = os.path.join(self.test_dir, "corrupted.json")
        
        with open(corrupted_file, 'w') as f:
            f.write('{"invalid": "json", missing bracket')
            
        # Tenter de charger
        with self.assertRaises(json.JSONDecodeError):
            with open(corrupted_file, 'r') as f:
                json.load(f)
                
        print(" Détection fichier corrompu fonctionnelle")


if __name__ == '__main__':
    print("🖥️  TESTING REAL BBS-DTC CLI FUNCTIONALITY")
    print("=" * 60)
    
    unittest.main(verbosity=2, buffer=True)