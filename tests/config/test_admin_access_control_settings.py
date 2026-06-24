"""Tests for ALLOW_ADMIN_FROM validation in Settings."""

from __future__ import annotations

import ipaddress

import pytest
from pydantic import ValidationError

from config.settings import Settings


class TestAllowAdminFromValidation:
    """Test the ALLOW_ADMIN_FROM field_validator."""

    def _settings(self, raw: str, **extra) -> Settings:
        base: dict[str, object] = {
            "ALLOW_ADMIN_FROM": raw,
        }
        base.update(extra)
        return Settings.model_validate(base)

    # -- blank/default behavior --
    def test_blank_defaults_to_empty_string(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("")
        assert settings.allow_admin_from == ""

    def test_none_treated_as_blank(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("")
        assert settings.allow_admin_from == ""

    # -- wildcard forms --
    def test_star_wildcard_accepted(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("*")
        assert settings.allow_admin_from == "*"

    def test_global_v4_wildcard_accepted(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("0.0.0.0")
        assert settings.allow_admin_from == "0.0.0.0"

    def test_global_v6_wildcard_accepted(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("::")
        assert settings.allow_admin_from == "::"

    # -- single IP / CIDR --
    def test_single_ip_accepted(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("10.0.0.5")
        assert settings.allow_admin_from == "10.0.0.5"

    def test_single_v6_ip_accepted(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("::1")
        assert settings.allow_admin_from == "::1"

    def test_cidr_block_accepted(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("10.0.0.0/24")
        assert settings.allow_admin_from == "10.0.0.0/24"

    # -- comma-separated list --
    def test_comma_separated_list_normalized(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("10.0.0.1, 10.0.0.2, 192.168.1.0/24")
        assert settings.allow_admin_from == "10.0.0.1, 10.0.0.2, 192.168.1.0/24"

    def test_comma_list_with_extra_spaces_cleaned(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("  10.0.0.1  ,   127.0.0.1  ")
        assert settings.allow_admin_from == "10.0.0.1, 127.0.0.1"

    def test_trailing_comma_ignored(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("10.0.0.1,")
        assert settings.allow_admin_from == "10.0.0.1"

    def test_leading_comma_ignored(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings(",10.0.0.1")
        assert settings.allow_admin_from == "10.0.0.1"

    # -- wildcard mixed with CIDRs --
    def test_wildcard_mixed_with_cidrs(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("10.0.0.0/24, *, ::1")
        assert settings.allow_admin_from == "10.0.0.0/24, *, ::1"

    # -- rejection of malformed entries --
    def test_malformed_ip_raises(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        with pytest.raises(ValidationError, match="Invalid ALLOW_ADMIN_FROM entry"):
            self._settings("not-a-valid-ip")

    def test_malformed_cidr_raises(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        with pytest.raises(ValidationError, match="Invalid ALLOW_ADMIN_FROM entry"):
            self._settings("10.0.0.0/99")

    def test_malformed_in_mixed_list_raises(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        with pytest.raises(ValidationError, match="Invalid ALLOW_ADMIN_FROM entry"):
            self._settings("127.0.0.1, garbage, 10.0.0.0/24")

    # -- env var loading --
    def test_env_var_loaded(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        monkeypatch.setenv("ALLOW_ADMIN_FROM", "10.0.0.0/24, 192.168.1.1")
        settings = Settings()
        assert settings.allow_admin_from == "10.0.0.0/24, 192.168.1.1"

    def test_env_var_blank_uses_empty_string(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        monkeypatch.setenv("ALLOW_ADMIN_FROM", "")
        settings = Settings()
        assert settings.allow_admin_from == ""

    def test_Host_and_Port_explicit_aliases(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        monkeypatch.setenv("HOST", "192.168.1.100")
        monkeypatch.setenv("PORT", "9090")
        settings = Settings()
        assert settings.host == "192.168.1.100"
        assert settings.port == 9090


class TestAllowAdminFromNetworks:
    """Test allow_admin_from_networks() method."""

    def _settings(self, raw: str) -> Settings:
        return Settings.model_validate({"ALLOW_ADMIN_FROM": raw})

    # -- default loopback --
    def test_blank_returns_loopback_networks(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("")
        nets = list(settings.allow_admin_from_networks())
        assert ipaddress.ip_network("127.0.0.0/8") in nets
        assert ipaddress.ip_network("::1/128") in nets

    def test_default_nets_cover_127001(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("")
        nets = settings.allow_admin_from_networks()
        assert any(ipaddress.ip_address("127.0.0.1") in net for net in nets)

    def test_default_nets_exclude_non_loopback(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("")
        nets = settings.allow_admin_from_networks()
        assert not any(ipaddress.ip_address("10.0.0.5") in net for net in nets)

    # -- wildcard --
    def test_star_returns_universal_networks(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("*")
        nets = settings.allow_admin_from_networks()
        assert ipaddress.ip_network("0.0.0.0/0") in nets
        assert ipaddress.ip_network("::/0") in nets

    def test_global_v4_maps_to_wildcard_network(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("0.0.0.0")
        nets = settings.allow_admin_from_networks()
        assert ipaddress.ip_network("0.0.0.0/0") in nets

    def test_global_v6_maps_to_wildcard_network(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("::")
        nets = settings.allow_admin_from_networks()
        assert ipaddress.ip_network("::/0") in nets

    # -- explicit CIDR --
    def test_explicit_cidr_converted_to_network(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("10.0.0.0/24")
        nets = settings.allow_admin_from_networks()
        assert ipaddress.ip_network("10.0.0.0/24") in nets

    def test_single_ip_becomes_host_network(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("10.0.0.5")
        nets = settings.allow_admin_from_networks()
        assert ipaddress.ip_network("10.0.0.5/32") in nets

    # -- comma-separated --
    def test_comma_list_creates_multiple_networks(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("10.0.0.0/24, 127.0.0.1, ::1")
        nets = settings.allow_admin_from_networks()
        assert len(nets) == 3
        assert ipaddress.ip_network("10.0.0.0/24") in nets
        assert ipaddress.ip_network("127.0.0.1/32") in nets
        assert ipaddress.ip_network("::1/128") in nets

    # -- frozenset type --
    def test_returns_frozenset(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", ())
        settings = self._settings("10.0.0.0/24")
        nets = settings.allow_admin_from_networks()
        assert isinstance(nets, frozenset)
