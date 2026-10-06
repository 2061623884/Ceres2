/** Compile the real aftersales component for isolated DOM evidence. */
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const root = process.cwd();
const ts = createRequire(path.join(root, 'frontend/package.json'))('typescript');
const out = path.join(root, 'work/clean-rebuild/14/compiled');
fs.mkdirSync(out, {recursive:true});
fs.writeFileSync(path.join(out, 'package.json'), JSON.stringify({type:'commonjs'}));
for (const file of ['AfterSalesPanel.tsx','lib/aftersales.ts','lib/saleGuide.ts']) {
  const destination = path.join(out, file.replace(/\.tsx?$/,'.js'));
  fs.mkdirSync(path.dirname(destination), {recursive:true});
  fs.writeFileSync(destination, ts.transpileModule(fs.readFileSync(path.join(root,'frontend/src',file),'utf8'), {
    compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},fileName:file}).outputText);
}
const modules = path.join(out,'node_modules');
fs.mkdirSync(modules,{recursive:true});
for (const name of ['react','react-dom']) {
  const target = path.join(modules,name);
  if (!fs.existsSync(target)) fs.symlinkSync(path.join(root,'frontend/node_modules',name),target,'dir');
}
console.log(JSON.stringify({compiled:true,out}));
