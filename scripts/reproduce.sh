#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-gpu}"
STAGE="${2:-all}"
export HF_ENDPOINT="${HF_ENDPOINT:-https://huggingface.co}"

cd "$(dirname "$0")/.."

COMPOSE_ARGS=(-p jobhunt-repro -f docker-compose.reproduce.yml)
if [[ "$MODE" == "gpu" ]]; then
  COMPOSE_ARGS+=(-f docker-compose.reproduce.gpu.yml)
elif [[ "$MODE" != "cpu" ]]; then
  echo "Mode must be cpu or gpu" >&2
  exit 2
fi

docker compose "${COMPOSE_ARGS[@]}" pull elasticsearch
docker compose "${COMPOSE_ARGS[@]}" build toolkit
docker compose "${COMPOSE_ARGS[@]}" up -d elasticsearch

healthy=false
for _ in $(seq 1 30); do
  if docker compose "${COMPOSE_ARGS[@]}" exec -T elasticsearch \
    curl -fsS http://localhost:9200/_cluster/health >/dev/null 2>&1; then
    healthy=true
    break
  fi
  sleep 2
done
if [[ "$healthy" != "true" ]]; then
  echo "Elasticsearch did not become healthy within 60 seconds." >&2
  exit 1
fi

if [[ "$STAGE" == "all" || "$STAGE" == "index" ]]; then
  docker compose "${COMPOSE_ARGS[@]}" run --rm toolkit \
    python backend-src/scripts/index_chinese_jobs.py \
    --url http://elasticsearch:9200 --recreate --batch-size 500
fi

BATCH_SIZE=1
[[ "$MODE" == "gpu" ]] && BATCH_SIZE=2

case "$STAGE" in
  all)
    docker compose "${COMPOSE_ARGS[@]}" run --rm toolkit \
      python dataset/scripts/run_bm25_bge_m3_experiment.py \
      --stage all --es-url http://elasticsearch:9200 \
      --batch-size "$BATCH_SIZE" --max-length 1024
    ;;
  bm25)
    docker compose "${COMPOSE_ARGS[@]}" run --rm toolkit \
      python dataset/scripts/run_bm25_bge_m3_experiment.py \
      --stage bm25 --es-url http://elasticsearch:9200
    ;;
  rerank)
    docker compose "${COMPOSE_ARGS[@]}" run --rm toolkit \
      python dataset/scripts/run_bm25_bge_m3_experiment.py \
      --stage rerank --es-url http://elasticsearch:9200 \
      --batch-size "$BATCH_SIZE" --max-length 1024
    ;;
  index) ;;
  *) echo "Stage must be all, index, bm25, or rerank" >&2; exit 2 ;;
esac

echo "Reproduction completed. Results: dataset/retrieval/test_30/"
