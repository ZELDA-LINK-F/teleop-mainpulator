"""Mavis 发送：指段 1 v3（修正尺寸：板厚 14→25 装得下 SG90）
- 步骤 0：清空
- 步骤 1：外壳 30x16x25mm（嵌套轮廓）→ 板带洞
- 步骤 2：XZ 平面画 3 个圆 → cut targetBody
- 步骤 3：XY 平面画 4 个手掌螺丝孔 → cut targetBody
- 步骤 4：自动 verify（期望 V≈3.66）
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

    # 1. 外壳 30x16mm + 内腔 24x14mm（嵌套轮廓）→ 拉伸 25mm (2.5cm)
    sk1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk1.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.5, -0.8, 0),    # 外轮廓：X=-1.5, Y=-0.8
        adsk.core.Point3D.create(1.5, 0.8, 0)       # 外轮廓：X=1.5, Y=0.8
    )
    sk1.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.2, -0.7, 0),    # 内腔：X=-1.2, Y=-0.7
        adsk.core.Point3D.create(1.2, 0.7, 0)       # 内腔：X=1.2, Y=0.7
    )
    chosen = max(range(sk1.profiles.count),
                 key=lambda j: abs(sk1.profiles.item(j).areaProperties().area))
    chosen_area = abs(sk1.profiles.item(chosen).areaProperties().area) * 100
    result["steps"].append(f"草图1: {sk1.profiles.count} profiles, 选[{chosen}]={chosen_area:.1f}mm2 (期望 752 净面积 30x16-24x14=480)")

    extrudes = rootComp.features.extrudeFeatures
    ext_in = extrudes.createInput(sk1.profiles.item(chosen),
                                   adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.5))  # 25mm
    extrudes.add(ext_in)
    body1 = rootComp.bRepBodies.item(0)
    result["steps"].append(f"步骤1: body={rootComp.bRepBodies.count}, V={body1.volume:.2f}cm3 (期望 ~4.27 净外壳-内腔)")

    # 2. XZ 平面画 3 个圆（输出轴 5mm + 2 个 SG90 螺丝孔 1.7mm）
    # 新尺寸：Y=±0.61 (SG90 螺丝耳位置 6.1mm)，Z=1.0 (SG90 中部 10mm)
    sk2 = rootComp.sketches.add(rootComp.xZConstructionPlane)
    c2 = sk2.sketchCurves.sketchCircles
    c2.addByCenterRadius(adsk.core.Point3D.create(1.5, 0, 1.25), 0.25)   # 输出轴孔 5mm (X+端面中心)
    c2.addByCenterRadius(adsk.core.Point3D.create(0, 0.61, 1.0), 0.085)  # SG90 螺丝孔 Y+ 侧
    c2.addByCenterRadius(adsk.core.Point3D.create(0, -0.61, 1.0), 0.085) # SG90 螺丝孔 Y- 侧
    result["steps"].append(f"草图2 (XZ): {sk2.profiles.count} 个圆")

    for j in range(sk2.profiles.count):
        cut_in = extrudes.createInput(sk2.profiles.item(j),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = body1
        cut_in.setDistanceExtent(True, adsk.core.ValueInput.createByReal(5.0))  # 双向 5cm 穿透
        try:
            extrudes.add(cut_in)
        except Exception as e:
            result["warnings"].append(f"孔{j} cut 失败: {str(e)[:100]}")
    result["steps"].append(f"步骤2后 body={rootComp.bRepBodies.count}")

    # 3. XY 平面画 4 个手掌螺丝孔 1.7mm（Z=0 底部 4 角）
    sk3 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    c3 = sk3.sketchCurves.sketchCircles
    for x, y in [(-1.3, -0.65), (1.3, -0.65), (-1.3, 0.65), (1.3, 0.65)]:
        c3.addByCenterRadius(adsk.core.Point3D.create(x, y, 0), 0.085)
    result["steps"].append(f"草图3 (XY): {sk3.profiles.count} 个圆")

    for j in range(sk3.profiles.count):
        cut_in = extrudes.createInput(sk3.profiles.item(j),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = body1
        cut_in.setDistanceExtent(True, adsk.core.ValueInput.createByReal(5.0))
        try:
            extrudes.add(cut_in)
        except Exception as e:
            result["warnings"].append(f"手掌孔{j} cut 失败: {str(e)[:100]}")
    result["steps"].append(f"步骤3后 body={rootComp.bRepBodies.count}")

    # 4. verify
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
        # 期望: 30x16x25=12cm3 - 24x14x23=7.73cm3 = 4.27cm3 净 - 孔体积
        # 孔: 1×⌀5 沿Y 0.31 + 2×⌀1.7 沿Y 0.07 + 4×⌀1.7 沿Z 0.23 = 0.61
        # 期望 V ≈ 3.66
        if abs(sz_list[0]-30) < 2 and abs(sz_list[1]-16) < 2 and abs(sz_list[2]-25) < 2:
            if 3.0 < v < 4.5:
                result["success"] = True
                result["judgment"] = f"OK 尺寸30x16x25对, V={v:.2f} (期望~3.66 净-孔)"
            elif v > 4.5:
                result["judgment"] = f"NO 体积偏大 V={v:.2f} (期望~3.66), 可能有孔没切"
            else:
                result["judgment"] = f"NO 体积偏小 V={v:.2f} (期望~3.66), 可能内腔出问题"
        else:
            result["judgment"] = f"NO 尺寸不对 (实际 {sz_list}, 期望 30x16x25)"
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
    "description": "指段 1 v3 (板厚 25mm 装得下 SG90)"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"指段1 v3 已发送！command_id: {data['command_id']}")
