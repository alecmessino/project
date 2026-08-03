"""The house mark, and the rules that are the whole point of having one.

A house mark is not a logo, and almost everything that can go wrong with it is a governance
failure rather than a drawing failure: it gets a second version, it turns up in the nav "just
this once", someone brightens it until it competes with the headline, or the animation acquires
a loop. Each of those is cheap to do and permanently expensive — the mark's meaning comes from
being rare, identical, and quiet, and there is no way to earn that back once it is spent.

So the drawing is tested lightly (it is generated and deterministic; the eye is the reviewer) and
the *rules* are tested hard.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from drift import heron  # noqa: E402

WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"
MASTER = WEB / "img" / "heron-engraving.svg"
HUB = WEB / "hub.html"

# Where the mark is allowed to appear at all. One page, one slot.
HOME = ("hub.html", "index.html")


# ── the master ────────────────────────────────────────────────────────────────────────────────

def test_the_master_is_byte_identical_on_every_run():
    """A house mark that differs run to run is not a house mark — and a generator that drifts
    rewrites the committed asset in every future diff."""
    assert heron.render_svg() == heron.render_svg()


def test_the_committed_master_matches_the_generator():
    """The SVG is a committed static asset. If heron.py changed, `python3 scripts/build_heron.py`
    was the other half of the change."""
    assert MASTER.exists(), "the house-mark master is missing"
    assert MASTER.read_text(encoding="utf-8") == heron.render_svg(), (
        "src/drift/web/img/heron-engraving.svg is stale — run python3 scripts/build_heron.py"
    )


def test_the_engraving_is_hatch_and_stipple_only():
    """Engraved vocabulary, stated structurally: paths of open marks, one solid dot for the eye,
    and nothing else. A <rect>, a gradient, or a filter would be a different kind of picture."""
    svg = MASTER.read_text(encoding="utf-8")
    tags = set(re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)", svg))
    assert tags <= {"svg", "g", "path", "circle"}, f"non-engraving elements in the master: {tags}"
    assert "gradient" not in svg and "filter" not in svg and "<image" not in svg


def test_the_engraving_carries_no_outline():
    """**No outlines** is the load-bearing rule of the whole mark: the bird's edge is where the
    tone stops, which is what makes it read as atmosphere before illustration — and what lets it
    survive being embossed, where a contour would not. Every subpath is an open mark; nothing
    closes, so nothing can be a silhouette."""
    svg = MASTER.read_text(encoding="utf-8")
    for d in re.findall(r' d="([^"]*)"', svg):
        assert "z" not in d.lower(), "a closed subpath appeared — the mark has grown an outline"
        # Every mark is a single move plus one short segment: M..l.. or M..h0 (a stipple dot).
        assert not re.search(r"[CcSsQqTtAa]", d), "curves are not the engraver's vocabulary here"


def test_the_engraving_is_one_ink():
    """Single ink tone. No editorial blue, no accent, no second colour anywhere — consumers that
    want it neutral apply grayscale at the point of use."""
    svg = MASTER.read_text(encoding="utf-8")
    colours = set(re.findall(r"#[0-9A-Fa-f]{3,8}", svg))
    assert colours == {heron.INK}, f"the master is no longer a single ink: {sorted(colours)}"


def test_the_bird_faces_left_into_the_page():
    """Standing, Alert, facing left — toward the headline. The bill is the leftmost thing on the
    plate and the eye sits well behind it; if that ever inverts, the pose has been redrawn."""
    bill_x = min(x for x, _ in heron._CULMEN)
    eye_x, _ = heron._EYE
    assert bill_x < eye_x, "the bird is no longer facing left"
    assert bill_x < 0.15 * heron.W, "the bill should reach the left edge of the plate"


def test_the_pose_is_standing_alert_on_two_legs():
    """Not striking, not in flight, not resting: both legs down and carrying weight, head above
    the body, nothing folded."""
    assert heron._LEG_A[-1][1] > 0.9 * heron.H and heron._LEG_B[-1][1] > 0.9 * heron.H, \
        "a leg has left the ground — this is no longer the standing pose"
    assert heron._EYE[1] < 0.2 * heron.H, "the head has dropped; the alert pose carries it high"


# ── scarcity: where the mark may and may not appear ───────────────────────────────────────────

def _pages(root: Path):
    return sorted(p for p in root.glob("*.html"))


def test_the_house_mark_appears_on_the_homepage_and_nowhere_else():
    """This is the rule the mark's meaning is made of. It is not a decorative asset that pages may
    reach for; it appears where Driftwood is making an enduring statement, and the homepage hero is
    the first of those. Every other page is a deliberate absence, not an oversight."""
    strays = []
    for root in (WEB, DOCS):
        for page in _pages(root):
            if page.name in HOME:
                continue
            if "heron-engraving" in page.read_text(encoding="utf-8"):
                strays.append(f"{root.name}/{page.name}")
    assert not strays, f"the house mark has spread to: {strays} — rarity is the whole instrument"


def test_the_homepage_uses_the_mark_exactly_once():
    """One appearance, one slot. A second instance on the same page is repetition, and repetition
    is what the scarcity rule exists to prevent."""
    for page in (HUB, DOCS / "index.html"):
        t = page.read_text(encoding="utf-8")
        assert t.count('src="img/heron-engraving.svg"') == 1, \
            f"{page.name} carries the mark more than once"


def test_the_mark_is_never_navigation_furniture():
    """Explicitly forbidden slots: nav, footer, favicon, mask icon, section dividers, avatars. The
    wordmark is the identity in all of them."""
    t = HUB.read_text(encoding="utf-8")
    for tag in re.findall(r"<(?:nav|footer)\b[^>]*>.*?</(?:nav|footer)>", t, re.S):
        assert "heron" not in tag.lower(), "the house mark has turned up in page furniture"
    for rel in re.findall(r'<link[^>]*rel="[^"]*icon[^"]*"[^>]*>', t):
        assert "heron" not in rel, "the house mark is being used as an icon"
    for meta in re.findall(r'<meta[^>]*property="og:image"[^>]*>', t):
        assert "heron" not in meta, "the house mark is being used as a social image"


def test_the_mark_is_decorative_and_unlinked():
    """The wordmark already provides the brand identity, so the engraving is announced to nobody:
    empty alt, aria-hidden, and never wrapped in a link."""
    t = HUB.read_text(encoding="utf-8")
    tag = re.search(r"<img[^>]*heron-engraving[^>]*>", t)
    assert tag, "the hero has lost the house mark"
    assert 'alt=""' in tag.group(0) and 'aria-hidden="true"' in tag.group(0)
    before = t[: tag.start()]
    assert before.rfind("<a ") < before.rfind("</a>"), "the house mark is inside a link"


# ── restraint: it never competes with the typography ──────────────────────────────────────────

def test_the_mark_stays_under_the_opacity_ceiling():
    """Tuned at .14 and capped at .18. Past that it stops being the ground the words sit on and
    starts being a picture they sit in front of."""
    t = HUB.read_text(encoding="utf-8")
    levels = [float(v) for v in re.findall(r"--mark-o:\s*(\.\d+|0?\.\d+)", t)]
    assert levels, "the house mark's opacity token is gone"
    assert max(levels) <= 0.18, f"the house mark is too loud: {levels}"


def test_the_mark_sits_behind_the_copy():
    """Typography has priority, structurally and not by luck: the mark is on the floor of the
    hero's stacking context and the headline and CTAs are above it."""
    t = HUB.read_text(encoding="utf-8")
    assert re.search(r"\.housemark\{[^}]*z-index:0", t, re.S), "the mark left the back plane"
    assert re.search(r"\.hero>\.hero-grid,\.hero>\.ctas\{[^}]*z-index:1", t), \
        "the hero copy is no longer lifted above the mark"
    assert re.search(r"\.housemark\{[^}]*mask-image:", t, re.S) or \
        re.search(r"mask-image:[^;]*\}\s*$", t), "the mark no longer fades toward the copy"


# ── motion: one pass, then permanent ──────────────────────────────────────────────────────────

def _housemark_animation(t: str) -> str:
    m = re.search(r"\.housemark\{animation:([^}]*)\}", t)
    assert m, "the one-time reveal (Option B) is gone"
    return m.group(1)


def test_the_reveal_runs_once_and_then_the_mark_is_permanent():
    """Option B is a plate coming off a press, not a logo animating. One pass, 800–1200ms, and
    then nothing: no loop, no alternate, no scroll replay, no parallax, no idle drift."""
    anim = _housemark_animation(HUB.read_text(encoding="utf-8"))
    assert "infinite" not in anim and "alternate" not in anim, "the reveal has started looping"
    ms = int(re.search(r"(\d+)ms", anim).group(1))
    assert 800 <= ms <= 1200, f"the reveal is {ms}ms; the brief is 800–1200ms"
    assert "both" in anim or "forwards" in anim, "the reveal does not hold its final state"


def test_the_reveal_never_draws_itself():
    """The forbidden register: paths drawing themselves, handwriting, illustration animation. The
    reveal resolves tone — opacity, blur, contrast — and moves nothing."""
    t = HUB.read_text(encoding="utf-8")
    frames = re.search(r"@keyframes housemark-resolve\{(.*?)\n", t, re.S)
    assert frames, "the reveal keyframes are gone"
    body = re.search(r"@keyframes housemark-resolve\{(.*?)\}\}", t, re.S).group(1)
    for banned in ("stroke-dash", "clip-path", "translate", "scale3d", " scale(",
                   "rotate(", "offset-path"):
        assert banned not in body, f"the reveal has grown a {banned} — that is logo animation"


def test_both_motion_versions_are_live_and_reduced_motion_is_honored():
    """Two versions in the page so the live implementation can be judged rather than argued about:
    B by default, A (static control) at ?mark=static. Reduced motion always lands on A."""
    t = HUB.read_text(encoding="utf-8")
    assert re.search(r'@media\(prefers-reduced-motion:reduce\)\{\.housemark\{animation:none\}', t)
    assert re.search(r'html\[data-housemark="static"\] \.housemark\{animation:none\}', t)


def test_the_static_control_is_reachable_from_the_url_not_only_from_the_css():
    """CLAUDE.md's standing rule: when one value has both a URL path and a page path, test the URL
    path explicitly — the two diverge silently. Here the divergence would cost the experiment its
    control arm, with nothing visibly broken. So: the attribute the inline script writes must be
    exactly the attribute the stylesheet selects on, for every accepted spelling of the param."""
    t = HUB.read_text(encoding="utf-8")
    script = re.search(r'get\("mark"\).*?dataset\.housemark = "(\w+)"', t, re.S)
    assert script, "the ?mark= switch is gone; Option A is unreachable from the URL"
    written = script.group(1)
    selected = re.search(r'html\[data-housemark="(\w+)"\] \.housemark', t).group(1)
    assert written == selected, (
        f'the script writes data-housemark="{written}" but the CSS selects "{selected}" — '
        "the static control arm silently does nothing"
    )
    accepted = set(re.findall(r'm === "(\w+)"', t))
    assert "static" in accepted, f"?mark=static no longer pins the control: {accepted}"
