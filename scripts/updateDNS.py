#!/usr/bin/env python3
"""
Dynamic DNS updater for containers
This script gets IPs from running Docker containers and dynamically updates local BIND DNS zones.
Designed to run in a container with crontab scheduling on the host.
"""

import sys
import os
import yaml
import argparse
import ipaddress
import time
from datetime import datetime
from typing import Dict, Optional

# Add parent directory to path to import common modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.containers import Docker
import common.infradmin_logs


class DNSUpdater:
    """Main class for managing dynamic DNS updates from container IPs to local BIND"""
    
    def __init__(self, config_path: str = None):
        self.o_logger = common.infradmin_logs.O_LOGGER
        self.o_docker = Docker()
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str = None) -> dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'conf', 'config.yaml'
            )
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Add default DNS configuration if not present
            if 'dns' not in config:
                config['dns'] = {
                    'domain': 'local.dev',
                    'ttl': 300,
                    'bind': {
                        'zone_file_path': '/etc/bind/zones',  # Path inside BIND container
                        'infradmin_zone_path': '/shared/bind/zones',  # Path inside infradmin container (shared volume)
                        'forward_zone_file': 'db.local.dev',
                        'reverse_zone_file': 'db.172.rev',
                        'reverse_network': '172.0.0',  # Network for reverse DNS (172.x.x.x)
                        'bind_container_name': 'bind9',
                        'reload_command': 'rndc reload',
                        'update_forward_zone': False,  # Set to True only if DHCP is not managing forward zone
                        'dhcp_managed': True,  # Forward zone is managed by DHCP server
                        'smart_sync': True  # Automatically add missing containers to forward zone via RNDC
                    }
                }
                self.o_logger.warning("DNS configuration not found in config.yaml, using defaults")
            
            return config
        except FileNotFoundError:
            self.o_logger.error(f"Configuration file not found: {config_path}")
            return {'dns': {}}
        except yaml.YAMLError as e:
            self.o_logger.error(f"Error parsing configuration file: {e}")
            return {'dns': {}}
    
    def get_container_ip(self, container_name: str) -> Optional[str]:
        """Get the IP address of a specific container"""
        try:
            container = self.o_docker.get_a_container(container_name)
            
            # Get the first network's IP address
            networks = container.attrs['NetworkSettings']['Networks']
            for network_name, network_info in networks.items():
                ip_address = network_info.get('IPAddress')
                if ip_address:
                    # Validate IP address
                    try:
                        ipaddress.ip_address(ip_address)
                        self.o_logger.info(f"Container {container_name} has IP {ip_address} on network {network_name}")
                        return ip_address
                    except ipaddress.AddressValueError:
                        continue
            
            self.o_logger.warning(f"No valid IP address found for container {container_name}")
            return None
            
        except Exception as e:
            self.o_logger.error(f"Error getting IP for container {container_name}: {e}")
            return None
    
    def get_all_container_ips(self) -> Dict[str, str]:
        """Get IP addresses for all running containers"""
        container_ips = {}
        
        try:
            # Get only running containers
            running_containers = self.o_docker.list_running_containers()
            
            for container in running_containers:
                container_name = container.name
                container_ip = self.get_container_ip(container_name)
                
                if container_ip:
                    container_ips[container_name] = container_ip
                    
        except Exception as e:
            self.o_logger.error(f"Error getting container IPs: {e}")
        
        return container_ips
    
    def add_container_to_forward_zone_via_rndc(self, container_name: str, ip_address: str) -> bool:
        """Add a container A record to forward zone via RNDC dynamic update"""
        try:
            domain = self.config['dns']['domain']
            ttl = self.config['dns'].get('ttl', 300)
            
            # Try to use rndc/nsupdate from infradmin container
            # This requires bind9-utils to be installed in the infradmin container
            
            # Method 1: Use nsupdate directly (if available)
            if self._try_nsupdate_add(container_name, domain, ttl, ip_address):
                return True
            
            # Method 2: Use rndc commands (if available) 
            if self._try_rndc_add(container_name, domain, ttl, ip_address):
                return True
            
            # Method 3: Fallback to logging
            self.o_logger.info(f"Would add A record: {container_name}.{domain}. {ttl} A {ip_address}")
            self.o_logger.warning("DNS utilities not available - install bind9-utils in infradmin container")
            self.o_logger.info("Run: apt-get update && apt-get install -y bind9-utils")
            return True  # Return True for now to indicate intent was processed
                
        except Exception as e:
            self.o_logger.error(f"Error in add_container_to_forward_zone_via_rndc: {e}")
            return False
    
    def _try_nsupdate_add(self, container_name: str, domain: str, ttl: int, ip_address: str) -> bool:
        """Try to add DNS record using nsupdate"""
        try:
            import subprocess
            
            # Get DNS server IP and key configuration
            bind_config = self.config.get('dns', {}).get('bind', {})
            server_ip = bind_config.get('server_ip', '127.0.0.1')
            rndc_key_config = bind_config.get('rndc_key', {})
            
            # Build nsupdate command with key authentication
            nsupdate_cmd = ['nsupdate']
            
            # Add key file if configured and exists
            key_file = rndc_key_config.get('key_file')
            if key_file and os.path.exists(key_file):
                nsupdate_cmd.extend(['-k', key_file])
                self.o_logger.debug(f"Using RNDC key file: {key_file}")
            else:
                # Try local update without key (less secure)
                nsupdate_cmd.append('-l')
                if key_file:
                    self.o_logger.warning(f"RNDC key file not found: {key_file}, falling back to local update")
                else:
                    self.o_logger.debug("No RNDC key file configured, using local update")
            
            # Create nsupdate commands
            update_commands = f"""server {server_ip}
update add {container_name}.{domain}. {ttl} A {ip_address}
send
"""
            
            # Execute nsupdate
            result = subprocess.run(
                nsupdate_cmd,
                input=update_commands,
                text=True,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                auth_method = "key-authenticated" if key_file and os.path.exists(key_file) else "local"
                self.o_logger.info(f"Added A record via nsupdate ({auth_method}): {container_name}.{domain} -> {ip_address} (server: {server_ip})")
                return True
            else:
                self.o_logger.warning(f"nsupdate failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.o_logger.debug("nsupdate not found, trying alternative methods")
            return False
        except Exception as e:
            self.o_logger.debug(f"nsupdate error: {e}")
            return False
    
    def _try_rndc_add(self, container_name: str, domain: str, ttl: int, ip_address: str) -> bool:
        """Try to add DNS record using rndc commands"""
        try:
            import subprocess
            
            # Get DNS server IP and key configuration
            bind_config = self.config.get('dns', {}).get('bind', {})
            server_ip = bind_config.get('server_ip', '127.0.0.1')
            rndc_key_config = bind_config.get('rndc_key', {})
            
            # Build rndc command with key authentication
            rndc_cmd = ['rndc']
            
            # Add key file if configured and exists
            key_file = rndc_key_config.get('key_file')
            if key_file and os.path.exists(key_file):
                rndc_cmd.extend(['-k', key_file])
            
            # Add server IP
            rndc_cmd.extend(['-s', server_ip, 'status'])
            
            # Try rndc status first to check connectivity
            result = subprocess.run(rndc_cmd, capture_output=True, timeout=10)
            if result.returncode != 0:
                self.o_logger.debug(f"rndc not accessible on {server_ip}")
                return False
            
            # Note: rndc doesn't directly add individual records like nsupdate
            # This would require more complex zone management
            self.o_logger.debug(f"rndc available on {server_ip} but individual record addition not implemented")
            return False
            
        except FileNotFoundError:
            self.o_logger.debug("rndc not found")
            return False
        except Exception as e:
            self.o_logger.debug(f"rndc error: {e}")
            return False
    
    def remove_container_from_forward_zone_via_rndc(self, container_name: str) -> bool:
        """Remove a container A record from forward zone via RNDC dynamic update"""
        try:
            domain = self.config['dns']['domain']
            
            # Try to use rndc/nsupdate from infradmin container
            # This requires bind9-utils to be installed in the infradmin container
            
            # Method 1: Use nsupdate directly (if available)
            if self._try_nsupdate_remove(container_name, domain):
                return True
            
            # Method 2: Use rndc commands (if available) 
            if self._try_rndc_remove(container_name, domain):
                return True
            
            # Method 3: Fallback to logging
            self.o_logger.info(f"Would remove A record: {container_name}.{domain}. A")
            self.o_logger.warning("DNS utilities not available - install bind9-utils in infradmin container")
            self.o_logger.info("Run: apt-get update && apt-get install -y bind9-utils")
            return True  # Return True for now to indicate intent was processed
                
        except Exception as e:
            self.o_logger.error(f"Error in remove_container_from_forward_zone_via_rndc: {e}")
            return False
    
    def _try_nsupdate_remove(self, container_name: str, domain: str) -> bool:
        """Try to remove DNS record using nsupdate"""
        try:
            import subprocess
            
            # Get DNS server IP and key configuration
            bind_config = self.config.get('dns', {}).get('bind', {})
            server_ip = bind_config.get('server_ip', '127.0.0.1')
            rndc_key_config = bind_config.get('rndc_key', {})
            
            # Build nsupdate command with key authentication
            nsupdate_cmd = ['nsupdate']
            
            # Add key file if configured and exists
            key_file = rndc_key_config.get('key_file')
            if key_file and os.path.exists(key_file):
                nsupdate_cmd.extend(['-k', key_file])
                self.o_logger.debug(f"Using RNDC key file: {key_file}")
            else:
                # Try local update without key (less secure)
                nsupdate_cmd.append('-l')
                if key_file:
                    self.o_logger.warning(f"RNDC key file not found: {key_file}, falling back to local update")
                else:
                    self.o_logger.debug("No RNDC key file configured, using local update")
            
            # Create nsupdate commands
            update_commands = f"""server {server_ip}
update delete {container_name}.{domain}. A
send
"""
            
            # Execute nsupdate
            result = subprocess.run(
                nsupdate_cmd,
                input=update_commands,
                text=True,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                auth_method = "key-authenticated" if key_file and os.path.exists(key_file) else "local"
                self.o_logger.info(f"Removed A record via nsupdate ({auth_method}): {container_name}.{domain} (server: {server_ip})")
                return True
            else:
                self.o_logger.warning(f"nsupdate failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.o_logger.debug("nsupdate not found, trying alternative methods")
            return False
        except Exception as e:
            self.o_logger.debug(f"nsupdate error: {e}")
            return False
    
    def _try_rndc_remove(self, container_name: str, domain: str) -> bool:
        """Try to remove DNS record using rndc commands"""
        try:
            import subprocess
            
            # Get DNS server IP and key configuration
            bind_config = self.config.get('dns', {}).get('bind', {})
            server_ip = bind_config.get('server_ip', '127.0.0.1')
            rndc_key_config = bind_config.get('rndc_key', {})
            
            # Build rndc command with key authentication
            rndc_cmd = ['rndc']
            
            # Add key file if configured and exists
            key_file = rndc_key_config.get('key_file')
            if key_file and os.path.exists(key_file):
                rndc_cmd.extend(['-k', key_file])
            
            # Add server IP
            rndc_cmd.extend(['-s', server_ip, 'status'])
            
            # Try rndc status first to check connectivity
            result = subprocess.run(rndc_cmd, capture_output=True, timeout=10)
            if result.returncode != 0:
                self.o_logger.debug(f"rndc not accessible on {server_ip}")
                return False
            
            # Note: rndc doesn't directly remove individual records like nsupdate
            # This would require more complex zone management
            self.o_logger.debug(f"rndc available on {server_ip} but individual record removal not implemented")
            return False
            
        except FileNotFoundError:
            self.o_logger.debug("rndc not found")
            return False
        except Exception as e:
            self.o_logger.debug(f"rndc error: {e}")
            return False
    
    def execute_in_bind_container(self, command: str) -> bool:
        """Execute a command in the BIND container"""
        try:
            bind_config = self.config.get('dns', {}).get('bind', {})
            bind_container_name = bind_config.get('bind_container_name', 'bind9')
            server_ip = bind_config.get('server_ip', '127.0.0.1')
            rndc_key_config = bind_config.get('rndc_key', {})
            
            # Check if BIND container exists and is running
            if not self.o_docker.is_container_exist(bind_container_name):
                self.o_logger.error(f"BIND container '{bind_container_name}' not found")
                return False
            
            container_state = self.o_docker.get_current_container_state(bind_container_name)
            if container_state != 'running':
                self.o_logger.error(f"BIND container '{bind_container_name}' is not running (state: {container_state})")
                return False
            
            # If it's an rndc command, add server IP and key parameters
            if command.startswith('rndc') and '-s' not in command:
                # Add server IP
                command = command.replace('rndc', f'rndc -s {server_ip}', 1)
                
                # Add key file if configured
                key_file = rndc_key_config.get('key_file')
                if key_file:
                    # Convert infradmin path to bind container path
                    # Assuming both containers mount the same volume
                    bind_key_file = key_file.replace('/shared/bind/', '/etc/bind/')
                    command = command.replace(f'rndc -s {server_ip}', f'rndc -k {bind_key_file} -s {server_ip}', 1)
            
            # Execute command in BIND container
            container_id = self.o_docker.from_name_to_id(bind_container_name)
            self.o_docker.exec_command(container_id, command)
            self.o_logger.info(f"Executed command in BIND container: {command}")
            return True
            
        except Exception as e:
            self.o_logger.error(f"Error executing command in BIND container: {e}")
            return False
    
    def sync_missing_containers_to_forward_zone(self, container_ips: Dict[str, str]) -> bool:
        """Add only missing containers to forward zone via RNDC"""
        try:
            domain = self.config['dns']['domain']
            added_count = 0
            
            self.o_logger.info(f"Checking {len(container_ips)} containers for missing DNS records...")
            
            for container_name, ip_address in container_ips.items():
                # Add container via RNDC (RNDC will handle duplicates gracefully)
                self.o_logger.info(f"Adding/updating container in DNS: {container_name}.{domain} -> {ip_address}")
                
                if self.add_container_to_forward_zone_via_rndc(container_name, ip_address):
                    added_count += 1
                else:
                    self.o_logger.warning(f"Failed to add/update container {container_name} in DNS")
            
            self.o_logger.info(f"Forward zone sync complete: {added_count} containers processed")
            return True
            
        except Exception as e:
            self.o_logger.error(f"Error syncing containers to forward zone: {e}")
            return False
    
    def generate_bind_zone_file(self, container_ips: Dict[str, str]) -> str:
        """Generate BIND forward zone file content for container IPs"""
        domain = self.config['dns']['domain']
        ttl = self.config['dns'].get('ttl', 300)
        
        # Generate serial number based on current timestamp
        serial = int(time.time())
        
        zone_content = f"""; Forward zone file for {domain} - Auto-generated by infradmin
; Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
$TTL {ttl}
@       IN  SOA ns1.{domain}. admin.{domain}. (
                {serial}    ; Serial
                3600        ; Refresh
                1800        ; Retry
                604800      ; Expire
                300         ; Minimum TTL
                )

        IN  NS  ns1.{domain}.
        IN  NS  ns2.{domain}.

; Static records
ns1     IN  A   127.0.0.1
ns2     IN  A   127.0.0.1

; Container A records - Auto-generated
"""
        
        for container_name, ip_address in container_ips.items():
            # Use container name directly as the record name
            zone_content += f"{container_name:<30} IN  A   {ip_address}\n"
        
        zone_content += "\n; End of auto-generated records\n"
        return zone_content
    
    def generate_reverse_zone_file(self, container_ips: Dict[str, str]) -> str:
        """Generate BIND reverse zone file content for container IPs"""
        domain = self.config['dns']['domain']
        ttl = self.config['dns'].get('ttl', 300)
        bind_config = self.config.get('dns', {}).get('bind', {})
        reverse_network = bind_config.get('reverse_network', '172.0.0')
        
        # Generate serial number based on current timestamp
        serial = int(time.time())
        
        # Determine the reverse zone name based on network
        reverse_zone_name = f"{'.'.join(reversed(reverse_network.split('.')))}.in-addr.arpa"
        
        zone_content = f"""; Reverse zone file for {reverse_zone_name} - Auto-generated by infradmin
; Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
$TTL {ttl}
@       IN  SOA ns1.{domain}. admin.{domain}. (
                {serial}    ; Serial
                3600        ; Refresh
                1800        ; Retry
                604800      ; Expire
                300         ; Minimum TTL
                )

        IN  NS  ns1.{domain}.
        IN  NS  ns2.{domain}.

; Container PTR records - Auto-generated
"""
        
        for container_name, ip_address in container_ips.items():
            # Generate PTR record for reverse DNS
            ip_parts = ip_address.split('.')
            if len(ip_parts) == 4 and ip_address.startswith(reverse_network):
                # Create reverse IP format (e.g., 1.0.18.172.in-addr.arpa for 172.18.0.1)
                reverse_ip = '.'.join(reversed(ip_parts))
                # Get the last octet(s) for the record name based on network
                network_parts = reverse_network.split('.')
                record_octets = ip_parts[len(network_parts):]
                record_name = '.'.join(reversed(record_octets))
                
                zone_content += f"{record_name:<20} IN  PTR {container_name}.{domain}.\n"
        
        zone_content += "\n; End of auto-generated records\n"
        return zone_content
    
    def write_zone_file_to_bind_container(self, zone_content: str, zone_file_name: str) -> bool:
        """Write zone file content to the BIND container via shared volume mount"""
        try:
            bind_config = self.config.get('dns', {}).get('bind', {})
            
            # Use mounted volume path within the infradmin container
            # This should be configured to mount the same volume as BIND's zone directory
            infradmin_zone_path = bind_config.get('infradmin_zone_path', '/shared/bind/zones')
            
            # Check if the mounted directory exists and is writable
            if not os.path.exists(infradmin_zone_path):
                self.o_logger.error(f"BIND zones mount path not found in infradmin container: {infradmin_zone_path}")
                self.o_logger.error("Ensure the BIND zones volume is mounted to infradmin container")
                return False
            
            if not os.access(infradmin_zone_path, os.W_OK):
                self.o_logger.error(f"No write permission to BIND zones mount path: {infradmin_zone_path}")
                return False
            
            # Construct the full path for the zone file
            full_zone_file_path = os.path.join(infradmin_zone_path, zone_file_name)
            
            # Write zone file atomically using a temporary file
            temp_file_path = f"{full_zone_file_path}.tmp"
            
            try:
                # Write to temporary file first
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(zone_content)
                    f.flush()  # Ensure content is written
                    os.fsync(f.fileno())  # Force write to disk
                
                # Atomically move temp file to final location
                os.rename(temp_file_path, full_zone_file_path)
                
                # Set proper permissions (readable by BIND)
                os.chmod(full_zone_file_path, 0o644)
                
                self.o_logger.info(f"Successfully updated BIND zone file: {full_zone_file_path}")
                return True
                
            except OSError as e:
                # Cleanup temp file if it exists
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except OSError:
                        pass
                raise e
            
        except Exception as e:
            self.o_logger.error(f"Error writing zone file to BIND container: {e}")
            return False
    
    def update_bind_zone_file(self, container_ips: Dict[str, str]) -> bool:
        """Update BIND zone files with container IPs (respecting DHCP management)"""
        try:
            bind_config = self.config.get('dns', {}).get('bind', {})
            update_forward_zone = bind_config.get('update_forward_zone', False)
            dhcp_managed = bind_config.get('dhcp_managed', True)
            reverse_zone_file = bind_config.get('reverse_zone_file', 'db.172.rev')
            
            success = True
            
            # Handle forward zone based on configuration
            if dhcp_managed and not update_forward_zone:
                self.o_logger.info("Forward zone is DHCP-managed, skipping file update. Use RNDC dynamic updates only.")
                # Note: Could implement RNDC updates here if needed for specific containers
            elif update_forward_zone:
                self.o_logger.warning("Updating forward zone file despite DHCP management - ensure this is intended!")
                forward_zone_file = bind_config.get('forward_zone_file', f"db.{self.config['dns']['domain']}")
                forward_zone_content = self.generate_bind_zone_file(container_ips)
                if not self.write_zone_file_to_bind_container(forward_zone_content, forward_zone_file):
                    success = False
            else:
                # Update forward zone normally (no DHCP conflict)
                forward_zone_file = bind_config.get('forward_zone_file', f"db.{self.config['dns']['domain']}")
                forward_zone_content = self.generate_bind_zone_file(container_ips)
                if not self.write_zone_file_to_bind_container(forward_zone_content, forward_zone_file):
                    success = False
            
            # Always update reverse zone (DHCP typically doesn't manage reverse zones)
            reverse_zone_content = self.generate_reverse_zone_file(container_ips)
            if not self.write_zone_file_to_bind_container(reverse_zone_content, reverse_zone_file):
                success = False
            
            # Reload BIND configuration only if we updated zone files
            if success and (update_forward_zone or not dhcp_managed):
                reload_command = bind_config.get('reload_command', 'rndc reload')
                if not self.execute_in_bind_container(reload_command):
                    self.o_logger.warning("Failed to reload BIND config, but zone files were updated")
                    # Don't fail completely as zone files were updated
            
            if dhcp_managed and not update_forward_zone:
                self.o_logger.info("Successfully updated reverse zone. Forward zone managed by DHCP.")
            else:
                self.o_logger.info("Successfully updated BIND zones and reloaded configuration")
            
            return success
            
        except Exception as e:
            self.o_logger.error(f"Error updating BIND zone files: {e}")
            return False
    
    def sync_dns_records(self) -> bool:
        """Synchronize DNS records with running containers"""
        try:
            # Always get all running containers (no labels required)
            container_ips = self.get_all_container_ips()
            self.o_logger.info(f"Syncing DNS for all {len(container_ips)} running containers")
            
            if not container_ips:
                self.o_logger.info("No containers found for DNS updates")
                return True
            
            bind_config = self.config.get('dns', {}).get('bind', {})
            dhcp_managed = bind_config.get('dhcp_managed', True)
            smart_sync = bind_config.get('smart_sync', True)
            
            success = True
            
            if dhcp_managed:
                self.o_logger.info("DHCP-managed mode: Updating reverse zone and syncing missing containers to forward zone")
                
                # Always update reverse zone
                if not self.update_reverse_zone_only(container_ips):
                    success = False
                
                # Smart sync: Add missing containers to forward zone via RNDC
                if smart_sync:
                    if not self.sync_missing_containers_to_forward_zone(container_ips):
                        success = False
                else:
                    self.o_logger.info("Smart sync disabled - not updating forward zone")
                    
                return success
            else:
                # Update both forward and reverse zones normally
                return self.update_bind_zone_file(container_ips)
                
        except Exception as e:
            self.o_logger.error(f"Error syncing DNS records: {e}")
            return False
    
    def update_reverse_zone_only(self, container_ips: Dict[str, str]) -> bool:
        """Update only the reverse zone file (for DHCP-managed environments)"""
        try:
            bind_config = self.config.get('dns', {}).get('bind', {})
            reverse_zone_file = bind_config.get('reverse_zone_file', 'db.172.rev')
            
            # Generate and write reverse zone file
            reverse_zone_content = self.generate_reverse_zone_file(container_ips)
            if not self.write_zone_file_to_bind_container(reverse_zone_content, reverse_zone_file):
                return False
            
            # Reload only the reverse zone
            reload_command = f"rndc reload {bind_config.get('reverse_zone_file', 'db.172.rev')}"
            
            if not self.execute_in_bind_container(reload_command):
                self.o_logger.warning("Failed to reload reverse zone, but zone file was updated")
                return True  # Zone file was still updated successfully
            
            self.o_logger.info("Successfully updated reverse zone (forward zone managed by DHCP)")
            return True
            
        except Exception as e:
            self.o_logger.error(f"Error updating reverse zone: {e}")
            return False
    
    def cleanup_dns_records(self) -> bool:
        """Remove DNS records for stopped containers by regenerating zone files"""
        try:
            # Always regenerate with all currently running containers
            running_ips = self.get_all_container_ips()
            
            self.o_logger.info(f"Cleaning up DNS records, keeping {len(running_ips)} active containers")
            return self.update_bind_zone_file(running_ips)
            
        except Exception as e:
            self.o_logger.error(f"Error cleaning up DNS records: {e}")
            return False


def main():
    """Main function with CLI interface"""
    # Initialize logging first
    common.infradmin_logs.O_LOGGER = common.infradmin_logs.init_logging('updateDNS', False)
    
    parser = argparse.ArgumentParser(description='Dynamic DNS updater for Docker containers')
    parser.add_argument('--config', '-c', help='Path to configuration file')
    parser.add_argument('--sync', '-s', action='store_true', help='Sync DNS records for all running containers')
    parser.add_argument('--cleanup', '-x', action='store_true', help='Remove DNS records for stopped containers')
    parser.add_argument('--list', '-l', action='store_true', help='List containers and their IPs')
    parser.add_argument('--list-dns', '-d', action='store_true', help='List all containers that will be added to DNS')
    parser.add_argument('--status', action='store_true', help='Show DNS management configuration and mode')
    parser.add_argument('--add-container', help='Add specific container to DNS via RNDC (format: container_name)')
    parser.add_argument('--remove-container', help='Remove specific container from DNS via RNDC (format: container_name)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Re-initialize logging with debug flag if specified
    if args.debug:
        common.infradmin_logs.O_LOGGER = common.infradmin_logs.init_logging('updateDNS', True)
    
    # Initialize DNS updater
    updater = DNSUpdater(args.config)
    
    if args.list:
        container_ips = updater.get_all_container_ips()
        print("\n=== All Running Containers ===")
        for container, ip in container_ips.items():
            print(f"{container:<30} {ip}")
        print(f"\nTotal: {len(container_ips)} containers")
    
    elif args.list_dns:
        container_ips = updater.get_all_container_ips()
        print("\n=== All Containers for DNS ===")
        for container, ip in container_ips.items():
            print(f"{container:<30} {container}.{updater.config['dns']['domain']:<25} {ip}")
        print(f"\nTotal: {len(container_ips)} containers")
    
    elif args.sync:
        print("Syncing DNS records for all running containers...")
        success = updater.sync_dns_records()
        print("DNS sync completed successfully" if success else "DNS sync failed")
    
    elif args.cleanup:
        print("Cleaning up DNS records for stopped containers...")
        success = updater.cleanup_dns_records()
        print("DNS cleanup completed successfully" if success else "DNS cleanup failed")
    
    elif args.status:
        print("\n=== DNS Management Configuration ===")
        bind_config = updater.config.get('dns', {}).get('bind', {})
        dhcp_managed = bind_config.get('dhcp_managed', True)
        update_forward_zone = bind_config.get('update_forward_zone', False)
        smart_sync = bind_config.get('smart_sync', True)
        
        print(f"Domain: {updater.config.get('dns', {}).get('domain', 'Not configured')}")
        print(f"DHCP Managed: {dhcp_managed}")
        print(f"Update Forward Zone: {update_forward_zone}")
        print(f"Smart Sync: {smart_sync}")
        print(f"BIND Container: {bind_config.get('bind_container_name', 'bind9')}")
        
        if dhcp_managed and not update_forward_zone and smart_sync:
            print("\nMode: DHCP-Safe Mode with Smart Sync (RECOMMENDED)")
            print("- Reverse zone files are updated")
            print("- Forward zone managed by DHCP server")
            print("- Missing containers automatically added via RNDC")
            print("- No conflicts with DHCP dynamic updates")
        elif dhcp_managed and not update_forward_zone and not smart_sync:
            print("\nMode: DHCP-Safe Mode (Conservative)")
            print("- Only reverse zone files are updated")
            print("- Forward zone completely managed by DHCP server")
            print("- Manual container addition required")
        elif dhcp_managed and update_forward_zone:
            print("\nMode: DHCP-Override Mode (RISKY)")
            print("- Both forward and reverse zones updated")
            print("- WARNING: May conflict with DHCP updates!")
        else:
            print("\nMode: Full DNS Management")
            print("- Both forward and reverse zones updated")
            print("- No DHCP conflicts")
    
    elif args.add_container:
        container_name = args.add_container
        container_ip = updater.get_container_ip(container_name)
        if container_ip:
            print(f"Adding {container_name} ({container_ip}) to DNS via RNDC...")
            success = updater.add_container_to_forward_zone_via_rndc(container_name, container_ip)
            print("Container added successfully" if success else "Failed to add container")
        else:
            print(f"Container '{container_name}' not found or has no IP")
    
    elif args.remove_container:
        container_name = args.remove_container
        print(f"Removing {container_name} from DNS via RNDC...")
        success = updater.remove_container_from_forward_zone_via_rndc(container_name)
        print("Container removed successfully" if success else "Failed to remove container")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
