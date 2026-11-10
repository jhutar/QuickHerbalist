// Phase 0 spike: run the local standalone bundle (web/index.html) headlessly.
// Usage: serve spike/ with any static server, then: node probe_bundle.mjs
import { chromium } from "playwright";

const base = process.env.BASE ?? "http://127.0.0.1:8321/web/";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1000, height: 700 } });
const t0 = Date.now();
const logs = [];
page.on("console", (m) => {
  const s = m.text();
  logs.push(s);
  if (s.includes("SPIKE")) console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${s}`);
});
page.on("pageerror", (e) => console.log("PAGEERROR:", e.message));

await page.goto(base, { waitUntil: "domcontentloaded" });
for (let i = 0; i < 240 && !logs.some((l) => l.includes("SPIKE: app started")); i++)
  await new Promise((r) => setTimeout(r, 500));

const canvas = await page.$("canvas");
if (canvas) {
  await canvas.click({ position: { x: 100, y: 100 } });
  await page.keyboard.press("a");
  await page.keyboard.press("Space");
} else {
  console.log("NO CANVAS FOUND");
}
for (let i = 0; i < 60 && !logs.some((l) => l.includes("SPIKE: key down a")); i++)
  await new Promise((r) => setTimeout(r, 500));
await new Promise((r) => setTimeout(r, 4000));

const perf = await page.evaluate(() =>
  performance.getEntriesByType("resource").map((e) => ({
    name: e.name.split("/").slice(-1)[0],
    kb: Math.round(e.transferSize / 102.4) / 10,
  }))
);
const total = perf.reduce((a, b) => a + b.kb, 0);
console.log("\n--- top resources (kb) ---");
for (const p of perf.sort((a, b) => b.kb - a.kb).slice(0, 8)) console.log(p);
console.log(`total transferred: ${Math.round(total)} kb`);
await page.screenshot({ path: "screenshot-bundle.png" });

const need = ["SPIKE: kv loaded + sprite decoded", "SPIKE: app started", "SPIKE: tick 1", "SPIKE: key down a", "SPIKE: key down space"];
console.log("\n--- assertions ---");
let fail = 0;
for (const n of need) {
  const ok = logs.some((l) => l.includes(n));
  console.log(`${ok ? "PASS" : "FAIL"}  ${n}`);
  if (!ok) fail++;
}
console.log(`\ndone in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
await browser.close();
process.exit(fail ? 1 : 0);
