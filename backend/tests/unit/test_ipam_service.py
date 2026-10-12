"""Unit Tests for IPAM Math & CIDR Calculators — Network Control Plane"""

import pytest
from app.services.ipam import IPAMCalculator, IPAMService
from app.schemas.ipam import IPAMValidationRequest


def test_ipam_calculator_parse_info():
    """Verify CIDR subnet parsing returns network, broadcast, and total usable host counts."""
    info = IPAMCalculator.parse_subnet_info("172.20.0.0/16")
    assert info["valid"] is True
    assert info["network_address"] == "172.20.0.0"
    assert info["broadcast_address"] == "172.20.255.255"
    assert info["total_ips"] == 65536
    assert info["usable_ips"] == 65534


def test_ipam_calculator_utilization():
    """Verify IP utilization calculation percentage."""
    util = IPAMCalculator.calculate_utilization("192.168.1.0/24", 25)
    assert util["total_ips"] == 256
    assert util["usable_ips"] == 254
    assert util["allocated_ips"] == 25
    assert util["utilization_percentage"] == 9.84


def test_ipam_subnet_overlap_detection():
    """Verify overlapping CIDR subnet detection."""
    # 172.18.0.0/16 and 172.18.5.0/24 overlap
    assert IPAMCalculator.check_subnet_overlap("172.18.0.0/16", "172.18.5.0/24") is True
    # 10.0.0.0/16 and 192.168.1.0/24 do not overlap
    assert IPAMCalculator.check_subnet_overlap("10.0.0.0/16", "192.168.1.0/24") is False


def test_ipam_validation_service():
    """Verify IPAM validation service rules for requested IP containment."""
    ipam_service = IPAMService(None)  # type: ignore

    # Valid IP inside subnet
    res1 = ipam_service.validate_allocation(IPAMValidationRequest(subnet="10.10.0.0/16", requested_ip="10.10.2.15"))
    assert res1.is_valid is True
    assert res1.is_ip_in_subnet is True
    assert res1.is_ip_reserved is False

    # IP outside subnet
    res2 = ipam_service.validate_allocation(IPAMValidationRequest(subnet="10.10.0.0/16", requested_ip="192.168.1.1"))
    assert res2.is_valid is False
    assert res2.is_ip_in_subnet is False

    # Reserved network address
    res3 = ipam_service.validate_allocation(IPAMValidationRequest(subnet="10.10.0.0/16", requested_ip="10.10.0.0"))
    assert res3.is_valid is False
    assert res3.is_ip_reserved is True
