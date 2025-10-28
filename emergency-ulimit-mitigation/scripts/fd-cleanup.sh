#!/bin/bash

# Immediate FD cleanup
echo "Current system FD usage:"
cat /proc/sys/fs/file-nr | awk '{printf "Used: %d, Free: %d, Max: %d (%.1f%% used)\n", $1, $2, $3, ($1/$3)*100}'

echo -e "\nTop FD consumers:"
for pid in $(ps -eo pid --no-headers | head -20); do
    if [ -d "/proc/$pid/fd" ]; then
        fd_count=$(ls /proc/$pid/fd 2>/dev/null | wc -l)
        if [ $fd_count -gt 50 ]; then
            cmd=$(ps -p $pid -o comm= 2>/dev/null)
            echo "PID $pid ($cmd): $fd_count FDs"
        fi
    fi
done

# Quick fixes
echo -e "\nApplying quick fixes..."
docker system prune -f >/dev/null 2>&1
systemctl reload traefik >/dev/null 2>&1
echo "Done."
