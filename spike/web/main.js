// Phase 0 spike bundle loader: boot pyodide, install kivy wheel, run the app.
// Static, no server logic; pyodide runtime comes from CDN (vendor in Phase 2).
// The kivy wheel is not committed (size limit) — fetch it with fetch-wheel.sh.
const status = (msg) => {
  console.log(`SPIKE-BUNDLE: ${msg}`);
  const el = document.getElementById("status");
  if (el) el.textContent = msg;
};

window.onerror = (msg) => status(`page error: ${msg}`);

async function main() {
  status("loading pyodide");
  const pyodide = await loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.29.5/full/" });
  pyodide.canvas.setCanvas3D(document.getElementById("canvas"));

  status("installing kivy wheel");
  await pyodide.loadPackage("micropip");
  const micropip = pyodide.pyimport("micropip");
  await micropip.install("./kivy-3.0.0.dev0-cp313-cp313-pyemscripten_2025_0_wasm32.whl");

  status("writing app files");
  const fs = pyodide.FS;
  // cwd is /home/pyodide; absolute paths below it misbehave in this pyodide build
  const put = async (path, url) => {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`fetch ${url} -> ${r.status}`);
    fs.writeFile(path, new Uint8Array(await r.arrayBuffer()));
  };
  await put("main.py", "../main.py");
  await put("main.kv", "../main.kv");
  await put("block.png", "../assets/block.png");

  status("running app");
  pyodide.runPython("import runpy; runpy.run_path('main.py', run_name='__main__')");
  status("app running");
}

main().catch((err) => status(`error: ${JSON.stringify(err, Object.getOwnPropertyNames(err).concat("message", "name"))}`));
