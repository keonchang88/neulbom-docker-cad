# Dummy model: stroller-bar clamp ~ 17mm ball arm (dambi777 phone mount,
# clamp-to-ball section only — the ball docks into the neulbom docker socket).
# Known from listing: clamp max opening 35.9mm, full product 200mm.
# Everything else is estimated from photos — re-measure with calipers and re-run.
import os
import FreeCAD as App
import Part
import Mesh
from FreeCAD import Vector

REPO = "/home/a15209/Documents/neulbom-docker-cad/neulbom_docker"

# ---------------- parameters (mm) ----------------
# clamp: two scissor jaws around the bar, bar axis = X, bar center at origin
CLAMP_BORE = 35.9        # max opening (listing)
CLAMP_OD = 56.0          # jaw outer diameter (est.)
CLAMP_W = 20.0           # total width along bar axis, two jaws (est.)
CLAMP_GAP_DEG = 75.0     # opening wedge angle, faces +Z (est.)
JAW_W = 9.0              # single jaw width (est.)
JAW_TAIL_DEG = 30.0      # tail past bottom center — the scissor cross region
PIN_D, PIN_L = 5.0, 24.0 # hinge pin at the cross point
# locking collar under the clamp, axis = Z
COLLAR_D, COLLAR_H = 31.0, 28.0   # est.
COLLAR_TOP = -CLAMP_OD / 2 + 4.0  # embeds slightly into clamp body
# hex joint block + arm down to the ball (est.)
HEX_W, HEX_T, HEX_H = 16.0, 12.0, 14.0
ARM_W, ARM_T, ARM_L = 14.0, 10.0, 38.0
ARM_TILT_DEG = 20.0      # arm leans in +Y as it goes down
# ball joint (matches neulbom docker 17mm socket)
BALL_D = 17.0
NECK_D, NECK_L = 8.0, 7.0

doc = App.newDocument("BallClampMount")
z0 = COLLAR_TOP

# clamp: two crossed scissor jaws, hinge pin at the bottom cross point.
# Built in a helper frame (ring axis = Z, angles CCW from +X), then rotated
# 90deg about Y so build +X -> -Z (bottom), build axis Z -> bar axis X.
# Opening centered at build angle 180 (-> +Z), half gap each side.
half_gap = CLAMP_GAP_DEG / 2.0
sweep = 180.0 - half_gap + JAW_TAIL_DEG   # tail crosses past bottom center

def jaw(start_deg, zoff):
    s = Part.makeCylinder(CLAMP_OD / 2, JAW_W, Vector(0, 0, zoff),
                          Vector(0, 0, 1), sweep)
    s = s.cut(Part.makeCylinder(CLAMP_BORE / 2, JAW_W + 2,
                                Vector(0, 0, zoff - 1), Vector(0, 0, 1)))
    s.rotate(Vector(0, 0, 0), Vector(0, 0, 1), start_deg)
    s.rotate(Vector(0, 0, 0), Vector(0, 1, 0), 90)
    return s

# right jaw: build angles -TAIL..(180-half_gap), occupies +X half of the width
# left jaw: mirror, occupies -X half
clamp = jaw(-JAW_TAIL_DEG, 0.5).fuse(jaw(180.0 + half_gap, -JAW_W - 0.5))
r_mid = (CLAMP_OD + CLAMP_BORE) / 4.0
pin = Part.makeCylinder(PIN_D / 2, PIN_L, Vector(-PIN_L / 2, 0, -r_mid),
                        Vector(1, 0, 0))
clamp = clamp.fuse(pin)

# collar: knurled locking wheel (plain cylinder dummy), axis Z
collar = Part.makeCylinder(COLLAR_D / 2, COLLAR_H,
                           Vector(0, 0, z0 - COLLAR_H), Vector(0, 0, 1))

# hex joint block below collar
zh = z0 - COLLAR_H
hexb = Part.makeBox(HEX_W, HEX_T, HEX_H,
                    Vector(-HEX_W / 2, -HEX_T / 2, zh - HEX_H))

# arm: tilted bar from hex block down to the ball neck
za = zh - HEX_H
arm = Part.makeBox(ARM_W, ARM_T, ARM_L,
                   Vector(-ARM_W / 2, -ARM_T / 2, za - ARM_L))
arm.rotate(Vector(0, 0, za), Vector(1, 0, 0), ARM_TILT_DEG)

# ball + neck at the arm tip, pointing down
import math
tilt = math.radians(ARM_TILT_DEG)
tip = Vector(0, ARM_T / 2 * 0 + math.sin(tilt) * ARM_L, za - math.cos(tilt) * ARM_L)
neck = Part.makeCylinder(NECK_D / 2, NECK_L, tip - Vector(0, 0, NECK_L),
                         Vector(0, 0, 1))
ball = Part.makeSphere(BALL_D / 2, tip - Vector(0, 0, NECK_L + BALL_D / 2 - 1.5))

shape = clamp.fuse(collar).fuse(hexb).fuse(arm).fuse(neck).fuse(ball)
shape = shape.removeSplitter()

obj = doc.addObject("Part::Feature", "BallClampMount_Dummy")
obj.Shape = shape
doc.recompute()

doc.saveAs(os.path.join(REPO, "FCstd", "BallClampMount.FCStd"))
Part.export([obj], os.path.join(REPO, "STL", "BallClampMount.step"))
Mesh.export([obj], os.path.join(REPO, "STL", "BallClampMount.stl"))

bb = obj.Shape.BoundBox
bc = ball.CenterOfMass
print("BBox: %.1f x %.1f x %.1f (z %.1f~%.1f)"
      % (bb.XLength, bb.YLength, bb.ZLength, bb.ZMin, bb.ZMax))
print("Ball center: (%.1f, %.1f, %.1f)  D=%.1f" % (bc.x, bc.y, bc.z, BALL_D))
print("Solids: %d  Valid: %s" % (len(obj.Shape.Solids), obj.Shape.isValid()))
