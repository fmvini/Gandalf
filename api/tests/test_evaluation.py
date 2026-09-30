import copy
import json
from pathlib import Path

import httpx
import pytest

from app.evaluation.metrics import ranking_metrics
from app.evaluation.runner import DEFAULT_DATASET, evaluate, load_dataset, regressions


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
