"""
Export Module for FinOps Dashboard

Exportação de relatórios em diferentes formatos:
- CSV
- JSON
- HTML (para PDF via browser)
"""

import os
import json
import csv
import io
from datetime import datetime
from typing import Dict, Any, List, Optional

import logging

logger = logging.getLogger(__name__)


def export_to_csv(data: Dict[str, Any]) -> str:
    """
    Exporta dados de análise para formato CSV.
    
    Args:
        data: Dados da análise FinOps
        
    Returns:
        String CSV formatada
    """
    output = io.StringIO()
    
    writer = csv.writer(output)
    writer.writerow(['FinOps AWS Report'])
    writer.writerow([f'Generated: {datetime.utcnow().isoformat()}'])
    writer.writerow([f'Account: {data.get("account_id", "Unknown")}'])
    writer.writerow([f'Region: {data.get("region", "Unknown")}'])
    writer.writerow([])
    
    writer.writerow(['COST SUMMARY'])
    costs = data.get('costs', {})
    writer.writerow(['Total Cost (30 days)', f'${costs.get("total", 0):.2f}'])
    writer.writerow([])
    
    writer.writerow(['COSTS BY SERVICE'])
    writer.writerow(['Service', 'Cost (USD)'])
    for service, cost in costs.get('by_service', {}).items():
        writer.writerow([service, f'${cost:.2f}'])
    writer.writerow([])
    
    writer.writerow(['RECOMMENDATIONS'])
    writer.writerow(['Type', 'Resource', 'Description', 'Priority', 'Estimated Savings (USD)', 'Source'])
    for rec in data.get('recommendations', []):
        writer.writerow([
            rec.get('type', ''),
            rec.get('resource_id', rec.get('resource', '')),
            rec.get('description', rec.get('title', '')),
            rec.get('priority', rec.get('impact', '')),
            f'${rec.get("savings", 0):.2f}',
            rec.get('service', rec.get('source', ''))
        ])
    writer.writerow([])
    
    summary = data.get('summary', {})
    writer.writerow(['SUMMARY'])
    writer.writerow(['Total Recommendations', summary.get('recommendations_count', 0)])
    writer.writerow(['Total Potential Savings', f'${summary.get("total_potential_savings", 0):.2f}'])
    writer.writerow(['Savings Percentage', f'{summary.get("savings_percentage", 0):.1f}%'])
    writer.writerow(['High Priority Items', summary.get('high_priority_count', 0)])
    
    return output.getvalue()


def export_to_json(data: Dict[str, Any], pretty: bool = True) -> str:
    """
    Exporta dados de análise para formato JSON.
    
    Args:
        data: Dados da análise FinOps
        pretty: Se True, formata JSON com indentação
        
    Returns:
        String JSON formatada
    """
    export_data = {
        'report_metadata': {
            'generated_at': datetime.utcnow().isoformat(),
            'account_id': data.get('account_id', 'Unknown'),
            'region': data.get('region', 'Unknown'),
            'format_version': '1.0'
        },
        'costs': data.get('costs', {}),
        'resources': data.get('resources', {}),
        'recommendations': data.get('recommendations', []),
        'summary': data.get('summary', {}),
        'integrations': data.get('integrations', {})
    }
    
    if pretty:
        return json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
    return json.dumps(export_data, ensure_ascii=False, default=str)


def export_to_html(data: Dict[str, Any]) -> str:
    """
    Exporta dados de análise para formato HTML (para impressão/PDF).
    
    Args:
        data: Dados da análise FinOps
        
    Returns:
        String HTML formatada
    """
    costs = data.get('costs', {})
    summary = data.get('summary', {})
    recommendations = data.get('recommendations', [])
    
    services_html = ""
    for service, cost in list(costs.get('by_service', {}).items())[:10]:
        services_html += f"<tr><td>{service}</td><td>${cost:.2f}</td></tr>"
    
    recs_html = ""
    for rec in recommendations[:20]:
        priority_class = 'high' if rec.get('priority') == 'HIGH' else ('medium' if rec.get('priority') == 'MEDIUM' else 'low')
        recs_html += f"""
        <tr class="priority-{priority_class}">
            <td>{rec.get('type', '')}</td>
            <td>{rec.get('resource_id', rec.get('resource', ''))}</td>
            <td>{rec.get('description', rec.get('title', ''))}</td>
            <td><span class="badge {priority_class}">{rec.get('priority', rec.get('impact', ''))}</span></td>
            <td>${rec.get('savings', 0):.2f}</td>
        </tr>
        """
    
    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinOps AWS Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header .meta {{
            opacity: 0.9;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        .summary-item {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .summary-item .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .summary-item .label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        .badge.high {{
            background: #fee2e2;
            color: #dc2626;
        }}
        .badge.medium {{
            background: #fef3c7;
            color: #d97706;
        }}
        .badge.low {{
            background: #dbeafe;
            color: #2563eb;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .card {{
                box-shadow: none;
                border: 1px solid #eee;
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>FinOps AWS Report</h1>
        <div class="meta">
            <p>Account: {data.get('account_id', 'Unknown')} | Region: {data.get('region', 'Unknown')}</p>
            <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
        </div>
    </div>
    
    <div class="card">
        <h2>Executive Summary</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <div class="value">${costs.get('total', 0):.2f}</div>
                <div class="label">Total Cost (30 days)</div>
            </div>
            <div class="summary-item">
                <div class="value">${summary.get('total_potential_savings', 0):.2f}</div>
                <div class="label">Potential Savings</div>
            </div>
            <div class="summary-item">
                <div class="value">{summary.get('recommendations_count', 0)}</div>
                <div class="label">Recommendations</div>
            </div>
            <div class="summary-item">
                <div class="value">{summary.get('high_priority_count', 0)}</div>
                <div class="label">High Priority</div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h2>Costs by Service</h2>
        <table>
            <thead>
                <tr>
                    <th>Service</th>
                    <th>Cost (USD)</th>
                </tr>
            </thead>
            <tbody>
                {services_html}
            </tbody>
        </table>
    </div>
    
    <div class="card">
        <h2>Recommendations</h2>
        <table>
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Resource</th>
                    <th>Description</th>
                    <th>Priority</th>
                    <th>Savings</th>
                </tr>
            </thead>
            <tbody>
                {recs_html}
            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>FinOps AWS - Enterprise Cost Optimization Solution</p>
        <p>Generated automatically by FinOps AWS Dashboard</p>
    </div>
</body>
</html>
"""
    
    return html


def save_report(data: Dict[str, Any], format: str = 'json', filename: Optional[str] = None) -> str:
    """
    Salva relatório em arquivo.
    
    Args:
        data: Dados da análise FinOps
        format: Formato do arquivo (csv, json, html)
        filename: Nome do arquivo (opcional, gera automaticamente)
        
    Returns:
        Caminho do arquivo salvo
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    if filename is None:
        filename = f"finops_report_{timestamp}"
    
    reports_dir = 'reports'
    os.makedirs(reports_dir, exist_ok=True)
    
    if format == 'csv':
        content = export_to_csv(data)
        filepath = os.path.join(reports_dir, f"{filename}.csv")
    elif format == 'html':
        content = export_to_html(data)
        filepath = os.path.join(reports_dir, f"{filename}.html")
    else:
        content = export_to_json(data)
        filepath = os.path.join(reports_dir, f"{filename}.json")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Relatório salvo em: {filepath}")
    
    return filepath
