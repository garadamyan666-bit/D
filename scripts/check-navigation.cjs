const {chromium}=require('C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const b=await chromium.launch({channel:'chrome',headless:true});
 try {
 const p=await b.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8000/');await p.waitForSelector('.workspace-menu');
 for(const key of ['analysis','levels','flow','backtest','alerts','leaders','history']){
   await p.locator(`a[href="#${key}"]`).click();
   await p.locator(`[data-page="${key}"]`).waitFor({state:'visible'});
   if(await p.locator('.workspace-panel:visible').count()!==1)throw Error(key+' panels');
   if(!await p.locator(`[data-page="${key}"]`).isVisible())throw Error(key+' hidden');
   console.log('OK',key);
 }
 await p.locator('[data-lang=en]').click();await p.waitForTimeout(100);
 console.log('English menu',await p.locator('.workspace-menu a').first().innerText());
 await p.setViewportSize({width:390,height:844});
 for(const key of ['analysis','levels','flow','backtest','alerts','leaders','history']){
   await p.locator(`a[href="#${key}"]`).click();
   await p.locator(`[data-page="${key}"]`).waitFor({state:'visible'});
   if(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow '+key);
 }
 if(errors.length)throw Error(errors.join(';'));
 console.log('Mobile layout and JS passed');
 } finally {await b.close();}
})().catch(e=>{console.error(e.message);process.exit(1)});
