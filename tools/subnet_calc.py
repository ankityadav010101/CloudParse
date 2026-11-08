"""Reproduce the assignment's smallest-fit VLSM allocation and print host ranges."""
import ipaddress

BLOCK = ipaddress.ip_network("10.20.0.0/16")
REQUIREMENTS = [("app", 1000), ("public", 250), ("data", 100), ("management", 20)]


def allocate():
    cursor = int(BLOCK.network_address)
    rows = []
    for name, required in REQUIREMENTS:
        prefix = 32 - (required + 2 - 1).bit_length()
        network = ipaddress.ip_network((cursor, prefix), strict=False)
        if network.network_address < BLOCK.network_address or network.broadcast_address > BLOCK.broadcast_address:
            raise ValueError(f"{name} subnet exceeds {BLOCK}")
        rows.append((name, required, network))
        cursor = int(network.broadcast_address) + 1
    return rows


if __name__ == "__main__":
    for name, required, network in allocate():
        first, last = network.network_address + 1, network.broadcast_address - 1
        usable = network.num_addresses - 2
        assert usable >= required
        print(f"{name:12} need={required:4} network={network} usable={first}-{last} broadcast={network.broadcast_address} usable_hosts={usable}")
