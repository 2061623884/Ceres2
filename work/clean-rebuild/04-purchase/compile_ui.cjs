/** Compile actual retained UI for isolated DOM evidence. Tester only. */
const fs=require('node:fs'),path=require('node:path'),{createRequire}=require('node:module');
const root=process.cwd(),ts=createRequire(path.join(root,'frontend/package.json'))('typescript');
const out=path.join(root,'work/clean-rebuild/04-purchase/compiled');fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'package.json'),JSON.stringify({type:'commonjs'}));
for(const file of ['ComparisonCards.tsx','App.tsx','AfterSalesPanel.tsx','lib/aftersales.ts','MercuryChat.tsx','HumanCasePanel.tsx','HumanOperatorPage.tsx','SimulatedOrders.tsx','components/MomoToast.tsx','lib/saleGuide.ts','lib/mercury.ts','lib/humanCases.ts','lib/orders.ts']){
 const dest=path.join(out,file.replace(/\.tsx?$/,'.js'));fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,ts.transpileModule(fs.readFileSync(path.join(root,'frontend/src',file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},fileName:file}).outputText);
}
fs.mkdirSync(path.join(out,'node_modules'),{recursive:true});for(const name of ['react','react-dom']){const dest=path.join(out,'node_modules',name);if(!fs.existsSync(dest))fs.symlinkSync(path.join(root,'frontend/node_modules',name),dest,'dir');}
console.log(JSON.stringify({compiled:true,out}));
