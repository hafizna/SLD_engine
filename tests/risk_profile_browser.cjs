/* NODE_PATH=scratchpad/node_modules node tests/risk_profile_browser.cjs
   Uses existing site/ snapshot data with the current viewer shell. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const root = path.resolve(__dirname,'..');
const server = http.createServer((req,res) => {
  const url = new URL(req.url,'http://localhost');
  const file = path.resolve(root,'site','.' + decodeURIComponent(url.pathname));
  if (!file.startsWith(path.join(root,'site') + path.sep) && url.pathname !== '/') { res.writeHead(403).end(); return; }
  if (url.pathname === '/' || url.pathname === '/index.html') {
    res.setHeader('Content-Type','text/html; charset=utf-8');
    res.end(fs.readFileSync(path.join(root,'app/static/index.html'),'utf8').replace('<script>','<script>window.STATIC_SNAPSHOT=true;'));
  } else if (fs.existsSync(file)) {
    res.setHeader('Content-Type',file.endsWith('.json') ? 'application/json' : file.endsWith('.svg') ? 'image/svg+xml' : 'application/octet-stream');
    fs.createReadStream(file).pipe(res);
  } else res.writeHead(404).end();
});
(async () => {
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  let browser;
  try {
    browser = await chromium.launch({channel:'msedge',headless:true});
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors = []; page.on('pageerror',e => errors.push(e.message));
    fs.mkdirSync(path.join(root,'scratchpad/risk-profile'),{recursive:true});
    const views = JSON.parse(fs.readFileSync(path.join(root,'site/data/views.json'),'utf8'));
    await page.goto(`http://127.0.0.1:${server.address().port}/#v=${views[0].view_key}`);
    await page.locator('#stage svg').waitFor({timeout:120000});
    await page.locator('#stageload').waitFor({state:'hidden'});
    if (await page.locator('#toggle-right').getAttribute('aria-expanded') !== 'true') await page.locator('#toggle-right').click();
    const seq = await page.evaluate(async () => {
      const risk = GRAPH.overlays.risk.find(r => r.condition && riskOnThisPage(r));
      if (!risk) throw Error('Fixture requires a mapped risk with condition text');
      await selectRisk(risk.seq_no,true); return risk.seq_no;
    });
    assert.equal(await page.locator('#rp-tab-risk').getAttribute('aria-selected'),'true');
    const condition = await page.evaluate(seq => plainText(GRAPH.overlays.risk.find(r => r.seq_no === seq).condition),seq);
    assert((await page.locator('#rp-content').innerText()).includes(condition),'full condition visible immediately');
    assert(await page.locator('#riskprofile').isVisible());
    await page.locator('#rp-tab-info').click();
    assert(await page.locator('#riskprofile .rp-facts').isVisible());
    await page.locator('#rp-tab-assets').click();
    assert(await page.locator('#riskprofile .rp-asset').count() > 0);
    const riskStyle = await page.locator('.rp-hero').evaluate(el => ({bg:getComputedStyle(el).backgroundImage,padding:getComputedStyle(el).padding,radius:getComputedStyle(el).borderRadius}));
    await page.locator('.rp-back').click();
    assert(await page.locator('#risklist').isVisible());
    for (const kind of ['node','circuit']) {
      await page.evaluate(kind => {
        const el = document.querySelector(kind === 'node' ? '#stage .sld-node' : '#stage [data-circuit-id]');
        if (kind === 'node') showNode(el); else showCircuit(el);
      },kind);
      assert(await page.locator('#obj-content-info .rp-facts').isVisible());
      const objectStyle = await page.locator('.obj-head').evaluate(el => ({bg:getComputedStyle(el).backgroundImage,padding:getComputedStyle(el).padding,radius:getComputedStyle(el).borderRadius}));
      assert.deepEqual(objectStyle,riskStyle,'object and risk share header styling');
      await page.locator('#obj-tab-risk').click();
      assert(await page.locator('#obj-content-risk').isVisible());
      await page.screenshot({path:path.join(root,`scratchpad/risk-profile/object-${kind}.png`),fullPage:true});
      await page.locator('#obj-tab-tech').click();
      assert(await page.locator('#obj-content-tech .tech').isVisible());
    }
    await page.evaluate(async seq => { await selectRisk(seq,true); },seq);
    assert.equal(await page.locator('#rp-tab-risk').getAttribute('aria-selected'),'true');
    assert((await page.locator('#rp-content').innerText()).includes(condition));
    await page.screenshot({path:path.join(root,'scratchpad/risk-profile/risk.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert(await page.locator('#rp-content').isVisible());
    assert((await page.locator('#rp-content').innerText()).includes(condition));
    assert(await page.locator('#riskprofile').evaluate(el => el.scrollWidth <= el.clientWidth + 1),'profile fits mobile panel');
    await page.screenshot({path:path.join(root,'scratchpad/risk-profile/mobile.png'),fullPage:true});
    assert.deepEqual(errors,[]);
    console.log('PASS: full risk description, default tab, all profile tabs, return to list, node/circuit tabs, shared header styles, no browser errors');
  } finally { if (browser) await browser.close(); server.close(); }
})().catch(e => { console.error(e); process.exitCode=1; });
