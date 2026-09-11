const {chromium}=require('C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
(async()=>{const b=await chromium.launch({channel:'chrome',headless:true});try{
 const page=await b.newPage();await page.goto('http://127.0.0.1:8000/admin');
 await page.waitForURL('**/admin/login');
 const password=fs.readFileSync('admin-access.txt','utf8').split(/\r?\n/).find(line=>line.startsWith('Password: ')).slice(10);
 await page.locator('[name=password]').fill(password);
 await page.locator('form button').click();await page.waitForURL('**/admin');
 await page.locator('#logout').waitFor();console.log('Login successful');
 await page.locator('#comparison-M1').waitFor();await page.locator('#comparison-M15').waitFor();
 const report=await (await page.request.get('http://127.0.0.1:8000/api/admin/verification')).json();
 for(const tf of ['M1','M15']){if(report.by_timeframe[tf].rows.some(row=>row.timeframe!==tf))throw Error('Mixed timeframes');console.log(tf,'rows',report.by_timeframe[tf].rows.length);}
 await page.setViewportSize({width:390,height:844});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow');
 console.log('Both timeframe tables verified');
 await page.locator('#logout').click();await page.waitForURL('**/admin/login');
 console.log('Logout successful');
}finally{await b.close();}})().catch(()=>{console.error('Login browser check failed');process.exit(1)});
