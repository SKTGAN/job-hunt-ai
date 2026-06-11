import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const datasetRoot = path.resolve(__dirname, "..");
const configPath = path.join(datasetRoot, "config", "seed_queries.json");
const rawDir = path.join(datasetRoot, "raw", "chinese_jobs");

const tencentCityIds = {
  北京: "1",
  上海: "2",
  深圳: "4",
  广州: "3",
  合肥: "",
  全国: ""
};

function timestamp() {
  const now = new Date();
  const pad = (value) => String(value).padStart(2, "0");
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

function parseCliArgs(argv) {
  const args = {
    source: "tencent",
    config: configPath,
    output: ""
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--help" || arg === "-h") args.help = true;
    else if (arg === "--source") args.source = argv[++index];
    else if (arg === "--config") args.config = path.resolve(argv[++index]);
    else if (arg === "--output") args.output = path.resolve(argv[++index]);
  }

  return args;
}

function printHelp() {
  console.log(`Usage:
  npm run collect
  npm run collect:tencent
  node scripts/collect_public_jobs.mjs --source tencent

说明：
  当前默认采集腾讯招聘公开岗位接口。
  输出 raw JSON 到 dataset/raw/chinese_jobs/*_public_jobs.json。
`);
}

async function fetchJson(url) {
  const response = await fetch(url, {
    headers: {
      accept: "application/json, text/plain, */*",
      "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }
  });
  const text = await response.text();
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch {
    // Keep raw text for diagnostics.
  }

  return {
    ok: response.ok,
    status: response.status,
    content_type: response.headers.get("content-type") || "",
    text,
    parsed
  };
}

function buildTencentQueryUrl({ keyword, city, pageIndex, pageSize }) {
  const params = new URLSearchParams({
    timestamp: String(Date.now()),
    countryId: "",
    cityId: tencentCityIds[city] || "",
    bgIds: "",
    productId: "",
    categoryId: "",
    parentCategoryId: "",
    attrId: "",
    keyword,
    pageIndex: String(pageIndex),
    pageSize: String(pageSize),
    language: "zh-cn",
    area: "cn"
  });
  return `https://careers.tencent.com/tencentcareer/api/post/Query?${params.toString()}`;
}

function normalizeTencentPost(post, queryContext) {
  return {
    source: "tencent_careers",
    source_name: "腾讯招聘",
    keyword: queryContext.keyword,
    city: queryContext.city,
    crawl_time: new Date().toISOString(),
    job_title: post.RecruitPostName || "",
    company_name: post.ComName || "腾讯",
    salary_text: "",
    location: post.LocationName || queryContext.city || "",
    tags: [post.BGName, post.ProductName, post.CategoryName, post.RequireWorkYearsName].filter(Boolean),
    job_description: post.Responsibility || "",
    source_url: post.PostURL || `https://careers.tencent.com/jobdesc.html?postId=${post.PostId}`,
    publish_time: post.LastUpdateTime || "",
    raw: post
  };
}

async function collectTencent(config) {
  const defaults = config.defaults || {};
  const pageSize = defaults.pageSize || 10;
  const maxPages = defaults.maxPages || 1;
  const queries = [];

  for (const query of config.queries || []) {
    for (const city of query.cities || ["全国"]) {
      const queryResult = {
        source: "tencent_careers",
        search_args: {
          keyword: query.keyword,
          city,
          pageSize,
          maxPages
        },
        searched_at: new Date().toISOString(),
        pages: [],
        jobs: []
      };

      for (let pageIndex = defaults.page || 1; pageIndex < (defaults.page || 1) + maxPages; pageIndex += 1) {
        const url = buildTencentQueryUrl({
          keyword: query.keyword,
          city,
          pageIndex,
          pageSize
        });

        console.log(`Tencent Careers: ${query.keyword} / ${city} / page ${pageIndex}`);
        const response = await fetchJson(url);
        const posts = response.parsed?.Data?.Posts || [];

        queryResult.pages.push({
          pageIndex,
          url,
          ok: response.ok,
          status: response.status,
          total_count: response.parsed?.Data?.Count ?? null,
          returned_count: posts.length,
          error: response.parsed?.Code && response.parsed.Code !== 200 ? response.parsed : null
        });

        for (const post of posts) {
          queryResult.jobs.push({
            index: queryResult.jobs.length,
            source_url: post.PostURL || "",
            list_item: normalizeTencentPost(post, { keyword: query.keyword, city }),
            detail: null
          });
        }
      }

      queryResult.parsed_job_count = queryResult.jobs.length;
      queries.push(queryResult);
    }
  }

  return queries;
}

async function main() {
  const args = parseCliArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    return;
  }

  if (args.source !== "tencent") {
    throw new Error(`Unsupported source: ${args.source}. Current supported source: tencent`);
  }

  const config = JSON.parse(await fs.readFile(args.config, "utf8"));
  const outputPath = args.output || path.join(rawDir, `${timestamp()}_${args.source}_public_jobs.json`);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });

  const output = {
    schema_version: 2,
    collector: "public-enterprise-careers",
    source: args.source,
    started_at: new Date().toISOString(),
    finished_at: null,
    config,
    queries: []
  };

  try {
    output.queries = await collectTencent(config);
  } finally {
    output.finished_at = new Date().toISOString();
    await fs.writeFile(outputPath, `${JSON.stringify(output, null, 2)}\n`, "utf8");
    console.log(`Saved public jobs output: ${outputPath}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
