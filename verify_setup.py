#!/usr/bin/env python3
"""
Verification script to ensure GoldMiner pipeline is ready for data ingestion and analysis.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("Checking dependencies...")
    missing_deps = []
    
    try:
        import pandas
        print(f"  ✓ pandas {pandas.__version__}")
    except ImportError:
        missing_deps.append("pandas>=2.0.0")
        print("  ✗ pandas (missing)")
    
    try:
        import numpy
        print(f"  ✓ numpy {numpy.__version__}")
    except ImportError:
        missing_deps.append("numpy>=1.24.0")
        print("  ✗ numpy (missing)")
    
    try:
        import openpyxl
        print(f"  ✓ openpyxl {openpyxl.__version__}")
    except ImportError:
        missing_deps.append("openpyxl>=3.1.0")
        print("  ✗ openpyxl (missing)")
    
    try:
        import yaml
        print(f"  ✓ pyyaml (yaml)")
    except ImportError:
        missing_deps.append("pyyaml>=6.0")
        print("  ✗ pyyaml (missing)")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    
    print("✓ All dependencies installed\n")
    return True


def check_directories():
    """Check if required directories exist."""
    print("Checking directory structure...")
    required_dirs = [
        'data/raw',
        'data/processed',
        'logs',
        'goldminer',
        'goldminer/config',
        'goldminer/etl',
        'goldminer/analysis',
        'goldminer/utils',
        'tests/unit'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} (missing)")
            all_exist = False
    
    if all_exist:
        print("✓ All directories present\n")
    else:
        print("\n❌ Some directories are missing\n")
    
    return all_exist


def check_config():
    """Check if configuration file exists and is valid."""
    print("Checking configuration...")
    
    if not os.path.exists('config.yaml'):
        print("  ✗ config.yaml not found")
        return False
    
    try:
        from goldminer.config import ConfigManager
        config = ConfigManager()
        
        # Check key configuration values
        db_path = config.get('database.path')
        print(f"  ✓ Configuration loaded")
        print(f"    - Database path: {db_path}")
        print(f"    - Raw data dir: {config.get('data_sources.raw_data_dir')}")
        print(f"    - Log file: {config.get('logging.file')}")
        print("✓ Configuration valid\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration error: {str(e)}")
        return False


def check_modules():
    """Check if all GoldMiner modules can be imported."""
    print("Checking GoldMiner modules...")
    modules = [
        ('goldminer.config', 'ConfigManager'),
        ('goldminer.etl.ingest', 'DataIngestion'),
        ('goldminer.etl.schema', 'SchemaInference'),
        ('goldminer.etl.normalize', 'DataNormalizer'),
        ('goldminer.etl.clean', 'DataCleaner'),
        ('goldminer.etl.database', 'DatabaseManager'),
        ('goldminer.etl.pipeline', 'ETLPipeline'),
        ('goldminer.analysis.analyzer', 'DataAnalyzer'),
    ]
    
    all_imported = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  ✓ {module_name}.{class_name}")
        except Exception as e:
            print(f"  ✗ {module_name}.{class_name} - {str(e)}")
            all_imported = False
    
    if all_imported:
        print("✓ All modules imported successfully\n")
    else:
        print("\n❌ Some modules failed to import\n")
    
    return all_imported


def test_pipeline():
    """Test basic pipeline functionality."""
    print("Testing pipeline functionality...")
    
    try:
        from goldminer.config import ConfigManager
        from goldminer.etl import ETLPipeline, DataIngestion, DatabaseManager
        import pandas as pd
        import tempfile
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("name,age,city\n")
            f.write("Alice,25,NYC\n")
            f.write("Bob,30,LA\n")
            temp_file = f.name
        
        # Test ingestion
        config = ConfigManager()
        ingest = DataIngestion(config)
        df = ingest.read_csv(temp_file)
        
        if len(df) == 2 and len(df.columns) == 3:
            print("  ✓ Data ingestion works")
        else:
            print("  ✗ Data ingestion failed")
            os.unlink(temp_file)
            return False
        
        # Test database operations
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
            db_path = db_file.name
        
        with DatabaseManager(db_path, config) as db:
            db.save_dataframe(df, 'test_table')
            loaded_df = db.load_dataframe('test_table')
            
            if len(loaded_df) == 2:
                print("  ✓ Database operations work")
            else:
                print("  ✗ Database operations failed")
                os.unlink(temp_file)
                os.unlink(db_path)
                return False
        
        # Cleanup
        os.unlink(temp_file)
        os.unlink(db_path)
        
        print("✓ Pipeline functionality verified\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Pipeline test failed: {str(e)}")
        return False


def run_unit_tests():
    """Run unit tests."""
    print("Running unit tests...")
    
    try:
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover('tests/unit', pattern='test_*.py')
        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print(f"  ✓ All {result.testsRun} tests passed")
            print("✓ Unit tests passed\n")
            return True
        else:
            print(f"  ✗ {len(result.failures)} test(s) failed")
            print(f"  ✗ {len(result.errors)} test(s) had errors")
            return False
            
    except Exception as e:
        print(f"  ✗ Test execution failed: {str(e)}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("GoldMiner Pipeline Verification")
    print("=" * 70)
    print()
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Configuration", check_config),
        ("Modules", check_modules),
        ("Pipeline", test_pipeline),
        ("Unit Tests", run_unit_tests),
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
    
    print("=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n✓ All checks passed! Pipeline is ready for data ingestion and analysis.")
        print("\nNext steps:")
        print("  1. Place your data files in data/raw/")
        print("  2. Run: python cli.py run data/raw/ --directory --analyze")
        print("  3. Or run: python example_usage.py")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
