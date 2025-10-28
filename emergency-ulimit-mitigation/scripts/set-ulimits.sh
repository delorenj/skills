#!/bin/bash

# System-wide ulimit configuration for FD stability
# Tags: AI/Prompt, ulimit, Stability

# Current limits
echo "Current limits:"
ulimit -n
cat /proc/sys/fs/file-max

# Set higher limits
echo "Setting new limits..."
ulimit -n 65536

# Make permanent
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf
echo "fs.file-max = 2097152" >> /etc/sysctl.conf

# Apply immediately
sysctl -p
echo "session required pam_limits.so" >> /etc/pam.d/common-session

echo "New limits set. Reboot recommended."
