"""Unit tests for configuration management."""
import unittest
import tempfile
import os
from goldminer.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.yaml')
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def test_default_config_loading(self):
        """Test loading default configuration."""
        config = ConfigManager(config_path=self.config_path)
        
        # Check default values exist
        self.assertIsNotNone(config.get('database.path'))
        self.assertIsNotNone(config.get('etl.date_formats'))
        self.assertIsNotNone(config.get('logging.level'))
    
    def test_get_nested_config(self):
        """Test getting nested configuration values."""
        config = ConfigManager(config_path=self.config_path)
        
        # Test nested key access
        db_path = config.get('database.path')
        self.assertIsInstance(db_path, str)
        
        # Test with default value
        unknown = config.get('unknown.key', 'default')
        self.assertEqual(unknown, 'default')
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        config = ConfigManager(config_path=self.config_path)
        config.save_config()
        
        # Check file was created
        self.assertTrue(os.path.exists(self.config_path))
        
        # Load and verify
        config2 = ConfigManager(config_path=self.config_path)
        self.assertEqual(
            config.get('database.path'),
            config2.get('database.path')
        )


if __name__ == '__main__':
    unittest.main()
