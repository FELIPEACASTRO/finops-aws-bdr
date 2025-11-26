"""
Monitor de execuções FinOps
Utilitário para monitorar, recuperar e gerenciar execuções
"""
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tabulate import tabulate

from ..core.state_manager import StateManager, ExecutionStatus, TaskType
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ExecutionMonitor:
    """
    Monitor para execuções FinOps
    Permite visualizar, recuperar e gerenciar execuções
    """
    
    def __init__(self, bucket_name: Optional[str] = None):
        self.state_manager = StateManager(bucket_name)

    def list_executions(self, account_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Lista execuções recentes para uma conta
        
        Args:
            account_id: ID da conta AWS
            days: Número de dias para buscar
            
        Returns:
            Lista de execuções
        """
        try:
            # Por simplicidade, vamos buscar a última execução
            # Em uma implementação completa, buscaríamos no S3
            latest = self.state_manager.get_latest_execution(account_id)
            
            if latest:
                return [self._execution_to_summary(latest)]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to list executions: {e}")
            return []

    def get_execution_details(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de uma execução específica
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Detalhes da execução
        """
        try:
            execution = self.state_manager.get_execution_state(execution_id)
            if not execution:
                return None
                
            return {
                'execution': self._execution_to_summary(execution),
                'tasks': [self._task_to_summary(task) for task in execution.tasks.values()],
                'metadata': execution.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get execution details: {e}")
            return None

    def resume_execution(self, execution_id: str) -> bool:
        """
        Resume uma execução pausada/falhada
        
        Args:
            execution_id: ID da execução
            
        Returns:
            True se conseguiu resumir
        """
        try:
            execution = self.state_manager.get_execution_state(execution_id)
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return False
                
            if execution.status == ExecutionStatus.COMPLETED:
                logger.info(f"Execution {execution_id} already completed")
                return True
                
            # Atualiza estado para running
            execution.status = ExecutionStatus.RUNNING
            self.state_manager.current_execution = execution
            self.state_manager.save_execution_state(execution)
            
            logger.info(f"Resumed execution {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume execution: {e}")
            return False

    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancela uma execução
        
        Args:
            execution_id: ID da execução
            
        Returns:
            True se conseguiu cancelar
        """
        try:
            execution = self.state_manager.get_execution_state(execution_id)
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return False
                
            execution.status = ExecutionStatus.FAILED
            execution.metadata['cancelled_at'] = datetime.now().isoformat()
            execution.metadata['cancelled_reason'] = 'Manual cancellation'
            
            self.state_manager.save_execution_state(execution)
            logger.info(f"Cancelled execution {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel execution: {e}")
            return False

    def retry_failed_tasks(self, execution_id: str) -> bool:
        """
        Marca tarefas falhadas para retry
        
        Args:
            execution_id: ID da execução
            
        Returns:
            True se conseguiu marcar para retry
        """
        try:
            execution = self.state_manager.get_execution_state(execution_id)
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return False
                
            failed_count = 0
            for task in execution.tasks.values():
                if task.status == ExecutionStatus.FAILED:
                    task.status = ExecutionStatus.PENDING
                    task.error_message = None
                    failed_count += 1
            
            if failed_count > 0:
                execution.status = ExecutionStatus.RUNNING
                self.state_manager.save_execution_state(execution)
                logger.info(f"Marked {failed_count} failed tasks for retry in execution {execution_id}")
            else:
                logger.info(f"No failed tasks found in execution {execution_id}")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry failed tasks: {e}")
            return False

    def get_execution_logs(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Obtém logs de uma execução (simulado)
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Lista de logs
        """
        # Em uma implementação real, buscaria logs do CloudWatch
        execution = self.state_manager.get_execution_state(execution_id)
        if not execution:
            return []
            
        logs = []
        logs.append({
            'timestamp': execution.started_at.isoformat(),
            'level': 'INFO',
            'message': f'Execution {execution_id} started'
        })
        
        for task in execution.tasks.values():
            if task.started_at:
                logs.append({
                    'timestamp': task.started_at.isoformat(),
                    'level': 'INFO',
                    'message': f'Task {task.task_id} started'
                })
                
            if task.completed_at:
                logs.append({
                    'timestamp': task.completed_at.isoformat(),
                    'level': 'INFO',
                    'message': f'Task {task.task_id} completed'
                })
                
            if task.error_message:
                logs.append({
                    'timestamp': task.started_at.isoformat() if task.started_at else execution.started_at.isoformat(),
                    'level': 'ERROR',
                    'message': f'Task {task.task_id} failed: {task.error_message}'
                })
        
        return sorted(logs, key=lambda x: x['timestamp'])

    def cleanup_old_executions(self, account_id: str, days: int = 7) -> int:
        """
        Remove execuções antigas
        
        Args:
            account_id: ID da conta AWS
            days: Número de dias para manter
            
        Returns:
            Número de execuções removidas
        """
        try:
            self.state_manager.cleanup_old_executions(account_id, days)
            logger.info(f"Cleaned up executions older than {days} days for account {account_id}")
            return 1  # Simplificado
        except Exception as e:
            logger.error(f"Failed to cleanup old executions: {e}")
            return 0

    def _execution_to_summary(self, execution) -> Dict[str, Any]:
        """Converte execução para resumo"""
        completed_tasks = sum(1 for task in execution.tasks.values() if task.status == ExecutionStatus.COMPLETED)
        failed_tasks = sum(1 for task in execution.tasks.values() if task.status == ExecutionStatus.FAILED)
        total_tasks = len(execution.tasks)
        
        return {
            'execution_id': execution.execution_id,
            'account_id': execution.account_id,
            'status': execution.status.value,
            'started_at': execution.started_at.isoformat(),
            'last_updated': execution.last_updated.isoformat(),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'completion_percentage': (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        }

    def _task_to_summary(self, task) -> Dict[str, Any]:
        """Converte tarefa para resumo"""
        duration = None
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            
        return {
            'task_id': task.task_id,
            'task_type': task.task_type.value,
            'status': task.status.value,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'duration_seconds': duration,
            'retry_count': task.retry_count,
            'error_message': task.error_message,
            'has_result': bool(task.result_data)
        }

    def print_execution_summary(self, execution_id: str):
        """Imprime resumo da execução em formato tabular"""
        details = self.get_execution_details(execution_id)
        if not details:
            print(f"Execution {execution_id} not found")
            return
            
        execution = details['execution']
        tasks = details['tasks']
        
        print(f"\n=== Execution {execution_id} ===")
        print(f"Account ID: {execution['account_id']}")
        print(f"Status: {execution['status']}")
        print(f"Started: {execution['started_at']}")
        print(f"Last Updated: {execution['last_updated']}")
        print(f"Progress: {execution['completion_percentage']:.1f}% ({execution['completed_tasks']}/{execution['total_tasks']} tasks)")
        
        if tasks:
            print("\n=== Tasks ===")
            table_data = []
            for task in tasks:
                table_data.append([
                    task['task_type'],
                    task['status'],
                    f"{task['duration_seconds']:.1f}s" if task['duration_seconds'] else 'N/A',
                    task['retry_count'],
                    '✓' if task['has_result'] else '✗',
                    task['error_message'][:50] + '...' if task['error_message'] and len(task['error_message']) > 50 else task['error_message'] or ''
                ])
            
            headers = ['Task Type', 'Status', 'Duration', 'Retries', 'Has Result', 'Error']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))

    def print_executions_list(self, account_id: str, days: int = 7):
        """Imprime lista de execuções em formato tabular"""
        executions = self.list_executions(account_id, days)
        
        if not executions:
            print(f"No executions found for account {account_id} in the last {days} days")
            return
            
        print(f"\n=== Executions for Account {account_id} (Last {days} days) ===")
        
        table_data = []
        for execution in executions:
            table_data.append([
                execution['execution_id'][:20] + '...',
                execution['status'],
                execution['started_at'][:19],
                f"{execution['completion_percentage']:.1f}%",
                f"{execution['completed_tasks']}/{execution['total_tasks']}",
                execution['failed_tasks']
            ])
        
        headers = ['Execution ID', 'Status', 'Started', 'Progress', 'Tasks', 'Failed']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))


def main():
    """CLI para monitoramento de execuções"""
    parser = argparse.ArgumentParser(description='FinOps Execution Monitor')
    parser.add_argument('--bucket', help='S3 bucket for state storage')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List executions
    list_parser = subparsers.add_parser('list', help='List executions')
    list_parser.add_argument('account_id', help='AWS Account ID')
    list_parser.add_argument('--days', type=int, default=7, help='Days to look back')
    
    # Show execution details
    show_parser = subparsers.add_parser('show', help='Show execution details')
    show_parser.add_argument('execution_id', help='Execution ID')
    
    # Resume execution
    resume_parser = subparsers.add_parser('resume', help='Resume execution')
    resume_parser.add_argument('execution_id', help='Execution ID')
    
    # Cancel execution
    cancel_parser = subparsers.add_parser('cancel', help='Cancel execution')
    cancel_parser.add_argument('execution_id', help='Execution ID')
    
    # Retry failed tasks
    retry_parser = subparsers.add_parser('retry', help='Retry failed tasks')
    retry_parser.add_argument('execution_id', help='Execution ID')
    
    # Cleanup old executions
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old executions')
    cleanup_parser.add_argument('account_id', help='AWS Account ID')
    cleanup_parser.add_argument('--days', type=int, default=7, help='Days to keep')
    
    # Show logs
    logs_parser = subparsers.add_parser('logs', help='Show execution logs')
    logs_parser.add_argument('execution_id', help='Execution ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    monitor = ExecutionMonitor(args.bucket)
    
    try:
        if args.command == 'list':
            monitor.print_executions_list(args.account_id, args.days)
            
        elif args.command == 'show':
            monitor.print_execution_summary(args.execution_id)
            
        elif args.command == 'resume':
            if monitor.resume_execution(args.execution_id):
                print(f"Execution {args.execution_id} resumed successfully")
            else:
                print(f"Failed to resume execution {args.execution_id}")
                
        elif args.command == 'cancel':
            if monitor.cancel_execution(args.execution_id):
                print(f"Execution {args.execution_id} cancelled successfully")
            else:
                print(f"Failed to cancel execution {args.execution_id}")
                
        elif args.command == 'retry':
            if monitor.retry_failed_tasks(args.execution_id):
                print(f"Failed tasks in execution {args.execution_id} marked for retry")
            else:
                print(f"Failed to retry tasks in execution {args.execution_id}")
                
        elif args.command == 'cleanup':
            count = monitor.cleanup_old_executions(args.account_id, args.days)
            print(f"Cleaned up {count} old executions")
            
        elif args.command == 'logs':
            logs = monitor.get_execution_logs(args.execution_id)
            if logs:
                print(f"\n=== Logs for Execution {args.execution_id} ===")
                for log in logs:
                    print(f"[{log['timestamp']}] {log['level']}: {log['message']}")
            else:
                print(f"No logs found for execution {args.execution_id}")
                
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())