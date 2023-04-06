# Kubernetes Pod Networking

## Network commands
| Command | Explain | Note |
| ------- | ------- | ---- |
| `ip addr` | Show network interfaces |  |
| `ip route` | Show routing table |  |
| `sudo iptables -L` | List all iptables rules |  |
| `sudo iptables -L -t nat` | List all iptables nat rules |  |

## Network Namespace Lab

Requirements for a valid network namespace:
- Loopback interface (ping 127.0.0.1)
- Ability to talk to the host (ping <host-ip>)
- Ability to talk to the internet (ping google.com)

The following section is a lab to help you understand network namespaces. You will be creating a network namespace and then creating a virtual ethernet pair to connect the namespace to the host. You will then be able to ping the host from the namespace and vice versa. You will also be able to ping the internet from the namespace by using iptables to masquerade the traffic. Kudos to the blog [Fun witn network namespaces](https://www.gilesthomas.com/2021/03/fun-with-network-namespaces) for the tutorial.

### Steps and Commands
| Execution Place | Command | Explain | Note | Expected Result |
| --------------- | ------- | ------- | ---- | --------------- |
| Host | `sudo ip netns add bard` | Create a network namespace called bard |  | Success |
| Host | `sudo ip netns` | List all network namespaces |  | bard |
| Host | `sudo ip netns exec bard bash` | Exec into the bard namespace |  | Success |
| Namespace | `ping 127.0.0.1` | Test loopback |  | Fail |
| Namespace | `ip a` | Show network interfaces in bard |  | Success |
| Namespace | `ip link set dev lo up` | Enable loopback |  | Success |
| Namespace | `ip a` | Show network interfaces in bard |  | Success |
| Namespace | `ping 127.0.0.1` | Test loopback |  | Success |
| Namespace | `ping <host-ip>` | Test host connection |  | Fail |
| Host | `sudo ip link add veth0 type veth peer veth1` | Create a virtual ethernet pair |  | Success |
| Host | `sudo ip addr` | Show network interfaces |  | Success |
| Host | `sudo ip link set veth1 netns bard` | Connect veth1 to bard namespace |  | Success |
| Host | `sudo ip addr` | Show network interfaces |  | Success |
| Namespace | `ip a` | Show network interfaces in bard |  | Success |
| Host | `sudo ip addr add <ip-for-veth0> dev veth0` | Add IP address to veth0 | The ip address you choose must under the same network with host. | Success |
| Host | `sudo ip link set dev veth0 up` | Enable veth0 |  | Success |
| Namespace | `sudo ip addr add <ip-for-veth1> dev veth1` | Add IP address to veth1 | The ip address you choose must under the same network with host. | Success |
| Namespace | `sudo ip link set dev veth1 up` | Enable veth1 |  | Success |
| Namespace | `ip a` | Show network interfaces in bard |  | Success |
| Namespace | `ping <host-ip>` | Test host connection |  | Success |
| Namespace | `ping 8.8.8.8` | Test internet connection |  | Fail |
| Namespace | `sudo ip route add default via <ip-for-veth0>` | Add default route to veth0 |  | Success |
| Host | `cat /proc/sys/net/ipv4/ip_forward` | Show ip forwarding status |  | Either 0 or 1 |
| Host | `echo 1 > /proc/sys/net/ipv4/ip_forward`/`sudo sysctl net.ipv4.ip_forward=1` | Enable ip forwarding |  | Success |
| Host | `sudo iptables -L FORWARD` | Show iptables FORWARD chain |  | Success |
| Host | `sudo iptables -P FORWARD DROP` | Set iptables FORWARD chain policy to DROP |  | Success |
| Host | `sudo iptables -t nat -A POSTROUTING -s <your-ip>/255.255.255.0 -o <main-eth-interface> -j MASQUERADE` | Add iptables rule to masquerade traffic from veth0 |  | Success |
| Host | `sudo iptables -A FORWARD -i <main-eth-interface> -o veth0 -j ACCEPT` | Add iptables rule to allow traffic from main ethernet to veth0 |  | Success |
| Host | `sudo iptables -A FORWARD -o <main-eth-interface> -i veth0 -j ACCEPT` | Add iptables rule to allow traffic from veth0 to main ethernet |  | Success |
| Namespace | `ping 8.8.8.8` | Test internet connection |  | Success |

## Clean Up
- Remove the network namespace
  - `sudo ip netns del bard`
- Remove the virtual ethernet pair
  - `sudo ip link del veth0`
