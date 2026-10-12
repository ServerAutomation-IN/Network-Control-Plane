"""Provider Factory & Registry — Network Control Plane

Dynamically resolves and instantiates standard BaseProviderAdapter runtime implementations
(DockerAdapter, PodmanAdapter, KubernetesAdapter, AWSAdapter, AzureAdapter, GCPAdapter, VMwareAdapter, NutanixAdapter, HyperVAdapter) based on host configuration and provider_type.
"""

from typing import Dict, Any, Type, Optional
from app.providers.base import BaseProviderAdapter


class ProviderFactory:
    """Factory resolving runtime provider adapters for managed infrastructure hosts."""

    _registry: Dict[str, Type[BaseProviderAdapter]] = {}

    @classmethod
    def register_provider(cls, name: str, adapter_cls: Type[BaseProviderAdapter]) -> None:
        """Register a new custom provider adapter class dynamically."""
        cls._registry[name.lower()] = adapter_cls

    @classmethod
    def get_adapter(
        cls,
        provider_type: str = "docker",
        endpoint: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseProviderAdapter:
        """Resolve and instantiate standard provider adapter instance.
        
        Args:
            provider_type: Provider identifier ('docker', 'podman', 'kubernetes', 'openshift', 'aws', 'azure', 'gcp', 'vmware', 'nutanix', 'hyperv').
            endpoint: Optional runtime socket or API server endpoint URL.
        """
        ptype = (provider_type or "docker").lower()

        if ptype in cls._registry:
            return cls._registry[ptype]()

        if ptype == "podman":
            from app.podman.adapter import PodmanAdapter
            return PodmanAdapter(base_url=endpoint or "unix:///run/podman/podman.sock")
        elif ptype in ("kubernetes", "openshift"):
            from app.kubernetes.adapter import KubernetesAdapter
            return KubernetesAdapter(kubeconfig_path=endpoint)
        elif ptype == "aws":
            from app.cloud.aws.adapter import AWSAdapter
            return AWSAdapter(region_name=endpoint or "us-east-1")
        elif ptype == "azure":
            from app.cloud.azure.adapter import AzureAdapter
            return AzureAdapter(subscription_id=endpoint)
        elif ptype == "gcp":
            from app.cloud.gcp.adapter import GCPAdapter
            return GCPAdapter(project_id=endpoint)
        elif ptype in ("vmware", "vsphere"):
            from app.cloud.vmware.adapter import VMwareAdapter
            return VMwareAdapter(vcenter_host=endpoint)
        elif ptype in ("nutanix", "ahv"):
            from app.cloud.nutanix.adapter import NutanixAdapter
            return NutanixAdapter(prism_host=endpoint)
        elif ptype in ("hyperv", "hyper-v", "scvmm"):
            from app.cloud.hyperv.adapter import HyperVAdapter
            return HyperVAdapter(hyperv_host=endpoint)

        # Default fallback to DockerAdapter
        from app.docker.adapter import DockerAdapter
        return DockerAdapter(base_url=endpoint or "unix:///var/run/docker.sock")
