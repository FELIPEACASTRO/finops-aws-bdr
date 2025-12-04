"""
Report Structurer

Estrutura relatórios finais em diferentes formatos
(Markdown, HTML, JSON) para entrega.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class StructuredReport:
    """Relatório estruturado para entrega"""
    title: str
    generated_at: str
    period: str
    format: str
    content: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "generated_at": self.generated_at,
            "period": self.period,
            "format": self.format,
            "content": self.content,
            "metadata": self.metadata
        }


class ReportStructurer:
    """
    Estruturador de relatórios FinOps
    
    Transforma dados parseados em relatórios formatados
    para diferentes canais de entrega.
    
    Example:
        ```python
        structurer = ReportStructurer()
        
        markdown_report = structurer.to_markdown(parsed_data)
        html_report = structurer.to_html(parsed_data)
        ```
    """
    
    def __init__(
        self,
        company_name: str = "FinOps AWS",
        language: str = "pt-BR"
    ):
        """
        Inicializa estruturador
        
        Args:
            company_name: Nome da empresa para branding
            language: Idioma do relatório
        """
        self.company_name = company_name
        self.language = language
    
    def to_markdown(
        self,
        data: Dict[str, Any],
        title: str = "Relatório FinOps",
        include_toc: bool = True
    ) -> StructuredReport:
        """
        Gera relatório em Markdown
        
        Args:
            data: Dados do relatório (parseados)
            title: Título do relatório
            include_toc: Incluir tabela de conteúdo
            
        Returns:
            StructuredReport em Markdown
        """
        now = datetime.utcnow()
        period = data.get('period', {})
        
        sections = []
        
        sections.append(f"# {title}")
        sections.append("")
        sections.append(f"**Gerado em:** {now.strftime('%d/%m/%Y %H:%M UTC')}")
        sections.append(f"**Período:** {period.get('description', 'N/A')}")
        sections.append(f"**Gerado por:** {self.company_name}")
        sections.append("")
        sections.append("---")
        sections.append("")
        
        if include_toc:
            sections.append("## Índice")
            sections.append("")
            sections.append("1. [Resumo Executivo](#resumo-executivo)")
            sections.append("2. [Top Oportunidades de Economia](#top-oportunidades-de-economia)")
            sections.append("3. [Quick Wins](#quick-wins)")
            sections.append("4. [Análise por Serviço](#analise-por-servico)")
            sections.append("5. [Riscos e Alertas](#riscos-e-alertas)")
            sections.append("6. [Plano de Ação](#plano-de-acao)")
            sections.append("")
            sections.append("---")
            sections.append("")
        
        if data.get('executive_summary'):
            sections.append("## Resumo Executivo")
            sections.append("")
            sections.append(data['executive_summary'])
            sections.append("")
        
        if data.get('recommendations'):
            sections.append("## Top Oportunidades de Economia")
            sections.append("")
            sections.append("| # | Oportunidade | Economia/Mês | Prioridade | Esforço |")
            sections.append("|---|--------------|--------------|------------|---------|")
            
            for i, rec in enumerate(data['recommendations'][:10], 1):
                desc = rec.get('description', '')[:50]
                savings = f"${rec.get('estimated_savings', 0):,.2f}"
                priority = rec.get('priority', 'MEDIUM')
                effort = rec.get('effort', 'MEDIUM')
                sections.append(f"| {i} | {desc} | {savings} | {priority} | {effort} |")
            sections.append("")
        
        if data.get('quick_wins'):
            sections.append("## Quick Wins")
            sections.append("")
            sections.append("Ações para os próximos 7 dias:")
            sections.append("")
            for qw in data['quick_wins']:
                savings = f" (economia: ${qw.get('estimated_savings', 0):,.2f}/mês)" if qw.get('estimated_savings') else ""
                sections.append(f"- [ ] {qw.get('description', '')}{savings}")
            sections.append("")
        
        if data.get('service_analysis'):
            sections.append("## Análise por Serviço")
            sections.append("")
            sections.append("| Serviço | Custo | % Total | Tendência |")
            sections.append("|---------|-------|---------|-----------|")
            
            for svc in data['service_analysis'][:10]:
                name = svc.get('name', 'Unknown')
                cost = f"${svc.get('cost', 0):,.2f}"
                pct = svc.get('percentage', 'N/A')
                trend = svc.get('trend', 'STABLE')
                sections.append(f"| {name} | {cost} | {pct}% | {trend} |")
            sections.append("")
        
        if data.get('risks'):
            sections.append("## Riscos e Alertas")
            sections.append("")
            sections.append("| Risco | Severidade | Mitigação |")
            sections.append("|-------|------------|-----------|")
            
            for risk in data['risks']:
                desc = risk.get('description', '')[:60]
                severity = risk.get('severity', risk.get('probability', 'MEDIUM'))
                mitigation = risk.get('mitigation', '-')[:40]
                sections.append(f"| {desc} | {severity} | {mitigation} |")
            sections.append("")
        
        if data.get('action_plan'):
            sections.append("## Plano de Ação")
            sections.append("")
            
            plan = data['action_plan']
            if plan.get('phase_1'):
                sections.append("### Fase 1: 0-30 dias")
                for item in plan['phase_1']:
                    sections.append(f"- [ ] {item}")
                sections.append("")
            
            if plan.get('phase_2'):
                sections.append("### Fase 2: 31-60 dias")
                for item in plan['phase_2']:
                    sections.append(f"- [ ] {item}")
                sections.append("")
            
            if plan.get('phase_3'):
                sections.append("### Fase 3: 61-90 dias")
                for item in plan['phase_3']:
                    sections.append(f"- [ ] {item}")
                sections.append("")
        
        sections.append("---")
        sections.append("")
        sections.append(f"*Relatório gerado automaticamente por {self.company_name} AI Consultant*")
        
        content = '\n'.join(sections)
        
        return StructuredReport(
            title=title,
            generated_at=now.isoformat(),
            period=period.get('description', ''),
            format='markdown',
            content=content,
            metadata={
                "company": self.company_name,
                "language": self.language,
                "sections_count": len([s for s in sections if s.startswith('## ')])
            }
        )
    
    def to_html(
        self,
        data: Dict[str, Any],
        title: str = "Relatório FinOps",
        include_styles: bool = True
    ) -> StructuredReport:
        """
        Gera relatório em HTML
        
        Args:
            data: Dados do relatório
            title: Título do relatório
            include_styles: Incluir CSS inline
            
        Returns:
            StructuredReport em HTML
        """
        now = datetime.utcnow()
        period = data.get('period', {})
        
        css = """
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; color: #333; }
            h1 { color: #232f3e; border-bottom: 3px solid #ff9900; padding-bottom: 10px; }
            h2 { color: #232f3e; margin-top: 30px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th { background: #232f3e; color: white; padding: 12px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #ddd; }
            tr:hover { background: #f5f5f5; }
            .summary-box { background: #f7f7f7; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .metric { display: inline-block; margin: 10px 20px; text-align: center; }
            .metric-value { font-size: 24px; font-weight: bold; color: #232f3e; }
            .metric-label { font-size: 12px; color: #666; }
            .priority-high { color: #d13212; font-weight: bold; }
            .priority-medium { color: #ff9900; }
            .priority-low { color: #1d8102; }
            .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }
        </style>
        """ if include_styles else ""
        
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='pt-BR'>",
            "<head>",
            f"<meta charset='UTF-8'>",
            f"<title>{title}</title>",
            css,
            "</head>",
            "<body>",
            f"<h1>{title}</h1>",
            f"<p><strong>Período:</strong> {period.get('description', 'N/A')} | ",
            f"<strong>Gerado em:</strong> {now.strftime('%d/%m/%Y %H:%M UTC')}</p>",
        ]
        
        if data.get('executive_summary'):
            html_parts.append("<div class='summary-box'>")
            html_parts.append("<h2>Resumo Executivo</h2>")
            summary_html = data['executive_summary'].replace('\n', '<br>')
            html_parts.append(f"<p>{summary_html}</p>")
            html_parts.append("</div>")
        
        if data.get('recommendations'):
            html_parts.append("<h2>Top Oportunidades de Economia</h2>")
            html_parts.append("<table>")
            html_parts.append("<tr><th>#</th><th>Oportunidade</th><th>Economia/Mês</th><th>Prioridade</th></tr>")
            
            for i, rec in enumerate(data['recommendations'][:10], 1):
                desc = rec.get('description', '')[:80]
                savings = f"${rec.get('estimated_savings', 0):,.2f}"
                priority = rec.get('priority', 'MEDIUM')
                priority_class = f"priority-{priority.lower()}"
                html_parts.append(f"<tr><td>{i}</td><td>{desc}</td><td>{savings}</td><td class='{priority_class}'>{priority}</td></tr>")
            
            html_parts.append("</table>")
        
        if data.get('service_analysis'):
            html_parts.append("<h2>Análise por Serviço</h2>")
            html_parts.append("<table>")
            html_parts.append("<tr><th>Serviço</th><th>Custo</th><th>% Total</th><th>Tendência</th></tr>")
            
            for svc in data['service_analysis'][:10]:
                name = svc.get('name', 'Unknown')
                cost = f"${svc.get('cost', 0):,.2f}"
                pct = svc.get('percentage', 'N/A')
                trend = svc.get('trend', 'STABLE')
                html_parts.append(f"<tr><td>{name}</td><td>{cost}</td><td>{pct}%</td><td>{trend}</td></tr>")
            
            html_parts.append("</table>")
        
        if data.get('risks'):
            html_parts.append("<h2>Riscos e Alertas</h2>")
            html_parts.append("<table>")
            html_parts.append("<tr><th>Risco</th><th>Severidade</th><th>Ação Sugerida</th></tr>")
            
            for risk in data['risks']:
                desc = risk.get('description', '')
                severity = risk.get('severity', 'MEDIUM')
                severity_class = f"priority-{severity.lower()}"
                mitigation = risk.get('mitigation', '-')
                html_parts.append(f"<tr><td>{desc}</td><td class='{severity_class}'>{severity}</td><td>{mitigation}</td></tr>")
            
            html_parts.append("</table>")
        
        html_parts.append("<div class='footer'>")
        html_parts.append(f"<p>Relatório gerado automaticamente por {self.company_name} AI Consultant</p>")
        html_parts.append("</div>")
        html_parts.append("</body></html>")
        
        content = '\n'.join(html_parts)
        
        return StructuredReport(
            title=title,
            generated_at=now.isoformat(),
            period=period.get('description', ''),
            format='html',
            content=content,
            metadata={
                "company": self.company_name,
                "language": self.language
            }
        )
    
    def to_json(
        self,
        data: Dict[str, Any],
        title: str = "Relatório FinOps"
    ) -> StructuredReport:
        """
        Gera relatório em JSON estruturado
        
        Args:
            data: Dados do relatório
            title: Título do relatório
            
        Returns:
            StructuredReport em JSON
        """
        now = datetime.utcnow()
        
        report_data = {
            "title": title,
            "generated_at": now.isoformat(),
            "generated_by": self.company_name,
            "period": data.get('period', {}),
            "executive_summary": data.get('executive_summary', ''),
            "recommendations": data.get('recommendations', []),
            "quick_wins": data.get('quick_wins', []),
            "service_analysis": data.get('service_analysis', []),
            "risks": data.get('risks', []),
            "action_plan": data.get('action_plan', {}),
            "metadata": {
                "language": self.language,
                "version": "2.0",
                "source": "amazon-q-business"
            }
        }
        
        content = json.dumps(report_data, indent=2, ensure_ascii=False, default=str)
        
        return StructuredReport(
            title=title,
            generated_at=now.isoformat(),
            period=data.get('period', {}).get('description', ''),
            format='json',
            content=content,
            metadata=report_data['metadata']
        )
    
    def to_slack_blocks(
        self,
        data: Dict[str, Any],
        title: str = "Relatório FinOps"
    ) -> List[Dict[str, Any]]:
        """
        Gera blocos Slack para mensagem rica
        
        Args:
            data: Dados do relatório
            title: Título do relatório
            
        Returns:
            Lista de blocos Slack
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":chart_with_upwards_trend: {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Período:* {data.get('period', {}).get('description', 'N/A')}"
                }
            },
            {"type": "divider"}
        ]
        
        if data.get('executive_summary'):
            summary = data['executive_summary'][:500]
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Resumo Executivo*\n{summary}"
                }
            })
        
        if data.get('recommendations'):
            rec_text = "*Top 3 Oportunidades de Economia:*\n"
            for i, rec in enumerate(data['recommendations'][:3], 1):
                savings = f"${rec.get('estimated_savings', 0):,.2f}"
                rec_text += f"{i}. {rec.get('description', '')[:50]} - *{savings}/mês*\n"
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": rec_text}
            })
        
        if data.get('risks'):
            risk_text = "*:warning: Alertas:*\n"
            for risk in data['risks'][:3]:
                risk_text += f"• {risk.get('description', '')[:50]}\n"
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": risk_text}
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Gerado por {self.company_name} AI Consultant"
                }
            ]
        })
        
        return blocks
