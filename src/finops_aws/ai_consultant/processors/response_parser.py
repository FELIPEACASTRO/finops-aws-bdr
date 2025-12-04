"""
Response Parser

Parseia respostas do Amazon Q Business e extrai
seções estruturadas do relatório.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ParsedReport:
    """Relatório parseado do Q Business"""
    raw_text: str
    executive_summary: str
    recommendations: List[Dict[str, Any]]
    quick_wins: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    service_analysis: List[Dict[str, Any]]
    action_plan: Dict[str, Any]
    tables: List[Dict[str, Any]]
    sections: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "recommendations": self.recommendations,
            "quick_wins": self.quick_wins,
            "risks": self.risks,
            "service_analysis": self.service_analysis,
            "action_plan": self.action_plan,
            "tables": self.tables,
            "sections": self.sections
        }


class ResponseParser:
    """
    Parser de respostas do Amazon Q Business
    
    Extrai e estrutura informações das respostas em Markdown
    geradas pelo Q Business.
    
    Example:
        ```python
        parser = ResponseParser()
        
        parsed = parser.parse(response_text)
        print(parsed.executive_summary)
        print(parsed.recommendations)
        ```
    """
    
    SECTION_PATTERNS = {
        "executive_summary": [
            r"(?i)#+\s*resumo\s+executivo",
            r"(?i)#+\s*executive\s+summary",
            r"(?i)#+\s*visão\s+geral",
            r"(?i)#+\s*overview"
        ],
        "recommendations": [
            r"(?i)#+\s*recomendações",
            r"(?i)#+\s*recommendations",
            r"(?i)#+\s*oportunidades\s+de\s+economia",
            r"(?i)#+\s*opportunities"
        ],
        "quick_wins": [
            r"(?i)#+\s*quick\s+wins",
            r"(?i)#+\s*ações\s+imediatas",
            r"(?i)#+\s*próximos\s+7\s+dias"
        ],
        "risks": [
            r"(?i)#+\s*riscos",
            r"(?i)#+\s*risks",
            r"(?i)#+\s*alertas",
            r"(?i)#+\s*alerts"
        ],
        "service_analysis": [
            r"(?i)#+\s*análise\s+por\s+serviço",
            r"(?i)#+\s*service\s+analysis",
            r"(?i)#+\s*análise\s+detalhada"
        ],
        "action_plan": [
            r"(?i)#+\s*plano\s+30-60-90",
            r"(?i)#+\s*action\s+plan",
            r"(?i)#+\s*roadmap"
        ]
    }
    
    def parse(self, response_text: str) -> ParsedReport:
        """
        Parseia resposta completa do Q Business
        
        Args:
            response_text: Texto da resposta em Markdown
            
        Returns:
            ParsedReport com seções estruturadas
        """
        sections = self._extract_sections(response_text)
        tables = self._extract_tables(response_text)
        
        exec_summary = self._extract_executive_summary(sections, response_text)
        recommendations = self._extract_recommendations(sections, tables)
        quick_wins = self._extract_quick_wins(sections)
        risks = self._extract_risks(sections, tables)
        service_analysis = self._extract_service_analysis(sections, tables)
        action_plan = self._extract_action_plan(sections)
        
        return ParsedReport(
            raw_text=response_text,
            executive_summary=exec_summary,
            recommendations=recommendations,
            quick_wins=quick_wins,
            risks=risks,
            service_analysis=service_analysis,
            action_plan=action_plan,
            tables=tables,
            sections=sections
        )
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extrai seções do texto Markdown"""
        sections = {}
        
        header_pattern = r'^(#{1,3})\s+(.+)$'
        lines = text.split('\n')
        
        current_section = None
        current_content = []
        section_level = 0
        
        for line in lines:
            match = re.match(header_pattern, line)
            if match:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                level = len(match.group(1))
                header = match.group(2).strip()
                
                section_key = self._normalize_section_key(header)
                current_section = section_key
                current_content = []
                section_level = level
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _normalize_section_key(self, header: str) -> str:
        """Normaliza nome de seção para chave"""
        header = re.sub(r'[^\w\s]', '', header.lower())
        header = re.sub(r'\s+', '_', header.strip())
        return header[:50]
    
    def _extract_tables(self, text: str) -> List[Dict[str, Any]]:
        """Extrai tabelas Markdown do texto"""
        tables = []
        
        table_pattern = r'\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n?)+'
        matches = re.finditer(table_pattern, text)
        
        for match in matches:
            table_text = match.group()
            parsed_table = self._parse_markdown_table(table_text)
            if parsed_table:
                tables.append(parsed_table)
        
        return tables
    
    def _parse_markdown_table(self, table_text: str) -> Optional[Dict[str, Any]]:
        """Parseia tabela Markdown"""
        lines = [l.strip() for l in table_text.strip().split('\n') if l.strip()]
        
        if len(lines) < 2:
            return None
        
        header_line = lines[0]
        headers = [h.strip() for h in header_line.strip('|').split('|')]
        
        rows = []
        for line in lines[2:]:
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) == len(headers):
                row = {headers[i]: cells[i] for i in range(len(headers))}
                rows.append(row)
        
        return {
            "headers": headers,
            "rows": rows,
            "row_count": len(rows)
        }
    
    def _extract_executive_summary(
        self,
        sections: Dict[str, str],
        full_text: str
    ) -> str:
        """Extrai resumo executivo"""
        for pattern_key in ['executive_summary', 'resumo_executivo', 'visao_geral']:
            for key in sections:
                if pattern_key in key.lower() or key.lower() in pattern_key:
                    return sections[key]
        
        lines = full_text.split('\n')
        summary_lines = []
        
        in_content = False
        for line in lines:
            if line.strip() and not line.startswith('#'):
                in_content = True
                summary_lines.append(line)
            elif in_content and line.startswith('#'):
                break
        
        return '\n'.join(summary_lines[:10]).strip()
    
    def _extract_recommendations(
        self,
        sections: Dict[str, str],
        tables: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extrai recomendações estruturadas"""
        recommendations = []
        
        for table in tables:
            headers_lower = [h.lower() for h in table.get('headers', [])]
            if any(k in ' '.join(headers_lower) for k in ['economia', 'savings', 'oportunidade', 'opportunity']):
                for row in table.get('rows', []):
                    rec = self._row_to_recommendation(row, table['headers'])
                    if rec:
                        recommendations.append(rec)
        
        for key, content in sections.items():
            if any(k in key.lower() for k in ['recomendac', 'recommend', 'oportunidade', 'opportunit']):
                items = self._extract_list_items(content)
                for item in items:
                    recommendations.append({
                        "description": item,
                        "estimated_savings": self._extract_money_value(item),
                        "priority": self._infer_priority(item),
                        "source": "text"
                    })
        
        return recommendations[:20]
    
    def _row_to_recommendation(
        self,
        row: Dict[str, str],
        headers: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Converte linha de tabela em recomendação"""
        rec = {}
        
        for header, value in row.items():
            header_lower = header.lower()
            
            if any(k in header_lower for k in ['descrição', 'description', 'oportunidade', 'opportunity', 'ação', 'action']):
                rec['description'] = value
            elif any(k in header_lower for k in ['economia', 'savings', 'valor']):
                rec['estimated_savings'] = self._extract_money_value(value)
            elif any(k in header_lower for k in ['prioridade', 'priority']):
                rec['priority'] = value.upper() if value else 'MEDIUM'
            elif any(k in header_lower for k in ['esforço', 'effort']):
                rec['effort'] = value.upper() if value else 'MEDIUM'
            elif any(k in header_lower for k in ['prazo', 'timeline', 'days']):
                rec['timeline'] = value
        
        return rec if rec.get('description') else None
    
    def _extract_quick_wins(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extrai quick wins"""
        quick_wins = []
        
        for key, content in sections.items():
            if any(k in key.lower() for k in ['quick_win', 'imediata', 'immediate', '7_dias', '7_days']):
                items = self._extract_list_items(content)
                for item in items:
                    quick_wins.append({
                        "description": item,
                        "estimated_savings": self._extract_money_value(item),
                        "timeline": "7 days"
                    })
        
        return quick_wins[:10]
    
    def _extract_risks(
        self,
        sections: Dict[str, str],
        tables: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extrai riscos e alertas"""
        risks = []
        
        for table in tables:
            headers_lower = [h.lower() for h in table.get('headers', [])]
            if any(k in ' '.join(headers_lower) for k in ['risco', 'risk', 'alerta', 'alert', 'probabilidade']):
                for row in table.get('rows', []):
                    risk = {}
                    for header, value in row.items():
                        header_lower = header.lower()
                        if any(k in header_lower for k in ['risco', 'risk', 'descrição']):
                            risk['description'] = value
                        elif any(k in header_lower for k in ['probabilidade', 'probability']):
                            risk['probability'] = value
                        elif any(k in header_lower for k in ['impacto', 'impact']):
                            risk['impact'] = value
                        elif any(k in header_lower for k in ['ação', 'action', 'mitigação']):
                            risk['mitigation'] = value
                    if risk.get('description'):
                        risks.append(risk)
        
        for key, content in sections.items():
            if any(k in key.lower() for k in ['risco', 'risk', 'alerta', 'alert']):
                items = self._extract_list_items(content)
                for item in items:
                    if not any(r.get('description') == item for r in risks):
                        risks.append({
                            "description": item,
                            "severity": self._infer_severity(item)
                        })
        
        return risks[:10]
    
    def _extract_service_analysis(
        self,
        sections: Dict[str, str],
        tables: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extrai análise por serviço"""
        services = []
        
        for table in tables:
            headers_lower = [h.lower() for h in table.get('headers', [])]
            if any(k in ' '.join(headers_lower) for k in ['serviço', 'service', 'custo', 'cost']):
                for row in table.get('rows', []):
                    svc = {}
                    for header, value in row.items():
                        header_lower = header.lower()
                        if any(k in header_lower for k in ['serviço', 'service', 'nome']):
                            svc['name'] = value
                        elif any(k in header_lower for k in ['custo', 'cost', 'valor']):
                            svc['cost'] = self._extract_money_value(value)
                        elif any(k in header_lower for k in ['%', 'percent', 'total']):
                            svc['percentage'] = value
                        elif any(k in header_lower for k in ['trend', 'tendência']):
                            svc['trend'] = value
                    if svc.get('name'):
                        services.append(svc)
        
        return services[:20]
    
    def _extract_action_plan(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Extrai plano de ação 30-60-90"""
        plan = {
            "phase_1": [],
            "phase_2": [],
            "phase_3": []
        }
        
        for key, content in sections.items():
            if any(k in key.lower() for k in ['30-60-90', 'plano', 'roadmap', 'action_plan']):
                current_phase = "phase_1"
                
                for line in content.split('\n'):
                    line_lower = line.lower()
                    if any(k in line_lower for k in ['fase 1', 'phase 1', '0-30', 'dias 1-30']):
                        current_phase = "phase_1"
                    elif any(k in line_lower for k in ['fase 2', 'phase 2', '31-60', 'dias 31-60']):
                        current_phase = "phase_2"
                    elif any(k in line_lower for k in ['fase 3', 'phase 3', '61-90', 'dias 61']):
                        current_phase = "phase_3"
                    elif line.strip().startswith(('-', '*', '•')):
                        plan[current_phase].append(line.strip().lstrip('-*• '))
        
        return plan
    
    def _extract_list_items(self, content: str) -> List[str]:
        """Extrai itens de lista do texto"""
        items = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('-', '*', '•')):
                items.append(line.lstrip('-*• ').strip())
            elif re.match(r'^\d+[\.\)]\s', line):
                items.append(re.sub(r'^\d+[\.\)]\s*', '', line).strip())
        
        return items
    
    def _extract_money_value(self, text: str) -> float:
        """Extrai valor monetário do texto"""
        patterns = [
            r'\$\s*([\d,]+(?:\.\d{2})?)',
            r'([\d,]+(?:\.\d{2})?)\s*(?:USD|usd)',
            r'R\$\s*([\d,]+(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(text))
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    return float(value_str)
                except ValueError:
                    continue
        
        return 0.0
    
    def _infer_priority(self, text: str) -> str:
        """Infere prioridade do texto"""
        text_lower = text.lower()
        
        if any(k in text_lower for k in ['urgent', 'crítico', 'critical', 'imediato', 'immediate', 'alta', 'high']):
            return 'HIGH'
        elif any(k in text_lower for k in ['baixa', 'low', 'opcional', 'optional']):
            return 'LOW'
        return 'MEDIUM'
    
    def _infer_severity(self, text: str) -> str:
        """Infere severidade de risco"""
        text_lower = text.lower()
        
        if any(k in text_lower for k in ['crítico', 'critical', 'grave', 'severe', 'alto', 'high']):
            return 'HIGH'
        elif any(k in text_lower for k in ['baixo', 'low', 'menor', 'minor']):
            return 'LOW'
        return 'MEDIUM'
