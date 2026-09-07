#!/usr/bin/env python3
"""Verify the approved editorial port against the actual built site.

Requires the same optional Playwright dependency as scripts/shots.py. Opens an isolated
browser against a temporary local server; never submits forms or contacts booking services.
Run: python scripts/check_site_merge.py [--browser /path/to/chromium]
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('index', 'coordination-review', 'fees', 'partners', 'manual', 'principles', 'leadership')
WIDTHS = (1600, 1440, 1280, 1200, 1180, 768, 390, 320)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def main():
    from playwright.sync_api import sync_playwright, expect
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser')
    parser.add_argument('--out', type=Path, default=ROOT / 'artifacts' / 'site-merge')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'docs')))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    results = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**({'executable_path': args.browser} if args.browser else {}))
            context = browser.new_context(reduced_motion='reduce', device_scale_factor=1)
            # The real analytics loader remains in the HTML. QA must not create production events.
            context.route('https://plausible.io/**', lambda route: route.fulfill(status=200, body=''))
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            for width in WIDTHS:
                page.set_viewport_size({'width': width, 'height': 1000})
                for name in PAGES:
                    errors.clear()
                    response = page.goto(f'{base}/{name}.html', wait_until='load')
                    assert response.status == 200
                    page.evaluate('document.fonts.ready')
                    expect(page.locator('h1')).to_have_count(1)
                    assert not errors, (name, width, errors)
                    assert page.locator('dc-import,x-dc,sc-for,iframe').count() == 0
                    assert page.locator('a[href="#"]').count() == 0
                    metrics = page.evaluate('''() => ({
                      scroll:document.documentElement.scrollWidth,width:innerWidth,
                      overflow:[...document.querySelectorAll('body *')].filter(el=>{
                        const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                        return r.width>0&&r.right>innerWidth+1&&s.visibility!=='hidden'&&s.display!=='none'
                          &&!el.closest('svg,.record-table-scroll,.dwnav-panel');
                      }).map(el=>[el.tagName,String(el.className),el.getBoundingClientRect().right]),
                      fonts:document.fonts.check('16px Satoshi')&&document.fonts.check('16px Erode')
                    })''')
                    assert metrics['scroll'] <= width and not metrics['overflow'], (name, width, metrics)
                    assert metrics['fonts'], (name, 'fonts not loaded')
                    nav = page.locator('nav.dwnav')
                    expect(nav).to_have_count(1)
                    if width < 1180:
                        toggle = nav.locator('.dwnav-toggle')
                        expect(toggle).to_be_visible()
                        toggle.click()
                        expect(toggle).to_have_attribute('aria-expanded', 'true')
                    expect(nav.locator('.dwnav-direct', has_text='Fees')).to_be_visible()
                    expect(nav.get_by_role('button', name='For professionals', exact=True)).to_be_visible()
                    expect(nav.get_by_role('button', name='For professionals', exact=True)).to_have_count(1)
                    expect(nav.locator('.dwnav-access')).to_be_visible()
                    expect(nav.locator('.dwnav-cta')).to_be_visible()
                    assert nav.locator('.dwnav-cta').inner_text().strip().startswith('Request a Coordination Review')
                    if width < 1180:
                        page.keyboard.press('Escape')
                        expect(toggle).to_have_attribute('aria-expanded', 'false')
                    elif width <= 1240:
                        expect(nav.locator('.dwnav-insights')).to_be_hidden()
                        trigger = nav.get_by_role('button', name='The record', exact=True)
                        trigger.focus(); page.keyboard.press('ArrowDown')
                        expect(nav.locator('.dwnav-folded-insights')).to_be_visible()
                        page.keyboard.press('Escape')
                        expect(trigger).to_have_attribute('aria-expanded', 'false')
                        expect(nav.locator('.dwnav-folded-insights')).to_be_hidden()
                    office = page.locator('.firm-anchor .fa-i').first
                    expect(office).to_have_text('Chicago, Illinois · Austin, Texas')
                    expect(page.locator('.firm-anchor a[href="tel:+17085487600"]')).to_have_count(1)
                    if name == 'index':
                        assert page.locator('.hero').bounding_box()['y'] < page.locator('#governance').bounding_box()['y'] < page.locator('#thesystem').bounding_box()['y']
                        plate = page.locator('.heron-col img')
                        assert plate.evaluate('(img)=>img.complete&&img.naturalWidth===660')
                        if width >= 1180:
                            assert 360 <= plate.bounding_box()['width'] <= 480
                        for i in range(5):
                            button = page.locator(f'.trig-btn[data-t="{i}"]')
                            button.click()
                            expect(button).to_have_attribute('aria-pressed', 'true')
                            assert page.locator('#sysDiagram .node.active').count() >= 5
                        page.keyboard.press('Escape')
                        assert page.locator('.trig-btn[aria-pressed="true"]').count() == 0
                        node = page.locator('#sysDiagram .node').first
                        node.hover()
                        assert 'active' in node.get_attribute('class')
                        page.mouse.move(0, 0)
                    if name == 'coordination-review':
                        expect(page.locator('.terms>div')).to_have_count(4)
                        expect(page.locator('.dv .spec')).to_have_count(5)
                    if name == 'fees':
                        expect(page.locator('.fee-schedule-label')).to_have_count(2)
                        assert page.locator('a.fee-schedule-label').count() == 0
                        assert not page.evaluate('''() => [...document.querySelectorAll('main *')].some(el=>{
                          const s=getComputedStyle(el);return [s.color,s.backgroundColor,s.borderColor].some(c=>['rgb(21, 128, 106)','rgb(21, 70, 58)'].includes(c));
                        })''')
                    if name == 'partners':
                        for book in page.locator('a.book').all():
                            assert book.inner_text().startswith('Professional introduction, 15 minutes')
                            assert 'utm_campaign=cpa_referral' in book.get_attribute('href')
                        assert page.locator('form,input').count() == 0
                    if name == 'manual':
                        page.evaluate('window.print=()=>{window.__printCalled=true}')
                        page.get_by_role('button', name='Read as one page').click()
                        assert page.evaluate('window.__printCalled === true')
                        assert page.locator('.ledger-row').count() == 8
                        assert page.locator('.deps .dep').count() == 10
                    page.evaluate('window.scrollTo(0,0)')
                    if width in (1440, 1200, 390):
                        page.screenshot(path=str(args.out / f'{name}-{width}.png'), full_page=True)
                    results.append({'page': name, 'width': width, 'status': 'passed'})
                    print(f'PASS {name} {width}px', flush=True)
            # Print at a phone viewport: CSS must restore every column, independent of screen width.
            page.goto(f'{base}/manual.html', wait_until='load')
            page.emulate_media(media='print')
            assert page.locator('.ledger .c5').first.is_visible()
            assert page.locator('.reg .c2').first.is_visible()
            page.pdf(path=str(args.out / 'manual.pdf'), format='A4', print_background=True)
            # With JavaScript disabled the full navigation and the record are still reachable.
            nojs = browser.new_context(java_script_enabled=False, viewport={'width':390,'height':900})
            np = nojs.new_page();np.goto(f'{base}/manual.html', wait_until='load')
            expect(np.locator('.dwnav-direct')).to_be_visible()
            expect(np.locator('a[href="partners.html"]')).to_be_visible()
            assert np.locator('.ledger-row').count() == 8
            browser.close()
    finally:
        server.shutdown()
        (args.out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    print(f'{len(results)} page/viewport checks passed; Manual print and no-JS checks passed.')


if __name__ == '__main__':
    main()
