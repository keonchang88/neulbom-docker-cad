# Canonical case generator: rebuilds Case_Bottom / Case_Top from parameters.
# Edit parameters below (e.g. after caliper measurements) and re-run.
import FreeCAD as App
import Part
from FreeCAD import Vector, Placement

OUT = "/tmp/claude-1001/-home-a15209-Documents-neulbom-docker-cad/a59d395a-4777-424f-8da4-9ac6f5e69d45/scratchpad/rebuild_case_result.txt"
lines = []
doc = App.openDocument("/home/a15209/Documents/neulbom-docker-cad/neulbom_pod/Case_dev/FCStd/CaseStatic.FCStd")

# ---------------- parameters ----------------
CAV = dict(x0=-4.60, x1=89.55, y0=-3.00, y1=58.00, z0=-21.50, z1=50.70)
OUT_ = dict(x0=-7.00, x1=91.95, y0=-5.40, y1=60.40, z0=-23.90, z1=53.10)  # wall 2.4mm
SPLIT = 8.0
FIL_V = 2.0   # vertical corner fillet (both halves)
CHAM_R = 1.5  # top/bottom rim chamfer (45deg, bed-side edge: FDM-safe)
# wall openings: (x0,x1,y0,y1,z0,z1), crosses_split flag for lip breaks
OPENINGS = [
    ("ethernet",   89.45, 92.05,  0.30, 20.20,  4.4, 23.7, True),
    ("usb1",       89.45, 92.05, 19.80, 38.30,  4.9, 26.6, True),
    ("usb2",       89.45, 92.05, 37.70, 56.20,  4.9, 26.5, True),
    ("pi_usbc",     4.70, 17.70, -5.50, -2.90,  5.4, 13.7, True),
    ("hdmi0",      20.10, 31.60, -5.50, -2.90,  6.7, 13.7, True),
    ("x1200_usbc", 45.30, 58.30, -5.50, -2.90, -1.4,  6.8, False),
    ("x1200_sw",   -7.10, -4.50, 37.30, 48.80, -9.5,  2.0, False),
    ("pwr_btn",    -7.10, -4.50, 14.80, 22.00,  6.5, 13.7, True),
]
# camera
CAM_HOLES = [(13.5, 3.5), (26.0, 3.5), (13.5, 24.5), (26.0, 24.5)]
CAM_SEAT = 45.25
CAM_LINK_Z = 44.55  # camera link z (11mm gap to AI HAT PCB top, clears measured 10mm heatsink +1mm)
CAM_LINK_X = 11.5   # camera link x (moved +10mm)
BOSS_R, PIN_R, PIN_LEN = 2.5, 1.0, 1.7
LENS_SQ = (20.15, 31.65, 8.25, 19.75)  # square lens hole X0,X1,Y0,Y1
# lip
LIP_H, LIP_IN, LIP_OUTX, REC_OUT, REC_TOPCLR = 3.0, 0.15, 1.15, 1.35, 0.2  # lip 1.0t
# stack mount (plan A): HAT corner guides + ledges (top), X1200 support posts (bottom)
HAT = dict(x0=0.0, x1=65.0, y0=0.0, y1=56.5, zbot=28.40)  # AI HAT PCB footprint, bottom z (20mm spacer on Pi PCB top 8.396, measured)
HAT_LINK_Z = 28.40  # AIHAT_Assembly link z (= HAT zbot)
G_CLR = 0.25    # guide-to-board clearance
G_T = 2.0       # guide leg thickness
G_LEG = 8.0     # guide leg length along edge
G_ZBOT = 27.97  # guide lower end (slightly below HAT bottom, lead-in)
STOP_W = 1.2    # stop tab reach over HAT top edge
STOP_CLR = 0.30 # vertical play above HAT top (print tolerance margin)
HAT_ZTOP = 30.95
POST_W, POST_D = 6.0, 4.0     # bottom support post XY size
# ventilation (FDM: slit 3.0 wide, rib 2.0 — both above min-feature limits)
VENT_W, VENT_PITCH = 3.0, 5.0
WALL_VENT = dict(x0=8.0, x1=81.0, z0=11.5, z1=27.4)  # +Y wall intake, active-cooler level (top just below G_ZBOT)
# top-face exhaust zones over Hailo heatsink (avoid lens hole/bosses y<=27, x<=38; guides/ribs at rims)
TOP_VENTS = [
    (40.0, 63.0,  6.0, 52.0),   # right of camera
    ( 6.0, 20.0, 32.0, 52.0),   # behind camera, left half
    (22.0, 36.0, 32.0, 52.0),   # behind camera, right half (2mm spine between)
]
POST_TOP = -0.30              # post top 0.3 below X1200 PCB bottom (print tolerance margin)
POST_STRIPS = [(0.7, 4.7), (51.3, 55.3)]  # y strips along X1200 edges
# magnet plate skirt pocket (neulbom_docker pod plate 30x90x8, magnets 2x D21 pockets, 48.45 pitch)
PLATE_L, PLATE_W, PLATE_T = 90.0, 30.0, 8.0  # plate long axis along case X, centered
PLATE_CLR = 0.2      # pocket clearance per side (glued fit)
PLATE_PROUD = 0.1    # plate magnet face proud of skirt rim (guarantees magnet contact on docker)
SKIRT_Z0 = OUT_['z0'] - PLATE_T + PLATE_PROUD  # skirt bottom rim (new bed face)
# --------------------------------------------

cam = doc.getObject("Camera3_Std")
_p = cam.Placement
if abs(_p.Base.z - CAM_LINK_Z) > 1e-6 or abs(_p.Base.x - CAM_LINK_X) > 1e-6:
    cam.Placement = Placement(Vector(CAM_LINK_X, _p.Base.y, CAM_LINK_Z), _p.Rotation)
    lines.append("camera link -> x %.2f z %.2f" % (CAM_LINK_X, CAM_LINK_Z))

hat_l = doc.getObject("AIHAT_Assembly")
_hp = hat_l.Placement
if abs(_hp.Base.z - HAT_LINK_Z) > 1e-6:
    hat_l.Placement = Placement(Vector(_hp.Base.x, _hp.Base.y, HAT_LINK_Z), _hp.Rotation)
    lines.append("AIHAT link -> z %.2f" % HAT_LINK_Z)

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1-x0, y1-y0, z1-z0, Vector(x0, y0, z0))

cav_box = box(CAV['x0'], CAV['x1'], CAV['y0'], CAV['y1'], CAV['z0'], CAV['z1'])
bottom = box(OUT_['x0'], OUT_['x1'], OUT_['y0'], OUT_['y1'], OUT_['z0'], SPLIT).cut(cav_box)
top    = box(OUT_['x0'], OUT_['x1'], OUT_['y0'], OUT_['y1'], SPLIT, OUT_['z1']).cut(cav_box)

# openings
for (_n, x0, x1, y0, y1, z0, z1, _c) in OPENINGS:
    b = box(x0, x1, y0, y1, z0, z1)
    bottom = bottom.cut(b)
    top = top.cut(b)

# camera square lens hole
top = top.cut(box(LENS_SQ[0], LENS_SQ[1], LENS_SQ[2], LENS_SQ[3], CAV['z1']-0.73, OUT_['z1']+1.3))

# ventilation: +Y wall intake slits (vertical, through wall)
nvw = 0
x = WALL_VENT['x0']
while x + VENT_W <= WALL_VENT['x1'] + 1e-6:
    top = top.cut(box(x, x + VENT_W, CAV['y1'] - 0.5, OUT_['y1'] + 0.5, WALL_VENT['z0'], WALL_VENT['z1']))
    nvw += 1
    x += VENT_PITCH
lines.append("wall vents +Y: %d slits %.1fw z %.1f..%.1f" % (nvw, VENT_W, WALL_VENT['z0'], WALL_VENT['z1']))

# ventilation: top-face exhaust slits over heatsink (X-direction slats)
nvt = 0
for (zx0, zx1, zy0, zy1) in TOP_VENTS:
    y = zy0
    while y + VENT_W <= zy1 + 1e-6:
        top = top.cut(box(zx0, zx1, y, y + VENT_W, CAV['z1'] - 0.5, OUT_['z1'] + 0.5))
        nvt += 1
        y += VENT_PITCH
lines.append("top vents: %d slits %.1fw in %d zones" % (nvt, VENT_W, len(TOP_VENTS)))

# lip (bottom) + recess (top)
def ring(ei, eo, z0, z1):
    o = box(CAV['x0']-eo, CAV['x1']+eo, CAV['y0']-eo, CAV['y1']+eo, z0, z1)
    i = box(CAV['x0']-ei, CAV['x1']+ei, CAV['y0']-ei, CAV['y1']+ei, z0-1, z1+1)
    return o.cut(i)

lip = ring(LIP_IN, LIP_OUTX, SPLIT, SPLIT+LIP_H)
for (_n, x0, x1, y0, y1, z0, z1, crosses) in OPENINGS:
    if crosses:
        lip = lip.cut(box(x0, x1, y0, y1, z0, z1))
bottom = bottom.fuse(lip)
top = top.cut(ring(0.0, REC_OUT, SPLIT, SPLIT+LIP_H+REC_TOPCLR))

# camera bosses + pins
for (hx, hy) in CAM_HOLES:
    top = top.fuse(Part.makeCylinder(BOSS_R, (CAV['z1']+0.77)-CAM_SEAT, Vector(hx, hy, CAM_SEAT), Vector(0,0,1)))
    top = top.fuse(Part.makeCylinder(PIN_R, PIN_LEN+1.0, Vector(hx, hy, CAM_SEAT-PIN_LEN), Vector(0,0,1)))

# ---- plan A: HAT corner guides + ledges on top ----
gz0, gz1 = G_ZBOT, CAV['z1'] + 0.3   # embed into top inner face for fusion
hx0, hx1 = HAT['x0'] - G_CLR, HAT['x1'] + G_CLR   # guide inner faces
hy0, hy1 = HAT['y0'] - G_CLR, HAT['y1'] + G_CLR
guide_parts = []
for (cx, cy, sx, sy) in [(hx0, hy0, -1, -1), (hx1, hy0, +1, -1), (hx0, hy1, -1, +1), (hx1, hy1, +1, +1)]:
    # leg parallel to Y (on +/-X side of board)
    lx = (CAV['x0'] - 0.5, cx) if sx < 0 else (cx, cx + G_T)  # -X legs merge into wall
    ly = (CAV['y0'] - 0.5, cy + G_LEG) if sy < 0 else (cy - G_LEG, min(cy + G_T, CAV['y1'] + 0.5))
    guide_parts.append(box(lx[0], lx[1], ly[0], ly[1], gz0, gz1))
    # leg parallel to X (on +/-Y side of board)
    lyy = (CAV['y0'] - 0.5, cy) if sy < 0 else (cy, min(cy + G_T, CAV['y1'] + 0.5))  # -Y legs merge into wall
    lxx = (CAV['x0'] - 0.5, cx + G_LEG) if sx < 0 else (cx - G_LEG, cx + G_T)
    guide_parts.append(box(lxx[0], lxx[1], lyy[0], lyy[1], gz0, gz1))
    # stop tab ABOVE HAT top edge, -Y corners only (clears heatsink/camera, allows insertion)
    if sy < 0:
        tx = (cx, cx + STOP_W) if sx < 0 else (cx - STOP_W, cx)
        guide_parts.append(box(tx[0], tx[1], cy + 1.75, cy + 7.75, HAT_ZTOP + STOP_CLR, CAV['z1'] + 0.3))
for g in guide_parts:
    top = top.fuse(g)
lines.append("HAT corner guides: 4 (legs %0.1ft x %0.1f long, z %.1f..%.1f) + 2 stop tabs above HAT top (clr %.2f)" % (G_T, G_LEG, gz0, gz1, STOP_CLR))

# ---- plan A: bottom support posts under X1200 PCB edges ----
obst = []
for nm in ("UPS_X1200", "Battery1", "Battery2"):
    o = doc.getObject(nm)
    pl = o.Placement
    for s in o.LinkedObject.Shape.Solids:
        bb = s.BoundBox
        pts = [pl.multVec(Vector(x, y, z)) for x in (bb.XMin, bb.XMax) for y in (bb.YMin, bb.YMax) for z in (bb.ZMin, bb.ZMax)]
        obst.append((min(p.x for p in pts), max(p.x for p in pts),
                     min(p.y for p in pts), max(p.y for p in pts),
                     min(p.z for p in pts), max(p.z for p in pts)))

def pad_free(px0, px1, py0, py1, pz0, pz1):
    for (ox0, ox1, oy0, oy1, oz0, oz1) in obst:
        if px0 < ox1 and ox0 < px1 and py0 < oy1 and oy0 < py1 and pz0 < oz1 and oz0 < pz1:
            return False
    return True

posts = []
for (sy0, sy1) in POST_STRIPS:
    found = []
    xs = [6 + 2*i for i in range(37)]  # 6..78
    for x in xs:
        if pad_free(x, x + POST_W, sy0, sy1, CAV['z0'] - 1, POST_TOP):
            found.append(x)
    if found:
        posts.append((found[0], sy0, sy1))
        if found[-1] != found[0]:
            posts.append((found[-1], sy0, sy1))
for (px, sy0, sy1) in posts:
    bottom = bottom.fuse(box(px, px + POST_W, sy0, sy1, CAV['z0'] - 1.0, POST_TOP))
    lines.append("bottom post: X %.1f..%.1f Y %.1f..%.1f top %.2f" % (px, px + POST_W, sy0, sy1, POST_TOP))

# ---- magnet plate skirt pocket on bottom underside ----
_cx = (OUT_['x0'] + OUT_['x1']) / 2.0
_cy = (OUT_['y0'] + OUT_['y1']) / 2.0
skirt = box(OUT_['x0'], OUT_['x1'], OUT_['y0'], OUT_['y1'], SKIRT_Z0, OUT_['z0'])
pocket = box(_cx - PLATE_L/2 - PLATE_CLR, _cx + PLATE_L/2 + PLATE_CLR,
             _cy - PLATE_W/2 - PLATE_CLR, _cy + PLATE_W/2 + PLATE_CLR,
             SKIRT_Z0 - 1.0, OUT_['z0'] + 1.0)
bottom = bottom.fuse(skirt.cut(pocket))
lines.append("plate skirt: pocket X %.2f..%.2f Y %.2f..%.2f z %.2f..%.2f (plate proud %.2f, magnets at X %.2f/%.2f)" % (
    _cx - PLATE_L/2 - PLATE_CLR, _cx + PLATE_L/2 + PLATE_CLR,
    _cy - PLATE_W/2 - PLATE_CLR, _cy + PLATE_W/2 + PLATE_CLR,
    SKIRT_Z0, OUT_['z0'], PLATE_PROUD, _cx - 24.225, _cx + 24.225))

bottom = bottom.removeSplitter()
top = top.removeSplitter()

# fillets
TOL = 0.05
def is_vert_corner(e):
    if len(e.Vertexes) != 2: return False
    a, b = e.Vertexes[0].Point, e.Vertexes[1].Point
    if abs(a.x-b.x) > TOL or abs(a.y-b.y) > TOL: return False
    return ((abs(a.x-OUT_['x0']) < TOL or abs(a.x-OUT_['x1']) < TOL) and
            (abs(a.y-OUT_['y0']) < TOL or abs(a.y-OUT_['y1']) < TOL))

def on_outer_rect(p):
    return (abs(p.x-OUT_['x0']) < 3.5 or abs(p.x-OUT_['x1']) < 3.5 or
            abs(p.y-OUT_['y0']) < 3.5 or abs(p.y-OUT_['y1']) < 3.5)

def rim_edges(sh, zval):
    res = []
    for e in sh.Edges:
        pts = [v.Point for v in e.Vertexes]
        if pts and all(abs(p.z-zval) < TOL for p in pts) and all(on_outer_rect(p) for p in pts):
            mid = e.valueAt(e.FirstParameter + 0.5*(e.LastParameter - e.FirstParameter))
            if on_outer_rect(mid):
                res.append(e)
    return res

def apply_fillets(sh, zrim, tag):
    vert = [e for e in sh.Edges if is_vert_corner(e)]
    s2 = sh.makeFillet(FIL_V, vert)
    lines.append("%s vert fillet R%.1f (%d edges) valid=%s" % (tag, FIL_V, len(vert), s2.isValid()))
    rim = rim_edges(s2, zrim)
    s3 = s2.makeChamfer(CHAM_R, rim)
    lines.append("%s rim chamfer C%.1f (%d edges) valid=%s" % (tag, CHAM_R, len(rim), s3.isValid()))
    return s3 if s3.isValid() else (s2 if s2.isValid() else sh)

bottom = apply_fillets(bottom, SKIRT_Z0, "bottom")
top = apply_fillets(top, OUT_['z1'], "top")

doc.getObject("Case_Bottom").Shape = bottom
doc.getObject("Case_Top").Shape = top
doc.recompute()

lines.append("bottom solids=%d valid=%s / top solids=%d valid=%s" % (len(bottom.Solids), bottom.isValid(), len(top.Solids), top.isValid()))
lines.append("bottom-top overlap %.4f mm3" % bottom.common(top).Volume)
for o in doc.Objects:
    if o.TypeId != "App::Link": continue
    s = o.LinkedObject.Shape.copy()
    s.Placement = o.Placement.multiply(s.Placement)
    for cn, csh in (("bottom", bottom), ("top", top)):
        c = csh.common(s)
        if c.Volume > 0.01:
            lines.append("INTERFERENCE %s vs %s: %.3f mm3" % (cn, o.Name, c.Volume))
lines.append("interference check done")

doc.save()
lines.append("saved")
open(OUT, "w").write("\n".join(lines))
