"""
FinOps AWS Dashboard Module

Módulo para análise de custos AWS e integração com dashboard web.
"""

from .integrations import (
    get_compute_optimizer_recommendations,
    get_cost_explorer_ri_recommendations,
    get_trusted_advisor_recommendations,
    get_amazon_q_insights,
)
from .multi_region import get_all_regions_analysis, get_region_costs
from .export import export_to_csv, export_to_json, export_to_html, save_report

__all__ = [
    'get_compute_optimizer_recommendations',
    'get_cost_explorer_ri_recommendations',
    'get_trusted_advisor_recommendations',
    'get_amazon_q_insights',
    'get_all_regions_analysis',
    'get_region_costs',
    'export_to_csv',
    'export_to_json',
    'export_to_html',
    'save_report',
]
