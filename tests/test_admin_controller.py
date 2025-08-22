"""
管理控制台控制器单元测试
"""

import unittest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

from admin.admin_controller import AdminController
from admin.flask_integration import init_admin_app
from config.config_manager import ConfigManager
from dictionary.dictionary_service import DictionaryService


class TestAdminController(unittest.TestCase):
    """管理控制台控制器测试类"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config.write('{}')
        self.temp_config.close()
        
        # 创建临时字典文件
        self.temp_dict = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_dict.write('{"rules": []}')
        self.temp_dict.close()
        
        # 创建 Flask 测试应用
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.secret_key = 'test_secret_key'
        
        # 创建应用上下文
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 模拟配置管理器
        self.config_patcher = patch('admin.admin_controller.config_manager')
        self.mock_config = self.config_patcher.start()
        self.mock_config.config_file = self.temp_config.name
        self.mock_config.admin.username = 'admin'
        self.mock_config.admin.password_hash = 'salt:hash'
        self.mock_config.admin.secret_key = 'test_secret'
        self.mock_config.admin.session_timeout = 3600
        self.mock_config.dictionary.rules_file = self.temp_dict.name
        
        # 初始化管理控制台
        init_admin_app(self.app)
        
        self.client = self.app.test_client()
        self.admin_controller = AdminController()
    
    def tearDown(self):
        """测试后清理"""
        self.config_patcher.stop()
        self.app_context.pop()
        os.unlink(self.temp_config.name)
        os.unlink(self.temp_dict.name)
    
    def test_login_success(self):
        """测试登录成功"""
        # 设置模拟配置
        self.mock_config.admin.username = 'admin'
        self.mock_config.admin.password_hash = 'test_salt:test_hash'
        
        # 模拟密码验证和配置管理器
        with patch('admin.admin_controller.config_manager', self.mock_config):
            with patch.object(AdminController, '_verify_password', return_value=True):
                response = self.client.post('/admin/login', 
                                          json={'username': 'admin', 'password': 'password'})
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                self.assertEqual(data['user'], 'admin')
    
    def test_login_invalid_credentials(self):
        """测试登录失败 - 无效凭据"""
        with patch.object(self.admin_controller, '_verify_password', return_value=False):
            response = self.client.post('/admin/login',
                                      json={'username': 'admin', 'password': 'wrong'})
            
            self.assertEqual(response.status_code, 401)
    
    def test_login_missing_data(self):
        """测试登录失败 - 缺少数据"""
        response = self.client.post('/admin/login', json={})
        self.assertEqual(response.status_code, 400)
    
    def test_logout(self):
        """测试登出"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'admin'
        
        response = self.client.post('/admin/logout')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success']) 
   
    def test_require_auth_decorator(self):
        """测试认证装饰器"""
        # 未认证的请求
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 401)
    
    def test_dashboard_authenticated(self):
        """测试仪表板 - 已认证"""
        # 设置已认证会话
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['login_time'] = datetime.now().isoformat()
        
        # 模拟系统信息和字典服务
        mock_system_info = {
            'uptime_seconds': 3600,
            'memory': {'total': 8000000000, 'used': 4000000000},
            'cpu_percent': 25.0
        }
        
        # 设置具体的配置值而不是MagicMock
        mock_tts_config = MagicMock()
        mock_tts_config.narration_voice = "zh-CN-YunjianNeural"
        mock_tts_config.dialogue_voice = "zh-CN-XiaoyiNeural"
        mock_tts_config.default_speed = 1.2
        
        mock_dict_config = MagicMock()
        mock_dict_config.enabled = True
        
        self.mock_config.tts = mock_tts_config
        self.mock_config.dictionary = mock_dict_config
        
        with patch('admin.admin_controller.config_manager', self.mock_config):
            with patch.object(AdminController, '_get_system_info', return_value=mock_system_info):
                with patch.object(DictionaryService, 'get_all_rules', return_value=[]):
                    response = self.client.get('/admin/dashboard')
                    
                    self.assertEqual(response.status_code, 200)
                    data = json.loads(response.data)
                    self.assertTrue(data['success'])
                    self.assertIn('data', data)
    
    def test_get_config(self):
        """测试获取配置"""
        self.mock_config.get_config_dict.return_value = {
            'tts': {'narration_voice': 'test_voice'},
            'admin': {'password_hash': 'secret', 'secret_key': 'secret'}
        }
        
        # 设置已认证会话
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['login_time'] = datetime.now().isoformat()
        
        response = self.client.get('/admin/config')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        # 确保敏感信息被移除
        self.assertNotIn('password_hash', data['data'].get('admin', {}))
    
    def test_update_config(self):
        """测试更新配置"""
        config_data = {
            'tts': {
                'narration_voice': 'new_voice',
                'default_speed': 1.5
            }
        }
        
        self.mock_config.set = Mock()
        self.mock_config.save = Mock()
        
        # 设置已认证会话
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['login_time'] = datetime.now().isoformat()
        
        with patch.object(self.admin_controller, '_validate_config_data'):
            response = self.client.post('/admin/config', json=config_data)
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # 验证配置更新调用
            self.mock_config.set.assert_called()
            self.mock_config.save.assert_called_once()
    
    def test_get_dictionary_rules(self):
        """测试获取字典规则"""
        mock_rules = [
            Mock(to_dict=Mock(return_value={'id': 'rule1', 'type': 'pronunciation'}))
        ]
        
        # 设置已认证会话
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['login_time'] = datetime.now().isoformat()
        
        with patch('admin.admin_controller.config_manager', self.mock_config):
            with patch.object(DictionaryService, 'get_all_rules', return_value=mock_rules):
                response = self.client.get('/admin/dictionary')
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                self.assertEqual(len(data['data']), 1)
    
    def test_add_dictionary_rule(self):
        """测试添加字典规则"""
        rule_data = {
            'pattern': 'test',
            'replacement': 'replacement',
            'type': 'pronunciation'
        }
        
        # 设置已认证会话
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['login_time'] = datetime.now().isoformat()
        
        with patch('admin.admin_controller.config_manager', self.mock_config):
            with patch.object(DictionaryService, 'add_rule', return_value='rule_001'):
                response = self.client.post('/admin/dictionary', json=rule_data)
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                self.assertEqual(data['rule_id'], 'rule_001')
    
    def test_update_dictionary_rule(self):
        """测试更新字典规则"""
        update_data = {'enabled': False}
        
        # 设置已认证会话
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['login_time'] = datetime.now().isoformat()
        
        with patch('admin.admin_controller.config_manager', self.mock_config):
            with patch.object(DictionaryService, 'update_rule', return_value=True):
                response = self.client.put('/admin/dictionary/rule_001', json=update_data)
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
    
    def test_delete_dictionary_rule(self):
        """测试删除字典规则"""
        # 设置已认证会话
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['login_time'] = datetime.now().isoformat()
        
        with patch('admin.admin_controller.config_manager', self.mock_config):
            with patch.object(DictionaryService, 'remove_rule', return_value=True):
                response = self.client.delete('/admin/dictionary/rule_001')
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
    
    @patch('admin.admin_controller.psutil')
    def test_system_status(self, mock_psutil):
        """测试系统状态"""
        # 模拟 psutil 返回值
        mock_memory = Mock()
        mock_memory.total = 8000000000
        mock_memory.available = 4000000000
        mock_memory.percent = 50.0
        mock_memory.used = 4000000000
        
        mock_disk = Mock()
        mock_disk.total = 100000000000
        mock_disk.used = 50000000000
        mock_disk.free = 50000000000
        
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.disk_usage.return_value = mock_disk
        
        # 设置已认证会话
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'admin'
            sess['login_time'] = datetime.now().isoformat()
        
        with patch('admin.admin_controller.config_manager', self.mock_config):
            with patch.object(AdminController, '_check_edge_tts_status', return_value=True):
                response = self.client.get('/admin/system/status')
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                self.assertIn('memory', data['data'])
                self.assertIn('cpu_percent', data['data'])
    
    def test_password_hashing(self):
        """测试密码哈希功能"""
        password = "test_password"
        password_hash = self.admin_controller._hash_password(password)
        
        # 验证bcrypt哈希格式
        self.assertTrue(password_hash.startswith('$2b$'))
        self.assertTrue(len(password_hash) > 50)  # bcrypt哈希通常很长
        
        # 验证密码验证
        self.assertTrue(self.admin_controller._verify_password(password, password_hash))
        self.assertFalse(self.admin_controller._verify_password("wrong_password", password_hash))
    
    def test_config_validation(self):
        """测试配置验证"""
        # 有效配置
        valid_config = {
            'tts': {
                'default_speed': 1.5,
                'cache_size_limit': 1024
            },
            'system': {
                'port': 5000
            }
        }
        
        # 应该不抛出异常
        try:
            self.admin_controller._validate_config_data(valid_config)
        except Exception:
            self.fail("有效配置验证失败")
        
        # 无效配置 - 负数速度
        invalid_config = {
            'tts': {
                'default_speed': -1.0
            }
        }
        
        with self.assertRaises(Exception):
            self.admin_controller._validate_config_data(invalid_config)


if __name__ == '__main__':
    unittest.main()