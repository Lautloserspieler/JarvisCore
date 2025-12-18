"""Tests for Plugin Manager"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from plugin_manager import PluginManager

class TestPluginManager:
    """Test suite for PluginManager"""
    
    def test_plugin_manager_initialization(self):
        """Test PluginManager initializes correctly"""
        manager = PluginManager()
        assert manager is not None
        assert hasattr(manager, 'plugins')
        assert hasattr(manager, 'enabled_plugins')
    
    def test_list_plugins(self):
        """Test listing available plugins"""
        manager = PluginManager()
        plugins = manager.list_plugins()
        
        assert isinstance(plugins, list)
        # Check that system plugins are filtered out
        plugin_ids = [p['id'] for p in plugins]
        assert 'calculator_plugin' not in plugin_ids
        assert 'system_info_plugin' not in plugin_ids
    
    def test_get_plugin_info(self, mock_plugin_config):
        """Test getting plugin information"""
        manager = PluginManager()
        
        # Mock a plugin
        with patch.object(manager, 'plugins', {'test_plugin': mock_plugin_config}):
            info = manager.get_plugin_info('test_plugin')
            
            assert info is not None
            assert info['id'] == 'test_plugin'
            assert info['name'] == 'Test Plugin'
            assert info['version'] == '1.0.0'
    
    def test_enable_plugin_without_api_key(self, mock_plugin_config):
        """Test enabling plugin that doesn't require API key"""
        manager = PluginManager()
        
        with patch.object(manager, 'plugins', {'test_plugin': mock_plugin_config}):
            result = manager.enable_plugin('test_plugin')
            
            assert result['success'] is True
            assert 'test_plugin' in manager.enabled_plugins
    
    def test_disable_plugin(self, mock_plugin_config):
        """Test disabling an enabled plugin"""
        manager = PluginManager()
        
        mock_plugin_config['enabled'] = True
        with patch.object(manager, 'plugins', {'test_plugin': mock_plugin_config}):
            with patch.object(manager, 'enabled_plugins', {'test_plugin'}):
                result = manager.disable_plugin('test_plugin')
                
                assert result['success'] is True
                assert 'test_plugin' not in manager.enabled_plugins
    
    def test_plugin_not_found(self):
        """Test handling of non-existent plugin"""
        manager = PluginManager()
        
        info = manager.get_plugin_info('nonexistent_plugin')
        assert info is None
    
    def test_execute_plugin(self):
        """Test plugin execution"""
        manager = PluginManager()
        
        # Mock plugin with execute method
        mock_plugin = MagicMock()
        mock_plugin.execute.return_value = {"success": True, "result": "test result"}
        
        with patch.object(manager, 'plugins', {'test_plugin': mock_plugin}):
            with patch.object(manager, 'enabled_plugins', {'test_plugin'}):
                result = manager.execute_plugin('test_plugin', {})
                
                assert result['success'] is True
                assert result['result'] == 'test result'
                mock_plugin.execute.assert_called_once()
