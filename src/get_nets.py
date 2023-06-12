import socket
import wmi

def is_ipv4_address(ip):
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        return False

def get_network_interfaces():
    wmi_obj = wmi.WMI()
    interfaces = []
    for interface in wmi_obj.Win32_NetworkAdapterConfiguration(IPEnabled=True):
        interfaces.append(interface)
    return interfaces

def get_ip_addresses(interface):
    ips = interface.IPAddress
    ipv4_addresses = [ip for ip in ips if is_ipv4_address(ip)]
    return ipv4_addresses

def get_interface_name(interface):
    return interface.Caption[11:]

def get_nets():
    nets = {}
    network_interfaces = get_network_interfaces()
    for interface in network_interfaces:
        interface_name = get_interface_name(interface)
        ip_addresses = get_ip_addresses(interface)
        for ip in ip_addresses:
            nets[interface_name] = ip
    return nets

