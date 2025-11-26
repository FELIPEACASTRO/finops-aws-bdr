"""
CleanupManager - Sistema de limpeza automática de arquivos internos.

Este módulo implementa a funcionalidade de limpeza automática de arquivos
temporários, backup e cache conforme especificado na FASE 1.1 do roadmap.
"""

import os
import time
import glob
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from datetime import datetime, timedelta

from .logger import setup_logger


@dataclass
class CleanupConfig:
    """Configuração para o sistema de limpeza."""
    max_file_age_hours: int = 24  # Idade máxima dos arquivos em horas
    max_total_size_mb: int = 100  # Tamanho máximo total em MB
    file_patterns: List[str] = None  # Padrões de arquivos para limpeza
    base_directories: List[str] = None  # Diretórios base para limpeza

    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ['*.bkp', '*.tmp', '*.cache', '*.log.old']
        if self.base_directories is None:
            self.base_directories = ['/tmp', '/var/tmp', '~/.cache']


@dataclass
class CleanupResult:
    """Resultado da operação de limpeza."""
    files_removed: int = 0
    total_size_freed_mb: float = 0.0
    errors: List[str] = None
    execution_time_seconds: float = 0.0
    directories_processed: int = 0

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CleanupManager:
    """
    Gerenciador de limpeza automática de arquivos internos.

    Responsável por:
    - Limpeza de arquivos .bkp, .tmp, .cache
    - Controle de idade e tamanho de arquivos
    - Relatórios de limpeza
    - Integração com métricas do sistema
    """

    def __init__(self, config: Optional[CleanupConfig] = None):
        self.config = config or CleanupConfig()
        self.logger = setup_logger(__name__)

    def cleanup_files(self) -> CleanupResult:
        """
        Executa a limpeza automática de arquivos.

        Returns:
            CleanupResult: Resultado da operação de limpeza
        """
        start_time = time.time()
        result = CleanupResult()

        self.logger.info("Iniciando limpeza automática de arquivos", extra={
            "max_file_age_hours": self.config.max_file_age_hours,
            "max_total_size_mb": self.config.max_total_size_mb,
            "file_patterns": self.config.file_patterns
        })

        try:
            for directory in self.config.base_directories:
                directory_result = self._cleanup_directory(directory)
                result.files_removed += directory_result.files_removed
                result.total_size_freed_mb += directory_result.total_size_freed_mb
                result.errors.extend(directory_result.errors)
                result.directories_processed += 1

        except Exception as e:
            error_msg = f"Erro durante limpeza automática: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)

        result.execution_time_seconds = time.time() - start_time

        self.logger.info("Limpeza automática concluída", extra={
            "files_removed": result.files_removed,
            "size_freed_mb": result.total_size_freed_mb,
            "execution_time_seconds": result.execution_time_seconds,
            "directories_processed": result.directories_processed,
            "errors_count": len(result.errors)
        })

        return result

    def _cleanup_directory(self, directory: str) -> CleanupResult:
        """
        Limpa arquivos em um diretório específico.

        Args:
            directory: Caminho do diretório para limpeza

        Returns:
            CleanupResult: Resultado da limpeza do diretório
        """
        result = CleanupResult()

        try:
            # Expandir ~ para home directory
            expanded_dir = os.path.expanduser(directory)

            # Verificar se o diretório existe
            if not os.path.exists(expanded_dir):
                self.logger.debug(f"Diretório não existe: {expanded_dir}")
                return result

            # Processar cada padrão de arquivo
            for pattern in self.config.file_patterns:
                file_pattern = os.path.join(expanded_dir, pattern)
                files_to_check = glob.glob(file_pattern, recursive=True)

                for file_path in files_to_check:
                    if self._should_remove_file(file_path):
                        file_size_mb = self._remove_file(file_path)
                        if file_size_mb >= 0:  # Sucesso na remoção
                            result.files_removed += 1
                            result.total_size_freed_mb += file_size_mb
                        else:  # Erro na remoção
                            result.errors.append(f"Erro ao remover arquivo: {file_path}")

        except Exception as e:
            error_msg = f"Erro ao processar diretório {directory}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)

        return result

    def _should_remove_file(self, file_path: str) -> bool:
        """
        Determina se um arquivo deve ser removido baseado nas regras de limpeza.

        Args:
            file_path: Caminho do arquivo

        Returns:
            bool: True se o arquivo deve ser removido
        """
        try:
            # Verificar se o arquivo ainda existe
            if not os.path.exists(file_path):
                return False

            # Verificar idade do arquivo
            file_stat = os.stat(file_path)
            file_age = time.time() - file_stat.st_mtime
            max_age_seconds = self.config.max_file_age_hours * 3600

            if file_age > max_age_seconds:
                self.logger.debug(f"Arquivo marcado para remoção por idade: {file_path}", extra={
                    "file_age_hours": file_age / 3600,
                    "max_age_hours": self.config.max_file_age_hours
                })
                return True

            return False

        except Exception as e:
            self.logger.error(f"Erro ao verificar arquivo {file_path}: {str(e)}")
            return False

    def _remove_file(self, file_path: str) -> float:
        """
        Remove um arquivo e retorna o tamanho liberado.

        Args:
            file_path: Caminho do arquivo para remoção

        Returns:
            float: Tamanho liberado em MB (negativo em caso de erro)
        """
        try:
            # Obter tamanho do arquivo antes da remoção
            file_size_bytes = os.path.getsize(file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)

            # Remover o arquivo
            os.remove(file_path)

            self.logger.debug(f"Arquivo removido: {file_path}", extra={
                "file_size_mb": file_size_mb
            })

            return file_size_mb

        except Exception as e:
            self.logger.error(f"Erro ao remover arquivo {file_path}: {str(e)}")
            return -1.0

    def get_cleanup_metrics(self) -> Dict[str, Any]:
        """
        Coleta métricas sobre arquivos que podem ser limpos.

        Returns:
            Dict[str, Any]: Métricas de limpeza
        """
        metrics = {
            "total_files_found": 0,
            "total_size_mb": 0.0,
            "files_by_pattern": {},
            "files_by_directory": {},
            "oldest_file_age_hours": 0,
            "largest_file_size_mb": 0.0
        }

        try:
            for directory in self.config.base_directories:
                expanded_dir = os.path.expanduser(directory)

                if not os.path.exists(expanded_dir):
                    continue

                dir_metrics = {
                    "file_count": 0,
                    "total_size_mb": 0.0
                }

                for pattern in self.config.file_patterns:
                    file_pattern = os.path.join(expanded_dir, pattern)
                    files_found = glob.glob(file_pattern, recursive=True)

                    pattern_metrics = {
                        "file_count": len(files_found),
                        "total_size_mb": 0.0
                    }

                    for file_path in files_found:
                        try:
                            file_size_bytes = os.path.getsize(file_path)
                            file_size_mb = file_size_bytes / (1024 * 1024)

                            pattern_metrics["total_size_mb"] += file_size_mb
                            dir_metrics["total_size_mb"] += file_size_mb
                            metrics["total_size_mb"] += file_size_mb

                            # Atualizar maior arquivo
                            if file_size_mb > metrics["largest_file_size_mb"]:
                                metrics["largest_file_size_mb"] = file_size_mb

                            # Atualizar arquivo mais antigo
                            file_stat = os.stat(file_path)
                            file_age_hours = (time.time() - file_stat.st_mtime) / 3600
                            if file_age_hours > metrics["oldest_file_age_hours"]:
                                metrics["oldest_file_age_hours"] = file_age_hours

                        except Exception as e:
                            self.logger.debug(f"Erro ao processar arquivo {file_path}: {str(e)}")

                    metrics["files_by_pattern"][pattern] = pattern_metrics
                    metrics["total_files_found"] += pattern_metrics["file_count"]

                dir_metrics["file_count"] = sum(
                    metrics["files_by_pattern"][p]["file_count"]
                    for p in self.config.file_patterns
                )
                metrics["files_by_directory"][directory] = dir_metrics

        except Exception as e:
            self.logger.error(f"Erro ao coletar métricas de limpeza: {str(e)}")

        return metrics

    def force_cleanup_by_size(self, target_size_mb: float) -> CleanupResult:
        """
        Força limpeza até atingir um tamanho alvo.

        Args:
            target_size_mb: Tamanho alvo a ser liberado em MB

        Returns:
            CleanupResult: Resultado da operação
        """
        start_time = time.time()
        result = CleanupResult()

        self.logger.info(f"Iniciando limpeza forçada para liberar {target_size_mb} MB")

        try:
            # Coletar todos os arquivos candidatos com suas idades
            candidates = []

            for directory in self.config.base_directories:
                expanded_dir = os.path.expanduser(directory)

                if not os.path.exists(expanded_dir):
                    continue

                for pattern in self.config.file_patterns:
                    file_pattern = os.path.join(expanded_dir, pattern)
                    files_found = glob.glob(file_pattern, recursive=True)

                    for file_path in files_found:
                        try:
                            file_stat = os.stat(file_path)
                            file_age = time.time() - file_stat.st_mtime
                            file_size_mb = file_stat.st_size / (1024 * 1024)

                            candidates.append({
                                "path": file_path,
                                "age": file_age,
                                "size_mb": file_size_mb
                            })
                        except Exception:
                            continue

            # Ordenar por idade (mais antigos primeiro)
            candidates.sort(key=lambda x: x["age"], reverse=True)

            # Remover arquivos até atingir o tamanho alvo
            for candidate in candidates:
                if result.total_size_freed_mb >= target_size_mb:
                    break

                file_size_mb = self._remove_file(candidate["path"])
                if file_size_mb >= 0:
                    result.files_removed += 1
                    result.total_size_freed_mb += file_size_mb
                else:
                    result.errors.append(f"Erro ao remover: {candidate['path']}")

        except Exception as e:
            error_msg = f"Erro durante limpeza forçada: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)

        result.execution_time_seconds = time.time() - start_time

        self.logger.info("Limpeza forçada concluída", extra={
            "target_size_mb": target_size_mb,
            "actual_freed_mb": result.total_size_freed_mb,
            "files_removed": result.files_removed,
            "execution_time_seconds": result.execution_time_seconds
        })

        return result
