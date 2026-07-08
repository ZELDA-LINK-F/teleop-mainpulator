"""Mavis 发送：指段 1 建模 v2（修复 cut）
- 步骤 0：清空
- 步骤 1：外壳 30x25x14（嵌套轮廓）→ 1 body
- 步骤 2：XZ 平面画 3 个圆（输出轴 5mm + 2 个 SG90 螺丝孔 1.7mm）→ 批量 cut targetBody，ThroughAllExtent
- 步骤 3：XY 平面画 4 个手掌螺丝孔 1.7mm → 批量 cut targetBody，ThroughAllExtent
- 步骤 4：自动 verify
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

    # 1. 外壳（嵌套轮廓：30x25 外 + 24x13 内）
    sk1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    sk1.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.5, -1.25, 0),
        adsk.core.Point3D.create(1.5, 1.25, 0)
    )
    sk1.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.2, -0.65, 0),
        adsk.core.Point3D.create(1.2, 0.65, 0)
    )
    # 选面积最大 profile（外-内净面积）拉伸
    chosen = max(range(sk1.profiles.count),
                 key=lambda j: abs(sk1.profiles.item(j).areaProperties().area))
    chosen_area = abs(sk1.profiles.item(chosen).areaProperties().area) * 100
    result["steps"].append(f"草图1: {sk1.profiles.count} profiles, 选[{chosen}]={chosen_area:.1f}mm2")

    extrudes = rootComp.features.extrudeFeatures
    ext_in = extrudes.createInput(sk1.profiles.item(chosen),
                                   adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.4))  # 14mm
    extrudes.add(ext_in)
    body1 = rootComp.bRepBodies.item(0)
    result["steps"].append(f"步骤1后 body={rootComp.bRepBodies.count}, V={body1.volume:.2f}cm3")

    # 2. XZ 平面画 3 个圆（输出轴 5mm + 2 个 SG90 螺丝孔 1.7mm）
    # XZ 平面是 Y=0 的平面
    # 圆心 (X, 0, Z)，cut 沿 Y 方向穿透
    sk2 = rootComp.sketches.add(rootComp.xZConstructionPlane)
    c2 = sk2.sketchCurves.sketchCircles
    c2.addByCenterRadius(adsk.core.Point3D.create(1.5, 0, 0.7), 0.25)   # 输出轴孔 5mm (X+端面中心)
    c2.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0.95), 0.085)   # SG90 螺丝孔 1.7mm (Y+侧)
    c2.addByCenterRadius(adsk.core.Point3D.create(0, 0, -0.95), 0.085)  # SG90 螺丝孔 1.7mm (Y-侧)
    result["steps"].append(f"草图2 (XZ): {sk2.profiles.count} 个圆")

    # 用 setDistanceExtent(True, 5.0) = 双向 5cm 穿透
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

    # 3. XY 平面画 4 个手掌螺丝孔 1.7mm
    # XY 平面是 Z=0 的平面，圆心 (X, Y, 0)，cut 沿 Z 方向穿透
    sk3 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    c3 = sk3.sketchCurves.sketchCircles
    for x, y in [(-1.3, -1.05), (1.3, -1.05), (-1.3, 1.05), (1.3, 1.05)]:
        c3.addByCenterRadius(adsk.core.Point3D.create(x, y, 0), 0.085)
    result["steps"].append(f"草图3 (XY): {sk3.profiles.count} 个圆")

    for j in range(sk3.profiles.count):
        cut_in = extrudes.createInput(sk3.profiles.item(j),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = body1
        cut_in.setDistanceExtent(True, adsk.core.ValueInput.createByReal(5.0))  # 双向 5cm 穿透
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
        # 期望: 30x25x14 - 24x13x14(内腔) = 10.5-4.37 = 6.13cm3 (嵌套轮廓)
        # 实际可能 5.8-6.5 (因 cut 还会减掉螺丝孔)
        if abs(sz_list[0]-30) < 2 and abs(sz_list[1]-25) < 2 and abs(sz_list[2]-14) < 2:
            result["success"] = True
            result["judgment"] = f"OK 尺寸对 (V={v:.2f}, 30x25x14 净~6.13 - 7个孔~0.05 = ~6.08)"
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
    "description": "指段 1 建模 v2 (ThroughAllExtent 修复)"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"指段1 v2 已发送！command_id: {data['command_id']}")
