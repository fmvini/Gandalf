"""Offline refusal boundaries; these tests do not claim a deployment PASS."""

import hashlib
import importlib.util
import json
import ssl
from copy import deepcopy
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock
from urllib.request import BaseHandler, ProxyHandler, Request, build_opener
from urllib.response import addinfourl

import pytest

PATH = Path(__file__).resolve().parents[2] / "scripts/deployment_gate.py"
SPEC = importlib.util.spec_from_file_location("deployment_gate", PATH)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
RUN = "9e1e2a1f-6a86-4e63-91ce-fd06d39da55d"
PROJECT = "gandalf_deploy_9e1e2a1f6a864e6391cefd06d39da55d"


def config_fixture():
    name = "gandalf_gate_9e1e2a1f6a864e6391cefd06d39da55d"
    env = {
        "GANDALF_GATE_UUID": RUN,
        "GANDALF_GATE_PROJECT": PROJECT,
        "POSTGRES_DB": name,
        "POSTGRES_USER": name,
        "POSTGRES_PASSWORD": "x" * 40,
        "JWT_SECRET": "j" * 48,
        "GANDALF_DEPLOY_DATABASE_URL": f"postgresql+psycopg://{name}:{'x' * 40}@db:5432/{name}",
    }
    services = {}
    for service, target in gate.SERVICES.items():
        value = {
            "labels": {gate.LABEL: RUN},
            "networks": {"default": {}},
            "ports": [
                {
                    "target": target,
                    "published": "0",
                    "host_ip": "127.0.0.1",
                    "protocol": "tcp",
                }
            ],
            "pull_policy": "never",
        }
        if service == "db":
            value.update(
                image=gate.PG_IMAGE,
                environment={
                    key: env[key]
                    for key in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
                },
                volumes=[
                    {
                        "type": "tmpfs",
                        "target": "/var/lib/postgresql",
                        "tmpfs": {"size": 536870912},
                    }
                ],
            )
        else:
            value.update(
                image=PROJECT + "-" + service + ":gate",
                build={
                    "context": str(gate.ROOT),
                    "dockerfile": service + "/Dockerfile",
                    "labels": {gate.LABEL: RUN},
                },
            )
        services[service] = value
    services["api"].update(
        command=["python", "deploy.py"],
        environment={
            "DATABASE_URL": env["GANDALF_DEPLOY_DATABASE_URL"],
            "JWT_SECRET": env["JWT_SECRET"],
            "ONLINE_CATALOG": "false",
            "BOOK_PROVIDER": "local",
            "GROQ_API_KEY": "",
            "GANDALF_ONLINE": "0",
            "CORS_ORIGINS": "[]",
        },
    )
    return {
        "name": PROJECT,
        "services": services,
        "networks": {
            "default": {
                "name": PROJECT + "_default",
                "internal": False,
                "driver": "bridge",
                "labels": {gate.LABEL: RUN},
            }
        },
    }, env


def test_valid_effective_config():
    config, env = config_fixture()
    gate.validate_config(config, env)


def test_compose_normalized_tmpfs_size_is_accepted():
    config, env = config_fixture()
    config["services"]["db"]["volumes"][0]["tmpfs"]["size"] = "536870912"
    gate.validate_config(config, env)


@pytest.mark.parametrize("size", ["512M", "536870913", "0", -1])
def test_other_tmpfs_size_is_refused(size):
    config, env = config_fixture()
    config["services"]["db"]["volumes"][0]["tmpfs"]["size"] = size
    with pytest.raises(gate.GateError):
        gate.validate_config(config, env)


@pytest.mark.parametrize(
    "path,value",
    [
        (("name",), "gandalf"),
        (("volumes",), {"production": {}}),
        (("secrets",), {"secret": {}}),
        (("services", "api", "env_file"), [{"path": "api/.env"}]),
        (
            ("services", "api", "volumes"),
            [{"type": "bind", "source": "/data", "target": "/data"}],
        ),
        (("services", "api", "command"), ["python", "local.py"]),
        (("services", "api", "privileged"), True),
        (("services", "api", "network_mode"), "host"),
        (("services", "api", "environment", "ONLINE_CATALOG"), "true"),
        (("services", "api", "environment", "GROQ_API_KEY"), "private-value"),
        (("services", "api", "build", "context"), "/other"),
        (("services", "api", "build", "dockerfile"), "other/Dockerfile"),
        (("services", "api", "build", "secrets"), ["production"]),
        (("services", "frontend", "image"), "gandalf-frontend:latest"),
        (("services", "db", "image"), "postgres:latest"),
        (
            ("services", "db", "volumes"),
            [{"type": "volume", "source": "existing", "target": "/var/lib/postgresql"}],
        ),
        (("networks", "default", "internal"), True),
        (("networks", "default", "driver"), "host"),
        (("networks", "default", "external"), True),
    ],
)
def test_rejects_unsafe_config(path, value):
    config, env = config_fixture()
    cursor = config
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises((gate.GateError, KeyError, ValueError)):
        gate.validate_config(config, env)


@pytest.mark.parametrize(
    "host,port", [("0.0.0.0", "0"), ("127.0.0.1", "5432"), ("localhost", "0")]
)
def test_config_refuses_non_ephemeral_publish(host, port):
    config, env = config_fixture()
    config["services"]["db"]["ports"][0].update(host_ip=host, published=port)
    with pytest.raises(gate.GateError):
        gate.validate_config(config, env)


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:49152",
        "http://127.1:49152",
        "http://2130706433:49152",
        "https://127.0.0.1:49152",
        "http://127.0.0.1:49152/path",
        "http://u:p@127.0.0.1:49152",
        "http://127.0.0.1:49152?secret=x",
        *[f"http://127.0.0.1:{port}" for port in gate.FORBIDDEN_PORTS],
    ],
)
def test_refuses_unsafe_http_origin(origin):
    with pytest.raises((gate.GateError, ValueError)):
        gate.validate_origin(origin)


def container_fixture():
    return {
        "Id": "a" * 64,
        "Image": "sha256:" + "b" * 64,
        "Config": {
            "Labels": {
                gate.LABEL: RUN,
                "com.docker.compose.project": PROJECT,
                "com.docker.compose.service": "api",
            },
            "Cmd": ["python", "deploy.py"],
        },
        "HostConfig": {
            "PortBindings": {"8000/tcp": [{"HostIp": "127.0.0.1", "HostPort": "0"}]}
        },
        "Mounts": [],
        "NetworkSettings": {"Networks": {PROJECT + "_default": {}}},
    }


@pytest.mark.parametrize(
    "change", ["uuid", "project", "service", "image", "mount", "port", "network", "id"]
)
def test_cleanup_refuses_foreign_identity(change):
    item = container_fixture()
    images = {"api": item["Image"]}
    if change in {"uuid", "project", "service"}:
        key = {
            "uuid": gate.LABEL,
            "project": "com.docker.compose.project",
            "service": "com.docker.compose.service",
        }[change]
        item["Config"]["Labels"][key] = "foreign"
    elif change == "image":
        item["Image"] = "sha256:" + "c" * 64
    elif change == "mount":
        item["Mounts"] = [{"Type": "bind", "Destination": "/data"}]
    elif change == "port":
        item["HostConfig"]["PortBindings"]["8000/tcp"][0]["HostIp"] = "0.0.0.0"
    elif change == "network":
        item["NetworkSettings"]["Networks"] = {"production": {}}
    elif change == "id":
        item["Id"] = "short"
    with pytest.raises((gate.GateError, KeyError)):
        gate.validate_container(item, RUN, PROJECT, images)


def test_container_valid_and_cleanup_reinspects_before_delete(monkeypatch):
    item = container_fixture()
    images = {"api": item["Image"]}
    assert gate.validate_container(item, RUN, PROJECT, images) == "api"
    runner = gate.Runner()
    runner.run, runner.project, runner.images = RUN, PROJECT, images
    runner.mutated = True
    runner.containers = {"api": item["Id"]}
    monkeypatch.setattr(runner, "discover", Mock())
    changed = deepcopy(item)
    changed["Config"]["Labels"][gate.LABEL] = "foreign"
    monkeypatch.setattr(runner, "inspect", Mock(return_value=changed))
    command = Mock(return_value="")
    monkeypatch.setattr(runner, "command", command)
    with pytest.raises(gate.GateError):
        runner.cleanup()
    assert all("rm" not in call.args[0] for call in command.call_args_list)


def test_network_refuses_foreign_endpoint():
    item = {
        "Id": "d" * 64,
        "Name": PROJECT + "_default",
        "Internal": False,
        "Driver": "bridge",
        "Labels": {gate.LABEL: RUN, "com.docker.compose.project": PROJECT},
        "Containers": {"foreign": {}},
    }
    with pytest.raises(gate.GateError):
        gate.validate_network(item, RUN, PROJECT, set())


def test_environment_drops_app_and_compose_inputs():
    source = {
        "PATH": "safe",
        "DATABASE_URL": "production",
        "JWT_SECRET": "secret",
        "GROQ_API_KEY": "secret",
        "COMPOSE_PROJECT_NAME": "production",
        "DOCKER_HOST": "tcp://remote:2375",
        "HTTP_PROXY": "production",
        "POSTGRES_DB": "production",
        "GANDALF_ONLINE": "1",
    }
    assert gate.clean_environment(source) == {"PATH": "safe"}


def test_no_optin_no_subprocess_and_sanitized_final_json(monkeypatch, capsys):
    monkeypatch.delenv("GANDALF_DEPLOYMENT_ALLOW", raising=False)
    subprocess = Mock()
    monkeypatch.setattr(gate.subprocess, "run", subprocess)
    assert gate.main() == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "FAIL" and output["stage"] == "opt-in"
    assert output["cleanup"]["verified"] is True
    subprocess.assert_not_called()


def test_command_failure_does_not_reflect_secrets():
    error = gate.CommandFailure(
        1,
        'secret DSN password\n{"status":"FAIL","stage":"browser-create","error_kind":"AssertionError","secret":"private"}',
    )
    assert str(error) == "Child command failed"
    assert (
        error.child_stage == "browser-create" and error.child_kind == "AssertionError"
    )


def test_sql_proof_is_syntactically_valid_and_read_only():
    compile(gate.SQL_PROOF, "postgres_proof", "exec")
    assert "SET TRANSACTION READ ONLY" in gate.SQL_PROOF


def test_redirect_is_rejected_before_second_request():
    calls = []

    class OfflineTransport(BaseHandler):
        handler_order = 0

        def http_open(self, request):
            calls.append(request.full_url)
            headers = Message()
            headers["Location"] = "http://127.0.0.1:8000/private"
            result = addinfourl(BytesIO(b""), headers, request.full_url, 302)
            result.msg = "Found"
            return result

    opener = build_opener(ProxyHandler({}), OfflineTransport(), gate.RejectRedirects())
    with pytest.raises(gate.GateError):
        opener.open(Request("http://127.0.0.1:49152/api/v1/system/status"))
    assert calls == ["http://127.0.0.1:49152/api/v1/system/status"]


def test_partial_build_cleanup_removes_only_verified_own_tag(monkeypatch):
    runner = gate.Runner()
    runner.run, runner.project, runner.images = (
        RUN,
        PROJECT,
        {"db": "sha256:" + "d" * 64},
    )
    runner.mutated = True
    tag = PROJECT + "-api:gate"
    image = {
        "Id": "sha256:" + "b" * 64,
        "RepoTags": [tag],
        "Config": {"Labels": {gate.LABEL: RUN}},
    }
    monkeypatch.setattr(runner, "inspect", Mock(return_value=image))
    monkeypatch.setattr(runner, "discover", Mock())
    calls = []

    def command(args, **_kwargs):
        calls.append(args)
        return tag + "\n" if args[1:3] == ["image", "ls"] else ""

    monkeypatch.setattr(runner, "command", command)
    assert runner.cleanup()["verified"] is True
    assert [args for args in calls if "rm" in args] == [["docker", "image", "rm", tag]]


def test_partial_build_cleanup_refuses_wrong_image_label(monkeypatch):
    runner = gate.Runner()
    runner.run, runner.project, runner.images = RUN, PROJECT, {}
    runner.mutated = True
    tag = PROJECT + "-api:gate"
    monkeypatch.setattr(
        runner,
        "inspect",
        Mock(
            return_value={
                "Id": "sha256:" + "b" * 64,
                "RepoTags": [tag],
                "Config": {"Labels": {gate.LABEL: "foreign"}},
            }
        ),
    )
    command = Mock(return_value=tag + "\n")
    monkeypatch.setattr(runner, "command", command)
    with pytest.raises(gate.GateError):
        runner.cleanup()
    assert all("rm" not in call.args[0] for call in command.call_args_list)


@pytest.fixture
def public_ca(tmp_path):
    path = tmp_path / ".impeccable/runtime/ca.pem"
    path.parent.mkdir(parents=True)
    certificate = ssl.create_default_context().get_ca_certs(binary_form=True)[0]
    path.write_text(ssl.DER_cert_to_PEM_cert(certificate), encoding="ascii")
    return tmp_path, path


def ca_config(root, path):
    config, env = config_fixture()
    env["GANDALF_BUILD_CA_CERT"] = str(path)
    config["secrets"] = {
        "gandalf_build_ca": {
            "name": PROJECT + "_gandalf_build_ca",
            "file": str(path),
        }
    }
    for service in ("api", "frontend"):
        config["services"][service]["build"].update(
            context=str(root),
            secrets=[{"source": "gandalf_build_ca", "target": "gandalf_build_ca"}],
        )
    return config, env


def test_explicit_public_build_ca_only(public_ca):
    root, path = public_ca
    resolved, digest = gate.validate_build_ca(str(path), root)
    assert resolved == path and len(digest) == 64
    config, env = ca_config(root, path)
    gate.validate_config(config, env, root)
    assert "GANDALF_BUILD_CA_CERT" not in gate.clean_environment(env)


@pytest.mark.parametrize(
    "change", ["outside", "relative", "private-key", "invalid-pem", "oversized"]
)
def test_build_ca_rejects_unapproved_file(public_ca, change):
    root, path = public_ca
    value = str(path)
    if change == "outside":
        outside = root / "outside.pem"
        outside.write_bytes(path.read_bytes())
        value = str(outside)
    elif change == "relative":
        value = ".impeccable/runtime/ca.pem"
    elif change == "private-key":
        path.write_text(
            "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----"
        )
    elif change == "invalid-pem":
        path.write_text("-----BEGIN CERTIFICATE-----\nYWJj\n-----END CERTIFICATE-----")
    else:
        path.write_bytes(b"x" * (1024 * 1024 + 1))
    with pytest.raises((gate.GateError, ssl.SSLError)):
        gate.validate_build_ca(value, root)


@pytest.mark.parametrize(
    "change", ["extra-secret", "runtime-secret", "wrong-target", "secret-env"]
)
def test_build_ca_exception_cannot_expand_to_other_secrets(public_ca, change):
    root, path = public_ca
    config, env = ca_config(root, path)
    if change == "extra-secret":
        config["secrets"]["production"] = {"file": str(path)}
    elif change == "runtime-secret":
        config["services"]["api"]["secrets"] = ["gandalf_build_ca"]
    elif change == "wrong-target":
        config["services"]["frontend"]["build"]["secrets"][0]["target"] = "other"
    else:
        config["secrets"]["gandalf_build_ca"] = {"environment": "PRIVATE_SECRET"}
    with pytest.raises(gate.GateError):
        gate.validate_config(config, env, root)


def test_ca_change_is_in_source_snapshot(public_ca):
    _, path = public_ca
    before = gate.source_snapshot(path)
    path.write_bytes(path.read_bytes() + b"\n")
    assert gate.source_snapshot(path) != before


def test_invalid_ca_fails_before_any_child_with_sanitized_output(monkeypatch, capsys):
    monkeypatch.setenv("GANDALF_DEPLOYMENT_ALLOW", "isolated-coordinated")
    monkeypatch.setenv("GANDALF_BUILD_CA_CERT", "private-path.pem")
    command = Mock()
    monkeypatch.setattr(gate.subprocess, "run", command)
    assert gate.main() == 1
    output = capsys.readouterr().out
    result = json.loads(output)
    assert result["stage"] == "preflight" and result["cleanup"]["verified"]
    assert "private-path" not in output
    command.assert_not_called()


def test_browser_failure_diagnostic_reconstructs_only_safe_fields():
    item = {
        "substage": "register-page-ready",
        "failure_location": [
            {"file": "deployment.mjs", "line": 195, "column": 4, "message": "private"}
        ],
        "auth_diagnostic": {
            "path": "/register",
            "form_present": True,
            "form_busy": False,
            "alert_count": 0,
            "invalid_fields": ["auth-email"],
            "email": "private",
        },
        "traffic": [
            {
                "request": "POST /api/v1/auth/register 201",
                "count": 1,
                "password": "private",
            },
            {"request": "GET /api/v1/private?token=private 200", "count": 1},
        ],
        "message": "private",
    }
    result = gate.child_diagnostic(item)
    assert result["substage"] == "register-page-ready"
    assert result["failure_location"] == [
        {"file": "deployment.mjs", "line": 195, "column": 4}
    ]
    assert result["traffic"] == [
        {"request": "POST /api/v1/auth/register 201", "count": 1}
    ]
    assert result["auth_diagnostic"]["invalid_fields"] == ["auth-email"]
    assert "private" not in json.dumps(result)


def test_browser_failure_diagnostic_rejects_unknown_routes_inputs_and_locations():
    result = gate.child_diagnostic(
        {
            "substage": "password:private",
            "failure_location": [{"file": "private", "line": 1, "column": 1}],
            "auth_diagnostic": {
                "path": "/private",
                "form_present": True,
                "form_busy": False,
                "alert_count": 0,
                "invalid_fields": ["private"],
            },
            "traffic": [
                {"request": "POST /api/v1/auth/register 201", "count": "private"}
            ],
        }
    )
    assert result == {"failure_location": [], "traffic": []}


def test_last_browser_progress_is_safe_and_does_not_replace_failure():
    progress = json.dumps(
        {
            "status": "PROGRESS",
            "stage": "account-a-register",
            "substage": "register-page-ready",
            "password": "private",
        }
    )
    failure = json.dumps(
        {
            "status": "FAIL",
            "stage": "account-a-register",
            "error_kind": "TimeoutError",
            "substage": "register-login-notice",
        }
    )
    cleanup = json.dumps(
        {
            "status": "FAIL",
            "stage": "account-a-register",
            "error_kind": "BrowserCleanupDeadline",
            "substage": "browser-close-finally",
        }
    )
    error = gate.CommandFailure(
        -1, progress + "\n" + failure + "\n" + progress + "\n" + cleanup
    )
    assert error.child_kind == "TimeoutError"
    assert error.child_diagnostic["substage"] == "register-login-notice"
    assert "private" not in json.dumps(error.child_diagnostic)
    pending = gate.CommandFailure(-1, progress)
    assert pending.child_diagnostic["substage"] == "register-page-ready"


def browser_fixture():
    other = "51ba605b-25e0-4b20-9bf4-661637a2d134"
    return {
        "version": 1,
        "phase": "create",
        "status": "PASS",
        "run_fingerprint": hashlib.sha256(RUN.encode()).hexdigest(),
        "base_url": "http://127.0.0.1:49152",
        "user_ids": [RUN, other],
        "favorite_ids": [RUN, other],
        "playlist_ids": [RUN],
        "public_snapshot_id": RUN,
        "public_snapshot_music_ids": [RUN],
        "playlist_music_ids": [RUN],
        "favorites": [
            {"id": RUN, "type": "MUSIC", "item_id": RUN},
            {"id": other, "type": "BOOK", "item_id": other},
        ],
        "checks": [
            "offline-status",
            "real-refresh-via-ui",
            "real-same-origin-api-and-clean-browser",
            "nginx-direct-spa-paths",
            "public-music-and-explanation",
            "two-accounts-ownership-and-logout-revocation",
            "saved-snapshots-preserved-for-runner-sql-and-restart",
        ],
        "browser_errors": 0,
        "console_errors": 0,
        "blocked_external_requests": 0,
        "proven_logout_abort_count": 0,
    }


def test_browser_success_reconstructs_nested_public_favorites():
    source = browser_fixture()
    source["favorites"][0]["token"] = "private"
    source["traffic"] = [{"password": "private"}]
    output = gate.browser_artifact(source, "create", RUN, source["base_url"])
    assert output["checks"] == source["checks"]
    assert "private" not in json.dumps(output) and "traffic" not in output


@pytest.mark.parametrize(
    "field,value",
    [
        ("checks", [{"token": "private"}]),
        ("checks", ["private"]),
        ("browser_errors", {"token": "private"}),
        ("console_errors", True),
        ("blocked_external_requests", 1),
        ("public_snapshot_id", "private"),
        ("playlist_music_ids", ["private"]),
        ("base_url", "http://127.0.0.1:8000"),
        ("version", True),
        ("proven_logout_abort_count", True),
        ("proven_logout_abort_count", 5),
    ],
)
def test_browser_success_rejects_unvalidated_nested_or_wrong_values(field, value):
    source = browser_fixture()
    source[field] = value
    with pytest.raises((gate.GateError, ValueError)):
        gate.browser_artifact(source, "create", RUN, "http://127.0.0.1:49152")


def test_browser_failure_counters_and_codes_are_reconstructed():
    result = gate.child_diagnostic(
        {
            "browser_errors": 0,
            "console_errors": 1,
            "blocked_external_requests": 0,
            "failures": [
                {
                    "kind": "requestfailed",
                    "method": "POST",
                    "path": "/api/v1/auth/logout",
                    "error_code": "net::ERR_ABORTED",
                    "token": "private",
                },
                {
                    "kind": "http",
                    "method": "GET",
                    "path": "/api/v1/private",
                    "status": 404,
                    "error_code": "private",
                },
            ],
        }
    )
    assert result["console_errors"] == 1
    assert result["failures"] == [
        {
            "kind": "requestfailed",
            "method": "POST",
            "path": "/api/v1/auth/logout",
            "error_code": "net::ERR_ABORTED",
        },
        {"kind": "http", "method": "GET", "path": "/other", "status": 404},
    ]
    assert "private" not in json.dumps(result)


@pytest.mark.parametrize(
    "change",
    [
        "authorized-api",
        "api-unannounced",
        "frontend",
        "wrong-id",
        "duplicate-port",
        "wrong-stage",
    ],
)
def test_restart_accepts_only_verified_api_port_rebind(monkeypatch, change):
    runner = gate.Runner()
    runner.run, runner.project = RUN, PROJECT
    runner.stage = "restart-own-api"
    runner.containers = {
        service: str(index) * 64 for index, service in enumerate(gate.SERVICES, 1)
    }
    runner.network_id = "d" * 64
    runner.ports = {"api": 49152, "frontend": 49153, "db": 49154}
    items = {}
    for service, identifier in runner.containers.items():
        port = runner.ports[service] + (10 if service == "api" else 0)
        items[identifier] = {
            "State": {"Running": True, "Health": {"Status": "healthy"}},
            "NetworkSettings": {
                "Networks": {PROJECT + "_default": {}},
                "Ports": {
                    str(gate.SERVICES[service]) + "/tcp": [
                        {"HostIp": "127.0.0.1", "HostPort": str(port)}
                    ]
                },
            },
        }
    api_id = runner.containers["api"]
    if change == "frontend":
        items[runner.containers["frontend"]]["NetworkSettings"]["Ports"]["80/tcp"][0][
            "HostPort"
        ] = "49200"
    elif change == "wrong-id":
        api_id = "f" * 64
    elif change == "duplicate-port":
        items[api_id]["NetworkSettings"]["Ports"]["8000/tcp"][0]["HostPort"] = "49153"
    elif change == "wrong-stage":
        runner.stage = "preflight"
    monkeypatch.setattr(runner, "discover", Mock())
    monkeypatch.setattr(runner, "inspect", lambda _kind, identifier: items[identifier])
    arguments = {} if change == "api-unannounced" else {"restarted_api": api_id}
    if change == "authorized-api":
        runner.live_identity(**arguments)
        assert runner.ports == {"api": 49162, "frontend": 49153, "db": 49154}
    else:
        with pytest.raises(gate.GateError):
            runner.live_identity(**arguments)
