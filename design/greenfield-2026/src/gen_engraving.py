import numpy as np
from PIL import Image, ImageDraw
import sys, json, base64

# ── Driftwood engraving generator ───────────────────────────────────────────
# Flow-field streamline drawing. Strict brand palette: limestone paper, editorial
# blue / slate ink lines. Deterministic (seeded) so re-runs are stable.
LIMESTONE = np.array([241,239,233], float)   # #f1efe9
BLUE      = np.array([44, 88,120], float)     # #2c5878 editorial blue
SLATE     = np.array([30, 40, 51], float)     # #1e2833 slate ink

def build(kind, W, H, seed, out):
    rng = np.random.default_rng(seed)
    SS = 2                                     # supersample
    w, h = W*SS, H*SS
    asp = w/h
    acc = np.zeros((h, w), np.float32)         # ink accumulation

    def angle(x, y):
        ax = np.abs(x)
        sx = np.sign(x); sx[sx==0] = 1.0
        if kind == "steady":
            # turbulent field, mirror-symmetric in x only; a calm laminar band that
            # holds the line. Vertical symmetry deliberately broken so it reads drawn.
            yb = -0.10                          # calm band sits just above center
            yy = y - yb
            w1 = np.sin(2.6*ax + 1.2*np.sin(1.9*y + 0.6))
            w2 = np.sin(3.4*y - 1.0*np.sin(2.3*ax + 0.3))
            t  = np.pi*(0.55*w1 + 0.52*w2)
            t  = t + 0.5*np.sin(1.3*y + 0.9)               # odd-in-y term breaks the mirror
            t  = t + 0.5*np.sin(3.1*ax)*np.clip(-yy, 0, 1) # extra swirl in the lower field
            s  = np.exp(-(yy/0.30)**2)          # 1 at band, ->0 outward
            vx = (1-s)*np.cos(t) + s*1.0
            vy = (1-s)*np.sin(t)
            vx = vx*sx                          # mirror the two navigators about x=0
            return np.arctan2(vy, vx), s
        elif kind == "shore":  # calm near-horizontal strata, gentle undulation; geography/coastline
            t = 0.24*np.sin(2.0*x + 1.3*np.sin(1.05*y)) + 0.12*np.sin(3.0*y + 0.5*x)
            s = np.clip((y+0.35)/1.1, 0, 1)     # denser toward the lower field
            return t, s
        else:  # "reach": calm vanishing-perspective, lines receding to a high, distant horizon
            cx, cy = 0.0, -1.02                 # vanishing point near the top edge, so no whirlpool
            dx, dy = x-cx, y-cy
            base = np.arctan2(dy, dx)           # radial toward/away the distant point
            # gentle, low-frequency drift so the field reads as drawn, not mechanical; fades near the point
            drift = 0.30*np.sin(1.7*x + 0.8*np.sin(1.4*y)) * np.clip((y+0.7), 0, 1)
            t = base + drift
            s = np.clip((y+0.2)/1.2, 0, 1)      # denser, calmer low field (accumulation)
            return t, s

    P = 3000                                    # streamlines
    NS = 150                                     # steps each direction
    ds = 0.0065
    # seed points, slight bias to noisy regions for the steady field
    xs = rng.uniform(-asp, asp, P)
    ys = rng.uniform(-1.02, 1.02, P)
    traj_x = np.empty((P, 2*NS+1)); traj_y = np.empty((P, 2*NS+1))
    for direction in (1, -1):
        x = xs.copy(); y = ys.copy()
        for k in range(NS+1):
            idx = NS + direction*k
            traj_x[:, idx] = x; traj_y[:, idx] = y
            a, _ = angle(x, y)
            x = x + np.cos(a)*ds*direction
            y = y + np.sin(a)*ds*direction

    # per-streamline ink weight: calmer band lighter, noise darker (signal vs noise)
    a0, s0 = angle(xs, ys)
    weight = 0.5 + 0.9*(1.0 - s0) if kind=="steady" else 0.45 + 0.8*s0

    def to_px(ax, ay):
        px = (ax/asp*0.5 + 0.5)*(w-1)
        py = (ay*0.5 + 0.5)*(h-1)
        return px, py

    # batch draw into 'L' layers, add to accumulator so overlaps build density
    BATCH = 60
    for b0 in range(0, P, BATCH):
        layer = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(layer)
        for p in range(b0, min(b0+BATCH, P)):
            px, py = to_px(traj_x[p], traj_y[p])
            pts = list(zip(px.tolist(), py.tolist()))
            d.line(pts, fill=255, width=SS)
        arr = np.asarray(layer, np.float32)/255.0
        # weighted add for this batch (use mean weight of batch members)
        wv = float(np.mean(weight[b0:min(b0+BATCH,P)]))
        acc += arr*wv

    # normalize and shape the density curve
    a = acc/ (np.percentile(acc, 99.5)+1e-6)
    a = np.clip(a, 0, 1) ** 0.85
    a_ink = np.clip((a-0.62)/0.38, 0, 1)        # deepest densities go slate
    a = a*0.9

    img = (LIMESTONE[None,None,:]*(1-a[...,None])
           + BLUE[None,None,:]*a[...,None])
    img = img*(1-0.55*a_ink[...,None]) + SLATE[None,None,:]*(0.55*a_ink[...,None])
    im = Image.fromarray(np.clip(img,0,255).astype(np.uint8), "RGB")
    im = im.resize((W, H), Image.LANCZOS)
    im.save(out, "JPEG", quality=84, optimize=True, progressive=True)
    return out

if __name__ == "__main__":
    kind, W, H, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    build(kind, W, H, seed, out)
    import os
    print(out, os.path.getsize(out)//1024, "KB")
