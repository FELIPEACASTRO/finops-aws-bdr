"""
Prompt Templates

Templates específicos para cada tipo de persona e relatório.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

from .executive import EXECUTIVE_REPORT_TEMPLATE
from .technical import TECHNICAL_REPORT_TEMPLATE
from .operational import OPERATIONAL_REPORT_TEMPLATE
from .analyst import ANALYST_REPORT_TEMPLATE

__all__ = [
    'EXECUTIVE_REPORT_TEMPLATE',
    'TECHNICAL_REPORT_TEMPLATE',
    'OPERATIONAL_REPORT_TEMPLATE',
    'ANALYST_REPORT_TEMPLATE'
]
