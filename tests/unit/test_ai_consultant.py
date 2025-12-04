"""
Tests for AI Consultant Module

Testes unitários para o módulo de integração com Amazon Q Business.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.finops_aws.ai_consultant.q_business.config import (
    QBusinessConfig,
    QBusinessRegion,
    QBusinessIndexType
)
from src.finops_aws.ai_consultant.q_business.client import (
    QBusinessClient,
    ChatResponse
)
from src.finops_aws.ai_consultant.q_business.chat import (
    QBusinessChat,
    FinOpsAnalysisRequest,
    FinOpsAnalysisResponse
)
from src.finops_aws.ai_consultant.prompts import (
    PromptBuilder,
    PromptPersona
)
from src.finops_aws.ai_consultant.prompts.personas import (
    PersonaConfig,
    get_persona_config,
    PERSONA_CONFIGS
)
from src.finops_aws.ai_consultant.processors import (
    DataFormatter,
    ResponseParser,
    ReportStructurer
)


class TestQBusinessConfig:
    """Testes para QBusinessConfig"""
    
    def test_config_from_env(self):
        """Testa criação de config a partir de env"""
        with patch.dict('os.environ', {
            'Q_BUSINESS_APP_ID': 'test-app-123',
            'Q_BUSINESS_INDEX_ID': 'test-index-456',
            'Q_BUSINESS_REGION': 'us-east-1',
            'FINOPS_REPORTS_BUCKET': 'test-bucket'
        }):
            config = QBusinessConfig.from_env()
            
            assert config.application_id == 'test-app-123'
            assert config.index_id == 'test-index-456'
            assert config.region == 'us-east-1'
            assert config.s3_bucket == 'test-bucket'
    
    def test_config_validation_missing_identity_center(self):
        """Testa validação sem Identity Center"""
        config = QBusinessConfig(
            application_id='test-app',
            identity_center_instance_arn=None
        )
        
        result = config.validate()
        
        assert result['valid'] is False
        assert any('IDENTITY_CENTER' in e for e in result['errors'])
    
    def test_config_validation_success(self):
        """Testa validação com sucesso"""
        config = QBusinessConfig(
            application_id='test-app',
            index_id='test-index',
            identity_center_instance_arn='arn:aws:sso:::instance/test',
            s3_bucket='test-bucket'
        )
        
        result = config.validate()
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_config_to_dict(self):
        """Testa conversão para dicionário"""
        config = QBusinessConfig(
            application_id='app-123',
            region='us-west-2'
        )
        
        result = config.to_dict()
        
        assert result['application_id'] == 'app-123'
        assert result['region'] == 'us-west-2'
        assert 'index_type' in result


class TestQBusinessClient:
    """Testes para QBusinessClient"""
    
    @pytest.fixture
    def mock_boto_client(self):
        """Mock do cliente boto3"""
        return MagicMock()
    
    @pytest.fixture
    def client(self, mock_boto_client):
        """Cliente Q Business com mock"""
        config = QBusinessConfig(
            application_id='test-app',
            index_id='test-index',
            retriever_id='test-retriever',
            region='us-east-1'
        )
        return QBusinessClient(config, boto_client=mock_boto_client)
    
    def test_chat_success(self, client, mock_boto_client):
        """Testa chat com sucesso"""
        mock_boto_client.chat_sync.return_value = {
            'systemMessage': 'Análise de custos concluída',
            'conversationId': 'conv-123',
            'systemMessageId': 'msg-456',
            'sourceAttributions': []
        }
        
        response = client.chat("Analise os custos de EC2")
        
        assert response.message == 'Análise de custos concluída'
        assert response.conversation_id == 'conv-123'
        mock_boto_client.chat_sync.assert_called_once()
    
    def test_chat_with_context(self, client, mock_boto_client):
        """Testa chat com contexto"""
        mock_boto_client.chat_sync.return_value = {
            'systemMessage': 'Resposta contextualizada',
            'conversationId': 'conv-789',
            'systemMessageId': 'msg-101',
            'sourceAttributions': []
        }
        
        context = {'total_cost': 47523.89, 'services': ['EC2', 'RDS']}
        response = client.chat_with_context(
            message="Por que os custos aumentaram?",
            context_data=context,
            persona="executive"
        )
        
        assert 'contextualizada' in response.message.lower() or response.message
        mock_boto_client.chat_sync.assert_called_once()
    
    def test_health_check(self, client, mock_boto_client):
        """Testa health check"""
        mock_boto_client.get_application.return_value = {
            'applicationId': 'test-app',
            'displayName': 'Test App',
            'status': 'ACTIVE'
        }
        
        client._s3_client = MagicMock()
        client._s3_client.head_bucket.return_value = {}
        
        result = client.health_check()
        
        assert 'components' in result
        assert 'application' in result['components']


class TestPromptBuilder:
    """Testes para PromptBuilder"""
    
    @pytest.fixture
    def builder(self):
        """PromptBuilder para testes"""
        return PromptBuilder()
    
    def test_build_analysis_prompt(self, builder):
        """Testa construção de prompt de análise"""
        cost_data = {
            'total_cost': 47523.89,
            'services': [
                {'name': 'EC2', 'cost': 18750.00},
                {'name': 'RDS', 'cost': 8200.00}
            ]
        }
        
        prompt = builder.build_analysis_prompt(
            cost_data=cost_data,
            period="2024-11-01 a 2024-11-30",
            persona=PromptPersona.EXECUTIVE
        )
        
        assert 'Resumo Executivo' in prompt or 'executive' in prompt.lower()
        assert '47523.89' in prompt or 'total_cost' in prompt
        assert 'EC2' in prompt
    
    def test_build_question_prompt(self, builder):
        """Testa construção de prompt de pergunta"""
        context = {'service': 'EC2', 'cost': 18750.00}
        
        prompt = builder.build_question_prompt(
            question="Por que o EC2 está caro?",
            context=context
        )
        
        assert 'EC2' in prompt
        assert '18750' in prompt
    
    def test_build_cost_explanation_prompt(self, builder):
        """Testa prompt de explicação de custo"""
        context = {
            'service': 'RDS',
            'current_cost': 8200.00,
            'previous_cost': 6500.00,
            'change_percentage': 26.15
        }
        
        prompt = builder.build_cost_explanation_prompt(context)
        
        assert 'RDS' in prompt
        assert '8200' in prompt or '8,200' in prompt
        assert 'aumentou' in prompt.lower() or 'variação' in prompt.lower()


class TestPromptPersonas:
    """Testes para Personas de Prompt"""
    
    def test_get_executive_persona(self):
        """Testa obtenção de persona executiva"""
        config = get_persona_config(PromptPersona.EXECUTIVE)
        
        assert config.name == "CEO/CFO - Executivo"
        assert config.include_technical_details is False
        assert config.include_commands is False
    
    def test_get_devops_persona(self):
        """Testa obtenção de persona DevOps"""
        config = get_persona_config(PromptPersona.DEVOPS)
        
        assert 'DevOps' in config.name or 'SRE' in config.name
        assert config.include_technical_details is True
        assert config.include_commands is True
    
    def test_persona_to_prompt_context(self):
        """Testa conversão de persona para contexto"""
        config = get_persona_config(PromptPersona.CTO)
        
        context = config.to_prompt_context()
        
        assert 'CTO' in context
        assert 'Tom de comunicação' in context


class TestDataFormatter:
    """Testes para DataFormatter"""
    
    @pytest.fixture
    def formatter(self):
        """DataFormatter para testes"""
        return DataFormatter()
    
    def test_format_cost_report(self, formatter):
        """Testa formatação de relatório de custo"""
        report = {
            'total_cost': 47523.89,
            'services': [
                {'name': 'EC2', 'cost': 18750.00, 'percentage': 39.5},
                {'name': 'RDS', 'cost': 8200.00, 'percentage': 17.3}
            ],
            'recommendations': [
                {'description': 'Rightsizing EC2', 'estimated_savings': 3200}
            ]
        }
        
        result = formatter.format_cost_report(report)
        
        assert result.summary['total_cost'] == 47523.89
        assert len(result.services) == 2
        assert result.services[0]['name'] == 'EC2'
        assert len(result.recommendations) == 1
    
    def test_format_for_comparison(self, formatter):
        """Testa formatação para comparação"""
        current = {'total_cost': 50000, 'services': [{'name': 'EC2', 'cost': 20000}]}
        previous = {'total_cost': 45000, 'services': [{'name': 'EC2', 'cost': 18000}]}
        
        result = formatter.format_for_comparison(current, previous)
        
        assert 'current_period' in result
        assert 'previous_period' in result
        assert 'total_delta' in result


class TestResponseParser:
    """Testes para ResponseParser"""
    
    @pytest.fixture
    def parser(self):
        """ResponseParser para testes"""
        return ResponseParser()
    
    def test_parse_markdown_response(self, parser):
        """Testa parsing de resposta Markdown"""
        response = """
# Relatório FinOps

## Resumo Executivo

O custo total do período foi $47,523.89, representando um aumento de 12.3%.

## Recomendações

| Oportunidade | Economia/Mês |
|--------------|--------------|
| Rightsizing EC2 | $3,200 |

## Quick Wins

- Desligar instâncias dev à noite
- Aplicar S3 lifecycle policy

## Riscos

| Risco | Impacto |
|-------|---------|
| RI expirando | Alto |
"""
        
        result = parser.parse(response)
        
        assert result.executive_summary != ""
        assert 'raw_text' in result.__dict__
    
    def test_extract_money_values(self, parser):
        """Testa extração de valores monetários"""
        assert parser._extract_money_value("$3,200.00") == 3200.0
        assert parser._extract_money_value("economia de $1500") == 1500.0
        assert parser._extract_money_value("sem valor") == 0.0


class TestReportStructurer:
    """Testes para ReportStructurer"""
    
    @pytest.fixture
    def structurer(self):
        """ReportStructurer para testes"""
        return ReportStructurer()
    
    def test_to_markdown(self, structurer):
        """Testa geração de Markdown"""
        data = {
            'executive_summary': 'Custo total: $47,523.89',
            'recommendations': [
                {'description': 'Rightsizing', 'estimated_savings': 3200}
            ],
            'period': {'description': 'Nov 2024'}
        }
        
        result = structurer.to_markdown(data)
        
        assert result.format == 'markdown'
        assert '# Relatório FinOps' in result.content
        assert 'Resumo Executivo' in result.content
    
    def test_to_html(self, structurer):
        """Testa geração de HTML"""
        data = {
            'executive_summary': 'Resumo do período',
            'recommendations': [],
            'period': {'description': 'Nov 2024'}
        }
        
        result = structurer.to_html(data)
        
        assert result.format == 'html'
        assert '<html' in result.content
        assert 'Resumo do período' in result.content
    
    def test_to_json(self, structurer):
        """Testa geração de JSON"""
        data = {
            'executive_summary': 'Resumo',
            'recommendations': [{'description': 'Test'}],
            'period': {'description': 'Nov 2024'}
        }
        
        result = structurer.to_json(data)
        
        assert result.format == 'json'
        parsed = json.loads(result.content)
        assert parsed['executive_summary'] == 'Resumo'
    
    def test_to_slack_blocks(self, structurer):
        """Testa geração de blocos Slack"""
        data = {
            'executive_summary': 'Resumo executivo',
            'recommendations': [
                {'description': 'Ação 1', 'estimated_savings': 1000}
            ],
            'period': {'description': 'Nov 2024'}
        }
        
        blocks = structurer.to_slack_blocks(data)
        
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        assert blocks[0]['type'] == 'header'


class TestQBusinessChat:
    """Testes para QBusinessChat"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock do QBusinessClient"""
        client = MagicMock()
        client.chat.return_value = ChatResponse(
            message="Análise completa do custo",
            source_attributions=[],
            conversation_id="conv-123",
            system_message_id="msg-456",
            action_review=None
        )
        return client
    
    @pytest.fixture
    def chat(self, mock_client):
        """QBusinessChat para testes"""
        config = QBusinessConfig(application_id='test-app')
        return QBusinessChat(config, client=mock_client)
    
    def test_analyze_costs(self, chat, mock_client):
        """Testa análise de custos"""
        request = FinOpsAnalysisRequest(
            cost_data={'total_cost': 47523.89},
            period='Nov 2024',
            persona=PromptPersona.EXECUTIVE
        )
        
        response = chat.analyze_costs(request)
        
        assert isinstance(response, FinOpsAnalysisResponse)
        assert response.report != ""
        assert response.generated_at != ""
        mock_client.chat.assert_called_once()
    
    def test_ask_question(self, chat, mock_client):
        """Testa pergunta específica"""
        response = chat.ask_question(
            question="Por que EC2 está caro?",
            context={'service': 'EC2', 'cost': 18750}
        )
        
        assert response.message != ""
        mock_client.chat.assert_called_once()


class TestIntegration:
    """Testes de integração do módulo"""
    
    def test_full_flow_mock(self):
        """Testa fluxo completo com mocks"""
        mock_q_client = MagicMock()
        mock_q_client.chat.return_value = ChatResponse(
            message="""
## Resumo Executivo

O custo total foi $47,523.89, aumento de 12.3%.

## Recomendações

1. Rightsizing EC2 - economia $3,200/mês

## Quick Wins

- Desligar dev à noite
""",
            source_attributions=[],
            conversation_id="test-conv",
            system_message_id="test-msg",
            action_review=None
        )
        
        config = QBusinessConfig(
            application_id='test-app',
            region='us-east-1'
        )
        
        formatter = DataFormatter()
        chat = QBusinessChat(config, client=mock_q_client)
        parser = ResponseParser()
        structurer = ReportStructurer()
        
        cost_data = {
            'total_cost': 47523.89,
            'services': [{'name': 'EC2', 'cost': 18750}],
            'recommendations': []
        }
        
        formatted = formatter.format_cost_report(cost_data)
        
        request = FinOpsAnalysisRequest(
            cost_data=formatted.to_dict(),
            period='Nov 2024'
        )
        response = chat.analyze_costs(request)
        
        parsed = parser.parse(response.report)
        
        report = structurer.to_markdown(parsed.to_dict())
        
        assert report.format == 'markdown'
        assert len(report.content) > 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
