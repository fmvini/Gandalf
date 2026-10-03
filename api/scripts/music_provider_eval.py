"""Describe one music-evaluation stage from bounded JSON, without collecting data.

Only the standard library is used. Fixtures and recorded observations never
approve G1; this tool cannot verify provenance claims, listening quality or terms.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from urllib.parse import urlsplit
from uuid import UUID

MAX_BYTES = 4 * 1024 * 1024
MAX_CASES = 200
MAX_PROVIDERS = 16
MAX_OBSERVATIONS = 3200
MAX_ITEMS = 100
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*", re.ASCII)
ITEM_FIELDS = {
    "id",
    "title",
    "artist",
    "tags",
    "duration_ms",
    "has_vocals",
    "energy",
    "provider",
    "external_id",
    "links",
}


class InvalidInput(ValueError):
    """Deliberately carries no input or filesystem details."""


def token(value, limit=64):
    return (
        type(value) is str
        and 0 < len(value) <= limit
        and TOKEN.fullmatch(value) is not None
    )


def require(condition):
    if not condition:
        raise InvalidInput


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def reject_constant(value):
    raise InvalidInput


def load_input(stream):
    raw = stream.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES)
    return json.loads(
        raw, object_pairs_hook=unique_object, parse_constant=reject_constant
    )


def validate_input(data):
    require(
        type(data) is dict
        and set(data)
        == {
            "schema_version",
            "evidence_kind",
            "stage",
            "cases",
            "providers",
            "observations",
        }
    )
    require(type(data["schema_version"]) is int and data["schema_version"] == 1)
    require(data["evidence_kind"] in ("fixture", "recorded"))
    require(data["stage"] in ("provider_search", "recommendation"))
    cases, providers, observations = (
        data["cases"],
        data["providers"],
        data["observations"],
    )
    require(type(cases) is list and len(cases) <= MAX_CASES)
    require(type(providers) is list and len(providers) <= MAX_PROVIDERS)
    require(type(observations) is list and len(observations) <= MAX_OBSERVATIONS)
    case_groups = {}
    for case in cases:
        require(type(case) is dict and set(case) == {"id", "group"})
        require(token(case["id"]) and token(case["group"]))
        require(case["id"] not in case_groups)
        case_groups[case["id"]] = case["group"]
    require(all(token(provider, 32) for provider in providers))
    require(len(set(providers)) == len(providers))
    for observation in observations:
        require(
            type(observation) is dict
            and set(observation)
            == {
                "case_id",
                "provider",
                "outcome",
                "result",
            }
        )
        require(token(observation["case_id"]) and observation["case_id"] in case_groups)
        require(
            token(observation["provider"], 32) and observation["provider"] in providers
        )
        require(observation["outcome"] in ("success", "error"))
        if observation["outcome"] == "error":
            require(observation["result"] is None)
        result = observation["result"]
        if type(result) is dict and type(result.get("items")) is list:
            require(len(result["items"]) <= MAX_ITEMS)
    return case_groups, sorted(providers)


def http_link(value):
    if (
        type(value) is not str
        or not value
        or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        return False
    try:
        parts = urlsplit(value)
        host = parts.hostname
        port = parts.port
        if (
            parts.scheme not in {"http", "https"}
            or not host
            or parts.username is not None
            or parts.password is not None
        ):
            return False
        if port is not None and not 1 <= port <= 65535:
            return False
        if ":" in host:
            from ipaddress import IPv6Address

            IPv6Address(host)
        else:
            labels = host.encode("idna").decode("ascii").rstrip(".").split(".")
            if any(
                not re.fullmatch(
                    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label
                )
                for label in labels
            ):
                return False
        return "\\" not in parts.netloc
    except (ValueError, UnicodeError):
        return False


def canonical_uuid(value):
    if type(value) is not str:
        return False
    try:
        return str(UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def identity_evidence(item):
    """Keep usable identity even when other metadata or the envelope is invalid."""
    if (
        type(item) is not dict
        or not canonical_uuid(item.get("id"))
        or not token(item.get("provider"), 32)
        or type(item.get("external_id")) is not str
        or not item["external_id"].strip()
    ):
        return None
    return {
        "uuid": item["id"],
        "identity": (item["provider"], item["external_id"]),
        "snapshot": json.dumps(item, sort_keys=True, allow_nan=False),
        "metadata": json.dumps(
            {
                key: value
                for key, value in item.items()
                if key not in {"id", "provider", "external_id"}
            },
            sort_keys=True,
            allow_nan=False,
        ),
    }


def item_issues(item, provider):
    if type(item) is not dict:
        return ["item_shape"]
    issues = []
    if not ITEM_FIELDS <= set(item) or set(item) - ITEM_FIELDS - {
        "classification_source"
    }:
        issues.append("item_fields")
    if not canonical_uuid(item.get("id")):
        issues.append("item_uuid")
    if not token(item.get("provider"), 32) or item.get("provider") != provider:
        issues.append("item_provider")
    for field in ("title", "artist", "external_id"):
        value = item.get(field)
        if type(value) is not str or not value.strip():
            issues.append("item_text")
            break
    tags = item.get("tags")
    if type(tags) is not list or any(type(tag) is not str for tag in tags):
        issues.append("item_tags")
    duration = item.get("duration_ms")
    if duration is not None and (type(duration) is not int or duration <= 0):
        issues.append("item_duration")
    vocals = item.get("has_vocals")
    if vocals is not None and type(vocals) is not bool:
        issues.append("item_vocals")
    if item.get("energy") not in (None, "low", "medium", "high"):
        issues.append("item_energy")
    if "classification_source" in item and item["classification_source"] not in (
        "provider_tags",
        "ai_estimate",
    ):
        issues.append("item_classification")
    links = item.get("links")
    if type(links) is not dict or any(
        type(key) is not str or not key or not http_link(value)
        for key, value in links.items()
    ):
        issues.append("item_links")
    return issues


def inspect_result(result, provider, issues):
    before = sum(issues.values())
    if type(result) is not dict:
        issues["result_shape"] += 1
        return [], [], 0, False
    envelope_ok = True
    for code, condition in (
        ("result_fields", set(result) == {"items", "total", "provider", "has_more"}),
        ("result_provider", result.get("provider") == provider),
        ("result_has_more", type(result.get("has_more")) is bool),
    ):
        if not condition:
            issues[code] += 1
            envelope_ok = False
    items = result.get("items")
    if type(items) is not list:
        issues["result_items"] += 1
        return [], [], 0, False
    if type(result.get("total")) is not int or result["total"] < len(items):
        issues["result_total"] += 1
        envelope_ok = False
    valid, evidence, seen = [], [], set()
    for item in items:
        identity = identity_evidence(item)
        if identity is not None:
            evidence.append(identity)
        if type(item) is dict and canonical_uuid(item.get("id")):
            if item["id"] in seen:
                issues["duplicate_item_uuid"] += 1
            seen.add(item["id"])
        failures = item_issues(item, provider)
        issues.update(failures)
        if failures:
            continue
        if envelope_ok:
            valid.append(item)
    return valid, evidence, len(items), sum(issues.values()) == before


def attribute_counts(items, field):
    counts = {
        "denominator_unique_uuid": len(items),
        "known": 0,
        "null": 0,
        "mixed_null_known": 0,
        "conflicting_known_values": 0,
    }
    for snapshots in items.values():
        values = {item[field] for item in snapshots}
        known = values - {None}
        state = (
            "null" if not known else "mixed_null_known" if None in values else "known"
        )
        counts[state] += 1
        counts["conflicting_known_values"] += len(known) > 1
    for state in ("known", "null", "mixed_null_known"):
        counts[state + "_rate"] = counts[state] / len(items) if items else None
    return counts


def unique_metrics(items):
    metrics = {
        field: attribute_counts(items, field)
        for field in ("duration_ms", "has_vocals", "energy")
    }
    duration = {
        "denominator_unique_uuid": len(items),
        "null": 0,
        "in_90_600_seconds": 0,
        "outside_90_600_seconds": 0,
        "mixed": 0,
    }
    classification = {
        "denominator_unique_uuid": len(items),
        "missing": 0,
        "provider_tags": 0,
        "ai_estimate": 0,
        "mixed": 0,
    }
    tags = {"denominator_unique_uuid": len(items), "present": 0, "empty": 0, "mixed": 0}
    for snapshots in items.values():
        states = {
            "null"
            if item["duration_ms"] is None
            else "in_90_600_seconds"
            if 90000 <= item["duration_ms"] <= 600000
            else "outside_90_600_seconds"
            for item in snapshots
        }
        duration[next(iter(states)) if len(states) == 1 else "mixed"] += 1
        states = {item.get("classification_source", "missing") for item in snapshots}
        classification[next(iter(states)) if len(states) == 1 else "mixed"] += 1
        states = {
            "present" if any(tag.strip() for tag in item["tags"]) else "empty"
            for item in snapshots
        }
        tags[next(iter(states)) if len(states) == 1 else "mixed"] += 1
    metrics.update(
        reading_duration=duration, classification_source=classification, tags=tags
    )
    return metrics


def summarize(records, expected_pairs, blocked_ids, ambiguous_pairs):
    observations = Counter(record["outcome"] for record in records)
    pairs = {record["pair"] for record in records}
    rows = [item for record in records for item in record["items"]]
    evidence = [entry for record in records for entry in record["identity_evidence"]]
    ids = {entry["uuid"] for entry in evidence}
    identities = {entry["identity"] for entry in evidence}
    conflicted_identities = {
        entry["identity"] for entry in evidence if entry["uuid"] in blocked_ids
    }
    snapshots, metadata, identity_rows = defaultdict(set), defaultdict(set), Counter()
    for entry in evidence:
        snapshots[entry["identity"]].add(entry["snapshot"])
        metadata[entry["identity"]].add(entry["metadata"])
        identity_rows[entry["identity"]] += 1
    eligible = defaultdict(list)
    for record in records:
        if record["pair"] not in ambiguous_pairs:
            for item in record["items"]:
                if item["id"] not in blocked_ids:
                    eligible[item["id"]].append(item)
    return {
        "matrix": {
            "expected_pairs": expected_pairs,
            "observed_pairs": len(pairs),
            "missing_pairs": expected_pairs - len(pairs),
            "ambiguous_pairs": len(pairs & ambiguous_pairs),
        },
        "observations": {
            key: observations[key]
            for key in ("success_nonempty", "success_empty", "error", "invalid_result")
        },
        "rows": {
            "reported": sum(record["reported"] for record in records),
            "typed_valid": len(rows),
            "invalid": sum(record["reported"] for record in records) - len(rows),
        },
        "unique_items": {
            "uuid_count": len(ids),
            "identity_count": len(identities),
            "conflicted_uuid_count": len(ids & blocked_ids),
            "conflicted_identity_count": len(conflicted_identities),
            "eligible_uuid_count": len(eligible),
            "eligible_identity_count": len(
                {
                    (item["provider"], item["external_id"])
                    for items in eligible.values()
                    for item in items
                }
            ),
        },
        "reobservations": {
            "identity_evidence_rows": len(evidence),
            "exact_repeat_rows_extra": len(evidence)
            - sum(len(values) for values in snapshots.values()),
            "reobserved_identity_count": sum(
                count > 1 for count in identity_rows.values()
            ),
            "metadata_changed_identity_count": sum(
                len(values) > 1 for values in metadata.values()
            ),
            "metadata_variants_extra": sum(
                len(values) - 1 for values in metadata.values()
            ),
        },
        "metrics": unique_metrics(eligible),
    }


def evaluate(data):
    case_groups, providers = validate_input(data)
    issues, records = Counter(), []
    identities, ids = defaultdict(set), defaultdict(set)
    for observation in data["observations"]:
        pair = (observation["case_id"], observation["provider"])
        items, evidence, reported, valid = [], [], 0, True
        outcome = "error"
        if observation["outcome"] == "success":
            items, evidence, reported, valid = inspect_result(
                observation["result"], pair[1], issues
            )
            outcome = (
                "invalid_result"
                if not valid
                else "success_nonempty"
                if reported
                else "success_empty"
            )
        records.append(
            {
                "pair": pair,
                "group": case_groups[pair[0]],
                "items": items,
                "identity_evidence": evidence,
                "reported": reported,
                "outcome": outcome,
            }
        )
        for entry in evidence:
            identities[entry["uuid"]].add(entry["identity"])
            ids[entry["identity"]].add(entry["uuid"])
    pair_counts = Counter(record["pair"] for record in records)
    ambiguous_pairs = {pair for pair, count in pair_counts.items() if count > 1}
    issues["duplicate_observation"] = sum(count - 1 for count in pair_counts.values())
    collision_ids = {
        item_id for item_id, values in identities.items() if len(values) > 1
    }
    conflicting_identities = {
        identity for identity, values in ids.items() if len(values) > 1
    }
    blocked_ids = collision_ids | {
        item_id for identity in conflicting_identities for item_id in ids[identity]
    }
    issues["uuid_identity_collision"] = len(collision_ids)
    issues["identity_uuid_conflict"] = len(conflicting_identities)
    violations = {code: count for code, count in sorted(issues.items()) if count}
    groups = sorted(set(case_groups.values()))
    return {
        "schema_version": 1,
        "stage": data["stage"],
        "evidence_kind": data["evidence_kind"],
        "status": "contract_violations" if violations else "ok",
        "g1_status": "NOT_EVALUATED",
        "g1_approved": False,
        "denominators": "Metrics use eligible unique UUIDs, excluding identity conflicts and ambiguous observation pairs; rows count all reported items. Mixed snapshots remain mixed.",
        "violations": violations,
        "totals": summarize(
            records, len(case_groups) * len(providers), blocked_ids, ambiguous_pairs
        ),
        "providers": {
            provider: summarize(
                [record for record in records if record["pair"][1] == provider],
                len(case_groups),
                blocked_ids,
                ambiguous_pairs,
            )
            for provider in providers
        },
        "groups": {
            group: {
                "providers": {
                    provider: summarize(
                        [
                            record
                            for record in records
                            if record["group"] == group
                            and record["pair"][1] == provider
                        ],
                        sum(value == group for value in case_groups.values()),
                        blocked_ids,
                        ambiguous_pairs,
                    )
                    for provider in providers
                }
            }
            for group in groups
        },
    }


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        require(len(args) == 1)
        if args[0] == "-":
            data = load_input(sys.stdin.buffer)
        else:
            with open(args[0], "rb") as stream:
                data = load_input(stream)
        report = evaluate(data)
        exit_code = 1 if report["violations"] else 0
    except (
        InvalidInput,
        OSError,
        ValueError,
        TypeError,
        RecursionError,
        OverflowError,
    ):
        report = {
            "schema_version": 1,
            "status": "invalid_input",
            "g1_status": "NOT_EVALUATED",
            "g1_approved": False,
            "error": {"code": "INVALID_INPUT", "message": "Unable to evaluate input."},
        }
        exit_code = 2
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
