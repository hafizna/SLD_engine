/* Run with NODE_PATH pointing at a Playwright installation.
   Start FastAPI with the snapshot database and serve site/ first.
   DASHBOARD_LIVE_URL and DASHBOARD_STATIC_URL override the local defaults. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const views = JSON.parse(fs.readFileSync('site/data/views.json','utf8'));
const targets = [
  views.find(v => /SUMSEL/.test(v.view_key)),
  views.find(v => /PRBC/.test(v.view_key)),
  views.find(v => /LBK/.test(v.view_key)),
  views.find(v => v.view_key === 'SS_SUMBAGTENG_GABUNGAN'),
].filter(Boolean);
assert.equal(targets.length,4,'all four review views must be present');
async function geometry(page) {
  return page.locator('#stage svg').evaluate(s => {
    const b=s.viewBox.baseVal, r=s.getBoundingClientRect();
    return {cx:b.x+b.width/2,cy:b.y+b.height/2,scale:Math.min(r.width/b.width,r.height/b.height),width:b.width};
  });
}
function same(a,b) { for (const k of ['cx','cy','scale']) assert(Math.abs(a[k]-b[k])<0.01,`${k}: ${a[k]} vs ${b[k]}`); }
(async()=>{
  const channel=process.env.DASHBOARD_BROWSER_CHANNEL || (process.platform==='win32' ? 'msedge' : 'chromium');
  const browser = await chromium.launch({...(channel==='chromium' ? {} : {channel}),headless:true});
  try {
    const bases = [process.env.DASHBOARD_LIVE_URL || 'http://127.0.0.1:8767',process.env.DASHBOARD_STATIC_URL || 'http://127.0.0.1:8766'];
    for(const base of process.env.DASHBOARD_ONLY === 'live' ? bases.slice(0,1) : process.env.DASHBOARD_ONLY === 'static' ? bases.slice(1) : bases) {
      const context = await browser.newContext({viewport:{width:1600,height:1000}});
      const page = await context.newPage(); const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      for(const view of targets) {
        await page.goto(`${base}/?browser-test=${view.id}#v=${view.view_key}`);
        await page.locator('#stage svg .risk-pin').first().waitFor({timeout:120000});
        await page.locator('#stageload').waitFor({state:'hidden'});
        assert.equal(await page.evaluate(()=>VIEW.id),view.id);
        if(view===targets[0]) {
          assert.equal(await page.locator('#left-panel').isVisible(),true);
          assert.equal(await page.locator('#right-panel').isVisible(),false);
        }
        // A known state for each geometry test; use the public controls.
        for(const side of ['left','right']) if(await page.locator(`#toggle-${side}`).getAttribute('aria-expanded')==='true') await page.locator(`#toggle-${side}`).click();
        const initial=await geometry(page);
        for(const side of ['left','right']) { await page.locator(`#toggle-${side}`).click(); same(initial,await geometry(page)); }
        for(const side of ['left','right']) { await page.locator(`#toggle-${side}`).press('Enter'); same(initial,await geometry(page)); }
        const pin=page.locator('#stage svg .risk-pin').first();
        // FIT brings a marker into the viewport for pointer and hover tests.
        await page.locator('#zfit').click();
        const sizes = await page.locator('#stage svg').evaluate(svg => ({
          labels:[...svg.querySelectorAll('.gi-label,.plant-label')].map(t=>({plant:t.classList.contains('plant-label'),px:parseFloat(getComputedStyle(t).fontSize)*Math.abs(t.getScreenCTM().a)})),
          pins:[...svg.querySelectorAll('.risk-pin')].map(p=>({text:parseFloat(getComputedStyle(p.querySelector('text')).fontSize)*Math.abs(p.querySelector('text').getScreenCTM().a),hit:p.querySelector('.pin-hit').getBoundingClientRect().width})),
        }));
        assert(sizes.labels.every(l=>l.px >= (l.plant ? 11.99 : 10.99)));
        assert(sizes.pins.every(p=>p.text>=11.99 && p.hit>=43.99));
        const seq=await pin.getAttribute('data-risk-seqs');
        await pin.hover();
        assert((await page.locator('#pintip').innerText()).includes(`#${seq}`));
        assert.equal(await page.locator('#pintip').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(255, 255, 255)');
        await pin.click();
        assert.equal(await page.locator('#right-panel').isVisible(),true);
        assert.equal(await page.locator('#risk-active .rcard').getAttribute('data-seq'),seq);
        assert.equal(await page.locator('#risk-active .rcard').count(),1);
        assert.equal(await page.locator('#risklist details').count(),0);
        for (const colocated of await page.locator('.risk-cluster').all()) {
          const badges=colocated.locator('.risk-pin');
          if(await badges.count()<2) continue;
          const targets=await colocated.locator('.pin-hit').evaluateAll(c=>c.map(x=>({left:x.getBoundingClientRect().left,right:x.getBoundingClientRect().right})));
          assert(targets.slice(1).every((t,i)=>t.left>=targets[i].right),'co-located badge targets must not overlap');
          for(const badge of await badges.all()) {
            await badge.press('Enter');
            assert.equal(await page.locator('#risk-active .rcard').getAttribute('data-seq'),await badge.getAttribute('data-risk-seqs'));
          }
          break;
        }
        await page.locator(`#risklist [data-seq="${seq}"]`).press('Enter');
        assert.equal(await page.locator('#risk-active .rcard').getAttribute('data-seq'),seq);
        for(const chip of await page.locator('#risk-cats [data-cat]').all()) {
          await chip.click(); const category=await chip.getAttribute('data-cat');
          if(category) {
            const categories=await page.locator('#risklist .risk-chip').allTextContents();
            assert(categories.every(c=>c===category));
            const shown=await page.locator('#stage .risk-pin').evaluateAll(p=>p.filter(x=>getComputedStyle(x).display!=='none').map(x=>x.dataset.category));
            assert(shown.every(c=>c===category));
          }
        }
        await page.locator('#risk-cats [data-cat=""]').click();
        await page.locator('#hl-all').click();
        assert.equal(await page.locator('#risk-active .rcard').count(),0);
        await page.locator('#toggle-right').click();
        await page.locator('#zfit').click();
        await pin.press('Enter');
        assert.equal(await page.locator('#right-panel').isVisible(),true);
        await page.locator('#toggle-right').click();
        await page.locator('#zfit').click();
        const objectPoint = await page.evaluate(() => {
          for (const line of document.querySelectorAll('#busbars .sld-node > line')) {
            const r=line.getBoundingClientRect();
            for (const f of [.15,.35,.65]) {
              const x=r.left+r.width*f, y=r.top+r.height/2;
              if (document.elementFromPoint(x,y)?.closest('.sld-node')===line.parentElement) return {x,y};
            }
          }
        });
        assert(objectPoint,'a visible GI busbar must be clickable');
        await page.mouse.click(objectPoint.x,objectPoint.y);
        assert.equal(await page.locator('#right-panel').isVisible(),true);
        assert.equal(await page.locator('#pane-detail').isVisible(),true);
        const beforeResize=await geometry(page);
        await page.setViewportSize({width:820,height:1100});
        await page.waitForTimeout(250); same(beforeResize,await geometry(page));
        await page.setViewportSize({width:390,height:844});
        await page.waitForTimeout(250); same(beforeResize,await geometry(page));
        assert.equal(await page.locator('#toggle-left').isVisible(),true);
        assert.equal(await page.locator('#toggle-right').isVisible(),true);
        await page.setViewportSize({width:1600,height:1000});
        await page.waitForTimeout(250);
        const popupPromise=page.waitForEvent('popup'); await page.locator('#printbtn').click();
        const print=await popupPromise; await print.waitForLoadState();
        await print.emulateMedia({media:'print'});
        assert.equal(await print.locator('section .rcard').count(),+(await page.locator('#risk-summary .summary-three b').first().innerText()));
        assert.equal(await print.locator('svg .risk-pin').count(),await page.locator('svg .risk-pin').count());
        assert(await print.locator('section .rcard').first().isVisible());
        await print.close();
        await page.getByRole('tab',{name:/Kerawanan/i}).click();
        for(const row of await page.locator('#risklist .offpage').all()) {
          const seq=await row.getAttribute('data-seq');
          const other=views.find(v=>v.subsystem_id===view.subsystem_id && v.id!==view.id && fs.readFileSync(`site/data/view-${v.id}.svg`,'utf8').includes(`data-risk-seqs="${seq}"`));
          if(!other) continue;
          await row.click();
          await page.waitForFunction(id=>VIEW.id===id && document.querySelector('#stageload').hidden,other.id,{timeout:120000});
          assert.equal(await page.locator('#risk-active .rcard').getAttribute('data-seq'),seq);
          await page.locator(`.risk-pin[data-risk-seqs="${seq}"].active`).first().waitFor({state:'visible',timeout:10000});
          console.log(`PASS ${base}: off-view item #${seq} opens ${other.view_key}`);
          break;
        }
        console.log(`PASS ${base} ${view.view_key}: panels, geometry, selection, filters, hover, keyboard, resize, print`);
      }
      // Panel preference is restored after reload.
      const expected=await page.locator('#toggle-left').getAttribute('aria-expanded');
      await page.reload(); await page.locator('#stage svg').waitFor({timeout:120000});
      assert.equal(await page.locator('#toggle-left').getAttribute('aria-expanded'),expected);
      await page.goto(`${base}/?browser-test=map#peta=JAMALI/JAKARTA_BANTEN`);
      await page.locator('.ss-pin').first().waitFor({timeout:120000});
      const ssPin=page.locator('.ss-pin').filter({hasText:'LBK'});
      await ssPin.hover();
      assert.equal(await page.locator('.ss-card .summary-three span').count(),3);
      assert((await page.locator('.ss-card').innerText()).includes('Per view'));
      assert.equal(await page.locator('.ss-card').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(255, 255, 255)');
      await ssPin.press('Enter');
      assert.equal(await page.locator('.ss-card').isVisible(),true);
      await page.locator('.ss-open').click();
      await page.locator('#stage svg').waitFor({timeout:120000});
      if(await page.locator('#toggle-right').getAttribute('aria-expanded')==='false') await page.locator('#toggle-right').click();
      await page.getByRole('tab',{name:/Kerawanan/i}).click();
      fs.mkdirSync('.render_tmp/dashboard-browser',{recursive:true});
      await page.screenshot({path:`.render_tmp/dashboard-browser/${base.endsWith('8766') ? 'snapshot' : 'live'}.png`});
      console.log(`PASS ${base}: SS hover/click/keyboard card, Buka SLD, persisted panels, no browser errors`);
      assert.deepEqual(errors,[]);
      await context.close();
      const tablet=await browser.newContext({viewport:{width:820,height:1100},hasTouch:true});
      const touch=await tablet.newPage();
      await touch.goto(`${base}/?browser-test=touch#v=${targets[0].view_key}`);
      const touchPin=touch.locator('#stage svg .risk-pin').first();
      await touchPin.waitFor({timeout:120000});
      await touch.locator('#toggle-left').tap();
      await touch.locator('#zfit').tap();
      const touchSeq=await touchPin.getAttribute('data-risk-seqs');
      await touchPin.tap();
      assert.equal(await touch.locator('#right-panel').isVisible(),true);
      assert.equal(await touch.locator('#risk-active .rcard').getAttribute('data-seq'),touchSeq);
      console.log(`PASS ${base}: tablet tap opens persistent detail without hover`);
      await tablet.close();
    }
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
