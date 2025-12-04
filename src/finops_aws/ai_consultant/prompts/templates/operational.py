"""
Operational Report Template

Template de prompt para relatórios operacionais (DevOps/SRE).
Foco em ações práticas, scripts e implementação.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

OPERATIONAL_REPORT_TEMPLATE = """
Produza um relatório operacional de custos AWS com as seguintes características:

### Tom e Estilo
- Altamente técnico e prático
- Foco em implementação e automação
- Inclua comandos AWS CLI e scripts
- Linguagem para engenheiros

### Estrutura do Relatório

#### 1. RESUMO OPERACIONAL

**Status Atual**
- Total de recursos ativos por serviço
- Recursos com alertas de custo
- Recursos sem tags obrigatórias
- Recursos órfãos identificados

**Ações Pendentes**
- [ ] Lista de ações imediatas com checkbox
- [ ] Ordenadas por prioridade

#### 2. RECURSOS PARA AÇÃO IMEDIATA

Para cada recurso que precisa de ação:

```
RECURSO: [ID/Nome do recurso]
SERVIÇO: [EC2, RDS, etc.]
REGIÃO: [us-east-1, etc.]
CUSTO ATUAL: $X/mês
UTILIZAÇÃO: Y%
PROBLEMA: [descrição]
AÇÃO: [o que fazer]
ECONOMIA: $Z/mês

COMANDOS:
```bash
# Comando 1 - Descrição
aws ec2 describe-instances --instance-ids i-xxx

# Comando 2 - Ação
aws ec2 modify-instance-attribute --instance-id i-xxx --instance-type m5.large
```
```

#### 3. EC2 - ANÁLISE DETALHADA

**Instâncias para Rightsizing**

| Instance ID | Tipo Atual | Tipo Sugerido | CPU Avg | Mem Avg | Economia |
|-------------|------------|---------------|---------|---------|----------|

**Comandos para Rightsizing**

```bash
# Listar instâncias com baixa utilização
aws cloudwatch get-metric-statistics \\
  --namespace AWS/EC2 \\
  --metric-name CPUUtilization \\
  --dimensions Name=InstanceId,Value=i-xxx \\
  --start-time $(date -d '7 days ago' --iso-8601) \\
  --end-time $(date --iso-8601) \\
  --period 3600 \\
  --statistics Average

# Modificar tipo de instância
aws ec2 stop-instances --instance-ids i-xxx
aws ec2 modify-instance-attribute --instance-id i-xxx --instance-type '{"Value": "t3.medium"}'
aws ec2 start-instances --instance-ids i-xxx
```

**Instâncias para Instance Scheduler**

Lista de instâncias candidatas a desligamento fora do horário:
- Desenvolvimento: [lista]
- Staging: [lista]
- Ferramentas: [lista]

```bash
# Tag para Instance Scheduler
aws ec2 create-tags \\
  --resources i-xxx \\
  --tags Key=Schedule,Value=office-hours
```

#### 4. RDS - ANÁLISE DETALHADA

**Instâncias para Otimização**

| DB Instance | Engine | Tipo | Storage | Custo | Ação |
|-------------|--------|------|---------|-------|------|

**Multi-AZ em Dev/Staging**

```bash
# Converter para Single-AZ
aws rds modify-db-instance \\
  --db-instance-identifier dev-db \\
  --no-multi-az \\
  --apply-immediately
```

**Storage não otimizado**

```bash
# Verificar storage provisionado vs usado
aws rds describe-db-instances \\
  --query 'DBInstances[*].{ID:DBInstanceIdentifier,Allocated:AllocatedStorage}'
```

#### 5. S3 - ANÁLISE DETALHADA

**Buckets sem Lifecycle Policy**

| Bucket | Tamanho | Custo/Mês | Ação Sugerida |
|--------|---------|-----------|---------------|

**Aplicar Lifecycle Policy**

```bash
# Criar lifecycle policy
cat > lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "ID": "MoveToIA",
      "Status": "Enabled",
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"},
        {"Days": 90, "StorageClass": "GLACIER"}
      ],
      "Expiration": {"Days": 365}
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \\
  --bucket my-bucket \\
  --lifecycle-configuration file://lifecycle.json
```

#### 6. EBS - VOLUMES ÓRFÃOS

**Volumes não anexados**

```bash
# Listar volumes disponíveis (não anexados)
aws ec2 describe-volumes \\
  --filters Name=status,Values=available \\
  --query 'Volumes[*].{ID:VolumeId,Size:Size,Created:CreateTime}'

# Criar snapshot antes de deletar
aws ec2 create-snapshot --volume-id vol-xxx --description "Backup before delete"

# Deletar volume órfão
aws ec2 delete-volume --volume-id vol-xxx
```

#### 7. SCRIPTS DE AUTOMAÇÃO

**Script: Identificar recursos subutilizados**

```python
#!/usr/bin/env python3
import boto3
from datetime import datetime, timedelta

def get_low_cpu_instances(threshold=10):
    ec2 = boto3.client('ec2')
    cw = boto3.client('cloudwatch')
    
    instances = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    low_cpu = []
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            
            metrics = cw.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.utcnow() - timedelta(days=7),
                EndTime=datetime.utcnow(),
                Period=3600,
                Statistics=['Average']
            )
            
            if metrics['Datapoints']:
                avg_cpu = sum(d['Average'] for d in metrics['Datapoints']) / len(metrics['Datapoints'])
                if avg_cpu < threshold:
                    low_cpu.append({
                        'InstanceId': instance_id,
                        'InstanceType': instance['InstanceType'],
                        'AvgCPU': round(avg_cpu, 2)
                    })
    
    return low_cpu

if __name__ == '__main__':
    for i in get_low_cpu_instances():
        print(f"{i['InstanceId']}: {i['InstanceType']} - CPU: {i['AvgCPU']}%")
```

#### 8. CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Rightsizing de X instâncias EC2
- [ ] Conversão de Y instâncias RDS para Single-AZ
- [ ] Aplicação de lifecycle em Z buckets S3
- [ ] Deleção de W volumes EBS órfãos
- [ ] Configuração de Instance Scheduler
- [ ] Revisão de Savings Plans

#### 9. MONITORAMENTO PÓS-IMPLEMENTAÇÃO

```bash
# Criar alarme de custo
aws cloudwatch put-metric-alarm \\
  --alarm-name "DailyCostSpike" \\
  --metric-name EstimatedCharges \\
  --namespace AWS/Billing \\
  --statistic Maximum \\
  --period 86400 \\
  --threshold 1000 \\
  --comparison-operator GreaterThanThreshold \\
  --evaluation-periods 1 \\
  --alarm-actions arn:aws:sns:us-east-1:xxx:alerts
```

### Diretrizes Adicionais

- Seja extremamente específico com IDs e nomes de recursos
- Todos os comandos devem ser copy-paste ready
- Inclua comandos de verificação (describe) antes de ações
- Adicione --dry-run quando disponível
- Priorize por economia esperada
"""
