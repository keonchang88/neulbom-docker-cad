# Dummy model generator: Lenovo Xiaoxin Pad Pro 12.7 (2025) 8+128GB tablet.
# Body/display dims from published specs; corner R, camera bump, port positions
# are assumptions — update after caliper measurement and re-run.
import os
import FreeCAD as App
import Part
import Mesh
from FreeCAD import Vector

REPO = "/home/a15209/Documents/neulbom-docker-cad/neulbom_UI"
OUT = os.path.join(REPO, "stl_step")

# ---------------- parameters (mm) ----------------
L, W, T = 291.77, 189.16, 6.9   # body: X length, Y width, Z thickness (spec)
CORNER_R = 11.0                  # corner radius (assumed)
EDGE_R = 1.2                     # side-edge round, top & bottom perimeter (assumed)
# display active area 12.7" 2944x1840 (1.6:1) -> 273.6 x 171.0, engraved 0.2 deep
SCR_L, SCR_W, SCR_DEPTH, SCR_R = 273.6, 171.0, 0.2, 6.0
# rear camera bump: rounded square island near +X +Y corner (landscape top-left
# when viewed from back), lens + flash cylinders (assumed)
BUMP_SQ, BUMP_H, BUMP_R = 26.0, 2.5, 8.0
BUMP_MARGIN = 8.0                # bump edge to body edges
LENS_D, LENS_H = 12.0, 0.6      # lens ring on bump
FLASH_D = 4.5
# front camera: engraved dot on +Y long-edge bezel, centered in X
FCAM_D, FCAM_DEPTH = 3.0, 0.2
# USB-C slot on +X short edge, centered
USBC_W, USBC_H, USBC_DEPTH = 9.0, 3.2, 1.5

doc = App.newDocument("XiaoxinPadPro127")

def rounded_plate(lx, ly, lz, r, cx=0.0, cy=0.0, z0=0.0):
    """XY-rounded-corner box centered at (cx, cy), from z0 up lz."""
    sk = Part.makeBox(lx, ly, lz, Vector(cx - lx / 2, cy - ly / 2, z0))
    edges = [e for e in sk.Edges
             if abs(e.tangentAt(e.FirstParameter).z) > 0.99]
    return sk.makeFillet(r, edges)

# body: rounded-corner slab, then round the top/bottom perimeter edges
body = rounded_plate(L, W, T, CORNER_R)
persim = [e for e in body.Edges
          if abs(e.tangentAt(e.FirstParameter).z) < 0.01
          and (abs(e.CenterOfMass.z) < 0.01 or abs(e.CenterOfMass.z - T) < 0.01)]
body = body.makeFillet(EDGE_R, persim)

# screen engraving (top face z=T)
screen = rounded_plate(SCR_L, SCR_W, SCR_DEPTH + 0.1, SCR_R, z0=T - SCR_DEPTH)
body = body.cut(screen)

# front camera dot on +Y bezel (between screen edge and body edge)
fcam_y = (SCR_W / 2 + W / 2) / 2
fcam = Part.makeCylinder(FCAM_D / 2, FCAM_DEPTH + 0.1,
                         Vector(0, fcam_y, T - FCAM_DEPTH))
body = body.cut(fcam)

# USB-C slot on +X edge, mid-thickness: stadium profile in the YZ plane,
# cut inward along X
sl_y = USBC_W - USBC_H  # straight span between the two end radii
sx = L / 2 - USBC_DEPTH
usbc = Part.makeBox(USBC_DEPTH * 2, sl_y, USBC_H,
                    Vector(sx, -sl_y / 2, T / 2 - USBC_H / 2))
for yc in (-sl_y / 2, sl_y / 2):
    c = Part.makeCylinder(USBC_H / 2, USBC_DEPTH * 2,
                          Vector(sx, yc, T / 2), Vector(1, 0, 0))
    usbc = usbc.fuse(c)
body = body.cut(usbc)

# rear camera bump on back face (z=0), +X +Y corner
bx = L / 2 - BUMP_MARGIN - BUMP_SQ / 2
by = W / 2 - BUMP_MARGIN - BUMP_SQ / 2
bump = rounded_plate(BUMP_SQ, BUMP_SQ, BUMP_H, BUMP_R, cx=bx, cy=by, z0=-BUMP_H)
bedge = [e for e in bump.Edges
         if abs(e.tangentAt(e.FirstParameter).z) < 0.01
         and abs(e.CenterOfMass.z + BUMP_H) < 0.01]
bump = bump.makeFillet(1.0, bedge)
lens = Part.makeCylinder(LENS_D / 2, LENS_H,
                         Vector(bx, by + BUMP_SQ / 4, -BUMP_H - LENS_H))
flash = Part.makeCylinder(FLASH_D / 2, 0.2,
                          Vector(bx, by - BUMP_SQ / 4, -BUMP_H - 0.2))
body = body.fuse(bump).fuse(lens).fuse(flash)
body = body.removeSplitter()

obj = doc.addObject("Part::Feature", "XiaoxinPadPro127_Dummy")
obj.Shape = body
doc.recompute()

os.makedirs(OUT, exist_ok=True)
doc.saveAs(os.path.join(REPO, "FCstd", "XiaoxinPadPro127.FCStd"))
Part.export([obj], os.path.join(OUT, "XiaoxinPadPro127.step"))
Mesh.export([obj], os.path.join(OUT, "XiaoxinPadPro127.stl"))

bb = obj.Shape.BoundBox
print("BBox: %.2f x %.2f x %.2f" % (bb.XLength, bb.YLength, bb.ZLength))
print("Volume(cm3): %.1f  Solids: %d  Valid: %s"
      % (obj.Shape.Volume / 1000, len(obj.Shape.Solids), obj.Shape.isValid()))
