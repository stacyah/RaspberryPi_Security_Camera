# ufw config notes

### baseline rules
```bash
# deny all incoming traffic by default
sudo ufw default deny incoming

# allow all outgoing traffic
sudo ufw default allow outgoing

# allow ssh for remote management
sudo ufw allow ssh

# allow splunk forwarder port for log shipping
sudo ufw allow 9997

# enable and verify firewall rules
sudo ufw enable
sudo ufw status verbose