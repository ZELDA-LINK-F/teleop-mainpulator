"""Mavis 发送：指段 1 v8（绕过 Fusion 2702 5cm 双向 cut bug）
关键修复：setDistanceExtent(True, 5.0) → setDistanceExtent(False, 2.5)
单方向 2.5cm 刚好穿透板（Z 方向 25mm 板厚），避免触发出 2 个 body 的 bug
"""
import json, uuid

code = r'''
import adsk.core, adsk.fusion, traceback
import json as _json

app = adsk.core.Application.get()
rootComp = app.activeProduct.rootComponent

result = {"steps": [], "verify": [], "success": False, "judgment": "?", "error": None, "warnings": []}

try:
    for i in range(rootComp.features.count - 1, -1, -1):
        try: rootComp.features.item(i).deleteMe()
        except: pass
    for i in range(rootComp.sketches.count - 1, -1, -1):
        try: rootComp.sketches.item(i).deleteMe()
        except: pass

    extrudes = rootComp.features.extrudeFeatures

    # 1. 草图1 外轮廓 30x16 → 拉伸 25mm
    sk1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk1.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.5, -0.8, 0),
        adsk.core.Point3D.create(1.5, 0.8, 0)
    )
    ext_in = extrudes.createInput(sk1.profiles.item(0),
                                   adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))
    extrudes.add(ext_in)
    body1 = rootComp.bRepBodies.item(0)
    result["steps"].append(f"步骤1: 板, V={body1.volume:.2f}")

    # 2. 草图2 内 hole 24x14 → cut
    sk2 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk2.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.2, -0.7, 0),
        adsk.core.Point3D.create(1.2, 0.7, 0)
    )
    cut_in = extrudes.createInput(sk2.profiles.item(0),
                                   adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_in.targetBody = body1
    cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))  # 单向 2.5cm
    extrudes.add(cut_in)
    result["steps"].append(f"步骤2: 内 hole, V={body1.volume:.2f}")

    # 3. 草图3 (XZ平面) 输出轴孔 (1.3, 0, 1.4)
    sk3 = rootComp.sketches.add(rootComp.xZConstructionPlane)
    sk3.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(1.3, 0, 1.4), 0.25
    )
    cut_in = extrudes.createInput(sk3.profiles.item(0),
                                   adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_in.targetBody = body1
    cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))
    try:
        extrudes.add(cut_in)
    except Exception as e:
        result["warnings"].append(f"输出轴孔: {str(e)[:80]}")
    result["steps"].append(f"步骤3: 输出轴孔, V={body1.volume:.2f}")

    # 4a. 草图4a XY 平面 1 个圆 (0, 0.75, 0) → Y+ SG90 螺丝
    sk4a = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk4a.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0.75, 0), 0.085
    )
    cut_in = extrudes.createInput(sk4a.profiles.item(0),
                                   adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_in.targetBody = body1
    cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))
    try:
        extrudes.add(cut_in)
    except Exception as e:
        result["warnings"].append(f"Y+ SG90: {str(e)[:80]}")
    result["steps"].append(f"步骤4a: Y+, V={body1.volume:.2f}")

    # 4b. 草图4b XY 平面 1 个圆 (0, -0.75, 0) → Y- SG90 螺丝
    sk4b = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk4b.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, -0.75, 0), 0.085
    )
    cut_in = extrudes.createInput(sk4b.profiles.item(0),
                                   adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_in.targetBody = body1
    cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))
    try:
        extrudes.add(cut_in)
    except Exception as e:
        result["warnings"].append(f"Y- SG90: {str(e)[:80]}")
    result["steps"].append(f"步骤4b: Y-, V={body1.volume:.2f}")

    # 5. 草图5 XY 平面 4 个手掌螺丝孔
    sk5 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    c5 = sk5.sketchCurves.sketchCircles
    for x, y in [(-1.3, -0.65), (1.3, -0.65), (-1.3, 0.65), (1.3, 0.65)]:
        c5.addByCenterRadius(adsk.core.Point3D.create(x, y, 0), 0.085)
    for j in range(sk5.profiles.count):
        cut_in = extrudes.createInput(sk5.profiles.item(j),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = body1
        cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))
        try:
            extrudes.add(cut_in)
        except Exception as e:
            result["warnings"].append(f"手掌孔{j}: {str(e)[:80]}")
    result["steps"].append(f"步骤5后 V={body1.volume:.2f}")

    # 6. verify
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
    if n == 1:
        v = rootComp.bRepBodies.item(0).volume
        sz_list = result["verify"][0]["size_mm"]
        if abs(sz_list[0]-30) < 2 and abs(sz_list[1]-16) < 2 and abs(sz_list[2]-25) < 2:
            if 2.5 < v < 4.0:
                result["success"] = True
                result["judgment"] = f"OK 30x16x25对, V={v:.2f} (期望~3.20 净-7孔)"
            else:
                result["judgment"] = f"NO 体积异常 V={v:.2f}"
        else:
            result["judgment"] = f"NO 尺寸不对 {sz_list}"
    else:
        result["judgment"] = f"NO {n} 个 body (失败)"

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
    "description": "指段 1 v8 (setDistanceExtent False 2.5 避免 5cm 双向 bug)"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"指段1 v8 已发送！command_id: {data['command_id']}")
