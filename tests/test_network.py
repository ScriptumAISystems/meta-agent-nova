import pytest

from nova.system.network import VPNPlan, build_vpn_plan, export_vpn_plan


def test_build_vpn_plan_wireguard():
    plan = build_vpn_plan("wireguard")
    assert isinstance(plan, VPNPlan)
    assert plan.vpn_type == "WireGuard"
    markdown = plan.to_markdown()
    assert "WireGuard" in markdown
    assert "Voraussetzungen" in markdown


def test_build_vpn_plan_openvpn_case_insensitive():
    plan = build_vpn_plan("OpenVPN")
    assert plan.vpn_type == "OpenVPN"
    assert "OpenVPN" in plan.to_markdown()


def test_build_vpn_plan_invalid():
    with pytest.raises(ValueError):
        build_vpn_plan("ipsec")


def test_export_vpn_plan(tmp_path):
    plan = build_vpn_plan("wireguard")
    path = tmp_path / "vpn" / "plan.md"
    exported = export_vpn_plan(plan, path)
    assert exported == path
    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("# Wireguard Remote Access Plan")
