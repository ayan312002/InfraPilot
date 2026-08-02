from pathlib import Path

import yaml

from engine.generators.base_generator import BaseGenerator
from engine.models.provisioning_spec import ProvisioningSpec
from engine.models.service_spec import ServiceSpec


class ComposeGenerator(BaseGenerator):

    def generate(self, spec: ProvisioningSpec) -> str:
        """
        Convert a ProvisioningSpec into a docker-compose YAML string.
        """

        compose = {
            "name": "demo",
            "services": {}
        }

        for service in spec.services:
            compose["services"][service.name] = self._build_service(service)

        return self._dump_yaml(compose)

    def _build_service(self, service: ServiceSpec) -> dict:
        """
        Convert a ServiceSpec into a Docker Compose service dictionary.
        """

        service_dict = {}

        if service.image:
            service_dict["image"] = service.image

        if service.ports:
            service_dict["ports"] = service.ports

        if service.environment:
            service_dict["environment"] = service.environment

        if service.volumes:
            service_dict["volumes"] = service.volumes

        if service.depends_on:
            service_dict["depends_on"] = service.depends_on

        if service.container_name:
            service_dict["container_name"] = service.container_name

        return service_dict

    def _dump_yaml(self, data: dict) -> str:
        """
        Convert a Python dictionary into YAML.
        """

        return yaml.dump(
            data,
            sort_keys=False,
            default_flow_style=False
        )

    def save(self, yaml_content: str, output_path: str) -> None:
        """
        Save generated YAML to disk.
        """

        file_path = Path(output_path)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(yaml_content)

        return output_path