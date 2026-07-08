"""Mavis 发送：指段 1 v4（两步法：外+内分开画）
- 步骤 0：清空
- 步骤 1：草图1 画外轮廓 30x16 → 拉伸 25mm → 板
- 步骤 2：草图2 画内 hole 24x14 → cut 板 → 洞
- 步骤 3：草图3 (XZ平面) 画 3 个圆 → cut 板 → 3 个孔
- 步骤 4：草图4 (XY平面) 画 4 个手掌螺丝孔 → cut 板 → 4 个孔
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
    # 0. 清空
    for i in range(rootComp.features.count - 1, -1, -1):
        try: rootComp.features.item(i).deleteMe()
        except: pass
    for i in range(rootComp.sketches.count - 1, -1, -1):
        try: rootComp.sketches.item(i).deleteMe()
        except: pass
    result["steps"].append(f"清空后 body={rootComp.bRepBodies.count}")

    extrudes = rootComp.features.extrudeFeatures

    # 1. 草图1 画外轮廓 30x16 → 拉伸 25mm
    sk1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk1.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.5, -0.8, 0),
        adsk.core.Point3D.create(1.5, 0.8, 0)
    )
    area1 = abs(sk1.profiles.item(0).areaProperties().area) * 100
    result["steps"].append(f"草图1: 外轮廓 30x16, area={area1:.1f}mm2")

    ext_in = extrudes.createInput(sk1.profiles.item(0),
                                   adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))  # 25mm
    extrudes.add(ext_in)
    body1 = rootComp.bRepBodies.item(0)
    result["steps"].append(f"步骤1: 板 30x16x25, body={rootComp.bRepBodies.count}, V={body1.volume:.2f}cm3 (期望 12.0)")

    # 2. 草图2 画内 hole 24x14 → cut 板 → 洞
    sk2 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk2.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.2, -0.7, 0),
        adsk.core.Point3D.create(1.2, 0.7, 0)
    )
    area2 = abs(sk2.profiles.item(0).areaProperties().area) * 100
    result["steps"].append(f"草图2: 内 hole 24x14, area={area2:.1f}mm2")

    cut_in = extrudes.createInput(sk2.profiles.item(0),
                                   adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_in.targetBody = body1
    cut_in.setDistanceExtent(True, adsk.core.ValueInput.createByReal(5.0))  # 双向 5cm
    try:
        extrudes.add(cut_in)
        result["steps"].append(f"步骤2: 切内 hole 成功, V={body1.volume:.2f}cm3 (期望 12.0-7.73=4.27)")
    except Exception as e:
        result["warnings"].append(f"切内 hole 失败: {str(e)[:100]}")

    # 3. 草图3 (XZ平面) 画 3 个圆 → cut 板 → 输出轴孔 + 2 个 SG90 螺丝孔
    sk3 = rootComp.sketches.add(rootComp.xZConstructionPlane)
    c3 = sk3.sketchCurves.sketchCircles
    c3.addByCenterRadius(adsk.core.Point3D.create(1.5, 0, 1.25), 0.25)   # 输出轴孔 5mm
    c3.addByCenterRadius(adsk.core.Point3D.create(0, 0.61, 1.0), 0.085)  # SG90 Y+ 螺丝孔
    c3.addByCenterRadius(adsk.core.Point3D.create(0, -0.61, 1.0), 0.085) # SG90 Y- 螺丝孔
    result["steps"].append(f"草图3 (XZ): 3 个圆")

    for j in range(sk3.profiles.count):
        cut_in = extrudes.createInput(sk3.profiles.item(j),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = body1
        cut_in.setDistanceExtent(True, adsk.core.ValueInput.createByReal(5.0))
        try:
            extrudes.add(cut_in)
        except Exception as e:
            result["warnings"].append(f"孔{j} cut 失败: {str(e)[:100]}")
    result["steps"].append(f"步骤3后 body={rootComp.bRepBodies.count}, V={body1.volume:.2f}cm3")

    # 4. 草图4 (XY平面) 画 4 个手掌螺丝孔 → cut 板
    sk4 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    c4 = sk4.sketchCurves.sketchCircles
    for x, y in [(-1.3, -0.65), (1.3, -0.65), (-1.3, 0.65), (1.3, 0.65)]:
        c4.addByCenterRadius(adsk.core.Point3D.create(x, y, 0), 0.085)
    result["steps"].append(f"草图4 (XY): 4 个圆")

    for j in range(sk4.profiles.count):
        cut_in = extrudes.createInput(sk4.profiles.item(j),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = body1
        cut_in.setDistanceExtent(True, adsk.core.ValueInput.createByReal(5.0))
        try:
            extrudes.add(cut_in)
        except Exception as e:
            result["warnings"].append(f"手掌孔{j} cut 失败: {str(e)[:100]}")
    result["steps"].append(f"步骤4后 body={rootComp.bRepBodies.count}, V={body1.volume:.2f}cm3")

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
            # 期望 12 - 7.73 - 孔体积(0.61) = 3.66
            if 3.0 < v < 4.5:
                result["success"] = True
                result["judgment"] = f"OK 尺寸30x16x25对, V={v:.2f} (期望~3.66 净-孔)"
            else:
                result["judgment"] = f"NO 尺寸对但体积异常 V={v:.2f} (期望 3.0-4.5)"
        else:
            result["judgment"] = f"NO 尺寸不对 (实际 {sz_list})"
    elif n == 2:
        result["judgment"] = f"NO 两个独立 body"
    else:
        result["judgment"] = f"? {n} 个 body"

except Exception as e:
    result["error"] = traceback.format_exc()
    result["judgment"] = f"ERROR: {e}"

# 写文件
with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\last_result.json", "w", encoding="utf-8") as f:
    _json.dump(result, f, ensure_ascii=False, indent=2)

# 弹窗
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
    "description": "指段 1 v4 (两步法 + 各孔 cut)"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"指段1 v4 已发送！command_id: {data['command_id']}")
