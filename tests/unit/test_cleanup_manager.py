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
    CleanupConfig,
    CleanupResult,
    CleanupManager
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

    def test_custom_config(self):
        """Testa configuração personalizada"""
        config = CleanupConfig(
            file_extensions={'.bkp', '.tmp'},
            max_file_age_hours=48,
            max_file_size_mb=50.0,
            dry_run=True
        )
        
        assert config.file_extensions == {'.bkp', '.tmp'}
        assert config.max_file_age_hours == 48
        assert config.max_file_size_mb == 50.0
        assert config.dry_run is True

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
        assert result.s3_objects_deleted == 0
        assert result.errors == []

    def test_custom_result(self):
        """Testa resultado personalizado"""
        result = CleanupResult(
            files_deleted=5,
            files_failed=1,
            bytes_freed=1024,
            errors=['error1']
        )
        
        assert result.files_deleted == 5
        assert result.files_failed == 1
        assert result.bytes_freed == 1024
        assert result.errors == ['error1']

    def test_result_to_dict(self):
        """Testa conversão para dicionário"""
        result = CleanupResult(
            files_deleted=10,
            bytes_freed=1048576  # 1 MB
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['files_deleted'] == 10
        assert result_dict['bytes_freed'] == 1048576
        assert result_dict['bytes_freed_mb'] == 1.0

    def test_result_merge(self):
        """Testa mesclagem de resultados"""
        result1 = CleanupResult(files_deleted=5, bytes_freed=1000)
        result2 = CleanupResult(files_deleted=3, bytes_freed=500)
        
        merged = result1.merge(result2)
        
        assert merged.files_deleted == 8
        assert merged.bytes_freed == 1500

    def test_success_rate_calculation(self):
        """Testa cálculo de taxa de sucesso"""
        result = CleanupResult(files_deleted=9, files_failed=1)
        
        result_dict = result.to_dict()
        
        assert result_dict['success_rate'] == 90.0


class TestCleanupManager:
    """Testes para CleanupManager"""

    @pytest.fixture
    def temp_dir(self):
        """Cria diretório temporário para testes"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def cleanup_manager(self, temp_dir):
        """Cria CleanupManager para testes"""
        config = CleanupConfig(
            file_extensions={'.bkp', '.tmp', '.cache'},
            max_file_age_hours=0,  # Todos os arquivos são "antigos"
            cleanup_directories=[temp_dir],
            s3_cleanup_enabled=False,
            dry_run=False
        )
        return CleanupManager(config=config)

    def test_init_default_config(self):
        """Testa inicialização com configuração padrão"""
        with patch.dict(os.environ, {}, clear=True):
            manager = CleanupManager()
            assert manager.config is not None

    def test_init_custom_config(self):
        """Testa inicialização com configuração personalizada"""
        config = CleanupConfig(max_file_age_hours=48)
        manager = CleanupManager(config=config)
        
        assert manager.config.max_file_age_hours == 48

    def test_cleanup_local_files_empty_directory(self, cleanup_manager):
        """Testa limpeza em diretório vazio"""
        result = cleanup_manager.cleanup_local_files()
        
        assert result.files_deleted == 0
        assert len(result.errors) == 0

    def test_cleanup_local_files_with_target_files(self, cleanup_manager, temp_dir):
        """Testa limpeza com arquivos alvo"""
        # Criar arquivos de teste
        test_file = os.path.join(temp_dir, 'test.bkp')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        result = cleanup_manager.cleanup_local_files()
        
        assert result.files_deleted == 1
        assert not os.path.exists(test_file)

    def test_cleanup_local_files_preserves_non_target_files(self, cleanup_manager, temp_dir):
        """Testa que arquivos não-alvo são preservados"""
        # Criar arquivo que não deve ser deletado
        keep_file = os.path.join(temp_dir, 'keep.txt')
        with open(keep_file, 'w') as f:
            f.write('keep this')
        
        result = cleanup_manager.cleanup_local_files()
        
        assert result.files_deleted == 0
        assert os.path.exists(keep_file)

    def test_cleanup_dry_run(self, temp_dir):
        """Testa modo dry run"""
        config = CleanupConfig(
            file_extensions={'.bkp'},
            max_file_age_hours=0,
            cleanup_directories=[temp_dir],
            s3_cleanup_enabled=False,
            dry_run=True
        )
        manager = CleanupManager(config=config)
        
        # Criar arquivo de teste
        test_file = os.path.join(temp_dir, 'test.bkp')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 1
        assert os.path.exists(test_file)  # Arquivo ainda existe em dry run

    def test_cleanup_pycache(self, temp_dir):
        """Testa limpeza de __pycache__"""
        config = CleanupConfig(
            cleanup_directories=[temp_dir],
            s3_cleanup_enabled=False
        )
        manager = CleanupManager(config=config)
        
        # Criar diretório __pycache__
        pycache_dir = os.path.join(temp_dir, '__pycache__')
        os.makedirs(pycache_dir)
        
        # Criar arquivo .pyc
        pyc_file = os.path.join(pycache_dir, 'test.pyc')
        with open(pyc_file, 'w') as f:
            f.write('bytecode')
        
        result = manager.cleanup_pycache(temp_dir)
        
        assert result.files_deleted >= 1
        assert not os.path.exists(pycache_dir)

    @mock_aws
    def test_cleanup_s3_objects(self):
        """Testa limpeza de objetos S3"""
        # Criar bucket mock
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'test-bucket'
        s3.create_bucket(Bucket=bucket_name)
        
        # Adicionar objeto antigo
        s3.put_object(
            Bucket=bucket_name,
            Key='executions/old-execution.json',
            Body=b'old data'
        )
        
        config = CleanupConfig(
            s3_cleanup_enabled=True,
            s3_max_age_days=0  # Todos os objetos são "antigos"
        )
        manager = CleanupManager(config=config, s3_bucket=bucket_name)
        
        result = manager.cleanup_s3_objects()
        
        assert result.s3_objects_deleted == 1

    @mock_aws
    def test_cleanup_s3_bucket_not_found(self):
        """Testa tratamento de bucket S3 inexistente"""
        config = CleanupConfig(s3_cleanup_enabled=True)
        manager = CleanupManager(config=config, s3_bucket='nonexistent-bucket')
        
        result = manager.cleanup_s3_objects()
        
        # Não deve lançar exceção, apenas logar warning
        assert result.s3_objects_deleted == 0

    def test_cleanup_all(self, temp_dir):
        """Testa limpeza completa"""
        config = CleanupConfig(
            file_extensions={'.bkp'},
            max_file_age_hours=0,
            cleanup_directories=[temp_dir],
            s3_cleanup_enabled=False
        )
        manager = CleanupManager(config=config)
        
        # Criar arquivo de teste
        test_file = os.path.join(temp_dir, 'test.bkp')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        result = manager.cleanup_all()
        
        assert isinstance(result, CleanupResult)
        assert result.execution_time_seconds > 0

    def test_cleanup_temp_directory(self, temp_dir):
        """Testa limpeza de diretório temporário"""
        config = CleanupConfig(s3_cleanup_enabled=False)
        manager = CleanupManager(config=config)
        
        # Criar arquivo com prefixo finops_
        with patch('tempfile.gettempdir', return_value=temp_dir):
            finops_file = os.path.join(temp_dir, 'finops_test.tmp')
            with open(finops_file, 'w') as f:
                f.write('finops temp data')
            
            result = manager.cleanup_temp_directory()
            
            assert result.files_deleted == 1

    def test_get_cleanup_status(self, temp_dir):
        """Testa obtenção de status de limpeza"""
        config = CleanupConfig(
            file_extensions={'.bkp'},
            max_file_age_hours=0,
            cleanup_directories=[temp_dir],
            s3_cleanup_enabled=False
        )
        manager = CleanupManager(config=config)
        
        # Criar arquivo de teste
        test_file = os.path.join(temp_dir, 'test.bkp')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        status = manager.get_cleanup_status()
        
        assert 'local_files' in status
        assert status['local_files']['count'] == 1

    def test_permission_error_handling(self, temp_dir):
        """Testa tratamento de erros de permissão"""
        config = CleanupConfig(
            file_extensions={'.bkp'},
            max_file_age_hours=0,
            cleanup_directories=['/root/nonexistent'],  # Diretório sem permissão
            s3_cleanup_enabled=False
        )
        manager = CleanupManager(config=config)
        
        result = manager.cleanup_local_files()
        
        # Não deve lançar exceção
        assert isinstance(result, CleanupResult)

    def test_empty_config(self, temp_dir):
        """Testa configuração com lista vazia"""
        config = CleanupConfig(
            file_extensions=set(),
            cleanup_directories=[temp_dir],
            s3_cleanup_enabled=False
        )
        
        manager = CleanupManager(config=config)
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 0

    def test_cleanup_multiple_extensions(self, temp_dir):
        """Testa limpeza de múltiplas extensões"""
        config = CleanupConfig(
            file_extensions={'.bkp', '.tmp', '.cache'},
            max_file_age_hours=0,
            cleanup_directories=[temp_dir],
            s3_cleanup_enabled=False
        )
        manager = CleanupManager(config=config)
        
        # Criar arquivos de diferentes extensões
        for ext in ['.bkp', '.tmp', '.cache']:
            test_file = os.path.join(temp_dir, f'test{ext}')
            with open(test_file, 'w') as f:
                f.write('test content')
        
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 3

    def test_cleanup_nested_directories(self, temp_dir):
        """Testa limpeza em diretórios aninhados"""
        config = CleanupConfig(
            file_extensions={'.bkp'},
            max_file_age_hours=0,
            cleanup_directories=[temp_dir],
            s3_cleanup_enabled=False
        )
        manager = CleanupManager(config=config)
        
        # Criar estrutura de diretórios
        nested_dir = os.path.join(temp_dir, 'level1', 'level2')
        os.makedirs(nested_dir)
        
        test_file = os.path.join(nested_dir, 'test.bkp')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        result = manager.cleanup_local_files()
        
        assert result.files_deleted == 1
        assert not os.path.exists(test_file)


class TestCleanupManagerEdgeCases:
    """Testes de casos extremos para CleanupManager"""

    def test_file_age_filtering(self):
        """Testa filtragem por idade do arquivo"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            config = CleanupConfig(
                file_extensions={'.bkp'},
                max_file_age_hours=24,
                cleanup_directories=[temp_dir],
                s3_cleanup_enabled=False
            )
            manager = CleanupManager(config=config)
            
            # Criar arquivo novo (não deve ser deletado)
            test_file = os.path.join(temp_dir, 'new.bkp')
            with open(test_file, 'w') as f:
                f.write('new content')
            
            result = manager.cleanup_local_files()
            
            assert result.files_deleted == 0
            assert os.path.exists(test_file)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_max_file_size_filtering(self):
        """Testa filtragem por tamanho máximo"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            config = CleanupConfig(
                file_extensions={'.bkp'},
                max_file_age_hours=0,
                max_file_size_mb=0.0001,  # Muito pequeno (cerca de 100 bytes)
                cleanup_directories=[temp_dir],
                s3_cleanup_enabled=False
            )
            manager = CleanupManager(config=config)
            
            # Criar arquivo grande (não deve ser deletado por exceder o limite)
            test_file = os.path.join(temp_dir, 'large.bkp')
            with open(test_file, 'w') as f:
                f.write('x' * 1000)  # 1000 bytes
            
            result = manager.cleanup_local_files()
            
            # Arquivo deve ser pulado por exceder tamanho máximo
            assert test_file in result.skipped_files or os.path.exists(test_file)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_result_merge_errors(self):
        """Testa mesclagem de erros em resultados"""
        result1 = CleanupResult(errors=['error1', 'error2'])
        result2 = CleanupResult(errors=['error3'])
        
        merged = result1.merge(result2)
        
        assert len(merged.errors) == 3
        assert 'error1' in merged.errors
        assert 'error3' in merged.errors

    def test_s3_client_lazy_initialization(self):
        """Testa inicialização lazy do cliente S3"""
        config = CleanupConfig(s3_cleanup_enabled=False)
        manager = CleanupManager(config=config)
        
        # Cliente S3 não deve ser inicializado ainda
        assert manager._s3_client is None
        
        # Acessar propriedade s3_client deve inicializá-lo
        with mock_aws():
            client = manager.s3_client
            assert client is not None
            assert manager._s3_client is not None
