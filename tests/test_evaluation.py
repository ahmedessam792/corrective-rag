from crag.evaluation import retrieval_metrics, support_metrics


def test_retrieval_metrics_are_computed() -> None:
    metrics = retrieval_metrics([["a", "b"], ["x", "y"]], [{"b"}, {"x"}], k=2)
    assert metrics.recall_at_k == 1.0
    assert metrics.mean_reciprocal_rank == 0.75
    assert metrics.ndcg_at_k > 0.8


def test_false_supported_is_explicit() -> None:
    metrics = support_metrics([True, True, False], [True, False, False])
    assert metrics.false_supported == 1
    assert metrics.precision == 0.5

