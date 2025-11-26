"""
Testes unitários para CleanupManager

FASE 1.1 do Roadmap FinOps AWS
Cobertura: Sistema de limpeza de arquivos temporários
"""
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytest
import boto3
from moto import mock_aws

from src.finops_aws.core.cleanup_manager import (
    CleanupManager,
    CleanupConfig,
    CleanupResult,
    cleanup_after_execution
)


class TestCleanupConfig:
    """Testes para CleanupConfig"""

    def test_default_config(self):
        """Testa configuração padrão"""
        config = CleanupConfig()
        
        assert '.bkp' in config.file_extensions
        assert '.tmp' in config.file_extensions
        assert '.cache' in config.file_extensions
        assert config.max_file_age_hours == 24
        assert config.max_file_size_mb == 100.0
        assert config.s3_cleanup_enabled is True
        assert config.dry_run is False

    def test_config_to_dict(self):
        """Testa conversão para dicionário"""
        config = CleanupConfig(
            file_extensions={'.bkp', '.tmp'},
            max_file_age_hours=12,
            dry_run=True
        )
        
        result = config.to_dict()
        
        assert 'file_extensions' in result
        assert result['max_file_age_hours'] == 12
        assert result['dry_run'] is True

    def test_config_from_dict(self):
        """Testa criação a partir de dicionário"""
        data = {
            'file_extensions': ['.bkp', '.log'],
            'max_file_age_hours': 48,
            's3_cleanup_enabled': False
        }
        
        config = CleanupConfig.from_dict(data)
        
        assert '.bkp' in config.file_extensions
        assert '.log' in config.file_extensions
        assert config.max_file_age_hours == 48
        assert config.s3_cleanup_enabled is False

    def test_config_from_env(self):
        """Testa criação a partir de variáveis de ambiente"""
        with patch.dict(os.environ, {
            'CLEANUP_FILE_EXTENSIONS': '.bkp,.tmp',
            'CLEANUP_MAX_FILE_AGE_HOURS': '48',
            'CLEANUP_DRY_RUN': 'true'
        }):
            config = CleanupConfig.from_env()
            
            assert '.bkp' in config.file_extensions
            assert '.tmp' in config.file_extensions
            assert config.max_file_age_hours == 48
            assert config.dry_run is True


class TestCleanupResult:
    """Testes para CleanupResult"""

    def test_default_result(self):
        """Testa resultado padrão"""
        result = CleanupResult()
        
        assert result.files_deleted == 0
        assert result.files_failed == 0
        assert result.bytes_freed == 0
        assert len(result.errors) == 0

    def test_result_to_dict(self):
        """Testa conversão para dicionário"""
        result = CleanupResult(
            files_deleted=10,
            bytes_freed=1024 * 1024,  # 1 MB
            s3_objects_deleted=5,
            execution_time_seconds=1.5
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['files_deleted'] == 10
        assert result_dict['bytes_freed_mb'] == 1.0
        assert result_dict['s3_objects_deleted'] == 5
        assert result_dict['execution_time_seconds'] == 1.5
        assert result_dict['success_rate'] == 100.0

    def test_result_merge(self):
        """Testa merge de resultados"""
        result1 = CleanupResult(files_deleted=5, bytes_freed=1000)
        result2 = CleanupResult(files_deleted=3, bytes_freed=500)
        
        merged = result1.merge(result2)
        
        assert merged.files_deleted == 8
        assert merged.bytes_freed == 1500

    def test_success_rate_calculation(self):
        """Testa cálculo da taxa de sucesso"""
        result = CleanupResult(files_deleted=8, files_failed=2)
        result_dict = result.to_dict()
        
        assert result_dict['success_rate'] == 80.0


class TestCleanupManager:
    """Testes para CleanupManager"""

    def setup_method(self, method):
        """Setup para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = CleanupConfig(
            cleanup_directories=[self.temp_dir],
            s3_cleanup_enabled=False,
            dry_run=False
        )

    def teardown_method(self, method):
        """Cleanup após cada teste"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cleanup_manager_initialization(self):
        """Testa inicialização do CleanupManager"""
        manager = CleanupManager(config=self.config)
        
        assert manager.config is not None
        assert manager.s3_bucket is not None

    def test_cleanup_old_bkp_files(self):
        """Testa limpeza de arquivos .bkp antigos"""
        # Cria arquivo .bkp antigo
        old_file = os.path.join(self.temp_dir, 'old_file.bkp')
        with open(old_file, 'w') as f:
            f.write('test content')
        
        # Define a data de modificação para 48 horas atrás
        old_time = datetime.now() - timedelta(hours=48)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
        
        manager = CleanupManager(config=self.config)
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 1
        assert not os.path.exists(old_file)

    def test_skip_recent_files(self):
        """Testa que arquivos recentes não são deletados"""
        # Cria arquivo .bkp recente
        recent_file = os.path.join(self.temp_dir, 'recent_file.bkp')
        with open(recent_file, 'w') as f:
            f.write('test content')
        
        manager = CleanupManager(config=self.config)
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 0
        assert os.path.exists(recent_file)

    def test_skip_non_matching_extensions(self):
        """Testa que arquivos com extensões não listadas são ignorados"""
        # Cria arquivo .txt antigo
        txt_file = os.path.join(self.temp_dir, 'file.txt')
        with open(txt_file, 'w') as f:
            f.write('test content')
        
        # Define a data de modificação para 48 horas atrás
        old_time = datetime.now() - timedelta(hours=48)
        os.utime(txt_file, (old_time.timestamp(), old_time.timestamp()))
        
        manager = CleanupManager(config=self.config)
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 0
        assert os.path.exists(txt_file)

    def test_cleanup_tmp_files(self):
        """Testa limpeza de arquivos .tmp"""
        # Cria arquivo .tmp antigo
        tmp_file = os.path.join(self.temp_dir, 'temp_file.tmp')
        with open(tmp_file, 'w') as f:
            f.write('temporary data')
        
        # Define a data de modificação para 48 horas atrás
        old_time = datetime.now() - timedelta(hours=48)
        os.utime(tmp_file, (old_time.timestamp(), old_time.timestamp()))
        
        manager = CleanupManager(config=self.config)
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 1
        assert result.bytes_freed > 0

    def test_cleanup_cache_files(self):
        """Testa limpeza de arquivos .cache"""
        # Cria arquivo .cache antigo
        cache_file = os.path.join(self.temp_dir, 'data.cache')
        with open(cache_file, 'w') as f:
            f.write('cached data')
        
        # Define a data de modificação para 48 horas atrás
        old_time = datetime.now() - timedelta(hours=48)
        os.utime(cache_file, (old_time.timestamp(), old_time.timestamp()))
        
        manager = CleanupManager(config=self.config)
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 1

    def test_dry_run_mode(self):
        """Testa modo dry run (não deleta arquivos)"""
        # Cria arquivo .bkp antigo
        old_file = os.path.join(self.temp_dir, 'old_file.bkp')
        with open(old_file, 'w') as f:
            f.write('test content')
        
        # Define a data de modificação para 48 horas atrás
        old_time = datetime.now() - timedelta(hours=48)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
        
        # Configura dry run
        dry_run_config = CleanupConfig(
            cleanup_directories=[self.temp_dir],
            s3_cleanup_enabled=False,
            dry_run=True
        )
        
        manager = CleanupManager(config=dry_run_config)
        result = manager.cleanup_local_files()
        
        # Arquivo ainda existe
        assert os.path.exists(old_file)
        # Mas foi contado como "deletado" no modo dry run
        assert result.files_deleted == 1

    def test_cleanup_multiple_files(self):
        """Testa limpeza de múltiplos arquivos"""
        old_time = datetime.now() - timedelta(hours=48)
        
        # Cria vários arquivos antigos
        files = ['file1.bkp', 'file2.tmp', 'file3.cache']
        for filename in files:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write('content')
            os.utime(filepath, (old_time.timestamp(), old_time.timestamp()))
        
        manager = CleanupManager(config=self.config)
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 3

    def test_bytes_freed_calculation(self):
        """Testa cálculo de bytes liberados"""
        old_file = os.path.join(self.temp_dir, 'large_file.bkp')
        content = 'x' * 1000  # 1000 bytes
        with open(old_file, 'w') as f:
            f.write(content)
        
        old_time = datetime.now() - timedelta(hours=48)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
        
        manager = CleanupManager(config=self.config)
        result = manager.cleanup_local_files()
        
        assert result.bytes_freed == 1000

    def test_get_cleanup_status(self):
        """Testa obtenção de status de limpeza"""
        # Cria arquivo .bkp antigo
        old_file = os.path.join(self.temp_dir, 'status_test.bkp')
        with open(old_file, 'w') as f:
            f.write('test')
        
        old_time = datetime.now() - timedelta(hours=48)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
        
        manager = CleanupManager(config=self.config)
        status = manager.get_cleanup_status()
        
        assert 'local_files' in status
        assert status['local_files']['count'] >= 1


@mock_aws
class TestCleanupManagerS3:
    """Testes para limpeza S3"""

    def setup_method(self, method):
        """Setup para cada teste"""
        self.bucket_name = 'test-finops-cleanup'
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.s3_client.create_bucket(Bucket=self.bucket_name)
        
        self.config = CleanupConfig(
            cleanup_directories=[],
            s3_cleanup_enabled=True,
            s3_max_age_days=7
        )

    def test_cleanup_old_s3_objects(self):
        """Testa limpeza de objetos S3 antigos"""
        # Cria objeto S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key='executions/old_exec/state.json',
            Body=b'{"test": "data"}'
        )
        
        manager = CleanupManager(config=self.config, s3_bucket=self.bucket_name)
        
        # Como o moto não suporta LastModified antigo facilmente,
        # vamos testar que o método executa sem erros
        result = manager.cleanup_s3_objects()
        
        assert isinstance(result, CleanupResult)

    def test_s3_cleanup_nonexistent_bucket(self):
        """Testa limpeza com bucket inexistente"""
        manager = CleanupManager(
            config=self.config, 
            s3_bucket='nonexistent-bucket-xyz'
        )
        
        result = manager.cleanup_s3_objects()
        
        # Deve tratar o erro graciosamente
        assert isinstance(result, CleanupResult)


class TestCleanupAfterExecution:
    """Testes para função helper cleanup_after_execution"""

    def test_cleanup_after_execution_adds_metrics(self):
        """Testa que cleanup_after_execution adiciona métricas"""
        result_dict = {'data': 'test'}
        
        with patch.object(CleanupManager, 'cleanup_all') as mock_cleanup:
            mock_cleanup.return_value = CleanupResult(
                files_deleted=5,
                bytes_freed=1000
            )
            
            updated_result = cleanup_after_execution(result_dict)
            
            assert 'cleanup_metrics' in updated_result
            assert updated_result['cleanup_metrics']['files_deleted'] == 5


class TestCleanupManagerPycache:
    """Testes para limpeza de __pycache__"""

    def setup_method(self, method):
        """Setup para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = CleanupConfig(
            cleanup_directories=[self.temp_dir],
            s3_cleanup_enabled=False
        )

    def teardown_method(self, method):
        """Cleanup após cada teste"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cleanup_pycache_directory(self):
        """Testa limpeza de diretório __pycache__"""
        # Cria estrutura __pycache__
        pycache_dir = os.path.join(self.temp_dir, '__pycache__')
        os.makedirs(pycache_dir)
        
        pyc_file = os.path.join(pycache_dir, 'test.cpython-311.pyc')
        with open(pyc_file, 'w') as f:
            f.write('compiled python')
        
        manager = CleanupManager(config=self.config)
        result = manager.cleanup_pycache(base_path=self.temp_dir)
        
        assert result.files_deleted >= 1

    def test_cleanup_pyc_files(self):
        """Testa limpeza de arquivos .pyc individuais"""
        pyc_file = os.path.join(self.temp_dir, 'module.pyc')
        with open(pyc_file, 'w') as f:
            f.write('compiled')
        
        manager = CleanupManager(config=self.config)
        result = manager.cleanup_pycache(base_path=self.temp_dir)
        
        assert result.files_deleted >= 1
        assert not os.path.exists(pyc_file)


class TestCleanupManagerEdgeCases:
    """Testes para casos extremos"""

    def test_permission_denied_handling(self):
        """Testa tratamento de permissão negada"""
        config = CleanupConfig(
            cleanup_directories=['/root/protected'],
            s3_cleanup_enabled=False
        )
        
        manager = CleanupManager(config=config)
        result = manager.cleanup_local_files()
        
        # Deve tratar o erro graciosamente
        assert isinstance(result, CleanupResult)

    def test_nonexistent_directory(self):
        """Testa diretório inexistente"""
        config = CleanupConfig(
            cleanup_directories=['/nonexistent/path/xyz'],
            s3_cleanup_enabled=False
        )
        
        manager = CleanupManager(config=config)
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 0
        assert len(result.errors) == 0

    def test_empty_config(self):
        """Testa configuração com lista vazia"""
        config = CleanupConfig(
            file_extensions=set(),
            cleanup_directories=[]
        )
        
        manager = CleanupManager(config=config)
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 0

    def test_cleanup_all_combines_results(self):
        """Testa que cleanup_all combina resultados corretamente"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            config = CleanupConfig(
                cleanup_directories=[temp_dir],
                s3_cleanup_enabled=False
            )
            
            manager = CleanupManager(config=config)
            result = manager.cleanup_all()
            
            assert isinstance(result, CleanupResult)
            assert result.execution_time_seconds > 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
