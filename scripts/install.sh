#!/usr/bin/env bash
# ==============================================================================
# Network Control Plane — Edge Host Agent Automated Installer (Linux)
# Product: Network Control Plane
# ==============================================================================

set -euo pipefail

CONTROL_PLANE=""
TOKEN=""
RUNTIME="auto"

print_banner() {
    echo "=================================================================="
    echo "   Network Control Plane — Remote Host Agent Installer"
    echo "=================================================================="
}

print_help() {
    echo "Usage: curl -sSL <CONTROL_PLANE_URL>/install.sh | sudo bash -s -- [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --control-plane, -c  URL of the central Network Control Plane API (Required)"
    echo "  --token, -t          One-time ephemeral bootstrap token (Required)"
    echo "  --runtime, -r        Target runtime engine (auto, docker, podman, linux) [default: auto]"
    echo "  --help, -h           Show this help message and exit"
    echo ""
}

# Parse command line flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --control-plane|-c)
            CONTROL_PLANE="${2:-}"
            shift 2
            ;;
        --token|-t)
            TOKEN="${2:-}"
            shift 2
            ;;
        --runtime|-r)
            RUNTIME="${2:-auto}"
            shift 2
            ;;
        --help|-h)
            print_banner
            print_help
            exit 0
            ;;
        *)
            echo "[-] Unknown parameter: $1"
            print_help
            exit 1
            ;;
    esac
done

print_banner

if [[ -z "${CONTROL_PLANE}" ]]; then
    echo "[-] Error: --control-plane URL is required."
    exit 1
fi

if [[ -z "${TOKEN}" ]]; then
    echo "[-] Error: --token is required."
    exit 1
fi

CONTROL_PLANE="${CONTROL_PLANE%/}"

echo "[*] Detecting host environment..."
OS_NAME="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
HOSTNAME_VAL="$(hostname -f 2>/dev/null || hostname 2>/dev/null || echo 'linux-host')"

echo "    Host: ${HOSTNAME_VAL} (${ARCH})"

# Auto-detect runtime if set to auto
DETECTED_RUNTIME="${RUNTIME}"
if [[ "${DETECTED_RUNTIME}" == "auto" ]]; then
    if command -v docker >/dev/null 2>&1 && (docker info >/dev/null 2>&1 || [[ -e /var/run/docker.sock ]]); then
        DETECTED_RUNTIME="docker"
    elif command -v podman >/dev/null 2>&1 || [[ -e /run/podman/podman.sock ]]; then
        DETECTED_RUNTIME="podman"
    else
        DETECTED_RUNTIME="linux"
    fi
fi
echo "    Target Runtime: ${DETECTED_RUNTIME}"

echo "[*] Enrolling host with Network Control Plane at ${CONTROL_PLANE}..."

ENROLL_PAYLOAD=$(cat <<EOF
{
  "bootstrap_token": "${TOKEN}",
  "hostname": "${HOSTNAME_VAL}",
  "provider_type": "${DETECTED_RUNTIME}",
  "os": "${OS_NAME}",
  "architecture": "${ARCH}",
  "environment": "production"
}
EOF
)

ENROLL_URL="${CONTROL_PLANE}/api/v1/agent/enroll"
HTTP_RESPONSE=$(curl -sS -w "\n%{http_code}" -X POST "${ENROLL_URL}" \
    -H "Content-Type: application/json" \
    -d "${ENROLL_PAYLOAD}" || {
        echo "[-] Error: Failed to connect to ${ENROLL_URL}"
        exit 1
    })

HTTP_BODY=$(echo "${HTTP_RESPONSE}" | sed '$d')
HTTP_STATUS=$(echo "${HTTP_RESPONSE}" | tail -n1)

if [[ "${HTTP_STATUS}" -ne 200 && "${HTTP_STATUS}" -ne 201 ]]; then
    echo "[-] Enrollment failed (HTTP ${HTTP_STATUS}):"
    echo "${HTTP_BODY}"
    exit 1
fi

# Extract credentials using Python or fallback parsing
HOST_ID=$(echo "${HTTP_BODY}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('host_id', ''))" 2>/dev/null || \
          echo "${HTTP_BODY}" | grep -o '"host_id":"[^"]*' | cut -d'"' -f4)
API_TOKEN=$(echo "${HTTP_BODY}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('api_token', ''))" 2>/dev/null || \
            echo "${HTTP_BODY}" | grep -o '"api_token":"[^"]*' | cut -d'"' -f4)

if [[ -z "${HOST_ID}" ]]; then
    echo "[-] Error: Could not parse host_id from enrollment response."
    echo "${HTTP_BODY}"
    exit 1
fi

echo "[✓] Successfully enrolled! Assigned Host ID: ${HOST_ID}"

# Prepare local agent configuration directory
CONFIG_DIR="/etc/network-control-plane-agent"
mkdir -p "${CONFIG_DIR}"

cat <<EOF > "${CONFIG_DIR}/agent.env"
# Network Control Plane Agent Environment Configuration
HOST_ID=${HOST_ID}
CONTROL_PLANE_URL=${CONTROL_PLANE}
API_TOKEN=${API_TOKEN}
RUNTIME=${DETECTED_RUNTIME}
EOF
chmod 600 "${CONFIG_DIR}/agent.env"

echo "[*] Saved agent configuration to ${CONFIG_DIR}/agent.env"

# If systemd is available, configure background systemd service
if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    SERVICE_FILE="/etc/systemd/system/network-control-plane-agent.service"
    cat <<EOF > "${SERVICE_FILE}"
[Unit]
Description=Network Control Plane Host Agent Daemon
After=network.target docker.service podman.service

[Service]
Type=simple
EnvironmentFile=${CONFIG_DIR}/agent.env
ExecStart=/usr/bin/python3 -m main --host-id \${HOST_ID} --control-plane-url \${CONTROL_PLANE_URL} --api-token \${API_TOKEN} --runtime \${RUNTIME}
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload || true
    echo "[*] Created systemd service: ${SERVICE_FILE}"
fi

echo ""
echo "=================================================================="
echo " [✓] Onboarding Complete! Node '${HOST_ID}' is connected."
echo "     Control Plane: ${CONTROL_PLANE}"
echo "     Runtime:       ${DETECTED_RUNTIME}"
echo "=================================================================="
