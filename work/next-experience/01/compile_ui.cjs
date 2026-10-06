/** Compile actual UI modules for controlled DOM evidence; Tester executes this. */
const fs=require('node:fs'),path=require('node:path'),{createRequire}=require('node:module');
const root=process.cwd(),ts=createRequire(path.join(root,'frontend/package.json'))('typescript');
const out=path.join(root,'work/next-experience/01/compiled');fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'package.json'),JSON.stringify({type:'commonjs'}));
function visit(folder){for(const name of fs.readdirSync(folder)){const source=path.join(folder,name);if(fs.statSync(source).isDirectory()){visit(source);continue;}const file=path.relative(path.join(root,'frontend/src'),source);if(/\.d\.ts$/.test(file))continue;if(!/\.(tsx?|css)$/.test(file))continue;const dest=path.join(out,file.replace(/\.tsx?$/,'.js'));fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,file.endsWith('.css')?fs.readFileSync(source):ts.transpileModule(fs.readFileSync(source,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},fileName:file}).outputText);}}
visit(path.join(root,'frontend/src'));
fs.mkdirSync(path.join(out,'node_modules'),{recursive:true});for(const name of ['react','react-dom']){const dest=path.join(out,'node_modules',name);if(!fs.existsSync(dest))fs.symlinkSync(path.join(root,'frontend/node_modules',name),dest,'dir');}
console.log(JSON.stringify({compiled:true,out}));
