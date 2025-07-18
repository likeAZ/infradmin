#!/bin/bash
# Example crontab setup script for DNS management
# This script should be run on the Docker host to set up automated DNS updates

# Add this line to your crontab (crontab -e) to run DNS updates every 2 minutes:
# */2 * * * * /usr/bin/docker exec infradmin python /usr/src/app/infradmin/scripts/updateDNS.py --sync

# Or for a more comprehensive approach with logging:
# */2 * * * * /usr/bin/docker exec infradmin python /usr/src/app/infradmin/scripts/updateDNS.py --sync >> /var/log/infradmin-dns.log 2>&1

# Cleanup old DNS records every hour:
# 0 * * * * /usr/bin/docker exec infradmin python /usr/src/app/infradmin/scripts/updateDNS.py --cleanup >> /var/log/infradmin-dns.log 2>&1

echo "Example crontab entries for DNS management:"
echo ""
echo "# Update DNS records every 2 minutes"
echo "*/2 * * * * /usr/bin/docker exec infradmin python /usr/src/app/infradmin/scripts/updateDNS.py --sync"
echo ""
echo "# Cleanup old DNS records every hour"
echo "0 * * * * /usr/bin/docker exec infradmin python /usr/src/app/infradmin/scripts/updateDNS.py --cleanup"
echo ""
echo "# With logging:"
echo "*/2 * * * * /usr/bin/docker exec infradmin python /usr/src/app/infradmin/scripts/updateDNS.py --sync >> /var/log/infradmin-dns.log 2>&1"
echo "0 * * * * /usr/bin/docker exec infradmin python /usr/src/app/infradmin/scripts/updateDNS.py --cleanup >> /var/log/infradmin-dns.log 2>&1"
echo ""

# Create log directory if it doesn't exist
if [ ! -d "/var/log" ]; then
    echo "Creating log directory..."
    sudo mkdir -p /var/log
fi

echo "To install these cron jobs, run:"
echo "crontab -e"
echo ""
echo "Then add the desired lines from above."
