/** Test artifact transpilation only; never writes application source. */
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const root = process.cwd();
const frontend = createRequire(path.join(root, 'frontend/package.json'));
const ts = frontend('typescript');
const out = process.env.MERCURY_COMPILED_DIR;
if (!out || !path.resolve(out).includes('clean-rebuild')) throw new Error('Explicit isolated output directory required');
fs.mkdirSync(out, {recursive:true});
fs.writeFileSync(path.join(out, 'package.json'), JSON.stringify({type:'commonjs'}));
for (const file of ['AfterSalesPanel.tsx','lib/aftersales.ts','MercuryChat.tsx','lib/mercury.ts','lib/saleGuide.ts','components/MomoToast.tsx','HumanCasePanel.tsx','lib/humanCases.ts']) {
  const destination = path.join(out, file.replace(/\.tsx?$/,'.js'));
  fs.mkdirSync(path.dirname(destination), {recursive:true});
  const source = fs.readFileSync(path.join(root,'frontend/src',file),'utf8');
  const emitted = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},fileName:file}).outputText;
  fs.writeFileSync(destination, emitted);
}
// Compiled React modules resolve precisely the application's installed React.
const nodeModules = path.join(out,'node_modules');
fs.mkdirSync(nodeModules,{recursive:true});
for (const name of ['react','react-dom']) {
  const target = path.join(nodeModules,name);
  if (!fs.existsSync(target)) fs.symlinkSync(path.join(root,'frontend/node_modules',name),target,'dir');
}
const script = fs.readFileSync(path.join(root,'work/clean-rebuild/02/ui_races.tsx'),'utf8');
fs.writeFileSync(path.join(out,'ui_races.mjs'), ts.transpileModule(script,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022},fileName:'ui_races.tsx'}).outputText);
console.log(JSON.stringify({compiled:true,out,component:path.join(out,'MercuryChat.js'),script:path.join(out,'ui_races.mjs')}));
