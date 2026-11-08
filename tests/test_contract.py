import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_schema_has_exactly_four_required_keys():
    schema = json.loads((ROOT / "data/schema.json").read_text())
    contract = schema["json_schema"]
    assert contract["additionalProperties"] is False
    assert set(contract["required"]) == {"intent", "date", "time", "place"}


def test_subnet_allocations_are_adjacent_and_fit_hosts():
    rows = [("10.20.0.0", 22, 1000), ("10.20.4.0", 24, 250),
            ("10.20.5.0", 25, 100), ("10.20.5.128", 27, 20)]
    import ipaddress
    previous_end = None
    for network, prefix, hosts in rows:
        subnet = ipaddress.ip_network(f"{network}/{prefix}")
        assert subnet.num_addresses - 2 >= hosts
        if previous_end is not None:
            assert int(subnet.network_address) == previous_end + 1
        previous_end = int(subnet.broadcast_address)


def test_nacl_denies_abusive_range_before_web_allows():
    import importlib.util
    spec = importlib.util.spec_from_file_location("nacl_sim", ROOT / "tools/nacl_sim.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rules = module.load_rules(str(ROOT / "network/nacl.json"))
    action, _ = module.decide(rules, {"direction": "inbound", "protocol": "tcp", "port": 443,
                                      "address": "198.51.100.9"})
    assert action == "deny"


def test_parse_service_rejects_invalid_model_json():
    import service.app as service
    try:
        service._extract_json("not json")
    except ValueError:
        return
    assert False, "invalid model output must be rejected"
