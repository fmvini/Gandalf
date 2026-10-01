import copy
import json
from pathlib import Path

import httpx
import pytest

from app.evaluation.metrics import ranking_metrics
from app.evaluation.runner import (
    DEFAULT_DATASET,
    compare_reports,
    evaluate,
    load_dataset,
    main,
    regressions,
)

REPORTS = Path(__file__).resolve().parents[2] / "docs/eval-reports"


def accepted_report(filename):
    return json.loads((REPORTS / filename).read_text(encoding="utf-8"))


def test_metrics_reward_order_and_penalize_missing_and_duplicate_items():
    judgments = {"a": 3, "b": 1}
    ideal = ranking_metrics(["a", "b"], judgments, 5)
    assert ideal == {"precision": 0.4, "ndcg": 1.0, "fill_rate": 0.4}
    assert ranking_metrics(["b", "a"], judgments, 5)["ndcg"] < 1
    assert ranking_metrics(["a", "a", "unknown"], judgments, 5)["precision"] == 0.2
    assert ranking_metrics([], judgments, 5) == {
        "precision": 0,
        "ndcg": 0,
        "fill_rate": 0,
    }
    assert ranking_metrics(["a"], {}, 5)["ndcg"] == 0
    with pytest.raises(ValueError):
        ranking_metrics([], judgments, 0)


def test_dataset_rejects_unknown_judgments_and_duplicate_cases(tmp_path):
    data = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    path = tmp_path / "dataset.json"
    data["cases"][0]["judgments"] = {"Invented title": 3}
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown judgment"):
        load_dataset(path)
    data["cases"][1]["id"] = data["cases"][0]["id"]
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="unique"):
        load_dataset(path)


def test_offline_evaluation_is_reproducible_and_does_not_regress(monkeypatch):
    def prohibit_network(*args, **kwargs):
        raise AssertionError("Offline evaluation must never use the network")

    monkeypatch.setattr(httpx.AsyncClient, "send", prohibit_network)
    monkeypatch.setattr(httpx.Client, "send", prohibit_network)
    report = evaluate()
    assert report == evaluate()
    assert report["cases_count"] == 45
    assert len(report["reading_modes"]) == 5
    baseline_dir = Path(__file__).resolve().parents[2] / "docs/eval-reports"
    for k in (5, 10):
        baseline = json.loads(
            (baseline_dir / f"local-v3-baseline-k{k}.json").read_text(encoding="utf-8")
        )
        assert regressions(evaluate(k=k), baseline) == []
        accepted = json.loads(
            (baseline_dir / f"local-v4-calm-k{k}.json").read_text(encoding="utf-8")
        )
        assert regressions(evaluate(k=k), accepted) == []
        cinematic = json.loads(
            (baseline_dir / f"local-v5-cinematic-k{k}.json").read_text(encoding="utf-8")
        )
        assert regressions(evaluate(k=k), cinematic) == []
        genres = accepted_report(f"local-v6-genres-k{k}.json")
        comparison = compare_reports(evaluate(k=k), genres)
        assert comparison["regressions"] == []
        assert comparison["case_regressions_count"] == 0
        instruments = accepted_report(f"local-v7-piano-detective-k{k}.json")
        comparison = compare_reports(evaluate(k=k), instruments)
        assert comparison["regressions"] == []
        assert comparison["case_regressions_count"] == 0
    assert report["summary"]["existence_rate"] == 1
    assert report["summary"]["constraint_satisfaction"] == 1
    assert report["summary"]["creator_limit_ok"] == 1


def test_regression_check_catches_mode_regressions_and_incomparable_data():
    baseline = evaluate()
    current = copy.deepcopy(baseline)
    current["reading_modes"]["FOCUS"]["precision"] = 0
    assert regressions(current, baseline) == [
        f"reading_modes.FOCUS.precision: {baseline['reading_modes']['FOCUS']['precision']} -> 0"
    ]
    current["dataset_sha256"] = "different"
    with pytest.raises(ValueError, match="same dataset"):
        regressions(current, baseline)


@pytest.mark.parametrize("k", [0, 11])
def test_evaluation_rejects_invalid_k(k):
    with pytest.raises(ValueError):
        evaluate(k=k)


def test_comparison_exposes_individual_loss_hidden_by_aggregate_improvement():
    comparison = compare_reports(
        accepted_report("local-v5-cinematic-k5.json"),
        accepted_report("local-v4-calm-k5.json"),
    )
    assert comparison["regressions"] == []
    assert comparison["case_regressions_count"] > 0
    assert not comparison["catalog_changed"]
    assert comparison["baseline_ranking_version"] == "local-rules-v4"
    assert comparison["current_ranking_version"] == "local-rules-v5"
    dune = next(row for row in comparison["case_changes"] if row["id"] == "r07")
    assert dune["metrics"]["precision"] == {"before": 1.0, "after": 0.8, "delta": -0.2}
    assert "precision" in dune["regressed_metrics"]
    assert dune["titles_before"] != dune["titles_after"]


def test_comparison_matches_by_id_not_row_order_and_reports_catalog_change():
    baseline = accepted_report("local-v5-cinematic-k5.json")
    current = copy.deepcopy(baseline)
    current["cases"].reverse()
    current["catalog_sha256"] = "different-catalog"
    comparison = compare_reports(current, baseline)
    assert comparison["catalog_changed"]
    assert comparison["case_changes"] == []
    assert comparison["case_regressions_count"] == 0


def test_comparison_reports_title_only_changes_and_nullable_metrics():
    baseline = accepted_report("local-v5-cinematic-k5.json")
    current = copy.deepcopy(baseline)
    old, new = baseline["cases"][0], current["cases"][0]
    new["titles"] = list(reversed(old["titles"]))
    change = compare_reports(current, baseline)["case_changes"][0]
    assert change["metrics"] == {}
    assert change["regressed_metrics"] == []

    old["metrics"]["existence_rate"] = None
    new["metrics"]["existence_rate"] = 1
    old["metrics"]["constraint_satisfaction"] = 1
    new["metrics"]["constraint_satisfaction"] = None
    new["metrics"]["precision"] = old["metrics"]["precision"] + 0.0000001
    change = compare_reports(current, baseline)["case_changes"][0]
    assert change["metrics"]["existence_rate"] == {
        "before": None,
        "after": 1,
        "delta": None,
    }
    assert change["metrics"]["constraint_satisfaction"] == {
        "before": 1,
        "after": None,
        "delta": None,
    }
    assert change["regressed_metrics"] == ["constraint_satisfaction"]
    assert "precision" not in change["metrics"]


@pytest.mark.parametrize("side", ["current", "baseline"])
@pytest.mark.parametrize(
    "defect", ["duplicate", "count", "id", "module", "mode", "metric"]
)
def test_comparison_rejects_inconsistent_cases(side, defect):
    baseline = accepted_report("local-v5-cinematic-k5.json")
    current = copy.deepcopy(baseline)
    report = current if side == "current" else baseline
    case = report["cases"][0]
    if defect == "duplicate":
        case["id"] = report["cases"][1]["id"]
    elif defect == "count":
        report["cases_count"] += 1
    elif defect == "id":
        case["id"] = "unknown-case"
    elif defect == "module":
        case["module"] = "changed-module"
    elif defect == "mode":
        case["mode"] = "changed-mode"
    else:
        case["metrics"].pop("precision")
    with pytest.raises(ValueError):
        compare_reports(current, baseline)


@pytest.mark.parametrize(
    "field",
    ["k", "dataset_sha256", "metrics_version", "modules", "reading_modes", "metric"],
)
def test_comparison_rejects_incompatible_aggregate_reports(field):
    baseline = accepted_report("local-v5-cinematic-k5.json")
    current = copy.deepcopy(baseline)
    if field in ("modules", "reading_modes"):
        current[field].pop(next(iter(current[field])))
    elif field == "metric":
        current["modules"]["books"].pop("precision")
    else:
        current[field] = "different"
    with pytest.raises(ValueError):
        compare_reports(current, baseline)


def test_cli_default_and_strict_gates_write_the_same_diagnostic(tmp_path, capsys):
    output = tmp_path / "nested/report.json"
    args = [
        "--baseline",
        str(REPORTS / "local-v4-calm-k5.json"),
        "--output",
        str(output),
    ]
    assert main(args) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert printed["comparison"] == report["comparison"]
    assert report["comparison"]["case_regressions_count"] > 0
    assert main([*args, "--fail-on-case-regression"]) == 1
    assert json.loads(output.read_text(encoding="utf-8")) == report
    capsys.readouterr()
    assert (
        main(
            [
                "--baseline",
                str(REPORTS / "local-v5-cinematic-k5.json"),
                "--fail-on-case-regression",
            ]
        )
        == 0
    )


def test_cli_aggregate_gate_still_fails_without_strict_flag(tmp_path, capsys):
    baseline = accepted_report("local-v5-cinematic-k5.json")
    baseline["modules"]["books"]["precision"] = 1
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")
    assert main(["--baseline", str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["regressions"]


def test_cli_without_baseline_preserves_standalone_evaluation(tmp_path, capsys):
    output = tmp_path / "report.json"
    assert main(["--output", str(output)]) == 0
    assert "comparison" not in json.loads(output.read_text(encoding="utf-8"))
    assert json.loads(capsys.readouterr().out)["regressions"] == []


@pytest.mark.parametrize("source", ["dataset", "baseline"])
def test_cli_cannot_overwrite_its_inputs(source, tmp_path, capsys):
    path = tmp_path / "input.json"
    content = (
        DEFAULT_DATASET.read_text(encoding="utf-8")
        if source == "dataset"
        else json.dumps(accepted_report("local-v5-cinematic-k5.json"))
    )
    path.write_text(content, encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main([f"--{source}", str(path), "--output", str(path)])
    assert error.value.code == 2
    assert path.read_text(encoding="utf-8") == content
    assert "must not overwrite" in capsys.readouterr().err


@pytest.mark.parametrize(
    "args, message",
    [
        (["--fail-on-case-regression"], "requires --baseline"),
        (["--k", "0"], "k must be between"),
        (
            ["--k", "10", "--baseline", str(REPORTS / "local-v5-cinematic-k5.json")],
            "same dataset hash and K",
        ),
    ],
)
def test_cli_reports_invalid_arguments_without_writing_output(
    args, message, tmp_path, capsys
):
    output = tmp_path / "report.json"
    with pytest.raises(SystemExit) as error:
        main([*args, "--output", str(output)])
    assert error.value.code == 2
    assert not output.exists()
    assert message in capsys.readouterr().err
