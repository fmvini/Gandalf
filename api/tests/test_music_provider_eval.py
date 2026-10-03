"""G1 tooling only: synthetic/manifest inputs, no collection or application."""

import ast
import builtins
import io
import json
import socket
import sys
from pathlib import Path
from uuid import UUID

import pytest

from scripts import music_provider_eval as evaluation

ROOT = Path(__file__).resolve().parents[2]


def item(number=1, provider="fixture-a", **changes):
    return {
        "id": str(UUID(int=number)),
        "title": "Synthetic private-looking title",
        "artist": "Synthetic artist",
        "tags": ["instrumental"],
        "duration_ms": None,
        "has_vocals": None,
        "energy": None,
        "provider": provider,
        "external_id": f"recording-{number}",
        "links": {"provider": "https://catalog.example.test/recording"},
        **changes,
    }


def observation(case="first", provider="fixture-a", items=None, **result_changes):
    items = [item(provider=provider)] if items is None else items
    return {
        "case_id": case,
        "provider": provider,
        "outcome": "success",
        "result": {
            "provider": provider,
            "total": len(items),
            "items": items,
            "has_more": False,
            **result_changes,
        },
    }


def dataset(observations=None, **changes):
    return {
        "schema_version": 1,
        "evidence_kind": "fixture",
        "stage": "provider_search",
        "providers": ["fixture-a"],
        "cases": [{"id": "first", "group": "ambient"}],
        "observations": [observation()] if observations is None else observations,
        **changes,
    }


def cli(data, tmp_path, capsys):
    path = tmp_path / "input.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    code = evaluation.main([str(path)])
    captured = capsys.readouterr()
    assert captured.err == ""
    return code, json.loads(captured.out)


def test_root_fixture_exact_counts_and_provenance():
    path = ROOT / "docs/evaluation/music-provider-fixture-v1.json"
    report = evaluation.evaluate(json.loads(path.read_text(encoding="utf-8")))
    assert report["status"] == "ok"
    assert report["violations"] == {}
    assert report["g1_approved"] is False
    assert report["totals"]["matrix"] == {
        "expected_pairs": 6,
        "observed_pairs": 5,
        "missing_pairs": 1,
        "ambiguous_pairs": 0,
    }
    assert report["totals"]["observations"] == {
        "success_nonempty": 3,
        "success_empty": 1,
        "error": 1,
        "invalid_result": 0,
    }
    assert report["totals"]["rows"] == {"reported": 3, "typed_valid": 3, "invalid": 0}
    assert report["totals"]["unique_items"]["eligible_uuid_count"] == 3
    assert report["providers"]["fixture-a"]["metrics"]["has_vocals"]["null"] == 1
    assert report["providers"]["fixture-b"]["metrics"]["has_vocals"]["known"] == 2
    assert report["totals"]["metrics"]["classification_source"] == {
        "denominator_unique_uuid": 3,
        "missing": 1,
        "provider_tags": 1,
        "ai_estimate": 1,
        "mixed": 0,
    }
    assert report["totals"]["metrics"]["reading_duration"]["in_90_600_seconds"] == 2


def test_root_snapshot_template_retains_every_missing_pair():
    path = ROOT / "docs/evaluation/music-provider-g1-snapshot-template.json"
    report = evaluation.evaluate(json.loads(path.read_text(encoding="utf-8")))
    assert report["evidence_kind"] == "recorded"
    assert report["g1_status"] == "NOT_EVALUATED"
    assert report["g1_approved"] is False
    assert report["totals"]["matrix"] == {
        "expected_pairs": 24,
        "observed_pairs": 0,
        "missing_pairs": 24,
        "ambiguous_pairs": 0,
    }
    assert len(report["groups"]) == 6
    for group in report["groups"].values():
        for provider in group["providers"].values():
            assert provider["matrix"]["missing_pairs"] == 2
            assert provider["metrics"]["energy"]["known_rate"] is None
            assert provider["metrics"]["energy"]["denominator_unique_uuid"] == 0


@pytest.mark.parametrize("stage", ["provider_search", "recommendation"])
def test_global_stage_total_and_has_more_are_only_declared(stage, tmp_path, capsys):
    data = dataset([observation(total=100000, has_more=False)], stage=stage)
    code, report = cli(data, tmp_path, capsys)
    assert code == 0
    assert report["stage"] == stage
    assert report["g1_approved"] is False
    assert report["totals"]["rows"]["reported"] == 1
    assert "exhausted" not in json.dumps(report)
    assert "100000" not in json.dumps(report), "Do not sum catalog/page totals"


def test_reobservation_is_not_duplicate_coverage_or_inferred_instrumental():
    data = dataset(
        [observation(), observation("second")],
        cases=[
            {"id": "first", "group": "ambient"},
            {"id": "second", "group": "ambient"},
        ],
    )
    report = evaluation.evaluate(data)
    assert report["violations"] == {}
    assert report["totals"]["rows"]["reported"] == 2
    assert report["totals"]["unique_items"]["uuid_count"] == 1
    metrics = report["groups"]["ambient"]["providers"]["fixture-a"]["metrics"]
    assert (
        metrics["has_vocals"]["null"]
        == metrics["has_vocals"]["denominator_unique_uuid"]
        == 1
    )
    assert metrics["tags"]["present"] == 1
    assert metrics["classification_source"]["missing"] == 1
    assert report["totals"]["unique_items"]["identity_count"] == 1
    assert report["totals"]["reobservations"] == {
        "identity_evidence_rows": 2,
        "exact_repeat_rows_extra": 1,
        "reobserved_identity_count": 1,
        "metadata_changed_identity_count": 0,
        "metadata_variants_extra": 0,
    }


def test_metadata_reobservation_is_mixed_without_arbitrary_winner():
    changed = item(
        duration_ms=180000,
        has_vocals=False,
        energy="low",
        classification_source="ai_estimate",
    )
    data = dataset(
        [observation(), observation("second", items=[changed])],
        cases=[{"id": "first", "group": "ambient"}, {"id": "second", "group": "other"}],
    )
    report = evaluation.evaluate(data)
    assert report["violations"] == {}
    assert report["totals"]["metrics"]["has_vocals"]["mixed_null_known"] == 1
    assert report["totals"]["metrics"]["reading_duration"]["mixed"] == 1
    assert report["totals"]["metrics"]["classification_source"]["mixed"] == 1
    assert report["totals"]["reobservations"]["exact_repeat_rows_extra"] == 0
    assert report["totals"]["reobservations"]["metadata_changed_identity_count"] == 1
    assert report["totals"]["reobservations"]["metadata_variants_extra"] == 1
    assert (
        report["groups"]["ambient"]["providers"]["fixture-a"]["metrics"]["has_vocals"][
            "null"
        ]
        == 1
    )
    assert (
        report["groups"]["other"]["providers"]["fixture-a"]["metrics"]["has_vocals"][
            "known"
        ]
        == 1
    )
    data["observations"].reverse()
    assert evaluation.evaluate(data) == report


def test_itemwide_provenance_never_assigns_origin_to_each_attribute():
    report = evaluation.evaluate(
        dataset(
            [
                observation(
                    items=[
                        item(
                            has_vocals=False,
                            energy="low",
                            classification_source="ai_estimate",
                        )
                    ]
                )
            ]
        )
    )
    metrics = report["totals"]["metrics"]
    assert metrics["classification_source"]["ai_estimate"] == 1
    assert metrics["has_vocals"]["known"] == 1
    assert "ai_estimate" not in metrics["has_vocals"]


def test_conflicting_known_metadata_remains_descriptive_not_identity_collision():
    first = item(has_vocals=False, energy="low", duration_ms=180000)
    second = item(has_vocals=True, energy="high", duration_ms=700000)
    report = evaluation.evaluate(
        dataset(
            [observation(items=[first]), observation("second", items=[second])],
            cases=[
                {"id": "first", "group": "ambient"},
                {"id": "second", "group": "ambient"},
            ],
        )
    )
    assert report["violations"] == {}
    for field in ("has_vocals", "energy", "duration_ms"):
        assert report["totals"]["metrics"][field]["known"] == 1
        assert report["totals"]["metrics"][field]["conflicting_known_values"] == 1
    assert report["totals"]["metrics"]["reading_duration"]["mixed"] == 1
    assert report["totals"]["metrics"]["classification_source"]["missing"] == 1
    assert report["g1_approved"] is False


@pytest.mark.parametrize(
    "duration,state",
    [
        (None, "null"),
        (89999, "outside_90_600_seconds"),
        (90000, "in_90_600_seconds"),
        (600000, "in_90_600_seconds"),
        (600001, "outside_90_600_seconds"),
    ],
)
def test_reading_duration_boundaries_are_descriptive(duration, state):
    report = evaluation.evaluate(
        dataset([observation(items=[item(duration_ms=duration)])])
    )
    assert report["totals"]["metrics"]["reading_duration"][state] == 1
    assert report["g1_approved"] is False


def test_duplicate_within_result_is_flagged_before_unique_aggregation(tmp_path, capsys):
    code, report = cli(dataset([observation(items=[item(), item()])]), tmp_path, capsys)
    assert code == 1
    assert report["violations"] == {"duplicate_item_uuid": 1}
    assert report["totals"]["rows"]["reported"] == 2
    assert report["totals"]["unique_items"]["uuid_count"] == 1


def test_duplicate_observation_has_no_winner_or_extra_matrix_coverage(tmp_path, capsys):
    code, report = cli(
        dataset([observation(), observation(items=[])]), tmp_path, capsys
    )
    assert code == 1
    assert report["violations"]["duplicate_observation"] == 1
    assert report["totals"]["matrix"]["observed_pairs"] == 1
    assert report["totals"]["matrix"]["ambiguous_pairs"] == 1
    assert report["totals"]["unique_items"]["eligible_uuid_count"] == 0


@pytest.mark.parametrize("same_uuid", [True, False])
def test_identity_conflicts_are_global_and_excluded_without_choosing_winner(
    same_uuid, tmp_path, capsys
):
    second = item(
        1 if same_uuid else 2, external_id="other" if same_uuid else "recording-1"
    )
    data = dataset(
        [observation(), observation("second", items=[second])],
        cases=[{"id": "first", "group": "one"}, {"id": "second", "group": "two"}],
    )
    code, report = cli(data, tmp_path, capsys)
    assert code == 1
    assert report["violations"] == {
        "uuid_identity_collision" if same_uuid else "identity_uuid_conflict": 1
    }
    assert report["totals"]["unique_items"]["eligible_uuid_count"] == 0
    assert report["totals"]["unique_items"]["conflicted_uuid_count"] == (
        1 if same_uuid else 2
    )
    data["observations"].reverse()
    assert evaluation.evaluate(data) == report


@pytest.mark.parametrize("same_uuid", [True, False])
def test_same_external_id_across_providers_is_only_conflict_if_uuid_shared(same_uuid):
    second = item(
        1 if same_uuid else 2, provider="fixture-b", external_id="recording-1"
    )
    report = evaluation.evaluate(
        dataset(
            [observation(), observation(provider="fixture-b", items=[second])],
            providers=["fixture-a", "fixture-b"],
        )
    )
    assert report["violations"] == ({"uuid_identity_collision": 1} if same_uuid else {})
    assert report["totals"]["unique_items"]["eligible_uuid_count"] == (
        0 if same_uuid else 2
    )


@pytest.mark.parametrize("same_uuid", [True, False])
@pytest.mark.parametrize("invalid_envelope", [True, False])
def test_bad_metadata_or_envelope_cannot_hide_identity_conflict(
    same_uuid, invalid_envelope
):
    second = item(
        1 if same_uuid else 2,
        external_id="other" if same_uuid else "recording-1",
        duration_ms=True,
    )
    record = observation("second", items=[second])
    if invalid_envelope:
        record["result"]["provider"] = "wrong-source"
    data = dataset(
        [observation(), record],
        cases=[{"id": "first", "group": "one"}, {"id": "second", "group": "two"}],
    )
    report = evaluation.evaluate(data)
    assert report["violations"]["item_duration"] == 1
    assert (
        report["violations"][
            "uuid_identity_collision" if same_uuid else "identity_uuid_conflict"
        ]
        == 1
    )
    assert report["totals"]["rows"] == {"reported": 2, "typed_valid": 1, "invalid": 1}
    assert report["totals"]["unique_items"]["eligible_uuid_count"] == 0
    assert report["providers"]["fixture-a"]["metrics"]["energy"]["known_rate"] is None
    data["observations"].reverse()
    assert evaluation.evaluate(data) == report


def test_exact_bad_metadata_duplicate_and_tags_changes_are_not_hidden():
    bad = item(duration_ms=True)
    report = evaluation.evaluate(dataset([observation(items=[bad, bad])]))
    assert report["violations"]["duplicate_item_uuid"] == 1
    assert report["totals"]["reobservations"]["exact_repeat_rows_extra"] == 1
    assert report["totals"]["unique_items"]["identity_count"] == 1
    changed = item(tags=["jazz"])
    report = evaluation.evaluate(dataset([observation(items=[item(), changed])]))
    assert "uuid_identity_collision" not in report["violations"]
    assert "identity_uuid_conflict" not in report["violations"]
    assert report["totals"]["reobservations"]["metadata_changed_identity_count"] == 1


def test_whitespace_tags_are_not_useful_presence():
    report = evaluation.evaluate(dataset([observation(items=[item(tags=["", "  "])])]))
    assert report["totals"]["metrics"]["tags"]["empty"] == 1


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("id", "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA", "item_uuid"),
        ("id", "invalid", "item_uuid"),
        ("id", 1, "item_uuid"),
        ("provider", "fixture-b", "item_provider"),
        ("duration_ms", True, "item_duration"),
        ("duration_ms", 90000.0, "item_duration"),
        ("duration_ms", 0, "item_duration"),
        ("duration_ms", -1, "item_duration"),
        ("has_vocals", 0, "item_vocals"),
        ("has_vocals", "false", "item_vocals"),
        ("energy", "unknown", "item_energy"),
        ("classification_source", None, "item_classification"),
        ("classification_source", "measured", "item_classification"),
        ("tags", [1], "item_tags"),
        ("artist", "", "item_text"),
        ("links", {"provider": "javascript:alert(1)"}, "item_links"),
        ("links", {"provider": "https://username:SECRET@example.test/"}, "item_links"),
        ("links", {"provider": "https://bad_host.test/"}, "item_links"),
        ("links", {"provider": "https://example.test:99999/"}, "item_links"),
        ("links", {"provider": "https://example.test/\nsecret"}, "item_links"),
    ],
)
def test_strict_item_contract_and_sanitized_violations(
    field, value, code, tmp_path, capsys
):
    data = dataset([observation(items=[item(**{field: value})])])
    exit_code, report = cli(data, tmp_path, capsys)
    assert exit_code == 1
    assert report["violations"][code] == 1
    assert report["totals"]["rows"]["invalid"] == 1
    assert "SECRET" not in json.dumps(report)
    assert "Synthetic private-looking title" not in json.dumps(report)


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("provider", "fixture-b", "result_provider"),
        ("total", True, "result_total"),
        ("total", 0, "result_total"),
        ("total", 1.0, "result_total"),
        ("has_more", 0, "result_has_more"),
        ("items", {}, "result_items"),
    ],
)
def test_strict_envelope_contract(field, value, code):
    record = observation()
    record["result"][field] = value
    report = evaluation.evaluate(dataset([record]))
    assert report["violations"][code] == 1
    assert report["totals"]["observations"]["invalid_result"] == 1


@pytest.mark.parametrize("missing", sorted(evaluation.ITEM_FIELDS))
def test_required_nullable_fields_must_be_present(missing):
    record = observation()
    del record["result"]["items"][0][missing]
    assert evaluation.evaluate(dataset([record]))["violations"]["item_fields"] == 1


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": True},
        {"schema_version": 2},
        {"stage": "mixed"},
        {"stage": None},
        {"providers": ["token with space"]},
        {"providers": ["é"]},
        {"providers": ["a" * 33]},
        {"providers": ["fixture-a", "fixture-a"]},
        {"cases": [{"id": "bad/slash", "group": "ambient"}]},
        {"cases": [{"id": "first", "group": "x" * 65}]},
        {"cases": [{"id": "first", "group": "ambient"}] * 2},
        {
            "observations": [
                {
                    "case_id": "unknown",
                    "provider": "fixture-a",
                    "outcome": "error",
                    "result": None,
                }
            ]
        },
        {
            "observations": [
                {
                    "case_id": "first",
                    "provider": "unknown",
                    "outcome": "error",
                    "result": None,
                }
            ]
        },
        {
            "observations": [
                {
                    "case_id": "first",
                    "provider": "fixture-a",
                    "outcome": "error",
                    "result": {"message": "SECRET"},
                }
            ]
        },
    ],
)
def test_invalid_dataset_is_generic_json_without_details(change, tmp_path, capsys):
    code, report = cli(dataset(**change), tmp_path, capsys)
    assert code == 2
    assert report == {
        "schema_version": 1,
        "status": "invalid_input",
        "g1_status": "NOT_EVALUATED",
        "g1_approved": False,
        "error": {"code": "INVALID_INPUT", "message": "Unable to evaluate input."},
    }


def test_stage_missing_unknown_fields_and_limits_are_refused():
    samples = []
    missing = dataset()
    del missing["stage"]
    samples.append(missing)
    samples.append(dataset(private_prompt="SECRET"))
    samples.append(
        dataset(cases=[{"id": f"c{i}", "group": "group"} for i in range(201)])
    )
    samples.append(dataset(providers=[f"p{i}" for i in range(17)]))
    samples.append(dataset(observations=[observation()] * 3201))
    samples.append(dataset([observation(items=[item(i) for i in range(101)])]))
    for data in samples:
        with pytest.raises(evaluation.InvalidInput):
            evaluation.evaluate(data)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"schema_version":1,"schema_version":1}',
        b"NaN",
        b"Infinity",
        b"-Infinity",
        b'{"secret":"SECRET"',
        b"\xff",
    ],
)
def test_invalid_json_is_sanitized(raw, tmp_path, capsys):
    path = tmp_path / "SECRET-private-path.json"
    path.write_bytes(raw)
    assert evaluation.main([str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "SECRET" not in captured.out
    assert "Traceback" not in captured.out
    assert json.loads(captured.out)["error"]["code"] == "INVALID_INPUT"


def test_byte_limit_no_application_network_or_environment_dependencies(monkeypatch):
    tree = ast.parse(Path(evaluation.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(
                alias.name.split(".")[0] in sys.stdlib_module_names
                for alias in node.names
            )
        if isinstance(node, ast.ImportFrom):
            assert node.module.split(".")[0] in sys.stdlib_module_names
    original_import = builtins.__import__

    def safe_import(name, *args, **kwargs):
        assert name.split(".")[0] not in {"app", "sqlalchemy", "httpx", "requests"}
        return original_import(name, *args, **kwargs)

    def no_network(*args, **kwargs):
        pytest.fail("Offline evaluation attempted network collection")

    monkeypatch.setattr(builtins, "__import__", safe_import)
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket, "socket", no_network)
    raw = json.dumps(dataset()).encode()
    padded = raw + b" " * (evaluation.MAX_BYTES - len(raw))
    assert (
        evaluation.evaluate(evaluation.load_input(io.BytesIO(padded)))["status"] == "ok"
    )
    with pytest.raises(evaluation.InvalidInput):
        evaluation.load_input(io.BytesIO(padded + b" "))


def test_stdin_io_failures_arguments_and_empty_matrix(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(
        sys,
        "stdin",
        type(
            "Input",
            (),
            {
                "buffer": io.BytesIO(
                    json.dumps(dataset([], cases=[], providers=[])).encode()
                )
            },
        )(),
    )
    assert evaluation.main(["-"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["totals"]["matrix"]["expected_pairs"] == 0
    assert report["g1_approved"] is False
    for args in ([], ["SECRET", "extra"], [str(tmp_path / "SECRET-missing.json")]):
        assert evaluation.main(args) == 2
        captured = capsys.readouterr()
        assert captured.err == ""
        assert "SECRET" not in captured.out
