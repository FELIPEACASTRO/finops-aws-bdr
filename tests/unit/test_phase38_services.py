"""
Testes unitários para FASE 3.8 - Game & Robotics Services.

GameLift, RoboMaker.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.finops_aws.services.gamelift_service import (
    GameLiftService, GameLiftFleet, GameLiftBuild, GameLiftGameSession
)
from src.finops_aws.services.robomaker_service import (
    RoboMakerService, RoboMakerRobotApplication, RoboMakerSimulationApplication,
    RoboMakerSimulationJob, RoboMakerWorldGenerationJob
)
from src.finops_aws.core.factories import ServiceFactory


class TestGameLiftFleetDataclass:
    """Testes para GameLiftFleet dataclass."""

    def test_fleet_active(self):
        """Testa fleet ativo."""
        fleet = GameLiftFleet(fleet_id="fleet-001", status="ACTIVE")
        assert fleet.is_active is True
        assert fleet.is_new is False

    def test_fleet_new(self):
        """Testa fleet novo."""
        fleet = GameLiftFleet(fleet_id="fleet-001", status="NEW")
        assert fleet.is_new is True

    def test_fleet_building(self):
        """Testa fleet em construção."""
        fleet = GameLiftFleet(fleet_id="fleet-001", status="BUILDING")
        assert fleet.is_building is True

    def test_fleet_downloading(self):
        """Testa fleet baixando."""
        fleet = GameLiftFleet(fleet_id="fleet-001", status="DOWNLOADING")
        assert fleet.is_downloading is True

    def test_fleet_validating(self):
        """Testa fleet validando."""
        fleet = GameLiftFleet(fleet_id="fleet-001", status="VALIDATING")
        assert fleet.is_validating is True

    def test_fleet_activating(self):
        """Testa fleet ativando."""
        fleet = GameLiftFleet(fleet_id="fleet-001", status="ACTIVATING")
        assert fleet.is_activating is True

    def test_fleet_terminated(self):
        """Testa fleet terminado."""
        fleet = GameLiftFleet(fleet_id="fleet-001", status="TERMINATED")
        assert fleet.is_terminated is True

    def test_fleet_error(self):
        """Testa fleet em erro."""
        fleet = GameLiftFleet(fleet_id="fleet-001", status="ERROR")
        assert fleet.is_error is True

    def test_fleet_on_demand(self):
        """Testa fleet on-demand."""
        fleet = GameLiftFleet(fleet_id="fleet-001", fleet_type="ON_DEMAND")
        assert fleet.is_on_demand is True
        assert fleet.is_spot is False

    def test_fleet_spot(self):
        """Testa fleet spot."""
        fleet = GameLiftFleet(fleet_id="fleet-001", fleet_type="SPOT")
        assert fleet.is_spot is True

    def test_fleet_uses_build(self):
        """Testa fleet com build."""
        fleet = GameLiftFleet(fleet_id="fleet-001", build_id="build-001")
        assert fleet.uses_build is True
        assert fleet.uses_script is False

    def test_fleet_uses_script(self):
        """Testa fleet com script."""
        fleet = GameLiftFleet(fleet_id="fleet-001", script_id="script-001")
        assert fleet.uses_script is True

    def test_fleet_ec2(self):
        """Testa fleet EC2."""
        fleet = GameLiftFleet(fleet_id="fleet-001", compute_type="EC2")
        assert fleet.is_ec2 is True
        assert fleet.is_anywhere is False

    def test_fleet_anywhere(self):
        """Testa fleet Anywhere."""
        fleet = GameLiftFleet(fleet_id="fleet-001", compute_type="ANYWHERE")
        assert fleet.is_anywhere is True

    def test_fleet_protection(self):
        """Testa fleet com proteção."""
        fleet = GameLiftFleet(fleet_id="fleet-001", new_game_session_protection_policy="FullProtection")
        assert fleet.has_protection is True

    def test_fleet_windows(self):
        """Testa fleet Windows."""
        fleet = GameLiftFleet(fleet_id="fleet-001", operating_system="WINDOWS_2012")
        assert fleet.is_windows is True

    def test_fleet_linux(self):
        """Testa fleet Linux."""
        fleet = GameLiftFleet(fleet_id="fleet-001", operating_system="AMAZON_LINUX_2")
        assert fleet.is_linux is True

    def test_fleet_cost(self):
        """Testa custo da fleet."""
        fleet_on_demand = GameLiftFleet(fleet_id="fleet-001", fleet_type="ON_DEMAND", instance_type="c5.large")
        fleet_spot = GameLiftFleet(fleet_id="fleet-002", fleet_type="SPOT", instance_type="c5.large")
        assert fleet_on_demand.estimated_hourly_cost > fleet_spot.estimated_hourly_cost

    def test_fleet_to_dict(self):
        """Testa conversão para dicionário."""
        fleet = GameLiftFleet(fleet_id="test-fleet")
        result = fleet.to_dict()
        assert result["fleet_id"] == "test-fleet"


class TestGameLiftBuildDataclass:
    """Testes para GameLiftBuild dataclass."""

    def test_build_ready(self):
        """Testa build pronto."""
        build = GameLiftBuild(build_id="build-001", status="READY")
        assert build.is_ready is True
        assert build.is_initialized is False

    def test_build_initialized(self):
        """Testa build inicializado."""
        build = GameLiftBuild(build_id="build-001", status="INITIALIZED")
        assert build.is_initialized is True

    def test_build_failed(self):
        """Testa build com falha."""
        build = GameLiftBuild(build_id="build-001", status="FAILED")
        assert build.is_failed is True

    def test_build_size(self):
        """Testa tamanho do build."""
        build = GameLiftBuild(build_id="build-001", size_on_disk=1073741824)
        assert build.size_gb == pytest.approx(1.0)

    def test_build_windows(self):
        """Testa build Windows."""
        build = GameLiftBuild(build_id="build-001", operating_system="WINDOWS_2012")
        assert build.is_windows is True

    def test_build_to_dict(self):
        """Testa conversão para dicionário."""
        build = GameLiftBuild(build_id="test-build")
        result = build.to_dict()
        assert result["build_id"] == "test-build"


class TestGameLiftGameSessionDataclass:
    """Testes para GameLiftGameSession dataclass."""

    def test_session_active(self):
        """Testa sessão ativa."""
        session = GameLiftGameSession(game_session_id="session-001", status="ACTIVE")
        assert session.is_active is True

    def test_session_activating(self):
        """Testa sessão ativando."""
        session = GameLiftGameSession(game_session_id="session-001", status="ACTIVATING")
        assert session.is_activating is True

    def test_session_terminated(self):
        """Testa sessão terminada."""
        session = GameLiftGameSession(game_session_id="session-001", status="TERMINATED")
        assert session.is_terminated is True

    def test_session_terminating(self):
        """Testa sessão terminando."""
        session = GameLiftGameSession(game_session_id="session-001", status="TERMINATING")
        assert session.is_terminating is True

    def test_session_error(self):
        """Testa sessão em erro."""
        session = GameLiftGameSession(game_session_id="session-001", status="ERROR")
        assert session.is_error is True

    def test_session_players(self):
        """Testa contagem de jogadores."""
        session = GameLiftGameSession(
            game_session_id="session-001",
            current_player_session_count=5,
            maximum_player_session_count=10
        )
        assert session.player_count == 5
        assert session.max_players == 10
        assert session.is_full is False
        assert session.availability_percentage == pytest.approx(50.0)

    def test_session_full(self):
        """Testa sessão cheia."""
        session = GameLiftGameSession(
            game_session_id="session-001",
            current_player_session_count=10,
            maximum_player_session_count=10
        )
        assert session.is_full is True

    def test_session_to_dict(self):
        """Testa conversão para dicionário."""
        session = GameLiftGameSession(game_session_id="test-session")
        result = session.to_dict()
        assert result["game_session_id"] == "test-session"


class TestGameLiftService:
    """Testes para GameLiftService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = GameLiftService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_fleets.return_value = {"FleetIds": []}
        mock_factory.get_client.return_value = mock_client

        service = GameLiftService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = GameLiftService(mock_factory)
        
        result = service.get_resources()
        
        assert "fleets" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = GameLiftService(mock_factory)
        
        result = service.get_metrics()
        
        assert "fleets_count" in result


class TestRoboMakerRobotApplicationDataclass:
    """Testes para RoboMakerRobotApplication dataclass."""

    def test_app_ros(self):
        """Testa app ROS."""
        app = RoboMakerRobotApplication(
            name="app-001",
            robot_software_suite={"name": "ROS", "version": "Melodic"}
        )
        assert app.uses_ros is True
        assert app.uses_ros2 is False
        assert app.ros_version == "Melodic"

    def test_app_ros2(self):
        """Testa app ROS2."""
        app = RoboMakerRobotApplication(
            name="app-001",
            robot_software_suite={"name": "ROS2", "version": "Foxy"}
        )
        assert app.uses_ros2 is True

    def test_app_version(self):
        """Testa versão do app."""
        app = RoboMakerRobotApplication(name="app-001", version="1.0")
        assert app.has_version is True

    def test_app_to_dict(self):
        """Testa conversão para dicionário."""
        app = RoboMakerRobotApplication(name="test-app")
        result = app.to_dict()
        assert result["name"] == "test-app"


class TestRoboMakerSimulationApplicationDataclass:
    """Testes para RoboMakerSimulationApplication dataclass."""

    def test_sim_app_ros(self):
        """Testa sim app ROS."""
        app = RoboMakerSimulationApplication(
            name="sim-001",
            robot_software_suite={"name": "ROS"}
        )
        assert app.uses_ros is True

    def test_sim_app_gazebo(self):
        """Testa sim app Gazebo."""
        app = RoboMakerSimulationApplication(
            name="sim-001",
            simulation_software_suite={"name": "Gazebo"}
        )
        assert app.uses_gazebo is True
        assert app.simulation_engine == "Gazebo"

    def test_sim_app_worldforge(self):
        """Testa sim app WorldForge."""
        app = RoboMakerSimulationApplication(
            name="sim-001",
            simulation_software_suite={"name": "WorldForge"}
        )
        assert app.uses_worldforge is True

    def test_sim_app_ogre(self):
        """Testa sim app OGRE."""
        app = RoboMakerSimulationApplication(
            name="sim-001",
            rendering_engine={"name": "OGRE"}
        )
        assert app.uses_ogre is True
        assert app.renderer == "OGRE"

    def test_sim_app_to_dict(self):
        """Testa conversão para dicionário."""
        app = RoboMakerSimulationApplication(name="test-sim")
        result = app.to_dict()
        assert result["name"] == "test-sim"


class TestRoboMakerSimulationJobDataclass:
    """Testes para RoboMakerSimulationJob dataclass."""

    def test_job_pending(self):
        """Testa job pendente."""
        job = RoboMakerSimulationJob(arn="arn:...", status="Pending")
        assert job.is_pending is True

    def test_job_preparing(self):
        """Testa job preparando."""
        job = RoboMakerSimulationJob(arn="arn:...", status="Preparing")
        assert job.is_preparing is True

    def test_job_running(self):
        """Testa job rodando."""
        job = RoboMakerSimulationJob(arn="arn:...", status="Running")
        assert job.is_running is True

    def test_job_restarting(self):
        """Testa job reiniciando."""
        job = RoboMakerSimulationJob(arn="arn:...", status="Restarting")
        assert job.is_restarting is True

    def test_job_completed(self):
        """Testa job completo."""
        job = RoboMakerSimulationJob(arn="arn:...", status="Completed")
        assert job.is_completed is True

    def test_job_failed(self):
        """Testa job com falha."""
        job = RoboMakerSimulationJob(arn="arn:...", status="Failed")
        assert job.is_failed is True

    def test_job_terminated(self):
        """Testa job terminado."""
        job = RoboMakerSimulationJob(arn="arn:...", status="Terminated")
        assert job.is_terminated is True

    def test_job_terminating(self):
        """Testa job terminando."""
        job = RoboMakerSimulationJob(arn="arn:...", status="Terminating")
        assert job.is_terminating is True

    def test_job_canceled(self):
        """Testa job cancelado."""
        job = RoboMakerSimulationJob(arn="arn:...", status="Canceled")
        assert job.is_canceled is True

    def test_job_time(self):
        """Testa tempo de simulação."""
        job = RoboMakerSimulationJob(arn="arn:...", simulation_time_millis=3600000)
        assert job.simulation_time_seconds == pytest.approx(3600.0)
        assert job.simulation_time_hours == pytest.approx(1.0)

    def test_job_failure(self):
        """Testa falha."""
        job = RoboMakerSimulationJob(arn="arn:...", failure_code="Error")
        assert job.has_failure is True

    def test_job_failure_behavior(self):
        """Testa comportamento de falha."""
        job_fail = RoboMakerSimulationJob(arn="arn:...", failure_behavior="Fail")
        job_continue = RoboMakerSimulationJob(arn="arn:...", failure_behavior="Continue")
        assert job_fail.fails_on_error is True
        assert job_continue.continues_on_error is True

    def test_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = RoboMakerSimulationJob(arn="test-arn")
        result = job.to_dict()
        assert result["arn"] == "test-arn"


class TestRoboMakerWorldGenerationJobDataclass:
    """Testes para RoboMakerWorldGenerationJob dataclass."""

    def test_world_job_pending(self):
        """Testa world job pendente."""
        job = RoboMakerWorldGenerationJob(arn="arn:...", status="Pending")
        assert job.is_pending is True

    def test_world_job_running(self):
        """Testa world job rodando."""
        job = RoboMakerWorldGenerationJob(arn="arn:...", status="Running")
        assert job.is_running is True

    def test_world_job_completed(self):
        """Testa world job completo."""
        job = RoboMakerWorldGenerationJob(arn="arn:...", status="Completed")
        assert job.is_completed is True

    def test_world_job_failed(self):
        """Testa world job com falha."""
        job = RoboMakerWorldGenerationJob(arn="arn:...", status="Failed")
        assert job.is_failed is True

    def test_world_job_partial_failed(self):
        """Testa world job com falha parcial."""
        job = RoboMakerWorldGenerationJob(arn="arn:...", status="PartialFailed")
        assert job.is_partial_failed is True

    def test_world_job_canceled(self):
        """Testa world job cancelado."""
        job = RoboMakerWorldGenerationJob(arn="arn:...", status="Canceled")
        assert job.is_canceled is True

    def test_world_job_canceling(self):
        """Testa world job cancelando."""
        job = RoboMakerWorldGenerationJob(arn="arn:...", status="Canceling")
        assert job.is_canceling is True

    def test_world_job_worlds(self):
        """Testa mundos."""
        job = RoboMakerWorldGenerationJob(
            arn="arn:...",
            finished_worlds_summary={"succeededWorldCount": 5, "failedWorldCount": 1}
        )
        assert job.succeeded_worlds == 5
        assert job.failed_worlds == 1

    def test_world_job_failure(self):
        """Testa falha."""
        job = RoboMakerWorldGenerationJob(arn="arn:...", failure_code="Error")
        assert job.has_failure is True

    def test_world_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = RoboMakerWorldGenerationJob(arn="test-arn")
        result = job.to_dict()
        assert result["arn"] == "test-arn"


class TestRoboMakerService:
    """Testes para RoboMakerService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = RoboMakerService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_robots.return_value = {"robots": []}
        mock_factory.get_client.return_value = mock_client

        service = RoboMakerService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = RoboMakerService(mock_factory)
        
        result = service.get_resources()
        
        assert "robot_applications" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = RoboMakerService(mock_factory)
        
        result = service.get_metrics()
        
        assert "robot_applications_count" in result


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""

    def test_factory_get_gamelift_service(self):
        """Testa obtenção do GameLiftService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_gamelift_service()
        
        assert isinstance(service, GameLiftService)

    def test_factory_get_robomaker_service(self):
        """Testa obtenção do RoboMakerService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_robomaker_service()
        
        assert isinstance(service, RoboMakerService)

    def test_factory_get_all_services_includes_game(self):
        """Testa que get_all_services inclui serviços de Game & Robotics."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        services = factory.get_all_services()
        
        assert 'gamelift' in services
        assert 'robomaker' in services
