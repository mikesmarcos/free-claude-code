"""Round-trip tests for ALLOW_ADMIN_FROM through admin config manifest."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app


def _local_client(app):
    return TestClient(app, client=("127.0.0.1", 50000))


def _local_allowed_client(app):
    return TestClient(app, client=("10.0.0.5", 50000))


def _set_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)


def _clear_process_config(monkeypatch) -> None:
    from config.settings import get_settings as get_cached_settings

    get_cached_settings.cache_clear()
    for key in (
        "MODEL",
        "NVIDIA_NIM_API_KEY",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "FCC_ENV_FILE",
        "HOST",
        "PORT",
        "ALLOW_ADMIN_FROM",
        "LOG_FILE",
        "ZAI_BASE_URL",
        "CLAUDE_WORKSPACE",
        "CLAUDE_CLI_BIN",
    ):
        monkeypatch.delenv(key, raising=False)


def test_admin_config_exposes_allow_admin_from_field(monkeypatch, tmp_path):
    _set_home(monkeypatch, tmp_path)
    _clear_process_config(monkeypatch)
    app = create_app(lifespan_enabled=False)

    response = _local_client(app).get("/admin/api/config")

    assert response.status_code == 200
    body = response.json()
    fields = {field["key"]: field for field in body["fields"]}
    assert "ALLOW_ADMIN_FROM" in fields
    af_field = fields["ALLOW_ADMIN_FROM"]
    assert af_field["label"] == "Admin Allow List"
    assert af_field["section"] == "runtime"
    assert af_field["secret"] is False
    assert af_field["restart_required"] is True
    assert af_field["locked"] is False


def test_admin_config_allows_valid_allow_admin_from_update(monkeypatch, tmp_path):
    _set_home(monkeypatch, tmp_path)
    _clear_process_config(monkeypatch)
    app = create_app(lifespan_enabled=False)

    response = _local_client(app).post(
        "/admin/api/config/validate",
        json={"values": {"ALLOW_ADMIN_FROM": "10.0.0.0/24, 127.0.0.1"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True


def test_admin_config_rejects_bad_allow_admin_from(monkeypatch, tmp_path):
    _set_home(monkeypatch, tmp_path)
    _clear_process_config(monkeypatch)
    app = create_app(lifespan_enabled=False)

    response = _local_client(app).post(
        "/admin/api/config/validate",
        json={"values": {"ALLOW_ADMIN_FROM": "garbage-value"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any("ALLOW_ADMIN_FROM" in error for error in body["errors"])


def test_admin_apply_writes_allow_admin_from_to_managed_env(monkeypatch, tmp_path):
    _set_home(monkeypatch, tmp_path)
    _clear_process_config(monkeypatch)
    # Pre-seed managed env so ALLOW_ADMIN_FROM is not locked as "process"
    env_file = tmp_path / ".fcc" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text("ALLOW_ADMIN_FROM=127.0.0.1\n", encoding="utf-8")
    app = create_app(lifespan_enabled=False)

    response = _local_client(app).post(
        "/admin/api/config/apply",
        json={
            "values": {
                "MODEL": "deepseek/deepseek-chat",
                "ALLOW_ADMIN_FROM": "10.0.0.0/24, 192.168.1.1",
            }
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["applied"] is True

    text = env_file.read_text(encoding="utf-8")
    assert "MODEL=deepseek/deepseek-chat" in text
    # ALLOW_ADMIN_FROM values containing spaces get quoted by the env writer
    assert "ALLOW_ADMIN_FROM" in text
    assert "10.0.0.0/24" in text
    assert "192.168.1.1" in text

    # ALLOW_ADMIN_FROM triggers restart_required
    assert body["pending_fields"] == ["ALLOW_ADMIN_FROM"]
    assert body["restart"]["required"] is True


def test_admin_apply_allow_admin_from_preserves_other_managed_keys(
    monkeypatch, tmp_path
):
    _set_home(monkeypatch, tmp_path)
    _clear_process_config(monkeypatch)
    env_file = tmp_path / ".fcc" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text(
        "\n".join(
            [
                "MODEL=deepseek/deepseek-chat",
                "DEEPSEEK_API_KEY=existing-secret",
                "HOST=0.0.0.0",
                "PORT=8082",
                "ALLOW_ADMIN_FROM=127.0.0.1",
                "",
            ]
        ),
        encoding="utf-8",
    )
    app = create_app(lifespan_enabled=False)

    response = _local_client(app).post(
        "/admin/api/config/apply",
        json={"values": {"ALLOW_ADMIN_FROM": "10.0.0.0/24, ::1"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["applied"] is True

    text = env_file.read_text(encoding="utf-8")
    assert "MODEL=deepseek/deepseek-chat" in text
    assert "DEEPSEEK_API_KEY=existing-secret" in text
    assert "10.0.0.0/24" in text
    assert "::1" in text
    # HOST/PORT should still be there (not stripped)
    assert "HOST=0.0.0.0" in text
    assert "PORT=8082" in text


def test_admin_apply_allows_blank_allow_admin_from(monkeypatch, tmp_path):
    _set_home(monkeypatch, tmp_path)
    _clear_process_config(monkeypatch)
    # Pre-seed managed env so ALLOW_ADMIN_FROM is not locked as "process"
    env_file = tmp_path / ".fcc" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text("ALLOW_ADMIN_FROM=127.0.0.1\n", encoding="utf-8")
    app = create_app(lifespan_enabled=False)

    response = _local_client(app).post(
        "/admin/api/config/apply",
        json={
            "values": {
                "MODEL": "deepseek/deepseek-chat",
                "ALLOW_ADMIN_FROM": "",
            }
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["applied"] is True

    text = env_file.read_text(encoding="utf-8")
    # ALLOW_ADMIN_FROM should be in the env file (blank resets to loopback default)
    assert "ALLOW_ADMIN_FROM" in text


def test_admin_status_reports_allow_admin_from_fields(monkeypatch, tmp_path):
    _set_home(monkeypatch, tmp_path)
    _clear_process_config(monkeypatch)
    monkeypatch.setenv("ALLOW_ADMIN_FROM", "10.0.0.0/24, 127.0.0.1")
    from config.settings import get_settings as get_cached_settings

    get_cached_settings.cache_clear()
    app = create_app(lifespan_enabled=False)

    response = _local_client(app).get("/admin/api/status")

    assert response.status_code == 200
    body = response.json()
    assert body["allow_admin_from"] == "10.0.0.0/24, 127.0.0.1"
    assert "10.0.0.0/24" in body["allow_admin_from_networks"]
    assert body["host"] == "0.0.0.0"
    assert body["port"] == 8082
