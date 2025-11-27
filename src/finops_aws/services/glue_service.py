"""
Glue FinOps Service - Análise de Custos de ETL

FASE 2 - Prioridade 2: Analytics
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de Jobs, Crawlers, Data Catalog
- Análise de DPU e execuções
- Recomendações de otimização
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class GlueJob:
    """Representa um Glue Job"""
    name: str
    role: str
    command: Dict[str, Any]
    glue_version: str = "3.0"
    max_capacity: float = 0.0
    worker_type: str = ""  # Standard, G.1X, G.2X, G.025X
    number_of_workers: int = 0
    timeout: int = 2880
    max_retries: int = 0
    allocated_capacity: int = 0
    last_modified_on: Optional[datetime] = None
    created_on: Optional[datetime] = None
    execution_class: str = "STANDARD"  # STANDARD, FLEX
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'glue_version': self.glue_version,
            'worker_type': self.worker_type,
            'number_of_workers': self.number_of_workers,
            'max_capacity': self.max_capacity,
            'timeout': self.timeout,
            'execution_class': self.execution_class,
            'command_type': self.command.get('Name', ''),
            'created_on': self.created_on.isoformat() if self.created_on else None
        }


@dataclass
class GlueCrawler:
    """Representa um Glue Crawler"""
    name: str
    role: str
    database_name: str
    state: str
    schedule: Optional[str] = None
    classifiers: List[str] = field(default_factory=list)
    table_prefix: str = ""
    schema_change_policy: Dict = field(default_factory=dict)
    recrawl_policy: Dict = field(default_factory=dict)
    last_crawl: Optional[Dict] = None
    creation_time: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'database_name': self.database_name,
            'state': self.state,
            'schedule': self.schedule,
            'last_crawl_status': self.last_crawl.get('Status') if self.last_crawl else None,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class GlueDatabase:
    """Representa um Glue Database"""
    name: str
    catalog_id: str
    location_uri: Optional[str] = None
    description: str = ""
    create_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'catalog_id': self.catalog_id,
            'location_uri': self.location_uri,
            'description': self.description
        }


@dataclass
class GlueJobRun:
    """Representa uma execução de Job"""
    job_name: str
    run_id: str
    state: str
    started_on: Optional[datetime]
    completed_on: Optional[datetime]
    execution_time: int  # seconds
    dpu_seconds: float
    max_capacity: float
    worker_type: str
    number_of_workers: int
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_name': self.job_name,
            'run_id': self.run_id,
            'state': self.state,
            'execution_time': self.execution_time,
            'dpu_seconds': self.dpu_seconds,
            'started_on': self.started_on.isoformat() if self.started_on else None
        }


class GlueService(BaseAWSService):
    """
    Serviço FinOps para análise de custos Glue
    
    Analisa Jobs, Crawlers, Data Catalog e fornece
    recomendações de otimização de custos.
    """
    
    def __init__(
        self,
        glue_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._glue_client = glue_client
    
    @property
    def glue_client(self):
        if self._glue_client is None:
            import boto3
            self._glue_client = boto3.client('glue')
        return self._glue_client
    
    def get_service_name(self) -> str:
        return "AWS Glue"
    
    def health_check(self) -> bool:
        try:
            self.glue_client.get_jobs(MaxResults=1)
            return True
        except Exception:
            return False
    
    
    def get_jobs(self) -> List[GlueJob]:
        """Lista todos os Glue Jobs"""
        jobs = []
        
        paginator = self.glue_client.get_paginator('get_jobs')
        
        for page in paginator.paginate():
            for job in page.get('Jobs', []):
                glue_job = GlueJob(
                    name=job['Name'],
                    role=job['Role'],
                    command=job.get('Command', {}),
                    glue_version=job.get('GlueVersion', '2.0'),
                    max_capacity=job.get('MaxCapacity', 0.0),
                    worker_type=job.get('WorkerType', ''),
                    number_of_workers=job.get('NumberOfWorkers', 0),
                    timeout=job.get('Timeout', 2880),
                    max_retries=job.get('MaxRetries', 0),
                    allocated_capacity=job.get('AllocatedCapacity', 0),
                    last_modified_on=job.get('LastModifiedOn'),
                    created_on=job.get('CreatedOn'),
                    execution_class=job.get('ExecutionClass', 'STANDARD')
                )
                jobs.append(glue_job)
        
        return jobs
    
    
    def get_crawlers(self) -> List[GlueCrawler]:
        """Lista todos os Glue Crawlers"""
        crawlers = []
        
        paginator = self.glue_client.get_paginator('get_crawlers')
        
        for page in paginator.paginate():
            for crawler in page.get('Crawlers', []):
                glue_crawler = GlueCrawler(
                    name=crawler['Name'],
                    role=crawler['Role'],
                    database_name=crawler.get('DatabaseName', ''),
                    state=crawler['State'],
                    schedule=crawler.get('Schedule', {}).get('ScheduleExpression'),
                    classifiers=crawler.get('Classifiers', []),
                    table_prefix=crawler.get('TablePrefix', ''),
                    schema_change_policy=crawler.get('SchemaChangePolicy', {}),
                    recrawl_policy=crawler.get('RecrawlPolicy', {}),
                    last_crawl=crawler.get('LastCrawl'),
                    creation_time=crawler.get('CreationTime'),
                    last_updated=crawler.get('LastUpdated')
                )
                crawlers.append(glue_crawler)
        
        return crawlers
    
    
    def get_databases(self) -> List[GlueDatabase]:
        """Lista Glue Databases"""
        databases = []
        
        paginator = self.glue_client.get_paginator('get_databases')
        
        for page in paginator.paginate():
            for db in page.get('DatabaseList', []):
                database = GlueDatabase(
                    name=db['Name'],
                    catalog_id=db.get('CatalogId', ''),
                    location_uri=db.get('LocationUri'),
                    description=db.get('Description', ''),
                    create_time=db.get('CreateTime')
                )
                databases.append(database)
        
        return databases
    
    
    def get_job_runs(self, job_name: str, days: int = 30) -> List[GlueJobRun]:
        """Obtém execuções recentes de um job"""
        runs = []
        
        response = self.glue_client.get_job_runs(JobName=job_name, MaxResults=100)
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        for run in response.get('JobRuns', []):
            started = run.get('StartedOn')
            if started and started.replace(tzinfo=None) < cutoff:
                continue
            
            job_run = GlueJobRun(
                job_name=job_name,
                run_id=run['Id'],
                state=run['JobRunState'],
                started_on=run.get('StartedOn'),
                completed_on=run.get('CompletedOn'),
                execution_time=run.get('ExecutionTime', 0),
                dpu_seconds=run.get('DPUSeconds', 0.0),
                max_capacity=run.get('MaxCapacity', 0.0),
                worker_type=run.get('WorkerType', ''),
                number_of_workers=run.get('NumberOfWorkers', 0),
                error_message=run.get('ErrorMessage', '')
            )
            runs.append(job_run)
        
        return runs
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        resources = []
        
        for job in self.get_jobs():
            res = job.to_dict()
            res['resource_type'] = 'job'
            resources.append(res)
        
        for crawler in self.get_crawlers():
            res = crawler.to_dict()
            res['resource_type'] = 'crawler'
            resources.append(res)
        
        for db in self.get_databases():
            res = db.to_dict()
            res['resource_type'] = 'database'
            resources.append(res)
        
        return resources
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de Glue"""
        jobs = self.get_jobs()
        crawlers = self.get_crawlers()
        databases = self.get_databases()
        
        total_dpu_hours = 0
        total_runs = 0
        failed_runs = 0
        
        for job in jobs[:10]:
            try:
                runs = self.get_job_runs(job.name, days=7)
                total_runs += len(runs)
                failed_runs += len([r for r in runs if r.state == 'FAILED'])
                total_dpu_hours += sum(r.dpu_seconds / 3600 for r in runs)
            except Exception:
                pass
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(jobs) + len(crawlers) + len(databases),
            metrics={
                'jobs': len(jobs),
                'crawlers': len(crawlers),
                'databases': len(databases),
                'total_dpu_hours_7d': round(total_dpu_hours, 2),
                'total_runs_7d': total_runs,
                'failed_runs_7d': failed_runs,
                'flex_jobs': len([j for j in jobs if j.execution_class == 'FLEX'])
            },
            period_days=7,
            collected_at=datetime.now(timezone.utc)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para Glue"""
        recommendations = []
        jobs = self.get_jobs()
        crawlers = self.get_crawlers()
        
        for job in jobs:
            if job.execution_class != 'FLEX' and job.command.get('Name') not in ['pythonshell']:
                recommendations.append(ServiceRecommendation(
                    resource_id=job.name,
                    resource_type='Glue Job',
                    recommendation_type='FLEX_OPPORTUNITY',
                    title='Candidato a Glue Flex',
                    description=f'Job {job.name} usa execution class STANDARD. '
                               f'Para jobs não críticos, Flex pode economizar até 35%.',
                    estimated_savings=job.max_capacity * 0.44 * 0.35 * 10,
                    priority='MEDIUM',
                    action='Avaliar migração para Flex execution'
                ))
            
            try:
                runs = self.get_job_runs(job.name, days=30)
                
                if len(runs) == 0:
                    recommendations.append(ServiceRecommendation(
                        resource_id=job.name,
                        resource_type='Glue Job',
                        recommendation_type='UNUSED_RESOURCE',
                        title='Job sem execuções nos últimos 30 dias',
                        description=f'Job {job.name} não foi executado nos últimos 30 dias. '
                                   f'Considere remover se não for mais necessário.',
                        estimated_savings=0.0,
                        priority='LOW',
                        action='Remover job não utilizado'
                    ))
                else:
                    failed = [r for r in runs if r.state == 'FAILED']
                    if len(failed) / len(runs) > 0.2:
                        recommendations.append(ServiceRecommendation(
                            resource_id=job.name,
                            resource_type='Glue Job',
                            recommendation_type='HIGH_FAILURE_RATE',
                            title=f'Alta taxa de falhas ({len(failed)}/{len(runs)})',
                            description=f'Job {job.name} tem {len(failed)} falhas em {len(runs)} execuções. '
                                       f'Falhas desperdiçam DPU. Investigue e corrija.',
                            estimated_savings=sum(r.dpu_seconds / 3600 * 0.44 for r in failed),
                            priority='HIGH',
                            action='Investigar e corrigir falhas'
                        ))
                    
                    if runs:
                        avg_exec = sum(r.execution_time for r in runs) / len(runs)
                        if job.timeout > avg_exec * 3 and avg_exec > 0:
                            recommendations.append(ServiceRecommendation(
                                resource_id=job.name,
                                resource_type='Glue Job',
                                recommendation_type='TIMEOUT_OPTIMIZATION',
                                title=f'Timeout superdimensionado',
                                description=f'Job {job.name} tem timeout de {job.timeout}min mas '
                                           f'executa em média {avg_exec/60:.1f}min.',
                                estimated_savings=0.0,
                                priority='LOW',
                                action='Ajustar timeout'
                            ))
                
            except Exception:
                pass
            
            if job.glue_version in ['1.0', '2.0']:
                recommendations.append(ServiceRecommendation(
                    resource_id=job.name,
                    resource_type='Glue Job',
                    recommendation_type='VERSION_UPGRADE',
                    title=f'Versão antiga do Glue: {job.glue_version}',
                    description=f'Job {job.name} usa Glue {job.glue_version}. '
                               f'Atualize para 3.0+ para melhor performance.',
                    estimated_savings=5.0,
                    priority='LOW',
                    action='Atualizar para Glue 3.0 ou 4.0'
                ))
        
        for crawler in crawlers:
            if crawler.last_crawl:
                status = crawler.last_crawl.get('Status', '')
                if status == 'FAILED':
                    recommendations.append(ServiceRecommendation(
                        resource_id=crawler.name,
                        resource_type='Glue Crawler',
                        recommendation_type='FAILED_CRAWL',
                        title='Último crawl falhou',
                        description=f'Crawler {crawler.name} falhou na última execução. '
                                   f'Crawlers falhos ainda consomem recursos. Investigue.',
                        estimated_savings=0.0,
                        priority='MEDIUM',
                        action='Investigar falha do crawler'
                    ))
            
            if not crawler.schedule:
                recommendations.append(ServiceRecommendation(
                    resource_id=crawler.name,
                    resource_type='Glue Crawler',
                    recommendation_type='NO_SCHEDULE',
                    title='Crawler sem agendamento',
                    description=f'Crawler {crawler.name} não tem schedule definido. '
                               f'Se executado manualmente com frequência, considere agendar.',
                    estimated_savings=0.0,
                    priority='LOW',
                    action='Avaliar necessidade de schedule'
                ))
        
        return recommendations
