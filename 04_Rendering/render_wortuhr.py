# -*- coding: utf-8 -*-
"""Fotorealistisches Bild der WortUhr mit leuchtenden Buchstaben (Blender, Cycles).

Aufruf:  blender.exe -b -P render_wortuhr.py -- [--samples N] [--res WxH] [--out datei.png] [--view front|angle]
                                              [--color warm|blau|R,G,B] [--dark 0|1]
Die Netze kommen aus FreeCAD (meshes/*.stl, Einheit mm). Die Uhr liegt in der XY-Ebene,
die Front zeigt nach +Z; die Wand ist die Ebene z = -10 mm.
"""
import bpy, os, sys, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MESH = os.path.join(HERE, "meshes")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
opt = {"--samples": "160", "--res": "1800x1800", "--out": os.path.join(HERE, "WortUhr_Render.png"), "--view": "angle", "--color": "warm", "--dark": "0"}
for i in range(0, len(argv) - 1, 2):
    opt[argv[i]] = argv[i + 1]
SAMPLES = int(opt["--samples"]); RX, RY = map(int, opt["--res"].split("x"))
COLORS = {"warm": (1.0, 0.80, 0.55), "blau": (0.10, 0.35, 1.0)}
LED_RGB = COLORS.get(opt["--color"]) or tuple(float(v) for v in opt["--color"].split(","))
DARK = opt["--dark"] == "1"

# ---------------------------------------------------------------- Szene leeren
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"


def imp(name):
    path = os.path.join(MESH, name + ".stl")
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=path, global_scale=0.001)
    else:
        bpy.ops.import_mesh.stl(filepath=path, global_scale=0.001)
    ob = bpy.context.selected_objects[0]
    ob.name = name
    bpy.ops.object.shade_flat()
    return ob


def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    return m, nt, bsdf


def setin(node, key, val):
    for k in ([key] if isinstance(key, str) else key):
        if k in node.inputs:
            node.inputs[k].default_value = val
            return


# ---------------------------------------------------------------- Materialien
# Cortenstahl: fleckige Rostpatina (grosse Flecken + feine Koernung + dunkle Adern)
corten, nt, b = node_mat("Cortenstahl")
tc = nt.nodes.new("ShaderNodeTexCoord")
big = nt.nodes.new("ShaderNodeTexNoise"); big.inputs["Scale"].default_value = 3.5; big.inputs["Detail"].default_value = 8; big.inputs["Roughness"].default_value = 0.7
fine = nt.nodes.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 120.0; fine.inputs["Detail"].default_value = 10; fine.inputs["Roughness"].default_value = 0.6
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 35.0
for n in (big, fine, vor):
    nt.links.new(tc.outputs["Generated"], n.inputs["Vector"])
r1 = nt.nodes.new("ShaderNodeValToRGB")          # grosse Flecken: dunkelbraun <-> orange
r1.color_ramp.elements[0].position = 0.30; r1.color_ramp.elements[0].color = (0.11, 0.037, 0.015, 1)
r1.color_ramp.elements[1].position = 0.70; r1.color_ramp.elements[1].color = (0.25, 0.082, 0.027, 1)
nt.links.new(big.outputs["Fac"], r1.inputs["Fac"])
r2 = nt.nodes.new("ShaderNodeValToRGB")          # feine Koernung
r2.color_ramp.elements[0].position = 0.40; r2.color_ramp.elements[0].color = (0.10, 0.035, 0.015, 1)
r2.color_ramp.elements[1].position = 0.62; r2.color_ramp.elements[1].color = (0.48, 0.19, 0.06, 1)
nt.links.new(fine.outputs["Fac"], r2.inputs["Fac"])
m1 = nt.nodes.new("ShaderNodeMix"); m1.data_type = "RGBA"; m1.blend_type = "MULTIPLY"; m1.inputs[0].default_value = 0.55
nt.links.new(r1.outputs["Color"], m1.inputs[6]); nt.links.new(r2.outputs["Color"], m1.inputs[7])
m2 = nt.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.blend_type = "MIX"; m2.inputs[0].default_value = 0.6
nt.links.new(r1.outputs["Color"], m2.inputs[6]); nt.links.new(m1.outputs[2], m2.inputs[7])
nt.links.new(m2.outputs[2], b.inputs["Base Color"])
setin(b, "Metallic", 0.1); setin(b, "Roughness", 0.9)
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.5; bump.inputs["Distance"].default_value = 0.0003
nt.links.new(fine.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])

# Diffusor aus (Opal-Acrylglas)
opal, nt, b = node_mat("Opal_aus")
setin(b, "Base Color", (0.62, 0.62, 0.60, 1)); setin(b, "Roughness", 0.35)
setin(b, ["Subsurface Weight", "Subsurface"], 0.6); setin(b, "Subsurface Radius", (0.004, 0.004, 0.004))
setin(b, ["Transmission Weight", "Transmission"], 0.25)

# Diffusor an: warmweisses Leuchten (SK6812 RGBW warmweiss)
led, nt, b = node_mat("Opal_an")
setin(b, "Base Color", (0.95, 0.9, 0.82, 1)); setin(b, "Roughness", 0.35)
setin(b, ["Emission Color", "Emission"], LED_RGB + (1,)); setin(b, "Emission Strength", 10.0 if DARK else 18.0)

# Gitter / Rueckrahmen: schwarzes PLA
pla, nt, b = node_mat("PLA_schwarz")
setin(b, "Base Color", (0.02, 0.02, 0.022, 1)); setin(b, "Roughness", 0.55)
# Leiterplatte
pcb, nt, b = node_mat("Leiterplatte")
setin(b, "Base Color", (0.03, 0.12, 0.05, 1)); setin(b, "Roughness", 0.4)
# Lichtleiter: klares PC
glas, nt, b = node_mat("Polycarbonat")
setin(b, "Base Color", (1, 1, 1, 1)); setin(b, "Roughness", 0.05); setin(b, ["Transmission Weight", "Transmission"], 1.0); setin(b, "IOR", 1.58)
# Wand: Putz
wall_m, nt, b = node_mat("Wandputz")
wn = nt.nodes.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 400; wn.inputs["Detail"].default_value = 10
wb = nt.nodes.new("ShaderNodeBump"); wb.inputs["Strength"].default_value = 0.15; wb.inputs["Distance"].default_value = 0.0005
nt.links.new(wn.outputs["Fac"], wb.inputs["Height"]); nt.links.new(wb.outputs["Normal"], b.inputs["Normal"])
setin(b, "Base Color", (0.72, 0.70, 0.66, 1)); setin(b, "Roughness", 0.9)

# ---------------------------------------------------------------- Modell
def assign(ob, m):
    ob.data.materials.clear(); ob.data.materials.append(m)


assign(imp("frontplatte"), corten)
assign(imp("diffusor_aus"), opal)
assign(imp("diffusor_an"), led)
for q in ("Q1_obenlinks", "Q2_obenrechts", "Q3_untenlinks", "Q4_untenrechts"):
    assign(imp("gitter_" + q), pla)
for q in ("PCB_Q4_Master", "PCB_Q2", "PCB_Q1", "PCB_Q3"):
    assign(imp("pcb_" + q), pcb)
assign(imp("rueckrahmen"), pla)
assign(imp("lichtleiter"), glas)

# Uhr senkrecht an die Wand haengen: Drehung +90 Grad um X (Front zeigt dann nach -Y, oben = +Z)
bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0.2506, -0.25, -0.0101))
assign(bpy.context.active_object, wall_m)
bpy.context.active_object.name = "Wand"
from mathutils import Matrix
R = Matrix.Rotation(math.radians(90), 4, "X")
for ob in bpy.data.objects:
    ob.matrix_world = R @ ob.matrix_world
C = R @ Vector((0.2506, -0.250, 0.0))      # Uhrmitte (m)
FRONT = Vector((0, -1, 0))

# ---------------------------------------------------------------- Licht
world = bpy.data.worlds.new("Raum"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.55, 0.52, 0.48, 1)
bg.inputs["Strength"].default_value = 0.008 if DARK else 0.06
LIGHT = 0.0 if DARK else 1.0                  # im Dunkeln leuchtet nur die Uhr


def area(name, loc, size, energy, color=(1, 0.95, 0.88)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    L = bpy.context.active_object; L.name = name
    L.data.size = size; L.data.energy = energy; L.data.color = color
    d = C + FRONT * 0.02 - L.location
    L.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return L


area("Fenster", (C.x - 1.5, C.y - 1.0, C.z + 0.9), 1.4, 110.0 * LIGHT, (0.92, 0.95, 1.0))   # kuehles Tageslicht von links oben
area("Raumlicht", (C.x + 1.3, C.y - 1.4, C.z - 0.4), 1.6, 25.0 * LIGHT, (1.0, 0.86, 0.7))  # warmes Fuelllicht

# ---------------------------------------------------------------- Kamera
bpy.ops.object.camera_add()
cam = bpy.context.active_object; scene.camera = cam
if opt["--view"] == "front":
    cam.location = C + Vector((0, -1.25, 0)); cam.data.lens = 50
else:
    cam.location = C + Vector((-0.50, -1.02, -0.10)); cam.data.lens = 50
d = C + FRONT * 0.02 - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 8.0
cam.data.dof.focus_distance = d.length

# ---------------------------------------------------------------- Rendern
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = RX, RY
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
scene.view_settings.look = "None"
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = opt["--out"]

# Leuchten (Glare) im Compositor, falls verfuegbar
try:
    if hasattr(scene, "compositing_node_group"):
        ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
        scene.compositing_node_group = ng
        rl = ng.nodes.new("CompositorNodeRLayers")
        gl = ng.nodes.new("CompositorNodeGlare")
        out = ng.nodes.new("NodeGroupOutput")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        gl.inputs["Type"].default_value = "Bloom"; gl.inputs["Quality"].default_value = "High"
        for k, v in (("Threshold", 2.0), ("Strength", 0.35), ("Size", 0.45)):
            if k in gl.inputs: gl.inputs[k].default_value = v
        ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
        ng.links.new(gl.outputs["Image"], out.inputs[0])
    else:
        scene.use_nodes = True
        tree = scene.node_tree; tree.nodes.clear()
        rl = tree.nodes.new("CompositorNodeRLayers"); gl = tree.nodes.new("CompositorNodeGlare"); comp = tree.nodes.new("CompositorNodeComposite")
        gl.glare_type = "BLOOM" if "BLOOM" in [i.identifier for i in gl.bl_rna.properties["glare_type"].enum_items] else "FOG_GLOW"
        gl.threshold = 1.5
        tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], comp.inputs["Image"])
    print("Glare aktiv")
except Exception as e:
    print("Glare nicht verfuegbar:", e)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "WortUhr_Szene.blend"))
bpy.ops.render.render(write_still=True)
print("RENDER FERTIG:", scene.render.filepath)
