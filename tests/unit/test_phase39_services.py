"""
Testes unitários para FASE 3.9 - Blockchain & Quantum Services.

QLDB, Managed Blockchain, Braket.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.finops_aws.services.qldb_service import (
    QLDBService, QLDBLedger, QLDBJournalExport, QLDBStream
)
from src.finops_aws.services.managedblockchain_service import (
    ManagedBlockchainService, ManagedBlockchainNetwork, 
    ManagedBlockchainMember, ManagedBlockchainNode
)
from src.finops_aws.services.braket_service import (
    BraketService, BraketQuantumTask, BraketJob
)
from src.finops_aws.core.factories import ServiceFactory


class TestQLDBLedgerDataclass:
    """Testes para QLDBLedger dataclass."""

    def test_ledger_active(self):
        """Testa ledger ativo."""
        ledger = QLDBLedger(name="ledger-001", state="ACTIVE")
        assert ledger.is_active is True
        assert ledger.is_creating is False

    def test_ledger_creating(self):
        """Testa ledger sendo criado."""
        ledger = QLDBLedger(name="ledger-001", state="CREATING")
        assert ledger.is_creating is True

    def test_ledger_deleting(self):
        """Testa ledger sendo deletado."""
        ledger = QLDBLedger(name="ledger-001", state="DELETING")
        assert ledger.is_deleting is True

    def test_ledger_protection(self):
        """Testa ledger com proteção."""
        ledger = QLDBLedger(name="ledger-001", deletion_protection=True)
        assert ledger.has_deletion_protection is True

    def test_ledger_allow_all(self):
        """Testa ledger com ALLOW_ALL."""
        ledger = QLDBLedger(name="ledger-001", permissions_mode="ALLOW_ALL")
        assert ledger.uses_allow_all is True
        assert ledger.uses_standard is False

    def test_ledger_standard(self):
        """Testa ledger com STANDARD."""
        ledger = QLDBLedger(name="ledger-001", permissions_mode="STANDARD")
        assert ledger.uses_standard is True

    def test_ledger_encrypted(self):
        """Testa ledger criptografado."""
        ledger = QLDBLedger(
            name="ledger-001",
            encryption_description={"EncryptionStatus": "ENABLED"}
        )
        assert ledger.is_encrypted is True

    def test_ledger_custom_kms(self):
        """Testa ledger com KMS customizado."""
        ledger = QLDBLedger(
            name="ledger-001",
            encryption_description={"KmsKeyArn": "arn:aws:kms:...custom"}
        )
        assert ledger.has_custom_kms is True

    def test_ledger_aws_kms(self):
        """Testa ledger com KMS AWS."""
        ledger = QLDBLedger(
            name="ledger-001",
            encryption_description={"KmsKeyArn": "arn:aws:kms:...alias/aws/qldb"}
        )
        assert ledger.has_custom_kms is False

    def test_ledger_to_dict(self):
        """Testa conversão para dicionário."""
        ledger = QLDBLedger(name="test-ledger")
        result = ledger.to_dict()
        assert result["name"] == "test-ledger"


class TestQLDBJournalExportDataclass:
    """Testes para QLDBJournalExport dataclass."""

    def test_export_in_progress(self):
        """Testa export em progresso."""
        export = QLDBJournalExport(export_id="export-001", status="IN_PROGRESS")
        assert export.is_in_progress is True

    def test_export_completed(self):
        """Testa export completo."""
        export = QLDBJournalExport(export_id="export-001", status="COMPLETED")
        assert export.is_completed is True

    def test_export_cancelled(self):
        """Testa export cancelado."""
        export = QLDBJournalExport(export_id="export-001", status="CANCELLED")
        assert export.is_cancelled is True

    def test_export_s3(self):
        """Testa export S3."""
        export = QLDBJournalExport(
            export_id="export-001",
            s3_export_configuration={"Bucket": "my-bucket", "Prefix": "exports/"}
        )
        assert export.s3_bucket == "my-bucket"
        assert export.s3_prefix == "exports/"

    def test_export_ion_binary(self):
        """Testa export ION_BINARY."""
        export = QLDBJournalExport(export_id="export-001", output_format="ION_BINARY")
        assert export.uses_ion_binary is True

    def test_export_ion_text(self):
        """Testa export ION_TEXT."""
        export = QLDBJournalExport(export_id="export-001", output_format="ION_TEXT")
        assert export.uses_ion_text is True

    def test_export_json(self):
        """Testa export JSON."""
        export = QLDBJournalExport(export_id="export-001", output_format="JSON")
        assert export.uses_json is True

    def test_export_to_dict(self):
        """Testa conversão para dicionário."""
        export = QLDBJournalExport(export_id="test-export")
        result = export.to_dict()
        assert result["export_id"] == "test-export"


class TestQLDBStreamDataclass:
    """Testes para QLDBStream dataclass."""

    def test_stream_active(self):
        """Testa stream ativo."""
        stream = QLDBStream(stream_id="stream-001", status="ACTIVE")
        assert stream.is_active is True

    def test_stream_completed(self):
        """Testa stream completo."""
        stream = QLDBStream(stream_id="stream-001", status="COMPLETED")
        assert stream.is_completed is True

    def test_stream_canceled(self):
        """Testa stream cancelado."""
        stream = QLDBStream(stream_id="stream-001", status="CANCELED")
        assert stream.is_canceled is True

    def test_stream_failed(self):
        """Testa stream com falha."""
        stream = QLDBStream(stream_id="stream-001", status="FAILED")
        assert stream.is_failed is True

    def test_stream_impaired(self):
        """Testa stream prejudicado."""
        stream = QLDBStream(stream_id="stream-001", status="IMPAIRED")
        assert stream.is_impaired is True

    def test_stream_kinesis(self):
        """Testa stream Kinesis."""
        stream = QLDBStream(
            stream_id="stream-001",
            kinesis_configuration={"StreamArn": "arn:...", "AggregationEnabled": True}
        )
        assert stream.kinesis_stream_arn == "arn:..."
        assert stream.aggregation_enabled is True

    def test_stream_error(self):
        """Testa stream com erro."""
        stream = QLDBStream(stream_id="stream-001", error_cause="Error")
        assert stream.has_error is True

    def test_stream_to_dict(self):
        """Testa conversão para dicionário."""
        stream = QLDBStream(stream_id="test-stream")
        result = stream.to_dict()
        assert result["stream_id"] == "test-stream"


class TestQLDBService:
    """Testes para QLDBService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = QLDBService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_ledgers.return_value = {"Ledgers": []}
        mock_factory.get_client.return_value = mock_client

        service = QLDBService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = QLDBService(mock_factory)
        
        result = service.get_resources()
        
        assert "ledgers" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = QLDBService(mock_factory)
        
        result = service.get_metrics()
        
        assert "ledgers_count" in result


class TestManagedBlockchainNetworkDataclass:
    """Testes para ManagedBlockchainNetwork dataclass."""

    def test_network_available(self):
        """Testa network disponível."""
        net = ManagedBlockchainNetwork(network_id="net-001", status="AVAILABLE")
        assert net.is_available is True
        assert net.is_creating is False

    def test_network_creating(self):
        """Testa network sendo criada."""
        net = ManagedBlockchainNetwork(network_id="net-001", status="CREATING")
        assert net.is_creating is True

    def test_network_deleting(self):
        """Testa network sendo deletada."""
        net = ManagedBlockchainNetwork(network_id="net-001", status="DELETING")
        assert net.is_deleting is True

    def test_network_deleted(self):
        """Testa network deletada."""
        net = ManagedBlockchainNetwork(network_id="net-001", status="DELETED")
        assert net.is_deleted is True

    def test_network_fabric(self):
        """Testa network Fabric."""
        net = ManagedBlockchainNetwork(network_id="net-001", framework="HYPERLEDGER_FABRIC")
        assert net.uses_fabric is True
        assert net.uses_ethereum is False

    def test_network_ethereum(self):
        """Testa network Ethereum."""
        net = ManagedBlockchainNetwork(network_id="net-001", framework="ETHEREUM")
        assert net.uses_ethereum is True

    def test_network_tags(self):
        """Testa network com tags."""
        net = ManagedBlockchainNetwork(network_id="net-001", tags={"env": "prod"})
        assert net.has_tags is True

    def test_network_to_dict(self):
        """Testa conversão para dicionário."""
        net = ManagedBlockchainNetwork(network_id="test-net")
        result = net.to_dict()
        assert result["network_id"] == "test-net"


class TestManagedBlockchainMemberDataclass:
    """Testes para ManagedBlockchainMember dataclass."""

    def test_member_available(self):
        """Testa member disponível."""
        member = ManagedBlockchainMember(member_id="member-001", status="AVAILABLE")
        assert member.is_available is True

    def test_member_creating(self):
        """Testa member sendo criado."""
        member = ManagedBlockchainMember(member_id="member-001", status="CREATING")
        assert member.is_creating is True

    def test_member_deleting(self):
        """Testa member sendo deletado."""
        member = ManagedBlockchainMember(member_id="member-001", status="DELETING")
        assert member.is_deleting is True

    def test_member_deleted(self):
        """Testa member deletado."""
        member = ManagedBlockchainMember(member_id="member-001", status="DELETED")
        assert member.is_deleted is True

    def test_member_updating(self):
        """Testa member atualizando."""
        member = ManagedBlockchainMember(member_id="member-001", status="UPDATING")
        assert member.is_updating is True

    def test_member_encryption(self):
        """Testa member com criptografia."""
        member = ManagedBlockchainMember(member_id="member-001", kms_key_arn="arn:...")
        assert member.has_encryption is True

    def test_member_logging(self):
        """Testa member com logging."""
        member = ManagedBlockchainMember(
            member_id="member-001",
            log_publishing_configuration={"Fabric": {}}
        )
        assert member.has_logging is True

    def test_member_to_dict(self):
        """Testa conversão para dicionário."""
        member = ManagedBlockchainMember(member_id="test-member")
        result = member.to_dict()
        assert result["member_id"] == "test-member"


class TestManagedBlockchainNodeDataclass:
    """Testes para ManagedBlockchainNode dataclass."""

    def test_node_available(self):
        """Testa node disponível."""
        node = ManagedBlockchainNode(node_id="node-001", status="AVAILABLE")
        assert node.is_available is True

    def test_node_creating(self):
        """Testa node sendo criado."""
        node = ManagedBlockchainNode(node_id="node-001", status="CREATING")
        assert node.is_creating is True

    def test_node_deleting(self):
        """Testa node sendo deletado."""
        node = ManagedBlockchainNode(node_id="node-001", status="DELETING")
        assert node.is_deleting is True

    def test_node_deleted(self):
        """Testa node deletado."""
        node = ManagedBlockchainNode(node_id="node-001", status="DELETED")
        assert node.is_deleted is True

    def test_node_updating(self):
        """Testa node atualizando."""
        node = ManagedBlockchainNode(node_id="node-001", status="UPDATING")
        assert node.is_updating is True

    def test_node_failed(self):
        """Testa node com falha."""
        node = ManagedBlockchainNode(node_id="node-001", status="FAILED")
        assert node.is_failed is True

    def test_node_level_db(self):
        """Testa node com LevelDB."""
        node = ManagedBlockchainNode(node_id="node-001", state_db="LevelDB")
        assert node.uses_level_db is True

    def test_node_couch_db(self):
        """Testa node com CouchDB."""
        node = ManagedBlockchainNode(node_id="node-001", state_db="CouchDB")
        assert node.uses_couch_db is True

    def test_node_encryption(self):
        """Testa node com criptografia."""
        node = ManagedBlockchainNode(node_id="node-001", kms_key_arn="arn:...")
        assert node.has_encryption is True

    def test_node_to_dict(self):
        """Testa conversão para dicionário."""
        node = ManagedBlockchainNode(node_id="test-node")
        result = node.to_dict()
        assert result["node_id"] == "test-node"


class TestManagedBlockchainService:
    """Testes para ManagedBlockchainService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = ManagedBlockchainService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_networks.return_value = {"Networks": []}
        mock_factory.get_client.return_value = mock_client

        service = ManagedBlockchainService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = ManagedBlockchainService(mock_factory)
        
        result = service.get_resources()
        
        assert "networks" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = ManagedBlockchainService(mock_factory)
        
        result = service.get_metrics()
        
        assert "networks_count" in result


class TestBraketQuantumTaskDataclass:
    """Testes para BraketQuantumTask dataclass."""

    def test_task_created(self):
        """Testa task criada."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", status="CREATED")
        assert task.is_created is True

    def test_task_queued(self):
        """Testa task na fila."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", status="QUEUED")
        assert task.is_queued is True

    def test_task_running(self):
        """Testa task rodando."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", status="RUNNING")
        assert task.is_running is True

    def test_task_completed(self):
        """Testa task completa."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", status="COMPLETED")
        assert task.is_completed is True

    def test_task_failed(self):
        """Testa task com falha."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", status="FAILED")
        assert task.is_failed is True

    def test_task_cancelling(self):
        """Testa task cancelando."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", status="CANCELLING")
        assert task.is_cancelling is True

    def test_task_cancelled(self):
        """Testa task cancelada."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", status="CANCELLED")
        assert task.is_cancelled is True

    def test_task_failure(self):
        """Testa task com falha."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", failure_reason="Error")
        assert task.has_failure is True

    def test_task_ionq(self):
        """Testa task IonQ."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", device_arn="arn:...ionq...")
        assert task.uses_ionq is True

    def test_task_rigetti(self):
        """Testa task Rigetti."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", device_arn="arn:...rigetti...")
        assert task.uses_rigetti is True

    def test_task_simulator(self):
        """Testa task simulador."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", device_arn="arn:...simulator...")
        assert task.uses_simulator is True

    def test_task_dwave(self):
        """Testa task D-Wave."""
        task = BraketQuantumTask(quantum_task_arn="arn:...", device_arn="arn:...d-wave...")
        assert task.uses_dwave is True

    def test_task_cost(self):
        """Testa custo da task."""
        sim_task = BraketQuantumTask(quantum_task_arn="arn:...", device_arn="arn:...simulator...", shots=100)
        ionq_task = BraketQuantumTask(quantum_task_arn="arn:...", device_arn="arn:...ionq...", shots=100)
        assert sim_task.estimated_cost < ionq_task.estimated_cost

    def test_task_to_dict(self):
        """Testa conversão para dicionário."""
        task = BraketQuantumTask(quantum_task_arn="test-arn")
        result = task.to_dict()
        assert result["quantum_task_arn"] == "test-arn"


class TestBraketJobDataclass:
    """Testes para BraketJob dataclass."""

    def test_job_created(self):
        """Testa job criado."""
        job = BraketJob(job_arn="arn:...", status="CREATED")
        assert job.is_created is True

    def test_job_queued(self):
        """Testa job na fila."""
        job = BraketJob(job_arn="arn:...", status="QUEUED")
        assert job.is_queued is True

    def test_job_running(self):
        """Testa job rodando."""
        job = BraketJob(job_arn="arn:...", status="RUNNING")
        assert job.is_running is True

    def test_job_completed(self):
        """Testa job completo."""
        job = BraketJob(job_arn="arn:...", status="COMPLETED")
        assert job.is_completed is True

    def test_job_failed(self):
        """Testa job com falha."""
        job = BraketJob(job_arn="arn:...", status="FAILED")
        assert job.is_failed is True

    def test_job_cancelling(self):
        """Testa job cancelando."""
        job = BraketJob(job_arn="arn:...", status="CANCELLING")
        assert job.is_cancelling is True

    def test_job_cancelled(self):
        """Testa job cancelado."""
        job = BraketJob(job_arn="arn:...", status="CANCELLED")
        assert job.is_cancelled is True

    def test_job_failure(self):
        """Testa job com falha."""
        job = BraketJob(job_arn="arn:...", failure_reason="Error")
        assert job.has_failure is True

    def test_job_instance(self):
        """Testa instância do job."""
        job = BraketJob(
            job_arn="arn:...",
            instance_config={"instanceType": "ml.m5.large", "instanceCount": 2, "volumeSizeInGb": 50}
        )
        assert job.instance_type == "ml.m5.large"
        assert job.instance_count == 2
        assert job.volume_size_gb == 50

    def test_job_billable(self):
        """Testa horas faturáveis."""
        job = BraketJob(job_arn="arn:...", billable_duration=3600)
        assert job.billable_hours == pytest.approx(1.0)

    def test_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = BraketJob(job_arn="test-arn")
        result = job.to_dict()
        assert result["job_arn"] == "test-arn"


class TestBraketService:
    """Testes para BraketService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = BraketService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.search_quantum_tasks.return_value = {"quantumTasks": []}
        mock_factory.get_client.return_value = mock_client

        service = BraketService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = BraketService(mock_factory)
        
        result = service.get_resources()
        
        assert "quantum_tasks" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = BraketService(mock_factory)
        
        result = service.get_metrics()
        
        assert "quantum_tasks_count" in result


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""

    def test_factory_get_qldb_service(self):
        """Testa obtenção do QLDBService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_qldb_service()
        
        assert isinstance(service, QLDBService)

    def test_factory_get_managedblockchain_service(self):
        """Testa obtenção do ManagedBlockchainService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_managedblockchain_service()
        
        assert isinstance(service, ManagedBlockchainService)

    def test_factory_get_braket_service(self):
        """Testa obtenção do BraketService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_braket_service()
        
        assert isinstance(service, BraketService)

    def test_factory_get_all_services_includes_blockchain(self):
        """Testa que get_all_services inclui serviços de Blockchain & Quantum."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        services = factory.get_all_services()
        
        assert 'qldb' in services
        assert 'managedblockchain' in services
        assert 'braket' in services
