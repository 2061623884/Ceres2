/** Tester-only: compile retained UI for public DOM scenarios. Strict checking is separate. */
const fs=require('node:fs'),path=require('node:path'),{createRequire}=require('node:module');
const root=process.cwd(),ts=createRequire(path.join(root,'frontend/package.json'))('typescript');
const out=path.join(root,'work/local-cloud-integration/05/compiled');
fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'package.json'),JSON.stringify({type:'commonjs'}));
function visit(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){
 const source=path.join(dir,entry.name);if(entry.isDirectory()){visit(source);continue}if(entry.name.endsWith('.css')){const dest=path.join(out,path.relative(path.join(root,'frontend/src'),source));fs.mkdirSync(path.dirname(dest),{recursive:true});fs.copyFileSync(source,dest);continue}if(!/\.tsx?$/.test(entry.name)||entry.name.endsWith('.d.ts'))continue;
 const dest=path.join(out,path.relative(path.join(root,'frontend/src'),source).replace(/\.tsx?$/,'.js'));fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,ts.transpileModule(fs.readFileSync(source,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},fileName:source}).outputText);
}}
visit(path.join(root,'frontend/src'));fs.mkdirSync(path.join(out,'node_modules'),{recursive:true});
for(const name of ['react','react-dom']){const dest=path.join(out,'node_modules',name);if(!fs.existsSync(dest))fs.symlinkSync(path.join(root,'frontend/node_modules',name),dest,'dir')}
console.log(JSON.stringify({compiled:true,out}));
