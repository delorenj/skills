#!/bin/bash
#
# OpenClaw Safe Upgrade Script
# Performs a safe upgrade with backups and verification
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="${HOME}/.openclaw-backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Functions
print_status() {
    echo -e "${GREEN}[*]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is required but not installed"
        exit 1
    fi
}

backup_config() {
    print_status "Backing up configuration..."
    mkdir -p "${BACKUP_DIR}"

    # Backup main config
    if openclaw config export > "${BACKUP_DIR}/config-${TIMESTAMP}.json" 2>/dev/null; then
        print_status "Config backed up to ${BACKUP_DIR}/config-${TIMESTAMP}.json"
    else
        print_warning "No config to backup or backup failed"
    fi

    # Backup credentials if they exist
    if [ -d "${HOME}/.openclaw/credentials" ]; then
        cp -R "${HOME}/.openclaw/credentials" "${BACKUP_DIR}/credentials-${TIMESTAMP}"
        print_status "Credentials backed up"
    fi

    # Backup sessions if they exist
    if [ -d "${HOME}/.openclaw/sessions" ]; then
        cp -R "${HOME}/.openclaw/sessions" "${BACKUP_DIR}/sessions-${TIMESTAMP}"
        print_status "Sessions backed up"
    fi
}

get_current_version() {
    if command -v openclaw &> /dev/null; then
        openclaw --version 2>/dev/null || echo "unknown"
    else
        echo "not installed"
    fi
}

get_latest_version() {
    npm view openclaw version --userconfig "$(mktemp)" 2>/dev/null || echo "unknown"
}

upgrade_openclaw() {
    local channel="${1:-latest}"

    print_status "Upgrading to openclaw@${channel}..."

    # Check if we need elevated permissions for global install
    local npm_prefix=$(npm config get prefix 2>/dev/null || echo "/usr")
    if [ ! -w "${npm_prefix}" ]; then
        print_warning "Global npm directory requires elevated permissions: ${npm_prefix}"
        print_status "Please run: sudo npm i -g openclaw@${channel}"
        print_status "Or use a Node version manager (nvm, n) to avoid sudo"
        return 1
    fi

    if npm i -g "openclaw@${channel}" 2>&1; then
        print_status "Upgrade successful!"
        return 0
    else
        print_error "Upgrade failed"
        return 1
    fi
}

verify_installation() {
    print_status "Verifying installation..."

    # Check version
    local new_version=$(get_current_version)
    print_status "Installed version: ${new_version}"

    # Run doctor
    if openclaw doctor &>/dev/null; then
        print_status "OpenClaw doctor check passed"
    else
        print_warning "OpenClaw doctor reported issues (may be normal)"
    fi

    # Test basic command
    if openclaw --help &>/dev/null; then
        print_status "Basic command test passed"
    else
        print_error "Basic command test failed"

        # Check for common issues
        if openclaw --version 2>&1 | grep -q "ERR_MODULE_NOT_FOUND"; then
            print_error "Missing dependency detected!"
            print_status "Attempting automatic fix..."
            fix_dependencies

            # Retry after fix
            if openclaw --help &>/dev/null; then
                print_status "Fixed! Basic command now works"
            else
                return 1
            fi
        else
            return 1
        fi
    fi

    # Check for systemd service issues
    if systemctl --user list-units --all 2>/dev/null | grep -q openclaw-gateway.service; then
        local service_status=$(systemctl --user is-active openclaw-gateway.service 2>/dev/null || echo "unknown")

        if [ "$service_status" = "failed" ] || [ "$service_status" = "activating" ]; then
            print_warning "Service status: $service_status"

            local restart_count=$(systemctl --user show openclaw-gateway.service -p NRestarts --value 2>/dev/null || echo "0")
            if [ "$restart_count" -gt 3 ]; then
                print_error "Service in restart loop (count: $restart_count)"
                print_status "Stopping service and checking dependencies..."
                systemctl --user stop openclaw-gateway.service
                fix_dependencies
            fi
        fi
    fi
}

check_systemd_service() {
    if systemctl --user list-units --all | grep -q openclaw-gateway.service 2>/dev/null; then
        local restart_count=$(systemctl --user show openclaw-gateway.service -p NRestarts --value 2>/dev/null || echo "0")

        if [ "$restart_count" -gt 5 ]; then
            print_warning "Service has restarted $restart_count times - likely in restart loop"
            print_status "Stopping service to prevent further restarts..."
            systemctl --user stop openclaw-gateway.service 2>/dev/null || true
            return 1
        fi
    fi
    return 0
}

fix_dependencies() {
    print_status "Checking for dependency issues..."

    # Check recent logs for module errors
    if command -v journalctl &>/dev/null; then
        if journalctl --user -u openclaw-gateway.service -n 20 2>/dev/null | grep -q "ERR_MODULE_NOT_FOUND.*long"; then
            print_warning "Missing 'long' package detected - fixing..."

            cd ~/code/openclaw 2>/dev/null || cd /usr/lib/node_modules/openclaw 2>/dev/null || return 1

            # Safety check before removing directories
            if [ -d "node_modules" ] && [ -f "package.json" ]; then
                print_status "Performing clean dependency reinstall..."
                print_warning "This will remove node_modules and pnpm-lock.yaml"

                # Only remove if we're in a valid project directory
                if [ -f "package.json" ] && grep -q "openclaw" package.json 2>/dev/null; then
                    rm -rf node_modules pnpm-lock.yaml 2>/dev/null || true
                else
                    print_error "Not in a valid OpenClaw project directory, aborting"
                    return 1
                fi
            fi

            if command -v pnpm &>/dev/null; then
                pnpm install
                pnpm add -w long
                pnpm build
            else
                npm install
                npm install long
            fi

            print_status "Dependencies fixed"
            return 0
        fi
    fi
    return 0
}

restart_gateway() {
    print_status "Checking for running gateway..."

    # Check for systemd service issues first
    if ! check_systemd_service; then
        print_warning "Service issues detected - attempting fix..."
        fix_dependencies
    fi

    if pgrep -f openclaw-gateway &>/dev/null; then
        print_status "Stopping existing gateway gracefully..."
        pkill -f openclaw-gateway || true

        # Wait for graceful shutdown (up to 5 seconds)
        local count=0
        while pgrep -f openclaw-gateway &>/dev/null && [ $count -lt 5 ]; do
            sleep 1
            count=$((count + 1))
        done

        # Force kill if still running
        if pgrep -f openclaw-gateway &>/dev/null; then
            print_warning "Gateway didn't stop gracefully, forcing..."
            pkill -9 -f openclaw-gateway 2>/dev/null || true
            sleep 1
        fi

        print_status "Starting gateway..."
        nohup openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &
        sleep 3

        if openclaw channels status --probe &>/dev/null; then
            print_status "Gateway restarted successfully"
        else
            print_warning "Gateway may not be fully started yet"
        fi
    else
        print_status "No gateway running (skipping restart)"
    fi

    # If using systemd, restart the service
    if systemctl --user list-units --all | grep -q openclaw-gateway.service 2>/dev/null; then
        print_status "Restarting systemd service..."
        systemctl --user restart openclaw-gateway.service || true
    fi
}

rollback() {
    local previous_version="$1"

    print_error "Rolling back to version ${previous_version}..."

    # Check if we need elevated permissions
    local npm_prefix=$(npm config get prefix 2>/dev/null || echo "/usr")
    if [ ! -w "${npm_prefix}" ]; then
        print_warning "Rollback requires elevated permissions for: ${npm_prefix}"
        print_status "Please manually run: sudo npm i -g openclaw@${previous_version}"
        return 1
    fi

    if npm i -g "openclaw@${previous_version}" 2>&1; then
        print_status "Rollback successful"

        # Restore latest config backup
        local latest_backup=$(ls -t "${BACKUP_DIR}"/config-*.json 2>/dev/null | head -1)
        if [ -n "${latest_backup}" ]; then
            print_status "Restoring config from ${latest_backup}"
            openclaw config import < "${latest_backup}"
        fi
    else
        print_error "Rollback failed! Manual intervention required."
        exit 1
    fi
}

# Main execution
main() {
    local channel="${1:-latest}"
    local skip_backup="${2:-false}"

    echo "====================================="
    echo "    OpenClaw Upgrade Tool"
    echo "====================================="
    echo

    # Check prerequisites
    check_command npm
    check_command node

    # Get current version
    CURRENT_VERSION=$(get_current_version)
    LATEST_VERSION=$(get_latest_version)

    print_status "Current version: ${CURRENT_VERSION}"
    print_status "Latest version:  ${LATEST_VERSION}"
    echo

    if [ "${CURRENT_VERSION}" = "${LATEST_VERSION}" ] && [ "${channel}" = "latest" ]; then
        print_status "Already at latest version!"
        exit 0
    fi

    # Backup unless skipped
    if [ "${skip_backup}" != "true" ]; then
        backup_config
    fi

    # Perform upgrade
    if upgrade_openclaw "${channel}"; then
        NEW_VERSION=$(get_current_version)

        if verify_installation; then
            restart_gateway

            echo
            print_status "Upgrade completed successfully!"
            print_status "Previous version: ${CURRENT_VERSION}"
            print_status "New version:      ${NEW_VERSION}"

            # Show backup location
            if [ "${skip_backup}" != "true" ]; then
                echo
                print_status "Backups stored in: ${BACKUP_DIR}"
            fi
        else
            print_error "Verification failed!"

            if [ "${CURRENT_VERSION}" != "not installed" ]; then
                read -p "Rollback to previous version? (y/N) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    rollback "${CURRENT_VERSION}"
                fi
            fi
            exit 1
        fi
    else
        print_error "Upgrade failed!"
        exit 1
    fi
}

# Handle arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [channel] [skip-backup]"
        echo
        echo "Channels:"
        echo "  latest    - Stable release (default)"
        echo "  beta      - Beta release"
        echo "  X.Y.Z     - Specific version"
        echo
        echo "Options:"
        echo "  skip-backup - Skip configuration backup"
        echo
        echo "Examples:"
        echo "  $0                    # Upgrade to latest"
        echo "  $0 beta              # Upgrade to beta"
        echo "  $0 2026.2.14         # Install specific version"
        echo "  $0 latest true       # Upgrade without backup"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac