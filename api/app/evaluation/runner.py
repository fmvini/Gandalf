import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.evaluation.metrics import ranking_metrics
from app.providers.local_catalog import BOOKS, MUSIC
from app.schemas.recommendation import DiscoveryRequest, MusicFilters, ReadingRequest
from app.services.recommendation_service import RANKING_VERSION, RecommendationService

DEFAULT_DATASET = (
    Path(__file__).resolve().parents[2] / "evaluation/local-golden-v1.json"
)


class Constraints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vocals: bool | None = None
    energy: list[Literal["low", "medium", "high"]] = Field(default_factory=list)
    forbidden_titles: list[str] = Field(default_factory=list)
    forbidden_tags: list[str] = Field(default_factory=list)


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    module: Literal["music", "books", "reading"]
    query: str = ""
    book: str | None = None
    mode: Literal["FOCUS", "IMMERSIVE", "CINEMATIC", "CALM", "CUSTOM"] = "FOCUS"
    vocals: Literal["INSTRUMENTAL", "MINIMAL", "ANY"] = "INSTRUMENTAL"
    filters: MusicFilters = Field(default_factory=MusicFilters)
    judgments: dict[str, Literal[1, 2, 3]]
    constraints: Constraints = Field(default_factory=Constraints)

    @model_validator(mode="after")
    def valid_request(self):
        if self.module == "reading":
            if self.book is None or (self.mode == "CUSTOM" and not self.query.strip()):
                raise ValueError(
                    "Reading cases require a book and CUSTOM requires context"
                )
        elif len(self.query.strip()) < 3:
            raise ValueError("Discovery cases require a query")
        if not self.judgments:
            raise ValueError("Each case requires at least one relevant item")
        return self


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    methodology: str
    cases: list[Case]


def load_dataset(path: Path) -> tuple[Dataset, str]:
    raw = path.read_bytes()
    dataset = Dataset.model_validate_json(raw)
    counts = Counter(case.module for case in dataset.cases)
    if any(counts[module] < 15 for module in ("music", "books", "reading")):
        raise ValueError("At least 15 cases per module are required")
    if len({case.id for case in dataset.cases}) != len(dataset.cases):
        raise ValueError("Case IDs must be unique")
    modes = Counter(case.mode for case in dataset.cases if case.module == "reading")
    if any(
        modes[mode] < 3
        for mode in ("FOCUS", "IMMERSIVE", "CINEMATIC", "CALM", "CUSTOM")
    ):
        raise ValueError("At least three cases per reading mode are required")
    catalogs = {"books": {b.title for b in BOOKS}, "music": {m["title"] for m in MUSIC}}
    for case in dataset.cases:
        titles = catalogs["books" if case.module == "books" else "music"]
        if not set(case.judgments) <= titles:
            raise ValueError(f"Unknown judgment title in {case.id}")
        if case.module == "reading" and case.book not in catalogs["books"]:
            raise ValueError(f"Unknown book in {case.id}")
    return dataset, hashlib.sha256(raw).hexdigest()


def evaluate(path: Path = DEFAULT_DATASET, k: int = 5) -> dict:
    if not 1 <= k <= 10:
        raise ValueError("k must be between 1 and 10")
    dataset, digest = load_dataset(path)
    service, rows = RecommendationService(), []
    books = {book.title: book for book in BOOKS}
    known = {"books": {str(b.id) for b in BOOKS}, "music": {m["id"] for m in MUSIC}}
    for case in dataset.cases:
        if case.module == "reading":
            book = books[case.book]
            result = service.reading(
                book,
                ReadingRequest(
                    book_id=book.id,
                    mode=case.mode,
                    context=case.query,
                    vocals=case.vocals,
                    target_duration_min=max(15, k * 5),
                ),
            )
        else:
            result = service.discover(
                case.module,
                DiscoveryRequest(
                    query=case.query,
                    filters=case.filters,
                    limit=k,
                ),
            )
        items = [row["item"] for row in result["items"][:k]]
        titles = [item["title"] for item in items]
        catalog = known["books" if case.module == "books" else "music"]
        valid, violations = 0, []
        creators = Counter()
        for item in items:
            creators[item.get("artist", ", ".join(item.get("authors", [])))] += 1
            valid += str(item["id"]) in catalog
            tags = set(item.get("tags", item.get("genres", [])))
            constraint = case.constraints
            if (
                item["title"] in constraint.forbidden_titles
                or tags & set(constraint.forbidden_tags)
                or (
                    constraint.vocals is not None
                    and item.get("has_vocals") is not constraint.vocals
                )
                or (constraint.energy and item.get("energy") not in constraint.energy)
            ):
                violations.append(item["title"])
        rows.append(
            {
                "id": case.id,
                "module": case.module,
                "mode": case.mode if case.module == "reading" else None,
                "titles": titles,
                "violations": violations,
                "metrics": {
                    **ranking_metrics(titles, case.judgments, k),
                    "diversity": len(creators) / k,
                    "existence_rate": valid / len(items) if items else None,
                    "constraint_satisfaction": 1 - len(violations) / len(items)
                    if items
                    else None,
                    "creator_limit_ok": float(
                        all(count <= 2 for count in creators.values())
                    ),
                    "nonempty": float(bool(items)),
                    "coverage": float(len(items) >= k),
                },
            }
        )

    def aggregate(selected):
        metrics = {}
        for name in rows[0]["metrics"]:
            values = [
                r["metrics"][name] for r in selected if r["metrics"][name] is not None
            ]
            metrics[name] = round(mean(values), 6) if values else None
        return metrics

    return {
        "metrics_version": "1",
        "dataset_version": dataset.version,
        "dataset_sha256": digest,
        "ranking_version": RANKING_VERSION,
        "catalog_sha256": hashlib.sha256(
            json.dumps(
                {
                    "books": [book.model_dump(mode="json") for book in BOOKS],
                    "music": MUSIC,
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode()
        ).hexdigest(),
        "k": k,
        "cases_count": len(rows),
        "methodology": dataset.methodology,
        "summary": aggregate(rows),
        "modules": {
            module: aggregate([r for r in rows if r["module"] == module])
            for module in ("music", "books", "reading")
        },
        "reading_modes": {
            mode: aggregate([r for r in rows if r["mode"] == mode])
            for mode in ("FOCUS", "IMMERSIVE", "CINEMATIC", "CALM", "CUSTOM")
        },
        "cases": rows,
    }


def regressions(current: dict, baseline: dict) -> list[str]:
    if (current["dataset_sha256"], current["k"]) != (
        baseline["dataset_sha256"],
        baseline["k"],
    ):
        raise ValueError("Baseline requires the same dataset hash and K")
    if current["metrics_version"] != baseline["metrics_version"]:
        raise ValueError("Baseline requires the same metric definitions")
    failures = []
    for group in ("modules", "reading_modes"):
        if current[group].keys() != baseline[group].keys():
            raise ValueError(f"Reports require the same {group} groups")
        for module in current[group]:
            if current[group][module].keys() != baseline[group][module].keys():
                raise ValueError(f"Group {module} requires the same metric definitions")
            for metric, old in baseline[group][module].items():
                new = current[group][module][metric]
                if old is not None and (new is None or new + 1e-6 < old):
                    failures.append(f"{group}.{module}.{metric}: {old} -> {new}")
    return failures


def compare_reports(current: dict, baseline: dict) -> dict:
    """Expose individual tradeoffs without changing the aggregate acceptance gate."""
    failures = regressions(current, baseline)

    def index_cases(report):
        cases = {case["id"]: case for case in report["cases"]}
        if len(cases) != len(report["cases"]) or len(cases) != report["cases_count"]:
            raise ValueError("Reports require unique case IDs and consistent counts")
        return cases

    before, after = index_cases(baseline), index_cases(current)
    if before.keys() != after.keys():
        raise ValueError("Reports require the same case IDs")
    changes = []
    for case_id in sorted(after):
        old, new = before[case_id], after[case_id]
        if (old["module"], old["mode"]) != (new["module"], new["mode"]):
            raise ValueError(f"Case {case_id} changed module or reading mode")
        if old["metrics"].keys() != new["metrics"].keys():
            raise ValueError(f"Case {case_id} requires the same metric definitions")
        metrics, losses = {}, []
        for name, value in old["metrics"].items():
            updated = new["metrics"][name]
            if value == updated or (
                value is not None
                and updated is not None
                and abs(value - updated) <= 1e-6
            ):
                continue
            metrics[name] = {
                "before": value,
                "after": updated,
                "delta": round(updated - value, 6)
                if value is not None and updated is not None
                else None,
            }
            if value is not None and (updated is None or updated < value):
                losses.append(name)
        if metrics or old["titles"] != new["titles"]:
            changes.append(
                {
                    "id": case_id,
                    "module": new["module"],
                    "mode": new["mode"],
                    "titles_before": old["titles"],
                    "titles_after": new["titles"],
                    "metrics": metrics,
                    "regressed_metrics": losses,
                }
            )
    return {
        "baseline_ranking_version": baseline["ranking_version"],
        "current_ranking_version": current["ranking_version"],
        "catalog_changed": baseline["catalog_sha256"] != current["catalog_sha256"],
        "regressions": failures,
        "case_regressions_count": sum(bool(c["regressed_metrics"]) for c in changes),
        "case_changes": changes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Evaluate local recommendations without network access"
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--fail-on-case-regression",
        action="store_true",
        help="Also fail when any individual case metric regresses (requires --baseline)",
    )
    args = parser.parse_args(argv)
    if args.fail_on_case_regression and not args.baseline:
        parser.error("--fail-on-case-regression requires --baseline")
    if args.output and args.output.resolve() in {
        path.resolve() for path in (args.dataset, args.baseline) if path
    }:
        parser.error("--output must not overwrite the dataset or baseline")
    comparison = None
    try:
        report = evaluate(args.dataset, args.k)
        if args.baseline:
            comparison = compare_reports(
                report, json.loads(args.baseline.read_text(encoding="utf-8"))
            )
            report["comparison"] = comparison
    except (ValueError, OSError) as error:
        parser.error(str(error))
    failures = comparison["regressions"] if comparison else []
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {
                "modules": report["modules"],
                "regressions": failures,
                **({"comparison": comparison} if comparison else {}),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return int(
        bool(failures)
        or bool(
            args.fail_on_case_regression
            and comparison
            and comparison["case_regressions_count"]
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
