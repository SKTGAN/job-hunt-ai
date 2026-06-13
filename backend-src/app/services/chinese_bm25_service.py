import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from elasticsearch import Elasticsearch, helpers


class ChineseBM25Service:
    """Index and retrieve normalized Chinese job records with weighted BM25."""

    DEFAULT_INDEX_NAME = "chinese_jobs_v1"
    SEARCH_FIELDS = [
        "job_title^6",
        "tags^5",
        "keyword^4",
        "job_description^2.5",
        "company_name^1.5",
        "location^1.2",
        "all_text",
    ]

    def __init__(
        self,
        client: Elasticsearch,
        index_name: str = DEFAULT_INDEX_NAME,
    ) -> None:
        self.client = client
        self.index_name = index_name

    @staticmethod
    def index_definition() -> Dict[str, Any]:
        text_field = {
            "type": "text",
            "analyzer": "zh_mixed",
            "similarity": "job_bm25",
        }
        return {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "zh_mixed": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase"],
                        }
                    }
                },
                "similarity": {
                    "job_bm25": {
                        "type": "BM25",
                        "k1": 1.2,
                        "b": 0.75,
                    }
                },
            },
            "mappings": {
                "dynamic": False,
                "properties": {
                    "job_id": {"type": "keyword"},
                    "source_type": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "source_name": {"type": "keyword"},
                    "keyword": text_field,
                    "city": {"type": "keyword"},
                    "crawl_time": {"type": "date", "ignore_malformed": True},
                    "job_title": {
                        **text_field,
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                    },
                    "company_name": {
                        **text_field,
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                    },
                    "salary_text": {"type": "keyword", "ignore_above": 256},
                    "location": {
                        **text_field,
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                    },
                    "tags": {
                        **text_field,
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                    },
                    "job_description": text_field,
                    "source_url": {"type": "keyword", "index": False},
                    "publish_time": {"type": "keyword", "ignore_above": 256},
                    "content_hash": {"type": "keyword"},
                    "is_content_duplicate": {"type": "boolean"},
                    "duplicate_of": {"type": "keyword"},
                    "all_text": text_field,
                },
            },
        }

    def create_index(self, recreate: bool = False) -> None:
        if self.client.indices.exists(index=self.index_name):
            if not recreate:
                return
            self.client.indices.delete(index=self.index_name)
        self.client.indices.create(index=self.index_name, **self.index_definition())

    @staticmethod
    def normalize_tags(tags: Any) -> List[str]:
        if isinstance(tags, list):
            return [str(tag).strip() for tag in tags if str(tag).strip()]
        if isinstance(tags, str):
            return [item.strip() for item in tags.split(";") if item.strip()]
        return []

    @classmethod
    def prepare_document(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        tags = cls.normalize_tags(row.get("tags"))
        document = {
            "job_id": str(row.get("job_id") or ""),
            "source_type": str(row.get("source_type") or ""),
            "source": str(row.get("source") or ""),
            "source_name": str(row.get("source_name") or ""),
            "keyword": str(row.get("keyword") or ""),
            "city": str(row.get("city") or ""),
            "crawl_time": row.get("crawl_time") or None,
            "job_title": str(row.get("job_title") or ""),
            "company_name": str(row.get("company_name") or ""),
            "salary_text": str(row.get("salary_text") or ""),
            "location": str(row.get("location") or ""),
            "tags": tags,
            "job_description": str(row.get("job_description") or ""),
            "source_url": str(row.get("source_url") or ""),
            "publish_time": str(row.get("publish_time") or ""),
            "content_hash": str(row.get("content_hash") or ""),
            "is_content_duplicate": bool(row.get("is_content_duplicate", False)),
            "duplicate_of": str(row.get("duplicate_of") or ""),
        }
        document["all_text"] = " ".join(
            value
            for value in [
                document["job_title"],
                " ".join(tags),
                document["keyword"],
                document["company_name"],
                document["location"],
                document["job_description"],
            ]
            if value
        )
        return document

    def iter_actions(self, input_path: Path) -> Iterable[Dict[str, Any]]:
        with input_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at line {line_number}: {exc}") from exc
                document = self.prepare_document(row)
                if not document["job_id"]:
                    raise ValueError(f"Missing job_id at line {line_number}")
                yield {
                    "_op_type": "index",
                    "_index": self.index_name,
                    "_id": document["job_id"],
                    "_source": document,
                }

    def bulk_index(self, input_path: Path, batch_size: int = 500) -> Dict[str, Any]:
        self.client.indices.put_settings(
            index=self.index_name,
            settings={"index": {"refresh_interval": "-1"}},
        )
        succeeded = 0
        failed = 0
        errors: List[Dict[str, Any]] = []
        try:
            for success, result in helpers.streaming_bulk(
                self.client,
                self.iter_actions(input_path),
                chunk_size=batch_size,
                max_retries=3,
                initial_backoff=1,
                max_backoff=8,
                request_timeout=120,
                raise_on_error=False,
                raise_on_exception=False,
            ):
                if success:
                    succeeded += 1
                else:
                    failed += 1
                    if len(errors) < 20:
                        errors.append(result)
        finally:
            self.client.indices.put_settings(
                index=self.index_name,
                settings={"index": {"refresh_interval": "1s"}},
            )
            self.client.indices.refresh(index=self.index_name)
        return {
            "index_name": self.index_name,
            "input_path": str(input_path),
            "succeeded": succeeded,
            "failed": failed,
            "errors": errors,
            "document_count": self.client.count(index=self.index_name)["count"],
        }

    def search(
        self,
        query_text: str,
        size: int = 20,
        source_type: Optional[str] = None,
        location: Optional[str] = None,
        exclude_duplicates: bool = True,
    ) -> Dict[str, Any]:
        filters: List[Dict[str, Any]] = []
        if source_type:
            filters.append({"term": {"source_type": source_type}})
        if location:
            filters.append({"match": {"location": {"query": location}}})

        bool_query: Dict[str, Any] = {
            "must": [
                {
                    "multi_match": {
                        "query": query_text,
                        "fields": self.SEARCH_FIELDS,
                        "type": "best_fields",
                        "operator": "or",
                        "minimum_should_match": "20%",
                        "tie_breaker": 0.2,
                    }
                }
            ],
            "should": [
                {"match_phrase": {"job_title": {"query": query_text, "boost": 2.0}}},
                {"match_phrase": {"tags": {"query": query_text, "boost": 1.5}}},
            ],
            "filter": filters,
        }
        if exclude_duplicates:
            bool_query["must_not"] = [{"term": {"is_content_duplicate": True}}]

        response = self.client.search(
            index=self.index_name,
            size=max(1, min(size, 200)),
            track_total_hits=True,
            query={"bool": bool_query},
            _source_excludes=["all_text"],
        )
        hits = []
        for rank, hit in enumerate(response["hits"]["hits"], start=1):
            hits.append({"rank": rank, "score": hit["_score"], **hit["_source"]})
        return {
            "index_name": self.index_name,
            "query": query_text,
            "took_ms": response["took"],
            "total": response["hits"]["total"]["value"],
            "hits": hits,
        }

    def stats(self) -> Dict[str, Any]:
        count = self.client.count(index=self.index_name)["count"]
        duplicate_count = self.client.count(
            index=self.index_name,
            query={"term": {"is_content_duplicate": True}},
        )["count"]
        return {
            "index_name": self.index_name,
            "document_count": count,
            "duplicate_count": duplicate_count,
            "search_fields": self.SEARCH_FIELDS,
        }
