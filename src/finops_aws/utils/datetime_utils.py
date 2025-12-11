"""
Datetime utilities for FinOps AWS

Provides timezone-aware datetime functions to replace deprecated
datetime.utcnow() calls.
"""
from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC datetime (timezone-aware).
    
    Replaces deprecated datetime.utcnow() with the recommended
    datetime.now(timezone.utc) pattern.
    
    Returns:
        datetime: Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def utc_iso_now() -> str:
    """
    Get current UTC datetime as ISO format string.
    
    Returns:
        str: ISO formatted datetime string
    """
    return utc_now().isoformat()


def to_utc(dt: datetime) -> datetime:
    """
    Convert a datetime to UTC timezone.
    
    Args:
        dt: Datetime to convert (can be naive or aware)
        
    Returns:
        datetime: UTC timezone-aware datetime
    """
    if dt.tzinfo is None:
        # Assume UTC if naive
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parse an ISO format datetime string.
    
    Args:
        iso_string: ISO formatted datetime string
        
    Returns:
        datetime: Parsed datetime (timezone-aware if present in string)
    """
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        # Fallback for formats without timezone
        dt = datetime.fromisoformat(iso_string)
        return dt.replace(tzinfo=timezone.utc)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime as a standard timestamp string.
    
    Args:
        dt: Datetime to format (defaults to current UTC time)
        
    Returns:
        str: Formatted timestamp string
    """
    if dt is None:
        dt = utc_now()
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
