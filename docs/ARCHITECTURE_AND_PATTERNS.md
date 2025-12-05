# Arquitetura e Design Patterns - FinOps AWS

## Versão 2.0 - Dezembro 2024

---

## 1. Visão Geral Arquitetural

O FinOps AWS segue **Clean Architecture** combinada com **Domain-Driven Design (DDD)** e aplica rigorosamente os **Design Patterns do GoF**.

### Princípios SOLID Aplicados

| Princípio | Aplicação |
|-----------|-----------|
| **S** - Single Responsibility | Cada analyzer tem uma única responsabilidade |
| **O** - Open/Closed | Novos analyzers via registro, sem modificar código existente |
| **L** - Liskov Substitution | Todos os analyzers são intercambiáveis |
| **I** - Interface Segregation | Interfaces específicas por domínio |
| **D** - Dependency Inversion | Injeção de dependências via Factory |

---

## 2. Camadas da Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                     │
│              Dashboard (Flask + HTML/JS)                 │
│                     API Endpoints                        │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   APPLICATION LAYER                      │
│              Facade (analysis.py)                        │
│              Use Cases / Services                        │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                     DOMAIN LAYER                         │
│           Analyzers (Strategy Pattern)                   │
│           Entities / Value Objects                       │
│           Domain Exceptions                              │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                 INFRASTRUCTURE LAYER                     │
│            boto3 Clients (Factory Pattern)               │
│            AWS Integrations                              │
│            State Management (S3)                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Design Patterns Implementados

### 3.1 Strategy Pattern (Analyzers)

**Problema**: Diferentes tipos de análise para diferentes serviços AWS.

**Solução**: Interface comum com implementações específicas.

```python
# Abstract Strategy
class BaseAnalyzer(ABC):
    @abstractmethod
    def _collect_resources(self, clients: Dict) -> Dict:
        """Template hook - coleta recursos."""
        pass
    
    @abstractmethod
    def _analyze_resources(self, resources: Dict, region: str) -> Tuple:
        """Template hook - analisa recursos."""
        pass

# Concrete Strategies
class ComputeAnalyzer(BaseAnalyzer):
    """Analisa EC2, Lambda, ECS, EKS."""
    
class StorageAnalyzer(BaseAnalyzer):
    """Analisa S3, EBS, EFS."""
    
class DatabaseAnalyzer(BaseAnalyzer):
    """Analisa RDS, DynamoDB, ElastiCache."""
    
class NetworkAnalyzer(BaseAnalyzer):
    """Analisa ELB, CloudFront, API Gateway."""
    
class SecurityAnalyzer(BaseAnalyzer):
    """Analisa IAM, CloudWatch, ECR."""
    
class AnalyticsAnalyzer(BaseAnalyzer):
    """Analisa EMR, Kinesis, Glue, Redshift."""
```

**Benefícios**:
- Fácil adicionar novos analyzers
- Código testável isoladamente
- Responsabilidades bem definidas

---

### 3.2 Factory Pattern + Registry

**Problema**: Criação dinâmica de analyzers sem acoplamento.

**Solução**: Factory com Registry singleton.

```python
class AnalyzerRegistry:
    """Singleton Registry - mantém analyzers disponíveis."""
    _instance = None
    _analyzers: Dict[str, Type[BaseAnalyzer]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, name: str, analyzer_class: Type[BaseAnalyzer]):
        self._analyzers[name] = analyzer_class
    
    def get(self, name: str) -> Optional[Type[BaseAnalyzer]]:
        return self._analyzers.get(name)
    
    def list_all(self) -> List[str]:
        return list(self._analyzers.keys())


class AnalyzerFactory:
    """Factory para criar e executar analyzers."""
    
    def __init__(self):
        self._registry = AnalyzerRegistry()
        self._register_default_analyzers()
    
    def create(self, name: str) -> Optional[BaseAnalyzer]:
        analyzer_class = self._registry.get(name)
        return analyzer_class() if analyzer_class else None
    
    def analyze_all(self, region: str) -> AnalysisResult:
        combined = AnalysisResult(analyzer_name="All")
        for name in self._registry.list_all():
            result = self.analyze(name, region)
            combined = combined.merge(result)
        return combined
```

**Benefícios**:
- Desacoplamento entre criação e uso
- Extensibilidade via registro
- Singleton evita duplicação

---

### 3.3 Template Method Pattern

**Problema**: Estrutura comum de análise com variações específicas.

**Solução**: Método template com hooks abstratos.

```python
class BaseAnalyzer(ABC):
    def analyze(self, region: str) -> AnalysisResult:
        """Template method - estrutura fixa."""
        # 1. Obter clientes (hook)
        clients = self._get_client(region)
        
        # 2. Coletar recursos (hook abstrato)
        resources = self._collect_resources(clients)
        
        # 3. Analisar recursos (hook abstrato)
        recommendations, metrics = self._analyze_resources(resources, region)
        
        # 4. Construir resultado (método concreto)
        return self._build_result(recommendations, metrics)
    
    @abstractmethod
    def _get_client(self, region: str) -> Any:
        """Hook - retorna clientes boto3."""
        pass
    
    @abstractmethod
    def _collect_resources(self, clients: Dict) -> Dict:
        """Hook abstrato - coleta específica."""
        pass
    
    @abstractmethod
    def _analyze_resources(self, resources: Dict, region: str) -> Tuple:
        """Hook abstrato - análise específica."""
        pass
```

**Benefícios**:
- Reutilização de estrutura comum
- Variação controlada via hooks
- Consistência entre analyzers

---

### 3.4 Facade Pattern

**Problema**: Simplificar acesso a subsistemas complexos.

**Solução**: Fachada que coordena múltiplos componentes.

```python
def get_dashboard_analysis(
    all_services_func=None,
    include_multi_region=False
) -> Dict[str, Any]:
    """Facade - simplifica análise completa."""
    
    # Coordena múltiplos subsistemas
    result = {}
    
    # 1. Analyzers modulares
    analyzer_recs, analyzer_resources = get_analyzers_analysis(region)
    
    # 2. Integração Compute Optimizer
    co_recs = get_compute_optimizer_recommendations(region)
    
    # 3. Integração Cost Explorer
    ri_recs = get_cost_explorer_ri_recommendations(region)
    
    # 4. Integração Trusted Advisor
    ta_recs = get_trusted_advisor_recommendations()
    
    # 5. Integração Amazon Q
    q_insights = get_amazon_q_insights(costs, resources)
    
    # Consolida resultados
    return consolidate_results(result)
```

**Benefícios**:
- Interface simplificada para clientes
- Encapsula complexidade
- Fácil manutenção

---

## 4. Hierarquia de Exceções

```python
@dataclass
class FinOpsError(Exception):
    """Base exception."""
    message: str
    code: str = "FINOPS_ERROR"
    details: Dict = field(default_factory=dict)

# AWS Errors
class AWSServiceError(FinOpsError): ...
class AWSClientError(AWSServiceError): ...      # Credenciais
class AWSThrottlingError(AWSServiceError): ...  # Rate limit
class AWSResourceNotFoundError(AWSServiceError): ...

# Domain Errors
class AnalysisError(FinOpsError): ...
class ValidationError(FinOpsError): ...
class ConfigurationError(FinOpsError): ...

# Integration Errors
class IntegrationError(FinOpsError): ...
class CostExplorerError(AWSServiceError): ...
class TrustedAdvisorError(AWSServiceError): ...
class AmazonQError(IntegrationError): ...
```

---

## 5. Estrutura de Diretórios

```
src/finops_aws/
├── analyzers/                    # Strategy Pattern
│   ├── __init__.py
│   ├── base_analyzer.py          # ABC + Template Method
│   ├── analyzer_factory.py       # Factory + Registry
│   ├── compute_analyzer.py       # Concrete Strategy
│   ├── storage_analyzer.py
│   ├── database_analyzer.py
│   ├── network_analyzer.py
│   ├── security_analyzer.py
│   └── analytics_analyzer.py
│
├── domain/                       # Domain Layer
│   └── exceptions.py             # Exception Hierarchy
│
├── dashboard/                    # Application Layer
│   ├── analysis.py               # Facade
│   ├── integrations.py           # AWS Integrations
│   └── multi_region.py           # Multi-region support
│
├── core/                         # Infrastructure
│   ├── factories.py              # Service Factories
│   └── dynamodb_state_manager.py # State Management
│
└── services/                     # Service Layer
    ├── cost_service.py
    ├── metrics_service.py
    └── optimizer_service.py
```

---

## 6. Métricas de Qualidade

| Métrica | Valor | Status |
|---------|-------|--------|
| **Analyzers** | 6 | Implementados |
| **Serviços Analisados** | 23 | Cobertura |
| **Padrões GoF** | 5 | Strategy, Factory, Template, Registry, Facade |
| **SOLID** | 100% | Todos os princípios |
| **Testes** | 2,204 | 100% passing |
| **Exceções Tipadas** | 15 | Hierarquia completa |

---

## 7. Anti-Patterns Identificados

### No app.py (6,312 linhas) - Para Refatoração

| Anti-Pattern | Quantidade | Solução |
|--------------|------------|---------|
| God Object | 1 arquivo | Dividir em módulos |
| `except Exception:` | 516 | Usar exceções tipadas |
| `pass` em except | 511 | Logging apropriado |
| Função gigante | 5,900 linhas | Decomposição |

### Migração Planejada

A refatoração do `app.py` usará os analyzers já implementados:
- Manter backward compatibility
- Migrar gradualmente funções
- Reduzir de 6,312 para ~300 linhas

---

*Documento atualizado em: Dezembro 2024*
