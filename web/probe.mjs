// Headless smoke test for the web bundle (node + playwright, see spike/).
// Serve the built bundle, then: node probe.mjs  (BASE env to override URL).
// Asserts: app boots to "app running", no page errors, canvas gets input.
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
// resolve playwright from spike/node_modules (spike/ owns the dev deps)
const require = createRequire(fileURLToPath(new URL("../spike/package.json", import.meta.url)));
const { chromium } = require("playwright");

const base = process.env.BASE ?? "http://127.0.0.1:8322/";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1000, height: 750 } });
const t0 = Date.now();
const errors = [];
page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
page.on("console", (m) => {
  const t = m.text();
  if (t.startsWith("WEB:")) console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${t}`);
  if (m.type() === "error") errors.push(t);
});

await page.goto(base, { waitUntil: "domcontentloaded" });
let status = "";
for (let i = 0; i < 180; i++) {
  status = (await page.textContent("#status")) ?? "";
  if (status.startsWith("app running") || status.startsWith("error")) break;
  await new Promise((r) => setTimeout(r, 500));
}
console.log(`status: ${status} (${((Date.now() - t0) / 1000).toFixed(1)}s)`);

// let the menu render, then drive it with keyboard + mouse
await page.waitForTimeout(4000);
const canvas = await page.$("canvas");
if (canvas) {
  await canvas.click({ position: { x: 400, y: 300 } });
  for (const key of ["a", "ArrowDown", "Enter", "Space", "Escape"]) {
    await page.keyboard.press(key);
    await page.waitForTimeout(400);
  }
} else {
  errors.push("no canvas element found");
}
await page.screenshot({ path: "probe-screenshot.png" });

console.log(errors.length ? `ERRORS:\n${errors.join("\n")}` : "no page errors");
let fail = 0;
for (const [label, ok] of [
  ["app reached 'app running'", status === "app running"],
  ["no page errors", errors.length === 0],
]) {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
  if (!ok) fail++;
}
console.log(`done in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
await browser.close();
process.exit(fail ? 1 : 0);
