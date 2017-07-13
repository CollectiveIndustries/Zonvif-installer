# Zonvif-installer
Zoneminder Mysql database installer for deploying Onvif compatible devices from the same manufacture. Using MAC Addresses this installer will configure every camera using
 Onvif, SSH, and MySQL connections.

installer will ARP the network and grab a list of IP/MAC address pairs. after attempting to use Onvif only the compatible IPs are kept. A hosts file will be created for DNS entries and MySQL records will be created for Zoneminder for zones, names (from DNS records), and auth strings.
