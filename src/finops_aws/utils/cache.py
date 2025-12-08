"""
FinOps AWS - Simple Cache Module

Sistema de cache em memória para evitar chamadas AWS repetidas.
Implementa TTL (Time To Live) configurável por chave.

Design Patterns:
- Singleton: Instância única do cache
- Decorator: Facilita caching de funções
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Callable, TypeVar, Dict
from functools import wraps
import threading

T = TypeVar('T')


class CacheEntry:
    """Entrada individual do cache com TTL"""
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class FinOpsCache:
    """
    Cache em memória thread-safe para dados FinOps.
    
    Usa padrão Singleton para garantir instância única.
    
    Exemplo de uso:
        cache = FinOpsCache()
        cache.set('budgets', budgets_data, ttl_seconds=300)
        cached_data = cache.get('budgets')
    """
    
    _instance: Optional['FinOpsCache'] = None
    _lock = threading.Lock()
    _cache: Dict[str, CacheEntry] = {}
    _stats: Dict[str, int] = {'hits': 0, 'misses': 0}
    
    def __new__(cls) -> 'FinOpsCache':
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._cache = {}
                cls._stats = {'hits': 0, 'misses': 0}
        return cls._instance
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache se existir e não estiver expirado.
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor cacheado ou None se não existir/expirado
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self._stats['misses'] += 1
            return None
        
        if entry.is_expired():
            del self._cache[key]
            self._stats['misses'] += 1
            return None
        
        self._stats['hits'] += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """
        Armazena valor no cache com TTL.
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl_seconds: Tempo de vida em segundos (padrão: 5 minutos)
        """
        self._cache[key] = CacheEntry(value, ttl_seconds)
    
    def delete(self, key: str) -> bool:
        """
        Remove entrada do cache.
        
        Args:
            key: Chave a remover
            
        Returns:
            True se removeu, False se não existia
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> int:
        """
        Limpa todo o cache.
        
        Returns:
            Número de entradas removidas
        """
        count = len(self._cache)
        self._cache.clear()
        return count
    
    def cleanup_expired(self) -> int:
        """
        Remove entradas expiradas.
        
        Returns:
            Número de entradas removidas
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache.
        
        Returns:
            Dict com hits, misses e taxa de acerto
        """
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'entries_count': len(self._cache),
            'expired_entries': sum(1 for e in self._cache.values() if e.is_expired())
        }
    
    def __len__(self) -> int:
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        entry = self._cache.get(key)
        return entry is not None and not entry.is_expired()


def cached(ttl_seconds: int = 300, key_prefix: str = '') -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator para cachear resultado de funções.
    
    Args:
        ttl_seconds: Tempo de vida do cache em segundos
        key_prefix: Prefixo para a chave do cache
        
    Exemplo:
        @cached(ttl_seconds=300, key_prefix='budgets')
        def get_budgets_analysis():
            # Chamada AWS cara
            return result
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            cache = FinOpsCache()
            
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{hash(args)}"
            if kwargs:
                cache_key += f":{hash(frozenset(kwargs.items()))}"
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            
            cache.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


def get_cache() -> FinOpsCache:
    """
    Obtém instância singleton do cache.
    
    Returns:
        Instância do FinOpsCache
    """
    return FinOpsCache()
