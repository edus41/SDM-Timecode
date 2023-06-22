import wmi
import re

def is_ip_address(ip):
    ipv4_pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    return bool(re.match(ipv4_pattern, ip))


def get_network_interfaces():
    wmi_obj = wmi.WMI()
    interfaces = []
    for interface in wmi_obj.Win32_NetworkAdapterConfiguration(IPEnabled=True):
        interfaces.append(interface)
    return interfaces

def get_ip_addresses(interface):
    ips = interface.IPAddress
    ipv4_addresses = [ip for ip in ips if is_ip_address(ip)]
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

