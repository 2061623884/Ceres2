/** Isolated test transpilation; Tester alone executes this file. */
const fs = require('node:fs');
const path = require('node:path');
const {createRequire} = require('node:module');
const root = process.cwd();
const ts = createRequire(path.join(root,'frontend/package.json'))('typescript');
const out = process.env.MERCURY_COMPILED_DIR;
if (!out || !path.resolve(out).includes('clean-rebuild')) throw new Error('Explicit isolated output required');
fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'package.json'),JSON.stringify({type:'commonjs'}));
for (const file of ['HumanCasePanel.tsx','HumanOperatorPage.tsx','lib/humanCases.ts']) {
 const target=path.join(out,file.replace(/\.tsx?$/,'.js'));
 fs.mkdirSync(path.dirname(target),{recursive:true});
 fs.writeFileSync(target,ts.transpileModule(fs.readFileSync(path.join(root,'frontend/src',file),'utf8'),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},fileName:file}).outputText);
}
const modules=path.join(out,'node_modules');fs.mkdirSync(modules,{recursive:true});
for(const name of ['react','react-dom']) if(!fs.existsSync(path.join(modules,name))) fs.symlinkSync(path.join(root,'frontend/node_modules',name),path.join(modules,name),'dir');
fs.writeFileSync(path.join(out,'ui_human.mjs'),ts.transpileModule(fs.readFileSync(path.join(root,'work/clean-rebuild/15/ui_human.tsx'),'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022},fileName:'ui_human.tsx'}).outputText);
console.log(JSON.stringify({compiled:true,out}));
