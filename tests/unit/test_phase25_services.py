"""
Testes Unitários para FASE 2.5 - Serviços de Alto Custo de Armazenamento e Banco de Dados

Este módulo testa os novos serviços FinOps:
- FSxService: File systems gerenciados (Lustre, Windows, ONTAP, OpenZFS)
- DocumentDBService: MongoDB compatível
- NeptuneService: Graph database
- TimestreamService: Time series database
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from src.finops_aws.services.fsx_service import (
    FSxService, FSxFileSystem, FSxVolume, FSxBackup
)
from src.finops_aws.services.documentdb_service import (
    DocumentDBService, DocumentDBCluster, DocumentDBInstance, DocumentDBClusterSnapshot
)
from src.finops_aws.services.neptune_service import (
    NeptuneService, NeptuneCluster, NeptuneInstance
)
from src.finops_aws.services.timestream_service import (
    TimestreamService, TimestreamDatabase, TimestreamTable, TimestreamScheduledQuery
)
from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory


class TestFSxFileSystem:
    """Testes para dataclass FSxFileSystem"""
    
    def test_create_file_system(self):
        """Testa criação de file system FSx"""
        fs = FSxFileSystem(
            file_system_id='fs-12345678',
            file_system_type='LUSTRE',
            arn='arn:aws:fsx:us-east-1:123456789:file-system/fs-12345678',
            lifecycle='AVAILABLE',
            storage_capacity=1200,
            storage_type='SSD',
            kms_key_id='arn:aws:kms:us-east-1:123456789:key/12345',
            throughput_capacity=500,
            deployment_type='PERSISTENT_1'
        )
        
        assert fs.file_system_id == 'fs-12345678'
        assert fs.is_lustre == True
        assert fs.is_encrypted == True
        assert fs.storage_capacity_gb == 1200
        assert fs.storage_capacity_tb == 1200 / 1024
    
    def test_file_system_types(self):
        """Testa identificação de tipos de file system"""
        lustre = FSxFileSystem(file_system_id='fs-1', file_system_type='LUSTRE', arn='', lifecycle='AVAILABLE', storage_capacity=100)
        windows = FSxFileSystem(file_system_id='fs-2', file_system_type='WINDOWS', arn='', lifecycle='AVAILABLE', storage_capacity=100)
        ontap = FSxFileSystem(file_system_id='fs-3', file_system_type='ONTAP', arn='', lifecycle='AVAILABLE', storage_capacity=100)
        openzfs = FSxFileSystem(file_system_id='fs-4', file_system_type='OPENZFS', arn='', lifecycle='AVAILABLE', storage_capacity=100)
        
        assert lustre.is_lustre == True
        assert windows.is_windows == True
        assert ontap.is_ontap == True
        assert openzfs.is_openzfs == True
    
    def test_file_system_to_dict(self):
        """Testa serialização de file system"""
        fs = FSxFileSystem(
            file_system_id='fs-12345678',
            file_system_type='WINDOWS',
            arn='arn:aws:fsx:us-east-1:123456789:file-system/fs-12345678',
            lifecycle='AVAILABLE',
            storage_capacity=500,
            automatic_backup_retention_days=7
        )
        
        data = fs.to_dict()
        assert 'file_system_id' in data
        assert 'is_encrypted' in data
        assert 'has_backups' in data
        assert data['has_backups'] == True


class TestFSxVolume:
    """Testes para dataclass FSxVolume"""
    
    def test_create_volume(self):
        """Testa criação de volume FSx"""
        vol = FSxVolume(
            volume_id='fsvol-12345678',
            volume_type='ONTAP',
            name='my-volume',
            lifecycle='CREATED',
            file_system_id='fs-12345678',
            size_in_megabytes=102400,
            storage_efficiency_enabled=True,
            tiering_policy='AUTO'
        )
        
        assert vol.volume_id == 'fsvol-12345678'
        assert vol.size_in_gb == 100.0
        assert vol.has_tiering == True
    
    def test_volume_to_dict(self):
        """Testa serialização de volume"""
        vol = FSxVolume(
            volume_id='fsvol-12345678',
            volume_type='ONTAP',
            name='test-vol',
            lifecycle='AVAILABLE',
            file_system_id='fs-12345678'
        )
        
        data = vol.to_dict()
        assert 'volume_id' in data
        assert 'size_in_gb' in data


class TestFSxService:
    """Testes para FSxService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = FSxService(mock_client_factory)
        assert service.service_name == "Amazon FSx"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_fsx = Mock()
        mock_fsx.describe_file_systems.return_value = {'FileSystems': []}
        mock_client_factory.get_client.return_value = mock_fsx
        
        service = FSxService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_file_systems_empty(self, mock_client_factory):
        """Testa listagem sem file systems"""
        mock_fsx = Mock()
        mock_fsx.get_paginator.return_value.paginate.return_value = [{'FileSystems': []}]
        mock_client_factory.get_client.return_value = mock_fsx
        
        service = FSxService(mock_client_factory)
        file_systems = service.get_file_systems()
        assert len(file_systems) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_fsx = Mock()
        mock_fsx.get_paginator.return_value.paginate.return_value = [
            {'FileSystems': []},
        ]
        mock_client_factory.get_client.return_value = mock_fsx
        
        service = FSxService(mock_client_factory)
        resources = service.get_resources()
        assert 'file_systems' in resources
        assert 'volumes' in resources
        assert 'summary' in resources


class TestDocumentDBCluster:
    """Testes para dataclass DocumentDBCluster"""
    
    def test_create_cluster(self):
        """Testa criação de cluster DocumentDB"""
        cluster = DocumentDBCluster(
            db_cluster_identifier='my-docdb-cluster',
            db_cluster_arn='arn:aws:rds:us-east-1:123456789:cluster:my-docdb-cluster',
            engine='docdb',
            engine_version='4.0.0',
            status='available',
            backup_retention_period=7,
            storage_encrypted=True,
            deletion_protection=True,
            db_cluster_members=[
                {'DBInstanceIdentifier': 'instance-1', 'IsClusterWriter': True},
                {'DBInstanceIdentifier': 'instance-2', 'IsClusterWriter': False}
            ]
        )
        
        assert cluster.db_cluster_identifier == 'my-docdb-cluster'
        assert cluster.is_available == True
        assert cluster.has_encryption == True
        assert cluster.has_deletion_protection == True
        assert cluster.instance_count == 2
        assert cluster.writer_count == 1
        assert cluster.reader_count == 1
    
    def test_cluster_to_dict(self):
        """Testa serialização de cluster"""
        cluster = DocumentDBCluster(
            db_cluster_identifier='test-cluster',
            db_cluster_arn='arn:aws:rds:us-east-1:123456789:cluster:test-cluster',
            engine='docdb',
            engine_version='4.0.0',
            status='available'
        )
        
        data = cluster.to_dict()
        assert 'db_cluster_identifier' in data
        assert 'instance_count' in data
        assert 'has_cloudwatch_logs' in data


class TestDocumentDBInstance:
    """Testes para dataclass DocumentDBInstance"""
    
    def test_create_instance(self):
        """Testa criação de instância DocumentDB"""
        instance = DocumentDBInstance(
            db_instance_identifier='my-docdb-instance',
            db_instance_arn='arn:aws:rds:us-east-1:123456789:db:my-docdb-instance',
            db_instance_class='db.r5.large',
            engine='docdb',
            engine_version='4.0.0',
            db_instance_status='available',
            is_cluster_writer=True
        )
        
        assert instance.db_instance_identifier == 'my-docdb-instance'
        assert instance.is_available == True
        assert instance.is_writer == True
        assert instance.is_reader == False
        assert instance.instance_family == 'r5'
        assert instance.instance_size == 'large'


class TestDocumentDBService:
    """Testes para DocumentDBService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = DocumentDBService(mock_client_factory)
        assert service.service_name == "Amazon DocumentDB"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_docdb = Mock()
        mock_docdb.describe_db_clusters.return_value = {'DBClusters': []}
        mock_client_factory.get_client.return_value = mock_docdb
        
        service = DocumentDBService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_clusters_empty(self, mock_client_factory):
        """Testa listagem sem clusters"""
        mock_docdb = Mock()
        mock_docdb.get_paginator.return_value.paginate.return_value = [{'DBClusters': []}]
        mock_client_factory.get_client.return_value = mock_docdb
        
        service = DocumentDBService(mock_client_factory)
        clusters = service.get_clusters()
        assert len(clusters) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_docdb = Mock()
        mock_docdb.get_paginator.return_value.paginate.return_value = [{'DBClusters': [], 'DBInstances': [], 'DBClusterSnapshots': []}]
        mock_client_factory.get_client.return_value = mock_docdb
        
        service = DocumentDBService(mock_client_factory)
        resources = service.get_resources()
        assert 'clusters' in resources
        assert 'instances' in resources
        assert 'summary' in resources


class TestNeptuneCluster:
    """Testes para dataclass NeptuneCluster"""
    
    def test_create_cluster(self):
        """Testa criação de cluster Neptune"""
        cluster = NeptuneCluster(
            db_cluster_identifier='my-neptune-cluster',
            db_cluster_arn='arn:aws:rds:us-east-1:123456789:cluster:my-neptune-cluster',
            engine='neptune',
            engine_version='1.2.0.0',
            status='available',
            storage_encrypted=True,
            iam_database_authentication_enabled=True,
            db_cluster_members=[
                {'DBInstanceIdentifier': 'instance-1', 'IsClusterWriter': True}
            ]
        )
        
        assert cluster.db_cluster_identifier == 'my-neptune-cluster'
        assert cluster.is_available == True
        assert cluster.has_encryption == True
        assert cluster.has_iam_auth == True
        assert cluster.instance_count == 1
    
    def test_serverless_cluster(self):
        """Testa cluster Neptune Serverless"""
        cluster = NeptuneCluster(
            db_cluster_identifier='serverless-cluster',
            db_cluster_arn='arn:aws:rds:us-east-1:123456789:cluster:serverless-cluster',
            engine='neptune',
            engine_version='1.2.0.0',
            status='available',
            serverless_v2_scaling_configuration={'MinCapacity': 1.0, 'MaxCapacity': 8.0}
        )
        
        assert cluster.is_serverless == True
        assert cluster.min_capacity == 1.0
        assert cluster.max_capacity == 8.0
    
    def test_cluster_to_dict(self):
        """Testa serialização de cluster"""
        cluster = NeptuneCluster(
            db_cluster_identifier='test-cluster',
            db_cluster_arn='arn',
            engine='neptune',
            engine_version='1.2.0.0',
            status='available'
        )
        
        data = cluster.to_dict()
        assert 'db_cluster_identifier' in data
        assert 'is_serverless' in data


class TestNeptuneInstance:
    """Testes para dataclass NeptuneInstance"""
    
    def test_create_instance(self):
        """Testa criação de instância Neptune"""
        instance = NeptuneInstance(
            db_instance_identifier='my-neptune-instance',
            db_instance_arn='arn:aws:rds:us-east-1:123456789:db:my-neptune-instance',
            db_instance_class='db.r5.large',
            engine='neptune',
            engine_version='1.2.0.0',
            db_instance_status='available',
            is_cluster_writer=True
        )
        
        assert instance.db_instance_identifier == 'my-neptune-instance'
        assert instance.is_available == True
        assert instance.is_writer == True
        assert instance.is_serverless == False


class TestNeptuneService:
    """Testes para NeptuneService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = NeptuneService(mock_client_factory)
        assert service.service_name == "Amazon Neptune"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_neptune = Mock()
        mock_neptune.describe_db_clusters.return_value = {'DBClusters': []}
        mock_client_factory.get_client.return_value = mock_neptune
        
        service = NeptuneService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_clusters_empty(self, mock_client_factory):
        """Testa listagem sem clusters"""
        mock_neptune = Mock()
        mock_neptune.get_paginator.return_value.paginate.return_value = [{'DBClusters': []}]
        mock_client_factory.get_client.return_value = mock_neptune
        
        service = NeptuneService(mock_client_factory)
        clusters = service.get_clusters()
        assert len(clusters) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_neptune = Mock()
        mock_neptune.get_paginator.return_value.paginate.return_value = [{'DBClusters': [], 'DBInstances': []}]
        mock_client_factory.get_client.return_value = mock_neptune
        
        service = NeptuneService(mock_client_factory)
        resources = service.get_resources()
        assert 'clusters' in resources
        assert 'instances' in resources
        assert 'summary' in resources


class TestTimestreamDatabase:
    """Testes para dataclass TimestreamDatabase"""
    
    def test_create_database(self):
        """Testa criação de database Timestream"""
        db = TimestreamDatabase(
            database_name='my-timestream-db',
            arn='arn:aws:timestream:us-east-1:123456789:database/my-timestream-db',
            table_count=5,
            kms_key_id='arn:aws:kms:us-east-1:123456789:key/12345'
        )
        
        assert db.database_name == 'my-timestream-db'
        assert db.is_encrypted == True
        assert db.has_tables == True
    
    def test_database_to_dict(self):
        """Testa serialização de database"""
        db = TimestreamDatabase(
            database_name='test-db',
            arn='arn',
            table_count=0
        )
        
        data = db.to_dict()
        assert 'database_name' in data
        assert 'is_encrypted' in data
        assert 'has_tables' in data


class TestTimestreamTable:
    """Testes para dataclass TimestreamTable"""
    
    def test_create_table(self):
        """Testa criação de table Timestream"""
        table = TimestreamTable(
            table_name='my-table',
            database_name='my-db',
            arn='arn:aws:timestream:us-east-1:123456789:database/my-db/table/my-table',
            table_status='ACTIVE',
            memory_store_retention_period_in_hours=24,
            magnetic_store_retention_period_in_days=365
        )
        
        assert table.table_name == 'my-table'
        assert table.is_active == True
        assert table.memory_retention_hours == 24
        assert table.magnetic_retention_days == 365
        assert table.total_retention_days == 366
    
    def test_table_with_magnetic_writes(self):
        """Testa table com magnetic writes"""
        table = TimestreamTable(
            table_name='my-table',
            database_name='my-db',
            arn='arn',
            table_status='ACTIVE',
            magnetic_store_write_properties={'EnableMagneticStoreWrites': True}
        )
        
        assert table.has_magnetic_writes == True
    
    def test_table_to_dict(self):
        """Testa serialização de table"""
        table = TimestreamTable(
            table_name='test-table',
            database_name='test-db',
            arn='arn',
            table_status='ACTIVE'
        )
        
        data = table.to_dict()
        assert 'table_name' in data
        assert 'is_active' in data
        assert 'total_retention_days' in data


class TestTimestreamService:
    """Testes para TimestreamService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = TimestreamService(mock_client_factory)
        assert service.service_name == "Amazon Timestream"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_timestream = Mock()
        mock_timestream.list_databases.return_value = {'Databases': []}
        mock_client_factory.get_client.return_value = mock_timestream
        
        service = TimestreamService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_databases_empty(self, mock_client_factory):
        """Testa listagem sem databases"""
        mock_timestream = Mock()
        mock_timestream.get_paginator.return_value.paginate.return_value = [{'Databases': []}]
        mock_client_factory.get_client.return_value = mock_timestream
        
        service = TimestreamService(mock_client_factory)
        databases = service.get_databases()
        assert len(databases) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_timestream_write = Mock()
        mock_timestream_write.get_paginator.return_value.paginate.return_value = [{'Databases': [], 'Tables': []}]
        
        mock_timestream_query = Mock()
        mock_timestream_query.get_paginator.return_value.paginate.return_value = [{'ScheduledQueries': []}]
        
        def get_client(service_name):
            if service_name == 'timestream-write':
                return mock_timestream_write
            elif service_name == 'timestream-query':
                return mock_timestream_query
            return Mock()
        
        mock_client_factory.get_client = get_client
        
        service = TimestreamService(mock_client_factory)
        resources = service.get_resources()
        assert 'databases' in resources
        assert 'tables' in resources
        assert 'summary' in resources


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_get_all_services_includes_new_services(self, mock_client_factory):
        """Testa que get_all_services inclui os novos serviços"""
        ServiceFactory._instance = None
        
        service_factory = ServiceFactory(client_factory=mock_client_factory)
        all_services = service_factory.get_all_services()
        
        assert 'fsx' in all_services
        assert 'documentdb' in all_services
        assert 'neptune' in all_services
        assert 'timestream' in all_services
        
        ServiceFactory._instance = None
    
    def test_services_are_cached(self, mock_client_factory):
        """Testa que serviços são cacheados"""
        ServiceFactory._instance = None
        
        service_factory = ServiceFactory(client_factory=mock_client_factory)
        
        fsx1 = service_factory.get_fsx_service()
        fsx2 = service_factory.get_fsx_service()
        assert fsx1 is fsx2
        
        docdb1 = service_factory.get_documentdb_service()
        docdb2 = service_factory.get_documentdb_service()
        assert docdb1 is docdb2
        
        ServiceFactory._instance = None


class TestRecommendations:
    """Testes para recomendações dos serviços"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_fsx_recommendations_empty(self, mock_client_factory):
        """Testa recomendações FSx sem recursos"""
        mock_fsx = Mock()
        mock_fsx.get_paginator.return_value.paginate.return_value = [{'FileSystems': [], 'Volumes': [], 'Backups': []}]
        mock_client_factory.get_client.return_value = mock_fsx
        
        service = FSxService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)
    
    def test_documentdb_recommendations_empty(self, mock_client_factory):
        """Testa recomendações DocumentDB sem recursos"""
        mock_docdb = Mock()
        mock_docdb.get_paginator.return_value.paginate.return_value = [{'DBClusters': [], 'DBInstances': []}]
        mock_client_factory.get_client.return_value = mock_docdb
        
        service = DocumentDBService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)
    
    def test_neptune_recommendations_empty(self, mock_client_factory):
        """Testa recomendações Neptune sem recursos"""
        mock_neptune = Mock()
        mock_neptune.get_paginator.return_value.paginate.return_value = [{'DBClusters': [], 'DBInstances': []}]
        mock_client_factory.get_client.return_value = mock_neptune
        
        service = NeptuneService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)
    
    def test_timestream_recommendations_empty(self, mock_client_factory):
        """Testa recomendações Timestream sem recursos"""
        mock_timestream_write = Mock()
        mock_timestream_write.get_paginator.return_value.paginate.return_value = [{'Databases': [], 'Tables': []}]
        
        mock_timestream_query = Mock()
        mock_timestream_query.get_paginator.return_value.paginate.return_value = [{'ScheduledQueries': []}]
        
        def get_client(service_name):
            if service_name == 'timestream-write':
                return mock_timestream_write
            elif service_name == 'timestream-query':
                return mock_timestream_query
            return Mock()
        
        mock_client_factory.get_client = get_client
        
        service = TimestreamService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)
