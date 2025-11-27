#!/bin/bash
################################################################################
# FinOps AWS - Script de Deploy e Teste Completo
# Faz deploy na AWS e executa testes de todos os 252 serviços
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_prerequisites() {
    print_header "1. Verificando Pré-requisitos"
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI não encontrado. Instale: https://aws.amazon.com/cli/"
        exit 1
    fi
    print_success "AWS CLI instalado"
    
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform não encontrado. Instale: https://terraform.io"
        exit 1
    fi
    print_success "Terraform instalado"
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "Credenciais AWS não configuradas ou inválidas"
        echo "  Configure: aws configure"
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    REGION=$(aws configure get region || echo "us-east-1")
    
    print_success "AWS Account: $ACCOUNT_ID"
    print_success "AWS Region: $REGION"
}

deploy_infrastructure() {
    print_header "2. Deploy da Infraestrutura (Terraform)"
    
    cd infrastructure/terraform
    
    if [ ! -f terraform.tfvars ]; then
        print_warning "terraform.tfvars não encontrado. Criando a partir do exemplo..."
        cp terraform.tfvars.example terraform.tfvars
        print_success "terraform.tfvars criado. Edite se necessário."
    fi
    
    echo "Inicializando Terraform..."
    terraform init -upgrade
    
    echo ""
    echo "Planejando alterações..."
    terraform plan -out=tfplan
    
    echo ""
    read -p "Deseja aplicar as alterações? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        terraform apply tfplan
        print_success "Infraestrutura deployada com sucesso!"
    else
        print_warning "Deploy cancelado pelo usuário"
        exit 0
    fi
    
    cd ../..
}

get_deployed_resources() {
    print_header "3. Recursos Deployados"
    
    cd infrastructure/terraform
    
    STATE_MACHINE_ARN=$(terraform output -raw step_functions_arn 2>/dev/null || echo "")
    LAMBDA_MAPPER_ARN=$(terraform output -raw lambda_mapper_arn 2>/dev/null || echo "")
    LAMBDA_WORKER_ARN=$(terraform output -raw lambda_worker_arn 2>/dev/null || echo "")
    LAMBDA_AGGREGATOR_ARN=$(terraform output -raw lambda_aggregator_arn 2>/dev/null || echo "")
    S3_BUCKET=$(terraform output -raw s3_bucket_name 2>/dev/null || echo "")
    
    cd ../..
    
    if [ -z "$STATE_MACHINE_ARN" ]; then
        print_error "Não foi possível obter ARNs. Verifique o deploy."
        exit 1
    fi
    
    print_success "Step Functions: $STATE_MACHINE_ARN"
    print_success "Lambda Mapper: $LAMBDA_MAPPER_ARN"
    print_success "Lambda Worker: $LAMBDA_WORKER_ARN"
    print_success "Lambda Aggregator: $LAMBDA_AGGREGATOR_ARN"
    print_success "S3 Bucket: $S3_BUCKET"
    
    export STATE_MACHINE_ARN
    export S3_BUCKET
}

run_test_execution() {
    print_header "4. Executando Teste Completo (252 serviços)"
    
    echo "Iniciando execução do Step Functions..."
    
    EXECUTION_ARN=$(aws stepfunctions start-execution \
        --state-machine-arn "$STATE_MACHINE_ARN" \
        --input '{"source": "deploy-test", "analysis_type": "full", "test_mode": false}' \
        --query 'executionArn' --output text)
    
    print_success "Execução iniciada: $EXECUTION_ARN"
    
    echo ""
    echo "Aguardando conclusão (pode levar 2-5 minutos)..."
    echo ""
    
    START_TIME=$(date +%s)
    
    while true; do
        STATUS=$(aws stepfunctions describe-execution \
            --execution-arn "$EXECUTION_ARN" \
            --query 'status' --output text)
        
        CURRENT_TIME=$(date +%s)
        ELAPSED=$((CURRENT_TIME - START_TIME))
        
        echo -ne "\r  Status: $STATUS | Tempo: ${ELAPSED}s"
        
        if [ "$STATUS" = "SUCCEEDED" ]; then
            echo ""
            print_success "Execução concluída com sucesso!"
            break
        elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "TIMED_OUT" ] || [ "$STATUS" = "ABORTED" ]; then
            echo ""
            print_error "Execução falhou com status: $STATUS"
            
            aws stepfunctions describe-execution \
                --execution-arn "$EXECUTION_ARN" \
                --query 'error' --output text
            exit 1
        fi
        
        sleep 5
    done
    
    export EXECUTION_ARN
}

show_results() {
    print_header "5. Resultados da Análise"
    
    OUTPUT=$(aws stepfunctions describe-execution \
        --execution-arn "$EXECUTION_ARN" \
        --query 'output' --output text)
    
    echo "$OUTPUT" | python3 -c "
import sys
import json

try:
    data = json.load(sys.stdin)
    summary = data.get('summary', data)
    
    print('=' * 60)
    print('RESUMO DA EXECUÇÃO')
    print('=' * 60)
    print(f\"Status: {summary.get('status', 'N/A')}\")
    print(f\"Serviços Analisados: {summary.get('total_services_analyzed', 'N/A')}\")
    print(f\"Recursos Analisados: {summary.get('resources_analyzed', 'N/A')}\")
    print(f\"Custo Total: \${summary.get('total_cost', 0):,.2f}\")
    print(f\"Economia Potencial: \${summary.get('total_savings_potential', 0):,.2f}\")
    print(f\"Recomendações: {summary.get('recommendations_count', 'N/A')}\")
    print(f\"Duração: {summary.get('duration_seconds', 0):.1f}s\")
    print()
    
    top_costs = summary.get('top_cost_services', [])
    if top_costs:
        print('TOP 5 SERVIÇOS POR CUSTO:')
        for i, svc in enumerate(top_costs[:5], 1):
            print(f\"  {i}. {svc['name']}: \${svc['value']:,.2f}\")
        print()
    
    top_savings = summary.get('top_savings_opportunities', [])
    if top_savings:
        print('TOP 5 OPORTUNIDADES DE ECONOMIA:')
        for i, svc in enumerate(top_savings[:5], 1):
            print(f\"  {i}. {svc['name']}: \${svc['value']:,.2f}\")
except Exception as e:
    print(f'Erro ao processar resultados: {e}')
    print('Output bruto:')
    print(sys.stdin.read()[:500])
"
}

download_report() {
    print_header "6. Download do Relatório"
    
    REPORT_PATH="reports/latest/report.json"
    LOCAL_PATH="finops_report_$(date +%Y%m%d_%H%M%S).json"
    
    echo "Baixando relatório do S3..."
    
    if aws s3 cp "s3://${S3_BUCKET}/${REPORT_PATH}" "$LOCAL_PATH" 2>/dev/null; then
        print_success "Relatório salvo em: $LOCAL_PATH"
        echo ""
        echo "Para visualizar:"
        echo "  cat $LOCAL_PATH | python3 -m json.tool | less"
    else
        print_warning "Relatório ainda não disponível no S3"
    fi
}

show_next_steps() {
    print_header "7. Próximos Passos"
    
    echo "O FinOps AWS está funcionando! Aqui estão algumas opções:"
    echo ""
    echo "  📊 Ver Dashboard CloudWatch:"
    echo "     https://console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards:"
    echo ""
    echo "  🔄 Execuções agendadas (EventBridge):"
    echo "     5 execuções por dia configuradas automaticamente"
    echo ""
    echo "  📧 Alertas (SNS):"
    echo "     Configure seu email no SNS Topic para receber alertas"
    echo ""
    echo "  📁 Relatórios (S3):"
    echo "     aws s3 ls s3://${S3_BUCKET}/reports/ --recursive"
    echo ""
    echo "  🔍 Logs (CloudWatch):"
    echo "     aws logs tail /aws/vendedlogs/states/finops-aws-orchestrator --follow"
    echo ""
}

main() {
    print_header "FinOps AWS - Deploy e Teste Completo"
    echo "Este script irá:"
    echo "  1. Verificar pré-requisitos"
    echo "  2. Fazer deploy da infraestrutura (Terraform)"
    echo "  3. Executar teste com todos os 252 serviços AWS"
    echo "  4. Mostrar resultados e relatório"
    echo ""
    
    read -p "Continuar? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operação cancelada."
        exit 0
    fi
    
    check_prerequisites
    deploy_infrastructure
    get_deployed_resources
    run_test_execution
    show_results
    download_report
    show_next_steps
    
    print_header "Deploy e Teste Concluídos com Sucesso!"
}

case "${1:-}" in
    --deploy-only)
        check_prerequisites
        deploy_infrastructure
        ;;
    --test-only)
        check_prerequisites
        get_deployed_resources
        run_test_execution
        show_results
        ;;
    --status)
        check_prerequisites
        get_deployed_resources
        ;;
    *)
        main
        ;;
esac
