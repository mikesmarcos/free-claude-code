"""Tests for admin access-control guard and the ALLOW_ADMIN_FROM allow-list."""

from __future__ import annotations

import ipaddress
from typing import Any

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from api.admin_routes import _host_in_networks, is_admin_request_allowed
from config.settings import Settings


def _build_request(client_addr: str, *, origin: str | None = None):
    scope = {
        "type": "http",
        "client": (client_addr, 54321),
        "headers": [],
    }
    if origin is not None:
        scope["headers"].append((b"origin", origin.encode()))
    return Request(scope)


class TestHostInNetworks:
    def _networks(self, *cidrs: str):
        return frozenset(ipaddress.ip_network(c, strict=False) for c in cidrs)

    # -- loopback coverage --
    def test_loopback_v4_allowed(self):
        nets = self._networks("127.0.0.0/8")
        assert _host_in_networks("127.0.0.1", nets) is True
        assert _host_in_networks("10.0.0.5", nets) is False

    def test_loopback_v6_allowed(self):
        nets = self._networks("::1/128")
        assert _host_in_networks("::1", nets) is True
        assert _host_in_networks("::2", nets) is False

    def test_none_host_false(self):
        nets = self._networks("127.0.0.0/8")
        assert _host_in_networks(None, nets) is False

    def test_invalid_host_false(self):
        nets = self._networks("127.0.0.0/8")
        assert _host_in_networks("not-an-ip", nets) is False

    def test_bracket_stripping(self):
        nets = self._networks("::1/128")
        assert _host_in_networks("[::1]", nets) is True

    # -- CIDR membership --
    def test_cidr_member_allowed(self):
        nets = self._networks("10.0.0.0/24")
        assert _host_in_networks("10.0.0.5", nets) is True
        assert _host_in_networks("10.0.0.255", nets) is True

    def test_cidr_nonmember_rejected(self):
        nets = self._networks("10.0.0.0/24")
        assert _host_in_networks("10.0.1.1", nets) is False

    # -- IPv4-mapped IPv6 --
    def test_ipv4_source_also_checked_as_mapped_v6(self):
        nets = self._networks("10.0.0.0/24", "::ffff:10.0.0.6/128")
        assert _host_in_networks("10.0.0.5", nets) is True
        assert _host_in_networks("10.0.0.6", nets) is True

    def test_mapped_v6_source_also_checked_as_native_v4(self):
        nets = self._networks("10.0.0.0/24")
        assert _host_in_networks("::ffff:10.0.0.5", nets) is True

    # -- wildcard --
    def test_global_ipv4_wildcard(self):
        nets = self._networks("0.0.0.0/0")
        assert _host_in_networks("8.8.8.8", nets) is True
        assert _host_in_networks("192.168.1.1", nets) is True

    def test_global_ipv6_wildcard(self):
        nets = self._networks("::/0")
        assert _host_in_networks("2001:db8::1", nets) is True
        assert _host_in_networks("::1", nets) is True

    # -- mixed v4/v6 list --
    def test_comma_mixed_list(self):
        nets = self._networks("127.0.0.0/8", "::1/128")
        assert _host_in_networks("127.0.0.1", nets) is True
        assert _host_in_networks("::1", nets) is True
        assert _host_in_networks("10.0.0.5", nets) is False


class TestIsAdminRequestAllowed:
    def _settings(self, raw: str) -> Settings:
        return Settings.model_validate(
            {
                "HOST": "0.0.0.0",
                "PORT": "8082",
                "ALLOW_ADMIN_FROM": raw,
                "nvidia_nim_api_key": "test_key",
                "model": "nvidia_nim/test-model",
            }
        )

    def test_default_loopback_allows_127001(self):
        settings = self._settings("")
        req = _build_request("127.0.0.1")
        assert is_admin_request_allowed(req, settings) is True

    def test_default_loopback_rejects_non_loopback(self):
        settings = self._settings("")
        req = _build_request("10.0.0.5")
        assert is_admin_request_allowed(req, settings) is False

    def test_allows_explicit_cidr_member(self):
        settings = self._settings("10.0.0.0/24")
        req = _build_request("10.0.0.5")
        assert is_admin_request_allowed(req, settings) is True

    def test_rejects_explicit_cidr_nonmember(self):
        settings = self._settings("10.0.0.0/24")
        req = _build_request("10.1.0.5")
        assert is_admin_request_allowed(req, settings) is False

    def test_star_wildcard_allows_any(self):
        settings = self._settings("*")
        assert is_admin_request_allowed(_build_request("8.8.8.8"), settings) is True
        assert is_admin_request_allowed(_build_request("192.168.1.1"), settings) is True
        assert is_admin_request_allowed(_build_request("::1"), settings) is True

    # -- Origin header --
    def test_matching_origin_allowed(self):
        settings = self._settings("127.0.0.1")
        req = _build_request("127.0.0.1", origin="http://127.0.0.1:8082")
        assert is_admin_request_allowed(req, settings) is True

    def test_non_matching_origin_rejected(self):
        settings = self._settings("127.0.0.1")
        req = _build_request("127.0.0.1", origin="https://evil.example.com")
        assert is_admin_request_allowed(req, settings) is False

    def test_missing_origin_not_rejected_by_itself(self):
        settings = self._settings("127.0.0.1")
        req = _build_request("127.0.0.1", origin=None)
        assert is_admin_request_allowed(req, settings) is True

    def test_origin_hostname_checked_against_allow_list(self):
        settings = self._settings("10.0.0.0/24")
        # Peer is allowed, but origin hostname is not in the allow-list
        req = _build_request("10.0.0.5", origin="https://8.8.8.8:8080")
        assert is_admin_request_allowed(req, settings) is False

    def test_origin_with_allowed_hostname(self):
        settings = self._settings("10.0.0.0/24")
        req = _build_request("10.0.0.5", origin="http://10.0.0.1:8082")
        assert is_admin_request_allowed(req, settings) is True


class TestRequireLoopbackAdminOnRoute:
    """Verify that the admin guard is wired on real routes."""

    def _clear_cache(self) -> None:
        from config.settings import get_settings as get_cached_settings

        get_cached_settings.cache_clear()

    def _make_app(self, monkeypatch: Any = None) -> Any:
        from api.app import create_app

        if monkeypatch is not None:
            monkeypatch.delenv("ALLOW_ADMIN_FROM", raising=False)
        self._clear_cache()
        app = create_app(lifespan_enabled=False)
        app.state.provider_registry = None
        return app

    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.delenv("ALLOW_ADMIN_FROM", raising=False)
        return TestClient(self._make_app(), client=("127.0.0.1", 50000))

    def test_loopback_gets_admin_page(self, client):
        response = client.get("/admin")
        assert response.status_code == 200

    def test_non_loopback_gets_403(self, monkeypatch):
        app = self._make_app(monkeypatch)
        client = TestClient(app, client=("10.0.0.5", 50000))
        response = client.get("/admin")
        assert response.status_code == 403

    def test_admin_api_route_uses_same_guard(self, monkeypatch):
        app = self._make_app(monkeypatch)
        client = TestClient(app, client=("10.0.0.5", 50000))
        response = client.post("/admin/api/config/apply", json={"values": {}})
        assert response.status_code == 403

    def test_allow_list_from_env_allows_external(self, monkeypatch):
        monkeypatch.setenv("ALLOW_ADMIN_FROM", "10.0.0.5")
        monkeypatch.setenv("NVIDIA_NIM_API_KEY", "test_key")
        monkeypatch.setenv("MODEL", "nvidia_nim/test-model")
        monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "")
        self._clear_cache()
        app = self._make_app()
        client = TestClient(app, client=("10.0.0.5", 50000))
        response = client.get("/admin")
        assert response.status_code == 200
