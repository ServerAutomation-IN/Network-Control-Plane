# ADR-003: Provider Adapter and Host Agent Architecture

## Context
The platform must manage multi-host container infrastructure without requiring direct socket exposure across public/untrusted networks.

## Decision
Introduce a provider host agent (`network-control-plane-agent`) for remote multi-host setups, communicating with the central control plane via secure TLS/gRPC or HTTPS protocols.

## Rationale
Prevents direct exposure of Docker Unix sockets over TCP and enables isolated event monitoring on remote provider hosts.
