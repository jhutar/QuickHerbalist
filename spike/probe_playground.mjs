// Phase 0 spike: run spike/main.py + main.kv in a real (headless) browser
// via the public kivy-browser playground, assert SPIKE: events.
// Usage: node probe_playground.mjs
import fs from "node:fs";
import { chromium } from "playwright";

const py = fs.readFileSync(new URL("./main.py", import.meta.url), "utf8");
const kv = fs.readFileSync(new URL("./main.kv", import.meta.url), "utf8");

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1000, height: 700 } });
const t0 = Date.now();
const logs = [];
page.on("console", (m) => {
  const s = m.text();
  logs.push(s);
  if (s.includes("SPIKE:")) console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${s}`);
});
page.on("pageerror", (e) => console.log("PAGEERROR:", e.message));

const url = process.env.URL ?? "https://kivy-school.github.io/kivy-browser/runner/?playground";
await page.goto(url, { waitUntil: "domcontentloaded" });
console.log("page loaded, waiting for pyodide+kivy boot (kivyReady)...");
await page.waitForFunction(() => typeof window.kivyReady !== "undefined", null, { timeout: 300_000 });
console.log(`boot ready at ${((Date.now() - t0) / 1000).toFixed(1)}s`);

await page.evaluate(
  ([py, kv]) =>
    (async () => {
      const play = await window.kivyReady;
      return play(py, kv);
    })(),
  [py, kv]
);
// wait for app to declare started
await page.waitForFunction(
  () => true,
  null,
  { timeout: 60_000 }
).catch(() => {});
for (let i = 0; i < 120 && !logs.some((l) => l.includes("SPIKE: app started")); i++)
  await new Promise((r) => setTimeout(r, 500));

// surface the runner's error overlay if any
const errText = await page.$eval("#error", (el) => el.textContent).catch(() => "");
if (errText.trim()) {
  console.log("\n--- kivy error overlay ---\n" + errText.slice(0, 4000));
  await page.screenshot({ path: "screenshot-error.png" });
  await browser.close();
  process.exit(1);
}
// focus canvas, send keys
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

// let a couple of tick batches print
await new Promise((r) => setTimeout(r, 4000));

const perf = await page.evaluate(() =>
  performance.getEntriesByType("resource").map((e) => ({
    name: e.name.split("/").slice(-1)[0],
    kb: Math.round(e.transferSize / 102.4) / 10,
  }))
);
const total = perf.reduce((a, b) => a + b.kb, 0);
console.log("\n--- resources (kb) ---");
for (const p of perf.filter((p) => p.kb > 50).sort((a, b) => b.kb - a.kb)) console.log(p);
console.log(`total transferred: ${Math.round(total)} kb`);
await page.screenshot({ path: "screenshot.png" });

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
