"""Unit Tests for Provider Factory — Network Control Plane"""

import pytest
from app.providers.factory import ProviderFactory
from app.docker.adapter import DockerAdapter
from app.podman.adapter import PodmanAdapter
from app.kubernetes.adapter import KubernetesAdapter
from app.cloud.aws.adapter import AWSAdapter
from app.cloud.azure.adapter import AzureAdapter
from app.cloud.gcp.adapter import GCPAdapter
from app.cloud.vmware.adapter import VMwareAdapter
from app.cloud.nutanix.adapter import NutanixAdapter
from app.cloud.hyperv.adapter import HyperVAdapter


def test_provider_factory_resolution():
    """Test ProviderFactory resolves appropriate adapter class per provider type."""
    docker_adapter = ProviderFactory.get_adapter(provider_type="docker")
    assert isinstance(docker_adapter, DockerAdapter)

    podman_adapter = ProviderFactory.get_adapter(provider_type="podman")
    assert isinstance(podman_adapter, PodmanAdapter)

    k8s_adapter = ProviderFactory.get_adapter(provider_type="kubernetes")
    assert isinstance(k8s_adapter, KubernetesAdapter)

    openshift_adapter = ProviderFactory.get_adapter(provider_type="openshift")
    assert isinstance(openshift_adapter, KubernetesAdapter)

    aws_adapter = ProviderFactory.get_adapter(provider_type="aws")
    assert isinstance(aws_adapter, AWSAdapter)

    azure_adapter = ProviderFactory.get_adapter(provider_type="azure")
    assert isinstance(azure_adapter, AzureAdapter)

    gcp_adapter = ProviderFactory.get_adapter(provider_type="gcp")
    assert isinstance(gcp_adapter, GCPAdapter)

    vmware_adapter = ProviderFactory.get_adapter(provider_type="vmware")
    assert isinstance(vmware_adapter, VMwareAdapter)

    nutanix_adapter = ProviderFactory.get_adapter(provider_type="nutanix")
    assert isinstance(nutanix_adapter, NutanixAdapter)

    hyperv_adapter = ProviderFactory.get_adapter(provider_type="hyperv")
    assert isinstance(hyperv_adapter, HyperVAdapter)


def test_provider_factory_fallback():
    """Test ProviderFactory falls back safely to DockerAdapter for unrecognized provider."""
    fallback_adapter = ProviderFactory.get_adapter(provider_type="unsupported_runtime")
    assert isinstance(fallback_adapter, DockerAdapter)
