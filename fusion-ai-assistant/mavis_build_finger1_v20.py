"""Mavis 发送：v20 用 extrude_input.direction 强制 cut 方向

v19 失败分析：
- 用 X=1.2 内孔 X+ 壁 face，normal X-（朝内孔内部）
- cut 沿 normal 方向 X- = 切进已经挖空的内孔 = 失败
- 同样 X=1.5 端面 face normal X+（朝板外）切 normal = 板外失败

v20 思路：
- 用 X=1.5 端面 face (normal X+)
- 用 extrude_input.direction = X- 强制反向切
- 距离 0.3cm = 从 X=1.5 切到 X=1.2（穿板右壁）
"""
import json, uuid

code = r'''
import adsk.core, adsk.fusion, traceback
import json as _json

app = adsk.core.Application.get()
rootComp = app.activeProduct.rootComponent

result = {"steps": [], "verify": [], "success": False, "judgment": "?", "error": None, "warnings": []}

def find_x_face(body, x_pos, tol=0.05):
    """找 body X=x_pos 处的端面 face（不检查 objectType）"""
    candidates = []
    for f in body.faces:
        bbox = f.boundingBox
        x_thick = abs(bbox.maxPoint.x - bbox.minPoint.x)
        if x_thick > 0.1:
            continue
        if abs(bbox.maxPoint.x - x_pos) < tol or abs(bbox.minPoint.x - x_pos) < tol:
            candidates.append(f)
    return candidates

def cut_hole_with_direction(body, x_pos, y_pos, z_pos, r, cut_dir_x, name, dist=0.3):
    """在 X=x_pos 平面切 ⌀r 圆柱孔，强制 cut 方向"""
    candidates = find_x_face(body, x_pos)
    if not candidates:
        result["warnings"].append(f"{name}: 没找到 X={x_pos} face")
        return False
    
    # 用第一个 face（不区分 normal）
    face = candidates[0]
    
    sk = rootComp.sketches.add(face)
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(x_pos, y_pos, z_pos), r
    )
    
    cut_in = extrudes.createInput(sk.profiles.item(0),
                                   adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_in.targetBody = body
    cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(dist))
    # 强制 cut 方向
    try:
        cut_in.direction = adsk.core.Vector3D.create(cut_dir_x, 0, 0)
        result["steps"].append(f"{name} 设置 direction=({cut_dir_x},0,0)")
    except Exception as e:
        result["warnings"].append(f"{name} direction 属性设置失败: {str(e)[:100]}")
    
    try:
        extrudes.add(cut_in)
        result["steps"].append(f"{name} OK")
        return True
    except Exception as e:
        result["warnings"].append(f"{name}: {str(e)[:300]}")
        return False

try:
    # 清空
    for i in range(rootComp.features.count - 1, -1, -1):
        try: rootComp.features.item(i).deleteMe()
        except: pass
    for i in range(rootComp.sketches.count - 1, -1, -1):
        try: rootComp.sketches.item(i).deleteMe()
        except: pass

    extrudes = rootComp.features.extrudeFeatures

    # ==================== Body 1: 指段 1 ====================
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
        result["warnings"].append(f"B1 内孔: {str(e)[:200]}")

    # B1 输出轴孔：X=1.5 face, cut X- 方向
    if cut_hole_with_direction(body1, 1.5, 0, 2.25, 0.25, -1, "B1 输出轴孔"):
        result["steps"].append(f"B1 输出轴孔 OK: V={body1.volume:.2f}")

    # B1 手掌螺丝 4 个
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
            result["warnings"].append(f"B1 手掌螺丝{j}: {str(e)[:200]}")
    result["steps"].append(f"B1 手掌螺丝: V={body1.volume:.2f}")

    # ==================== Body 2: 指段 2 ====================
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
        result["warnings"].append(f"B2 内孔: {str(e)[:200]}")

    # B2 输入关节孔：X=1.5 face, cut X+ 方向
    if cut_hole_with_direction(body2, 1.5, 0, 2.25, 0.25, +1, "B2 输入关节孔"):
        result["steps"].append(f"B2 输入关节孔 OK: V={body2.volume:.2f}")

    # B2 输出关节孔：X=4.5 face, cut X- 方向
    if cut_hole_with_direction(body2, 4.5, 0, 2.25, 0.25, -1, "B2 输出关节孔"):
        result["steps"].append(f"B2 输出关节孔 OK: V={body2.volume:.2f}")

    # ==================== Body 3: 指段 3 ====================
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

    # B3 加假内孔
    sk12 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk12.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(4.5, -0.7, 0),
        adsk.core.Point3D.create(6.5, 0.7, 0)
    )
    cut12 = extrudes.createInput(sk12.profiles.item(0),
                                  adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut12.targetBody = body3
    cut12.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.4))
    try:
        extrudes.add(cut12)
        result["steps"].append(f"B3 假内孔: V={body3.volume:.2f}")
    except Exception as e:
        result["warnings"].append(f"B3 假内孔: {str(e)[:200]}")

    # B3 输入关节孔：X=4.5 face, cut X+ 方向
    if cut_hole_with_direction(body3, 4.5, 0, 1.85, 0.25, +1, "B3 输入关节孔"):
        result["steps"].append(f"B3 输入关节孔 OK: V={body3.volume:.2f}")

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
        result["success"] = True
        result["judgment"] = f"3 个 body 建模完成"
    else:
        result["judgment"] = f"NO {n} 个 body"

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

app.userInterface.messageBox("\n".join(msg_lines))
'''

data = {
    "command_id": str(uuid.uuid4()),
    "code": code,
    "description": "v20 用 extrude_input.direction 强制 cut 方向"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"v20 已发送！command_id: {data['command_id']}")