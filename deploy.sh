#!/bin/bash

# Script de deploy para FinOps AWS
# Este script empacota e faz deploy da solução FinOps AWS

set -e

# Configurações padrão
STACK_NAME="finops-aws-stack"
FUNCTION_NAME="finops-aws-analyzer"
REGION="us-east-1"
S3_BUCKET=""
STATE_BUCKET=""
LOG_LEVEL="INFO"
ENABLE_SCHEDULE="true"
CREATE_API="true"
USE_RESILIENT_HANDLER="true"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para print colorido
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Função de ajuda
show_help() {
    cat << EOF
Script de deploy para FinOps AWS

Uso: $0 [OPÇÕES]

OPÇÕES:
    -s, --stack-name NOME       Nome da stack CloudFormation (padrão: $STACK_NAME)
    -f, --function-name NOME    Nome da função Lambda (padrão: $FUNCTION_NAME)
    -r, --region REGIÃO         Região AWS (padrão: $REGION)
    -b, --bucket BUCKET         Bucket S3 para upload do código (obrigatório)
    --state-bucket BUCKET       Bucket S3 para armazenar estado das execuções (opcional)
    -l, --log-level LEVEL       Nível de log (padrão: $LOG_LEVEL)
    --use-legacy-handler        Usar handler legacy ao invés do resiliente
    --no-schedule               Desabilitar execução agendada
    --no-api                    Não criar API Gateway
    --update-only               Apenas atualizar código da função (não criar stack)
    -h, --help                  Mostrar esta ajuda

EXEMPLOS:
    $0 -b meu-bucket-deploy
    $0 -s finops-prod -f finops-analyzer -r us-west-2 -b deploy-bucket
    $0 --update-only -b meu-bucket

EOF
}

# Parse de argumentos
UPDATE_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        -f|--function-name)
            FUNCTION_NAME="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -b|--bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        --state-bucket)
            STATE_BUCKET="$2"
            shift 2
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --no-schedule)
            ENABLE_SCHEDULE="false"
            shift
            ;;
        --no-api)
            CREATE_API="false"
            shift
            ;;
        --use-legacy-handler)
            USE_RESILIENT_HANDLER="false"
            shift
            ;;
        --update-only)
            UPDATE_ONLY=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Opção desconhecida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validações
if [[ -z "$S3_BUCKET" ]]; then
    print_error "Bucket S3 é obrigatório. Use -b ou --bucket"
    exit 1
fi

# Se não especificou bucket de estado, usar o mesmo bucket de deploy
if [[ -z "$STATE_BUCKET" ]]; then
    STATE_BUCKET="$S3_BUCKET"
    print_warning "Usando bucket de deploy para estado: $STATE_BUCKET"
fi

# Verifica se AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI não encontrado. Instale o AWS CLI primeiro."
    exit 1
fi

# Verifica se está autenticado
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "Não autenticado na AWS. Configure suas credenciais."
    exit 1
fi

print_status "Iniciando deploy do FinOps AWS..."
print_status "Stack: $STACK_NAME"
print_status "Função: $FUNCTION_NAME"
print_status "Região: $REGION"
print_status "Bucket: $S3_BUCKET"
print_status "State Bucket: $STATE_BUCKET"
print_status "Handler: $([ "$USE_RESILIENT_HANDLER" == "true" ] && echo "Resilient" || echo "Legacy")"

# Criar diretório temporário
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

print_status "Criando pacote de deploy..."

# Copiar código fonte
cp -r src/ $TEMP_DIR/
cp requirements.txt $TEMP_DIR/

# Criar lambda_handler.py que aponta para o handler correto
if [[ "$USE_RESILIENT_HANDLER" == "true" ]]; then
    cat > $TEMP_DIR/lambda_handler.py << EOF
# Auto-generated handler selector
from src.finops_aws.resilient_lambda_handler import lambda_handler
EOF
    print_status "Usando handler resiliente"
else
    cat > $TEMP_DIR/lambda_handler.py << EOF
# Auto-generated handler selector
from src.finops_aws.lambda_handler import lambda_handler
EOF
    print_status "Usando handler legacy"
fi

# Instalar dependências
cd $TEMP_DIR
pip install -r requirements.txt -t .

# Remover arquivos desnecessários
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true

# Criar ZIP
ZIP_FILE="finops-aws-$(date +%Y%m%d-%H%M%S).zip"
zip -r $ZIP_FILE . -x "*.git*" "*.pytest_cache*" "*__pycache__*"

print_status "Pacote criado: $ZIP_FILE"

# Upload para S3
S3_KEY="finops-aws-deployments/$ZIP_FILE"
print_status "Fazendo upload para S3: s3://$S3_BUCKET/$S3_KEY"

aws s3 cp $ZIP_FILE s3://$S3_BUCKET/$S3_KEY --region $REGION

cd - > /dev/null

# Se for apenas atualização de código
if [[ "$UPDATE_ONLY" == "true" ]]; then
    print_status "Atualizando código da função Lambda..."

    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --s3-bucket $S3_BUCKET \
        --s3-key $S3_KEY \
        --region $REGION

    print_status "Código atualizado com sucesso!"
    exit 0
fi

# Deploy da stack CloudFormation
TEMPLATE_FILE="infrastructure/cloudformation-template.yaml"

if [[ ! -f "$TEMPLATE_FILE" ]]; then
    print_error "Template CloudFormation não encontrado: $TEMPLATE_FILE"
    exit 1
fi

print_status "Fazendo deploy da stack CloudFormation..."

# Verificar se stack existe
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION &> /dev/null; then
    ACTION="update-stack"
    print_status "Stack existente encontrada. Atualizando..."
else
    ACTION="create-stack"
    print_status "Criando nova stack..."
fi

# Parâmetros da stack
PARAMETERS="ParameterKey=FunctionName,ParameterValue=$FUNCTION_NAME"
PARAMETERS="$PARAMETERS ParameterKey=LogLevel,ParameterValue=$LOG_LEVEL"
PARAMETERS="$PARAMETERS ParameterKey=EnableSchedule,ParameterValue=$ENABLE_SCHEDULE"
PARAMETERS="$PARAMETERS ParameterKey=CreateApiGateway,ParameterValue=$CREATE_API"
PARAMETERS="$PARAMETERS ParameterKey=StateBucket,ParameterValue=$STATE_BUCKET"

# Deploy
aws cloudformation $ACTION \
    --stack-name $STACK_NAME \
    --template-body file://$TEMPLATE_FILE \
    --parameters $PARAMETERS \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION

print_status "Aguardando conclusão do deploy..."

# Aguardar conclusão
if [[ "$ACTION" == "create-stack" ]]; then
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $REGION
else
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $REGION
fi

# Atualizar código da função
print_status "Atualizando código da função Lambda..."

aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --s3-bucket $S3_BUCKET \
    --s3-key $S3_KEY \
    --region $REGION

# Obter outputs da stack
print_status "Obtendo informações da stack..."

OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs' \
    --output table)

print_status "Deploy concluído com sucesso!"
echo
echo "=== INFORMAÇÕES DA STACK ==="
echo "$OUTPUTS"

# Obter URL da API se criada
if [[ "$CREATE_API" == "true" ]]; then
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text)

    if [[ "$API_URL" != "None" && -n "$API_URL" ]]; then
        echo
        print_status "API Gateway URL: $API_URL"
        print_status "Teste a API: curl $API_URL"
    fi
fi

echo
print_status "Para testar a função diretamente:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --region $REGION output.json && cat output.json"

echo
print_warning "Lembre-se de:"
print_warning "1. Habilitar o AWS Compute Optimizer se quiser recomendações de otimização"
print_warning "2. Verificar as permissões IAM se encontrar erros de acesso"
print_warning "3. Monitorar os logs no CloudWatch: /aws/lambda/$FUNCTION_NAME"
