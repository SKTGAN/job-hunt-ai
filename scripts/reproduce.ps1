param(
    [ValidateSet("cpu", "gpu")]
    [string]$Mode = "gpu",

    [ValidateSet("all", "index", "bm25", "rerank")]
    [string]$Stage = "all",

    [string]$HfEndpoint = "https://huggingface.co"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$env:HF_ENDPOINT = $HfEndpoint
$composeArgs = @("-p", "jobhunt-repro", "-f", "docker-compose.reproduce.yml")
if ($Mode -eq "gpu") {
    $composeArgs += @("-f", "docker-compose.reproduce.gpu.yml")
}

Write-Host "[1/4] Pulling base images and building the toolkit image..."
docker compose @composeArgs pull elasticsearch
docker compose @composeArgs build toolkit

Write-Host "[2/4] Starting isolated Elasticsearch..."
docker compose @composeArgs up -d elasticsearch
$healthy = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
    docker compose @composeArgs exec -T elasticsearch `
        curl -fsS http://localhost:9200/_cluster/health *> $null
    if ($LASTEXITCODE -eq 0) {
        $healthy = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $healthy) {
    throw "Elasticsearch did not become healthy within 60 seconds."
}

if ($Stage -in @("all", "index")) {
    Write-Host "[3/4] Indexing 23,714 normalized jobs..."
    docker compose @composeArgs run --rm toolkit `
        python backend-src/scripts/index_chinese_jobs.py `
        --url http://elasticsearch:9200 `
        --recreate `
        --batch-size 500
}

$batchSize = if ($Mode -eq "gpu") { 2 } else { 1 }
if ($Stage -eq "all") {
    Write-Host "[4/4] Running BM25 Top200 and BGE-M3 reranking..."
    docker compose @composeArgs run --rm toolkit `
        python dataset/scripts/run_bm25_bge_m3_experiment.py `
        --stage all `
        --es-url http://elasticsearch:9200 `
        --batch-size $batchSize `
        --max-length 1024
} elseif ($Stage -eq "bm25") {
    Write-Host "[4/4] Running BM25 Top200..."
    docker compose @composeArgs run --rm toolkit `
        python dataset/scripts/run_bm25_bge_m3_experiment.py `
        --stage bm25 `
        --es-url http://elasticsearch:9200
} elseif ($Stage -eq "rerank") {
    Write-Host "[4/4] Running BGE-M3 reranking from saved BM25 results..."
    docker compose @composeArgs run --rm toolkit `
        python dataset/scripts/run_bm25_bge_m3_experiment.py `
        --stage rerank `
        --es-url http://elasticsearch:9200 `
        --batch-size $batchSize `
        --max-length 1024
}

Write-Host "Reproduction completed. Results: dataset/retrieval/test_30/"
