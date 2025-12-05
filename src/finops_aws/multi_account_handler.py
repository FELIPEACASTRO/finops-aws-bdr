"""
Multi-Account & Multi-Region Support for FinOps AWS
Permite análise de múltiplas contas AWS e regiões com assumeRole
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError

from .utils.logger import setup_logger

logger = setup_logger(__name__)


class MultiAccountOrchestrator:
    """Orquestra análise em múltiplas contas e regiões"""
    
    def __init__(self):
        self.sts_client = boto3.client('sts')
        self.organizations_client = boto3.client('organizations')
        self.target_regions = os.environ.get('TARGET_REGIONS', 'us-east-1,us-west-2,sa-east-1').split(',')
        self.org_role_name = os.environ.get('ORG_ROLE_NAME', 'FinOpsReadOnlyRole')
    
    def get_all_accounts(self) -> List[Dict[str, str]]:
        """Obtém todas as contas da Organization"""
        accounts = []
        try:
            paginator = self.organizations_client.get_paginator('list_accounts')
            for page in paginator.paginate():
                for account in page.get('Accounts', []):
                    if account['Status'] == 'ACTIVE':
                        accounts.append({
                            'id': account['Id'],
                            'name': account['Name'],
                            'arn': account['Arn']
                        })
            logger.info(f"Found {len(accounts)} active accounts in organization")
        except ClientError as e:
            logger.warning(f"Could not list organization accounts: {e}. Using only current account.")
            try:
                current_account = self.sts_client.get_caller_identity()
                accounts = [{
                    'id': current_account['Account'],
                    'name': 'Current Account',
                    'arn': current_account['Arn']
                }]
            except Exception:
                accounts = []
        
        return accounts
    
    def assume_role_in_account(self, account_id: str, role_name: Optional[str] = None) -> Dict[str, Any]:
        """Assume role em outra conta e retorna credentials"""
        role_name = role_name or self.org_role_name
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        
        try:
            response = self.sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"FinOps-Analysis-{account_id}",
                DurationSeconds=3600
            )
            
            credentials = response['Credentials']
            logger.info(f"Successfully assumed role in account {account_id}")
            
            return {
                'aws_access_key_id': credentials['AccessKeyId'],
                'aws_secret_access_key': credentials['SecretAccessKey'],
                'aws_session_token': credentials['SessionToken'],
                'account_id': account_id
            }
        except ClientError as e:
            logger.error(f"Failed to assume role in account {account_id}: {e}")
            return {
                'error': str(e),
                'account_id': account_id,
                'status': 'failed'
            }
    
    def create_cross_account_batch(self, accounts: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Cria batches de contas e regiões para processamento paralelo"""
        batches = []
        batch_id = 0
        
        for account in accounts:
            for region in self.target_regions:
                batch = {
                    'batch_id': f"cross-account-{batch_id}",
                    'account_id': account['id'],
                    'account_name': account['name'],
                    'region': region,
                    'role_name': self.org_role_name,
                    'credentials_required': True
                }
                batches.append(batch)
                batch_id += 1
        
        logger.info(f"Created {len(batches)} cross-account batches ({len(accounts)} accounts × {len(self.target_regions)} regions)")
        return batches


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler para multi-account analysis
    Retorna batches preparados com credenciais para assumeRole
    """
    try:
        logger.info("Multi-account orchestrator started")
        
        orchestrator = MultiAccountOrchestrator()
        accounts = orchestrator.get_all_accounts()
        batches = orchestrator.create_cross_account_batch(accounts)
        
        return {
            'status': 'success',
            'accounts_count': len(accounts),
            'batches_count': len(batches),
            'batches': batches,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Multi-account orchestrator error: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }
