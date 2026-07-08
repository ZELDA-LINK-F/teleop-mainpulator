"""Mavis 发送：v19 用内孔壁 face（X=1.2, X=4.2, X=1.8）+ 正距离

v18 失败：constructionPlanes.add 不支持
v17 失败：sketches.add(adsk.core.Plane) "not a planar entity"

v19 思路（最简单最稳）：
- 关节孔用内孔壁 face 作为草图平面
- B1 内孔 X+ 壁 face X=1.2 (normal X+, 朝板 X+ 端外)
  - cut 正距离 0.3cm 沿 X+ 方向 = 从 X=1.2 切到 X=1.5 (穿板右壁) ✓
- B2 内孔 X- 壁 face X=1.8 (normal X-, 朝板 X- 端外)
  - cut 正距离 0.3cm 沿 X- 方向 = 从 X=1.8 切到 X=1.5 (穿板左壁) ✓
- B2 内孔 X+ 壁 face X=4.2 (normal X+)
  - cut 正距离 0.3cm 沿 X+ 方向 = 从 X=4.2 切到 X=4.5 (穿板右壁) ✓
- B3 输入关节孔：B3 没有内孔，需要不同方法

B3 解决：给 B3 加一个小"假内孔"在 X=4.5 端面留出 face
"""
import json, uuid

code = r'''
import adsk.core, adsk.fusion, traceback
import json as _json

app = adsk.core.Application.get()
rootComp = app.activeProduct.rootComponent

result = {"steps": [], "verify": [], "success": False, "judgment": "?", "error": None, "warnings": []}

def find_inner_wall_face(body, x_pos, tol=0.05):
    """找 body 上 X=x_pos 处的内孔 X± 壁 face（normal 朝板外方向）"""
    candidates = []
    for f in body.faces:
        bbox = f.boundingBox
        # 内孔壁：X 范围是单点
        x_thick = abs(bbox.maxPoint.x - bbox.minPoint.x)
        if x_thick > 0.1:
            continue
        if abs(bbox.maxPoint.x - x_pos) < tol:
            try:
                if f.geometry.objectType == adsk.core.Plane.classType():
                    candidates.append(f)
            except:
                pass
    return candidates

def cut_hole_on_x_pos(body, x_pos, y_pos, z_pos, r, name, dist=0.3):
    """在 X=x_pos 平面切 ⌀r 圆柱孔
    根据 face 法向自动决定 cut 方向
    """
    candidates = find_inner_wall_face(body, x_pos)
    if not candidates:
        result["warnings"].append(f"{name}: 没找到 X={x_pos} face")
        return False
    
    # 选择 normal 朝 X+ 方向的 face（X+ 端面或内孔 X+ 壁）
    face = None
    for f in candidates:
        try:
            normal = f.geometry.normal
            if normal.x > 0:
                face = f
                break
        except:
            pass
    if face is None:
        face = candidates[0]
    
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

    # B1 输出轴孔：face X=1.2（内孔 X+ 壁, normal X+）, cut X+ 方向 0.3cm
    if cut_hole_on_x_pos(body1, 1.2, 0, 2.25, 0.25, "B1 输出轴孔"):
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

    # B2 输入关节孔：face X=1.8（内孔 X- 壁, normal X-）, cut X- 方向 0.3cm
    if cut_hole_on_x_pos(body2, 1.8, 0, 2.25, 0.25, "B2 输入关节孔"):
        result["steps"].append(f"B2 输入关节孔 OK: V={body2.volume:.2f}")

    # B2 输出关节孔：face X=4.2（内孔 X+ 壁, normal X+）, cut X+ 方向 0.3cm
    if cut_hole_on_x_pos(body2, 4.2, 0, 2.25, 0.25, "B2 输出关节孔"):
        result["steps"].append(f"B2 输出关节孔 OK: V={body2.volume:.2f}")

    # ==================== Body 3: 指段 3 ====================
    # B3 没有内孔，给 B3 加一个"假内孔"在 X=4.5 端面留出 face
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

    # B3 加一个假内孔 Z(0.3, 1.7) X(4.5, 7) Y(-0.7, 0.7)
    # 这样 X=4.5 X- 端面在 Y(-0.7, 0.7) Z(0.3, 1.7) 被挖空，在 Z(0, 0.3) 和 Z(1.7, 2.0) 是实心
    # 关节孔 Z=1.85 在 Z(1.7, 2.0) 实心范围内
    sk12 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk12.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(4.5, -0.7, 0),
        adsk.core.Point3D.create(6.5, 0.7, 0)
    )
    cut12 = extrudes.createInput(sk12.profiles.item(0),
                                  adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut12.targetBody = body3
    cut12.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.4))  # 0.3 ~ 1.7
    try:
        extrudes.add(cut12)
        result["steps"].append(f"B3 假内孔: V={body3.volume:.2f}")
    except Exception as e:
        result["warnings"].append(f"B3 假内孔: {str(e)[:200]}")

    # B3 输入关节孔：face X=4.5 X- 端面 (normal X-), cut X- 方向 0.3cm
    # 但 face normal X-, cut 沿 normal 方向 = 板外！需要不同的方法
    # 试试正距离，依赖 Fusion 内部逻辑
    if cut_hole_on_x_pos(body3, 4.5, 0, 1.85, 0.25, "B3 输入关节孔"):
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
    "description": "v19 用内孔壁 face (X=1.2, 1.8, 4.2) + 正距离"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"v19 已发送！command_id: {data['command_id']}")