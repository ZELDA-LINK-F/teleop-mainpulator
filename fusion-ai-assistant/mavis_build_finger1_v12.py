"""Mavis 发送：v12 修复关节孔方向错误

v11 失败原因分析：
- find_face_at_x 找到了 X+ 端面 face（法向 X+）
- 但 cut setDistanceExtent(False, 0.5) 沿 X+ 方向切 = 切出板外
- 板上无材料 → "未找到目标实体"

v12 修复：
- 判断 face 法向
- 如果 face 法向 X+（X+ 端面），用负距离 -0.5 切 X- 方向（切进板）
- 如果 face 法向 X-（X- 端面），用正距离 +0.5 切 X+ 方向（切进板）
- 如果是内孔壁 face（X=1.2, X=4.2），法向 X+，用正距离 +0.5 切穿到板端
"""
import json, uuid

code = r'''
import adsk.core, adsk.fusion, traceback
import json as _json

app = adsk.core.Application.get()
rootComp = app.activeProduct.rootComponent

result = {"steps": [], "verify": [], "success": False, "judgment": "?", "error": None, "warnings": []}

def find_face_at_x(body, x_pos, tol=0.01):
    """找 body 上 X 坐标 = x_pos 的 face（端面）"""
    for f in body.faces:
        bbox = f.boundingBox
        if abs(bbox.maxPoint.x - x_pos) < tol:
            try:
                if f.geometry.objectType == adsk.core.Plane.classType():
                    return f
            except:
                pass
    return None

def cut_hole_at_x(body, x_pos, y_pos, z_pos, r, name):
    """在 body X=x_pos 处切 ⌀r 圆柱孔，自动判断方向"""
    face = find_face_at_x(body, x_pos)
    if face is None:
        result["warnings"].append(f"{name}: 没找到 X={x_pos} face")
        return False

    # 判断 face 法向
    normal = face.geometry.normal
    # 关键：切距离方向应该沿 -face 法向（切进板内）
    if normal.x > 0:
        # face 法向 X+（X+ 端面或内孔 X+ 壁），切 X- 方向（负距离）
        dist = -0.5
    else:
        # face 法向 X-（X- 端面），切 X+ 方向（正距离）
        dist = 0.5

    sk = rootComp.sketches.add(face)
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(x_pos, y_pos, z_pos), r
    )
    cut_in = extrudes.createInput(sk.profiles.item(0),
                                   adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_in.targetBody = body
    cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(dist))
    try:
        extrudes.add(cut_in)
        return True
    except Exception as e:
        result["warnings"].append(f"{name}: {str(e)[:80]}")
        return False

try:
    # 1. 清空
    for i in range(rootComp.features.count - 1, -1, -1):
        try: rootComp.features.item(i).deleteMe()
        except: pass
    for i in range(rootComp.sketches.count - 1, -1, -1):
        try: rootComp.sketches.item(i).deleteMe()
        except: pass

    extrudes = rootComp.features.extrudeFeatures

    # ==================== Body 1: 指段 1 (基段) ====================
    # X(-1.5, 1.5), Y(-0.8, 0.8), Z(0, 2.5)
    sk1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk1.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.5, -0.8, 0),
        adsk.core.Point3D.create(1.5, 0.8, 0)
    )
    ext1 = extrudes.createInput(sk1.profiles.item(0),
                                 adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext1.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))
    extrudes.add(ext1)
    body1 = rootComp.bRepBodies.item(0)
    result["steps"].append(f"B1 板: V={body1.volume:.2f}")

    # B1 内 hole 24x14, Z 贯穿
    sk2 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk2.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.2, -0.7, 0),
        adsk.core.Point3D.create(1.2, 0.7, 0)
    )
    cut2 = extrudes.createInput(sk2.profiles.item(0),
                                 adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut2.targetBody = body1
    cut2.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))
    try:
        extrudes.add(cut2)
        result["steps"].append(f"B1 内孔: V={body1.volume:.2f}")
    except Exception as e:
        result["warnings"].append(f"B1 内孔: {str(e)[:80]}")

    # B1 输出轴孔 (face X=1.5 X+ 端面, 圆心 (1.5, 0, 2.25))
    if cut_hole_at_x(body1, 1.5, 0, 2.25, 0.25, "B1 输出轴孔"):
        result["steps"].append(f"B1 输出轴孔: V={body1.volume:.2f}")

    # B1 手掌螺丝 4 个 (XY 平面 Z=0)
    sk5 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    for x, y in [(-1.3, -0.65), (1.3, -0.65), (-1.3, 0.65), (1.3, 0.65)]:
        sk5.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(x, y, 0), 0.085
        )
    for j in range(sk5.profiles.count):
        cut5 = extrudes.createInput(sk5.profiles.item(j),
                                     adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut5.targetBody = body1
        cut5.setDistanceExtent(False, adsk.core.ValueInput.createByReal(0.5))
        try:
            extrudes.add(cut5)
        except Exception as e:
            result["warnings"].append(f"B1 手掌螺丝{j}: {str(e)[:80]}")
    result["steps"].append(f"B1 手掌螺丝: V={body1.volume:.2f}")

    # ==================== Body 2: 指段 2 (中段) ====================
    # X(1.5, 4.5), Y(-0.8, 0.8), Z(0, 2.5)
    sk6 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk6.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(1.5, -0.8, 0),
        adsk.core.Point3D.create(4.5, 0.8, 0)
    )
    ext6 = extrudes.createInput(sk6.profiles.item(0),
                                 adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext6.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))
    extrudes.add(ext6)
    body2 = rootComp.bRepBodies.item(1)
    result["steps"].append(f"B2 板: V={body2.volume:.2f}")

    # B2 内 hole 24x14 (X=1.8~4.2), Z 贯穿
    sk7 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk7.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(1.8, -0.7, 0),
        adsk.core.Point3D.create(4.2, 0.7, 0)
    )
    cut7 = extrudes.createInput(sk7.profiles.item(0),
                                 adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut7.targetBody = body2
    cut7.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))
    try:
        extrudes.add(cut7)
        result["steps"].append(f"B2 内孔: V={body2.volume:.2f}")
    except Exception as e:
        result["warnings"].append(f"B2 内孔: {str(e)[:80]}")

    # B2 输入关节孔 (face X=1.5 X- 端面, 圆心 (1.5, 0, 2.25))
    if cut_hole_at_x(body2, 1.5, 0, 2.25, 0.25, "B2 输入关节孔"):
        result["steps"].append(f"B2 输入关节孔: V={body2.volume:.2f}")

    # B2 输出关节孔 (face X=4.5 X+ 端面, 圆心 (4.5, 0, 2.25))
    if cut_hole_at_x(body2, 4.5, 0, 2.25, 0.25, "B2 输出关节孔"):
        result["steps"].append(f"B2 输出关节孔: V={body2.volume:.2f}")

    # ==================== Body 3: 指段 3 (指尖) ====================
    # X(4.5, 7.0), Y(-0.8, 0.8), Z(0, 2.0)
    sk11 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk11.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(4.5, -0.8, 0),
        adsk.core.Point3D.create(7.0, 0.8, 0)
    )
    ext11 = extrudes.createInput(sk11.profiles.item(0),
                                  adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext11.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))
    extrudes.add(ext11)
    body3 = rootComp.bRepBodies.item(2)
    result["steps"].append(f"B3 板: V={body3.volume:.2f}")

    # B3 输入关节孔 (face X=4.5 X- 端面, 圆心 (4.5, 0, 2.25))
    if cut_hole_at_x(body3, 4.5, 0, 2.25, 0.25, "B3 输入关节孔"):
        result["steps"].append(f"B3 输入关节孔: V={body3.volume:.2f}")

    # ==================== Verify ====================
    for i, b in enumerate(rootComp.bRepBodies):
        bbox = b.boundingBox
        sx = (bbox.maxPoint.x - bbox.minPoint.x) * 10
        sy = (bbox.maxPoint.y - bbox.minPoint.y) * 10
        sz = (bbox.maxPoint.z - bbox.minPoint.z) * 10
        result["verify"].append({
            "id": i, "size_mm": [round(sx, 1), round(sy, 1), round(sz, 1)],
            "volume_cm3": round(b.volume, 2)
        })

    n = rootComp.bRepBodies.count
    if n == 3:
        sizes = [v["size_mm"] for v in result["verify"]]
        volumes = [v["volume_cm3"] for v in result["verify"]]
        b1_ok = abs(sizes[0][0]-30)<2 and abs(sizes[0][1]-16)<2 and abs(sizes[0][2]-25)<2
        b2_ok = abs(sizes[1][0]-30)<2 and abs(sizes[1][1]-16)<2 and abs(sizes[1][2]-25)<2
        b3_ok = abs(sizes[2][0]-25)<2 and abs(sizes[2][1]-16)<2 and abs(sizes[2][2]-20)<2
        if b1_ok and b2_ok and b3_ok:
            result["success"] = True
            result["judgment"] = f"OK 3 个 body 尺寸正确, V={volumes}"
        else:
            result["judgment"] = f"NO 尺寸不对 {sizes}"
    else:
        result["judgment"] = f"NO {n} 个 body (期望 3)"

except Exception as e:
    result["error"] = traceback.format_exc()
    result["judgment"] = f"ERROR: {e}"

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\last_result.json", "w", encoding="utf-8") as f:
    _json.dump(result, f, ensure_ascii=False, indent=2)

msg_lines = []
if result.get("error"):
    msg_lines.append("ERROR:")
    msg_lines.append(result["error"][:600])
else:
    msg_lines.append("=" * 40)
    msg_lines.extend(result["steps"])
    if result.get("warnings"):
        msg_lines.append("WARNINGS:")
        msg_lines.extend(result["warnings"])
    msg_lines.append("=" * 40)
    msg_lines.append(f"判断: {result['judgment']}")
    msg_lines.append("=" * 40)
    for v in result["verify"]:
        msg_lines.append(f"Body {v['id']}: {v['size_mm']} mm, V={v['volume_cm3']} cm3")

app.userInterface.messageBox("\n".join(msg_lines))
'''

data = {
    "command_id": str(uuid.uuid4()),
    "code": code,
    "description": "v12 修复关节孔方向错误（用 face 法向判断 + 负距离）"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"v12 已发送！command_id: {data['command_id']}")