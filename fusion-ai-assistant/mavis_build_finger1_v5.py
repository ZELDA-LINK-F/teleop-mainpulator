"""Mavis 发送：指段 1 v5（修正输出轴孔位置 + 两步法）
- 步骤 0：清空
- 步骤 1：草图1 外轮廓 30x16 → 拉伸 25mm → 板
- 步骤 2：草图2 内 hole 24x14 → cut 板 → 洞
- 步骤 3：草图3 (XZ平面) 输出轴孔 (1.3, 0, 1.4) + 2 个 SG90 螺丝孔 (0, ±0.61, 1.0) → cut 板
- 步骤 4：草图4 (XY平面) 4 个手掌螺丝孔 → cut 板
- 步骤 5：自动 verify
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
    result["steps"].append(f"清空后 body={rootComp.bRepBodies.count}")

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
    result["steps"].append(f"步骤1: 板 30x16x25, V={body1.volume:.2f}cm3 (期望 12.0)")

    # 2. 草图2 内 hole 24x14 → cut 板
    sk2 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk2.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.2, -0.7, 0),
        adsk.core.Point3D.create(1.2, 0.7, 0)
    )
    cut_in = extrudes.createInput(sk2.profiles.item(0),
                                   adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_in.targetBody = body1
    cut_in.setDistanceExtent(True, adsk.core.ValueInput.createByReal(5.0))
    extrudes.add(cut_in)
    result["steps"].append(f"步骤2: 切内 hole, V={body1.volume:.2f}cm3 (期望 12-7.73=4.27)")

    # 3. 草图3 (XZ平面 Y=0) 画 3 个圆 → cut 板
    # 输出轴孔位置 (1.3, 0, 1.4)：X=1.3 在 body 内 0.2cm，Z=1.4 在 SG90 中部
    # SG90 螺丝孔 (0, ±0.61, 1.0)：Y 方向 0.61 在 body 内
    sk3 = rootComp.sketches.add(rootComp.xZConstructionPlane)
    c3 = sk3.sketchCurves.sketchCircles
    c3.addByCenterRadius(adsk.core.Point3D.create(1.3, 0, 1.4), 0.25)    # 输出轴孔 5mm
    c3.addByCenterRadius(adsk.core.Point3D.create(0, 0.61, 1.0), 0.085)   # SG90 螺丝孔 Y+
    c3.addByCenterRadius(adsk.core.Point3D.create(0, -0.61, 1.0), 0.085)  # SG90 螺丝孔 Y-
    result["steps"].append(f"草图3 (XZ): 3 个圆 (输出轴 1.3,0,1.4 + SG90 螺丝 ±0.61,1.0)")

    for j in range(sk3.profiles.count):
        cut_in = extrudes.createInput(sk3.profiles.item(j),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = body1
        cut_in.setDistanceExtent(True, adsk.core.ValueInput.createByReal(5.0))
        try:
            extrudes.add(cut_in)
        except Exception as e:
            result["warnings"].append(f"sk3 孔{j} cut 失败: {str(e)[:100]}")
    result["steps"].append(f"步骤3后 V={body1.volume:.2f}cm3")

    # 4. 草图4 (XY平面 Z=0) 画 4 个手掌螺丝孔
    sk4 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    c4 = sk4.sketchCurves.sketchCircles
    for x, y in [(-1.3, -0.65), (1.3, -0.65), (-1.3, 0.65), (1.3, 0.65)]:
        c4.addByCenterRadius(adsk.core.Point3D.create(x, y, 0), 0.085)
    result["steps"].append(f"草图4 (XY): 4 个手掌螺丝孔")

    for j in range(sk4.profiles.count):
        cut_in = extrudes.createInput(sk4.profiles.item(j),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = body1
        cut_in.setDistanceExtent(True, adsk.core.ValueInput.createByReal(5.0))
        try:
            extrudes.add(cut_in)
        except Exception as e:
            result["warnings"].append(f"sk4 孔{j} cut 失败: {str(e)[:100]}")
    result["steps"].append(f"步骤4后 V={body1.volume:.2f}cm3")

    # 5. verify
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
            # 12 - 7.728 = 4.272 - 孔
            # ⌀5输出轴(0.13) + 2×⌀1.7沿Y(0.07) + 4×⌀1.7沿Z(0.23) = 0.43
            # 期望 V ≈ 3.84
            if 3.0 < v < 4.5:
                result["success"] = True
                result["judgment"] = f"OK 尺寸30x16x25对, V={v:.2f} (期望~3.84 净-孔)"
            else:
                result["judgment"] = f"NO 尺寸对但体积异常 V={v:.2f}"
        else:
            result["judgment"] = f"NO 尺寸不对 (实际 {sz_list})"
    elif n == 2:
        result["judgment"] = f"NO 两个独立 body"
    else:
        result["judgment"] = f"? {n} 个 body"

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
    "description": "指段 1 v5 (输出轴孔 (1.3,0,1.4) + 两步法)"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"指段1 v5 已发送！command_id: {data['command_id']}")
