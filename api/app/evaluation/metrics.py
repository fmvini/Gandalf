from math import log2


def ranking_metrics(titles: list[str], judgments: dict[str, int], k: int) -> dict:
    if k < 1:
        raise ValueError("k must be positive")
    seen = set()
    grades = []
    for title in titles[:k]:
        grades.append(judgments.get(title, 0) if title not in seen else 0)
        seen.add(title)

    def dcg(values):
        return sum(
            (2**grade - 1) / log2(index + 2) for index, grade in enumerate(values)
        )

    ideal = dcg(sorted(judgments.values(), reverse=True)[:k])
    return {
        "precision": sum(grade > 0 for grade in grades) / k,
        "ndcg": dcg(grades) / ideal if ideal else 0.0,
        "fill_rate": min(len(titles), k) / k,
    }
