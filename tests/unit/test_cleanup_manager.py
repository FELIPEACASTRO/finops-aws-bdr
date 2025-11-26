"""
Testes unitários para o CleanupManager.

Testa todas as funcionalidades do sistema de limpeza automática
conforme especificado na FASE 1.1 do roadmap.
"""

import os
import time
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.finops_aws.utils.cleanup_manager import (
    CleanupManager, 
    CleanupConfig, 
    CleanupResult
)


class TestCleanupConfig:
    """Testes para a configuração do CleanupManager."""
    
    def test_default_config(self):
        """Testa configuração padrão."""
        config = CleanupConfig()
        
        assert config.max_file_age_hours == 24
        assert config.max_total_size_mb == 100
        assert '*.bkp' in config.file_patterns
        assert '*.tmp' in config.file_patterns
        assert '*.cache' in config.file_patterns
        assert '*.log.old' in config.file_patterns
        assert '/tmp' in config.base_directories
    
    def test_custom_config(self):
        """Testa configuração personalizada."""
        config = CleanupConfig(
            max_file_age_hours=48,
            max_total_size_mb=200,
            file_patterns=['*.custom'],
            base_directories=['/custom/path']
        )
        
        assert config.max_file_age_hours == 48
        assert config.max_total_size_mb == 200
        assert config.file_patterns == ['*.custom']
        assert config.base_directories == ['/custom/path']


class TestCleanupResult:
    """Testes para o resultado da limpeza."""
    
    def test_default_result(self):
        """Testa resultado padrão."""
        result = CleanupResult()
        
        assert result.files_removed == 0
        assert result.total_size_freed_mb == 0.0
        assert result.errors == []
        assert result.execution_time_seconds == 0.0
        assert result.directories_processed == 0
    
    def test_custom_result(self):
        """Testa resultado personalizado."""
        result = CleanupResult(
            files_removed=5,
            total_size_freed_mb=10.5,
            errors=['error1', 'error2'],
            execution_time_seconds=2.5,
            directories_processed=3
        )
        
        assert result.files_removed == 5
        assert result.total_size_freed_mb == 10.5
        assert result.errors == ['error1', 'error2']
        assert result.execution_time_seconds == 2.5
        assert result.directories_processed == 3


class TestCleanupManager:
    """Testes para o CleanupManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Cria diretório temporário para testes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def cleanup_manager(self, temp_dir):
        """Cria CleanupManager para testes."""
        config = CleanupConfig(
            max_file_age_hours=1,  # 1 hora para testes rápidos
            max_total_size_mb=10,
            file_patterns=['*.bkp', '*.tmp', '*.cache'],
            base_directories=[temp_dir]
        )
        return CleanupManager(config)
    
    def test_init_default_config(self):
        """Testa inicialização com configuração padrão."""
        manager = CleanupManager()
        
        assert manager.config is not None
        assert manager.logger is not None
        assert manager.config.max_file_age_hours == 24
    
    def test_init_custom_config(self):
        """Testa inicialização com configuração personalizada."""
        config = CleanupConfig(max_file_age_hours=48)
        manager = CleanupManager(config)
        
        assert manager.config.max_file_age_hours == 48
    
    def test_cleanup_files_empty_directory(self, cleanup_manager, temp_dir):
        """Testa limpeza em diretório vazio."""
        result = cleanup_manager.cleanup_files()
        
        assert result.files_removed == 0
        assert result.total_size_freed_mb == 0.0
        assert len(result.errors) == 0
        assert result.directories_processed == 1
        assert result.execution_time_seconds > 0
    
    def test_cleanup_files_with_old_files(self, cleanup_manager, temp_dir):
        """Testa limpeza com arquivos antigos."""
        # Criar arquivos de teste
        old_file = os.path.join(temp_dir, 'old_file.bkp')
        new_file = os.path.join(temp_dir, 'new_file.tmp')
        
        # Criar arquivo antigo
        with open(old_file, 'w') as f:
            f.write('test content old')
        
        # Criar arquivo novo
        with open(new_file, 'w') as f:
            f.write('test content new')
        
        # Modificar tempo do arquivo antigo (2 horas atrás)
        old_time = time.time() - (2 * 3600)
        os.utime(old_file, (old_time, old_time))
        
        result = cleanup_manager.cleanup_files()
        
        assert result.files_removed == 1  # Apenas o arquivo antigo
        assert result.total_size_freed_mb > 0
        assert len(result.errors) == 0
        assert not os.path.exists(old_file)  # Arquivo antigo removido
        assert os.path.exists(new_file)  # Arquivo novo mantido
    
    def test_cleanup_files_nonexistent_directory(self):
        """Testa limpeza em diretório inexistente."""
        config = CleanupConfig(
            base_directories=['/nonexistent/directory']
        )
        manager = CleanupManager(config)
        
        result = manager.cleanup_files()
        
        assert result.files_removed == 0
        assert result.total_size_freed_mb == 0.0
        assert result.directories_processed == 1
    
    def test_should_remove_file_old(self, cleanup_manager, temp_dir):
        """Testa se arquivo antigo deve ser removido."""
        old_file = os.path.join(temp_dir, 'old_file.bkp')
        
        with open(old_file, 'w') as f:
            f.write('test')
        
        # Modificar tempo (2 horas atrás)
        old_time = time.time() - (2 * 3600)
        os.utime(old_file, (old_time, old_time))
        
        assert cleanup_manager._should_remove_file(old_file) is True
    
    def test_should_remove_file_new(self, cleanup_manager, temp_dir):
        """Testa se arquivo novo não deve ser removido."""
        new_file = os.path.join(temp_dir, 'new_file.tmp')
        
        with open(new_file, 'w') as f:
            f.write('test')
        
        assert cleanup_manager._should_remove_file(new_file) is False
    
    def test_should_remove_file_nonexistent(self, cleanup_manager):
        """Testa arquivo inexistente."""
        assert cleanup_manager._should_remove_file('/nonexistent/file') is False
    
    def test_remove_file_success(self, cleanup_manager, temp_dir):
        """Testa remoção bem-sucedida de arquivo."""
        test_file = os.path.join(temp_dir, 'test_file.bkp')
        test_content = 'test content for size calculation'
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        size_freed = cleanup_manager._remove_file(test_file)
        
        assert size_freed > 0
        assert not os.path.exists(test_file)
    
    def test_remove_file_nonexistent(self, cleanup_manager):
        """Testa remoção de arquivo inexistente."""
        size_freed = cleanup_manager._remove_file('/nonexistent/file')
        
        assert size_freed == -1.0
    
    def test_get_cleanup_metrics_empty(self, cleanup_manager, temp_dir):
        """Testa métricas em diretório vazio."""
        metrics = cleanup_manager.get_cleanup_metrics()
        
        assert metrics["total_files_found"] == 0
        assert metrics["total_size_mb"] == 0.0
        assert metrics["oldest_file_age_hours"] == 0
        assert metrics["largest_file_size_mb"] == 0.0
        assert temp_dir in metrics["files_by_directory"]
    
    def test_get_cleanup_metrics_with_files(self, cleanup_manager, temp_dir):
        """Testa métricas com arquivos."""
        # Criar arquivos de teste
        bkp_file = os.path.join(temp_dir, 'test.bkp')
        tmp_file = os.path.join(temp_dir, 'test.tmp')
        
        with open(bkp_file, 'w') as f:
            f.write('backup content')
        
        with open(tmp_file, 'w') as f:
            f.write('temp content')
        
        metrics = cleanup_manager.get_cleanup_metrics()
        
        assert metrics["total_files_found"] == 2
        assert metrics["total_size_mb"] > 0
        assert "*.bkp" in metrics["files_by_pattern"]
        assert "*.tmp" in metrics["files_by_pattern"]
        assert metrics["files_by_pattern"]["*.bkp"]["file_count"] == 1
        assert metrics["files_by_pattern"]["*.tmp"]["file_count"] == 1
    
    def test_force_cleanup_by_size(self, cleanup_manager, temp_dir):
        """Testa limpeza forçada por tamanho."""
        # Criar múltiplos arquivos
        files = []
        for i in range(5):
            file_path = os.path.join(temp_dir, f'file_{i}.bkp')
            with open(file_path, 'w') as f:
                f.write(f'content for file {i}' * 100)  # Arquivo maior
            
            # Tornar alguns arquivos mais antigos
            if i < 3:
                old_time = time.time() - (i + 1) * 3600
                os.utime(file_path, (old_time, old_time))
            
            files.append(file_path)
        
        # Forçar limpeza de 0.001 MB (deve remover pelo menos 1 arquivo)
        result = cleanup_manager.force_cleanup_by_size(0.001)
        
        assert result.files_removed > 0
        assert result.total_size_freed_mb > 0
        assert result.execution_time_seconds > 0
    
    def test_force_cleanup_by_size_no_files(self, cleanup_manager, temp_dir):
        """Testa limpeza forçada sem arquivos."""
        result = cleanup_manager.force_cleanup_by_size(10.0)
        
        assert result.files_removed == 0
        assert result.total_size_freed_mb == 0.0
        assert result.execution_time_seconds > 0
    
    @patch('os.remove')
    def test_cleanup_with_permission_error(self, mock_remove, cleanup_manager, temp_dir):
        """Testa limpeza com erro de permissão."""
        # Configurar mock para simular erro de permissão
        mock_remove.side_effect = PermissionError("Permission denied")
        
        # Criar arquivo de teste
        test_file = os.path.join(temp_dir, 'test.bkp')
        with open(test_file, 'w') as f:
            f.write('test')
        
        # Tornar arquivo antigo
        old_time = time.time() - (2 * 3600)
        os.utime(test_file, (old_time, old_time))
        
        result = cleanup_manager.cleanup_files()
        
        assert result.files_removed == 0
        assert len(result.errors) > 0
        assert any('Erro ao remover arquivo' in error for error in result.errors)
    
    @patch('glob.glob')
    def test_cleanup_with_glob_error(self, mock_glob, cleanup_manager):
        """Testa limpeza com erro no glob."""
        mock_glob.side_effect = Exception("Glob error")
        
        result = cleanup_manager.cleanup_files()
        
        assert result.files_removed == 0
        assert len(result.errors) > 0
    
    def test_cleanup_files_integration(self, temp_dir):
        """Teste de integração completo."""
        # Configuração personalizada
        config = CleanupConfig(
            max_file_age_hours=0.5,  # 30 minutos
            file_patterns=['*.bkp', '*.tmp', '*.cache', '*.log.old'],
            base_directories=[temp_dir]
        )
        manager = CleanupManager(config)
        
        # Criar mix de arquivos antigos e novos
        files_created = []
        
        # Arquivos antigos (devem ser removidos)
        for i in range(3):
            file_path = os.path.join(temp_dir, f'old_{i}.bkp')
            with open(file_path, 'w') as f:
                f.write(f'old content {i}' * 50)
            
            old_time = time.time() - (1 * 3600)  # 1 hora atrás
            os.utime(file_path, (old_time, old_time))
            files_created.append(file_path)
        
        # Arquivos novos (devem ser mantidos)
        for i in range(2):
            file_path = os.path.join(temp_dir, f'new_{i}.tmp')
            with open(file_path, 'w') as f:
                f.write(f'new content {i}' * 30)
            files_created.append(file_path)
        
        # Arquivo que não corresponde ao padrão (deve ser mantido)
        other_file = os.path.join(temp_dir, 'other.txt')
        with open(other_file, 'w') as f:
            f.write('other content')
        files_created.append(other_file)
        
        # Executar limpeza
        result = manager.cleanup_files()
        
        # Verificar resultados
        assert result.files_removed == 3  # Apenas arquivos .bkp antigos
        assert result.total_size_freed_mb > 0
        assert result.directories_processed == 1
        assert len(result.errors) == 0
        assert result.execution_time_seconds > 0
        
        # Verificar arquivos restantes
        remaining_files = os.listdir(temp_dir)
        assert len(remaining_files) == 3  # 2 .tmp novos + 1 .txt
        assert any('new_0.tmp' in f for f in remaining_files)
        assert any('new_1.tmp' in f for f in remaining_files)
        assert any('other.txt' in f for f in remaining_files)
        
        # Verificar métricas
        metrics = manager.get_cleanup_metrics()
        assert metrics["total_files_found"] == 2  # Apenas arquivos .tmp restantes
        assert metrics["total_size_mb"] > 0