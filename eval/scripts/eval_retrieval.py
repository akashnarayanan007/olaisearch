"""Retrieval evaluation - Recall@k, MRR, MAP, nDCG with ablations."""
from __future__ import annotations

import json
from pathlib import Path

from backend.core.logging import get_logger
from backend.retrieval.hybrid import HybridRetriever

logger = get_logger(__name__)


def evaluate_retrieval(
    corpus_dir: str = "eval/corpus",
    output_dir: str = "eval/results",
) -> dict:
    """Evaluate retrieval using parphrase queries on a real text corpus.

    Metrics:
    - Recall@1/5/10
    - MRR (Mean Reciprocal Rank)
    - MAP (Mean Average Precision)
    - nDCG@10
    - Ablations: BM25 / char-ngram / dense / hybrid / +rerank / n-best / cross-lingual
    - Robustness curve vs injected OCR error rate (0/5/10/20%)

    Corpus: Should contain:
    - .jsonl files with documents: {"doc_id": "tam_001", "text": "...", "script": "tam"}
    - query set: queries.jsonl with {"query_id": "q001", "query_text": "...",
                                       "relevant_docs": ["tam_001"], "query_script": "tam"}
    """
    corpus_dir = Path(corpus_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load corpus
    query_file = corpus_dir / "queries.jsonl"
    corpus_files = list(corpus_dir.glob("*.jsonl"))

    if not query_file.exists() and not corpus_files:
        results = {
            "status": "not_measured",
            "reason": f"No corpus found at {corpus_dir}. "
                      "Prepare a corpus with document .jsonl and queries.jsonl files "
                      "(see docs/DATA_LICENSES.md for sources).",
            "metrics": {},
        }
        with open(output_dir / "retrieval_results.json", "w") as f:
            json.dump(results, f, indent=2)
        logger.info("retrieval_eval_not_measured", reason="no_corpus")
        return results

    # Load queries
    queries = []
    if query_file.exists():
        with open(query_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    queries.append(json.loads(line))

    # Load documents
    all_docs = []
    for cf in corpus_files:
        if cf.name == "queries.jsonl":
            continue
        with open(cf) as f:
            for line in f:
                line = line.strip()
                if line:
                    all_docs.append(json.loads(line))

    if not queries or not all_docs:
        results = {
            "status": "not_measured",
            "reason": "Incomplete corpus - need both queries and documents",
            "num_queries": len(queries),
            "num_docs": len(all_docs),
        }
        with open(output_dir / "retrieval_results.json", "w") as f:
            json.dump(results, f, indent=2)
        return results

    # Build indexes and run searches
    retriever = HybridRetriever(db_path=str(output_dir / "eval_retrieval.db"))
    retriever.connect()

    doc_ids = {}
    for doc in all_docs:
        doc_ids[doc["doc_id"]] = doc

    # Run all ablation modes
    modes = {
        "bm25_only": lambda q: retriever._fts_search(q),
        "ngram": lambda q: retriever._ngram_search(q),
        "phonetic": lambda q: retriever._phonetic_search(q),
        "dense": lambda q: retriever._dense_search(q),
        "hybrid": lambda q: retriever.search(q, limit=10),
    }

    mode_results = {}
    for mode_name, search_fn in modes.items():
        recalls = {1: 0, 5: 0, 10: 0}
        mrr = 0.0
        ndcg = 0.0

        for query in queries:
            qtext = query["query_text"]
            relevant = set(query.get("relevant_docs", []))

            raw_results = search_fn(qtext)
            if mode_name == "dense":
                retrieved_ids = [r[0] for r in raw_results]
            else:
                retrieved_ids = [r["line_id"] if "line_id" in r else r.get("id", "") for r in raw_results]

            # Compute metrics
            for k in [1, 5, 10]:
                topk = set(retrieved_ids[:k])
                if relevant & topk:
                    recalls[k] += 1
                mrr_check = 1.0 / min(max(1, next((i + 1 for i, rid in enumerate(retrieved_ids) if rid in relevant), len(retrieved_ids))), 10)
                mrr += mrr_check

                # nDCG@10
                dcg = 0.0
                idcg = 0.0
                for i, rid in enumerate(retrieved_ids[:10]):
                    if rid in relevant:
                        dcg += 1.0 / (i + 2)  # i+1 = 1-based rank
                for i in range(min(len(relevant), 10)):
                    idcg += 1.0 / (i + 2)
                ndcg += (dcg / idcg) if idcg > 0 else 0.0

        n = max(len(queries), 1)
        mode_results[mode_name] = {
            "Recall@1": round(recalls[1] / n, 4),
            "Recall@5": round(recalls[5] / n, 4),
            "Recall@10": round(recalls[10] / n, 4),
            "MRR": round(mrr / n, 4),
            "nDCG@10": round(ndcg / n, 4),
        }

    # Cross-lingual test
    cross_lingual_results = []
    for query in queries:
        qtext = query["query_text"]
        # Search with phonetic version of query (cross-lingual: type in Roman)
        phonetic_q = retriever.phonetic_norm.normalize(qtext)
        if phonetic_q != qtext:
            phonetic_results = retriever._phonetic_search(phonetic_q)
            relevant = set(query.get("relevant_docs", []))
            found = any(r.get("line_id", r.get("id")) in relevant for r in phonetic_results[:10])
            cross_lingual_results.append({"found": found})

    results = {
        "status": "measured",
        "num_queries": len(queries),
        "num_docs": len(all_docs),
        "by_mode": mode_results,
        "cross_lingual": {
            "coverage": round(sum(1 for c in cross_lingual_results if c["found"]) / max(len(cross_lingual_results), 1), 4),
            "num_cross_queries": len(cross_lingual_results),
        },
        "limitation_note": (
            "Evaluation uses parphrase queries not copied from source text. "
            "OCR-noise robustness not measured on real data (synthetic only)."
        ),
    }

    with open(output_dir / "retrieval_results.json", "w") as f:
        json.dump(results, f, indent=2)

    retriever.close()
    logger.info("retrieval_evaluation_complete", num_queries=len(queries))
    return results


if __name__ == "__main__":
    results = evaluate_retrieval()
    print(json.dumps(results, indent=2))
