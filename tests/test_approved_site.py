"""Production-port contracts: approved records, real links, inert design artifacts and shared chrome."""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'src/drift/web'
DOCS = ROOT / 'docs'
PAGES = ('hub', 'coordination-review', 'fees', 'partners', 'manual', 'principles', 'leadership')
RECORD = ('ic-memo.html', 'opportunity-register.html', 'manual.html', 'transition-plan.html', 'decision-register.html')


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.ids = set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if 'id' in attrs:
            self.ids.add(attrs['id'])


def test_only_production_html_is_shipped_on_the_ported_pages():
    for name in PAGES:
        text = (DOCS / ('index.html' if name == 'hub' else name + '.html')).read_text()
        for artifact in ('dc-import', '<x-dc', '<sc-for', 'support.js', '.dc.html', '_ds/', 'localhost', '127.0.0.1', '{{', '<iframe'):
            assert artifact not in text, (name, artifact)
        assert len(re.findall(r'<h1\b', text)) == 1
        assert 'plausible.io/js/pa-h6JBp-7giRA83TjPL4uHQ.js' in text
        assert 'Park Avenue Securities' in text and 'privacy.html' in text and 'terms.html' in text


def test_all_ported_page_links_and_fragments_resolve():
    for name in PAGES:
        filename = 'index.html' if name == 'hub' else name + '.html'
        for href in Links((DOCS / filename).read_text()).links:
            assert href != '#', (filename, 'placeholder link')
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            target = DOCS / (unquote(url.path) or filename)
            if target.is_dir():
                target /= 'index.html'
            assert target.exists(), (filename, href)
            if url.fragment:
                assert url.fragment in Links(target.read_text()).ids, (filename, href)


def test_the_four_record_strips_use_the_same_five_live_documents():
    for name in ('hub', 'coordination-review', 'manual', 'principles'):
        text = (WEB / (name + '.html')).read_text()
        strip = re.search(r'<div[^>]*class="record-strip"[^>]*>(.*?)</div>', text, re.S)
        assert strip, name
        assert tuple(Links(strip.group(1)).links) == RECORD
        plain = unescape(re.sub(r'<[^>]*>', '', strip.group(1)))
        for label in ('01 Coordination Report', '02 Opportunity Register', '03 Wealth Operating Manual', '04 90-Day Plan', '05 Decision Register'):
            assert label in plain, (name, label)


def test_retired_record_names_are_not_public_product_labels():
    for page in WEB.glob('*.html'):
        text = re.sub(r'<!--.*?-->', '', page.read_text(), flags=re.S)
        assert 'Coordination Index' not in text, page.name
        assert 'Coordination Register' not in text, page.name


def test_review_and_partner_booking_audiences_remain_distinct():
    for name, campaign, label in (
        ('coordination-review', 'coordination_review', 'Request a Coordination Review'),
        ('partners', 'cpa_referral', 'Professional introduction, 15 minutes'),
    ):
        text = (WEB / (name + '.html')).read_text()
        bookings = [link for link in Links(text).links if 'calendly.com' in link]
        assert len(bookings) == 2
        assert all('utm_campaign=' + campaign in link for link in bookings)
        assert label in text
        assert 'Schedule the' not in text
    assert '<form' not in (WEB / 'partners.html').read_text()


def test_missing_fee_pdf_is_not_a_fake_download_and_teal_remains_elsewhere():
    fees = (WEB / 'fees.html').read_text()
    assert fees.count('class="fee-schedule-label"') == 2
    assert 'PDF not yet published.' in fees
    assert not re.search(r'<a[^>]*fee-schedule', fees)
    assert '#15806a' not in fees and 'var(--teal' not in fees
    assert '#15806a' in (WEB / 'manual.html').read_text()
    assert '--teal:#15463a; --teal2:#15806a;' in (WEB / 'driftwood.css').read_text()


def test_manual_records_are_static_printable_and_the_key_precedes_the_ledger():
    text = (WEB / 'manual.html').read_text()
    assert text.index('How to read this book:') < text.index('Household Decision Ledger')
    assert text.count('class="ledger ledger-row"') == 8
    assert 'onclick="window.print()"' in text
    assert 'Set in Satoshi' not in text and 'a concept for' not in text
    assert 'tabindex="0"' in text and 'role="table"' in text


def test_fees_and_professionals_are_standing_nav_entries_everywhere():
    from drift.nav import render
    from drift.site import firm_anchor_html
    nav = render()
    assert nav.count('>For professionals<') == 1
    assert nav.count('href="fees.html"') == 1
    assert 'class="dwnav-direct"' in nav and '>The record<' in nav
    assert 'class="dwnav-folded-insights"' in nav
    for page in (DOCS / 'atlas').rglob('*.html'):
        text = page.read_text()
        if '<nav ' not in text:
            continue
        assert 'data-chrome="waterline"' in text, page
        assert firm_anchor_html() in text, page
