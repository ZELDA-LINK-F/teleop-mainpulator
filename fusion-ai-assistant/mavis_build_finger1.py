"""Mavis 发送：指段 1 建模 + 自动 verify
- 步骤 0：清空文档
- 步骤 1：草图 1（外轮廓 30x25 + 内腔 24x13 嵌套）→ 拉伸 14mm 厚 → 外壳带空腔
- 步骤 2：草图 2（输出轴孔 5mm 圆）→ 拉伸穿透 → 输出轴孔
- 步骤 3：草图 3（6 个螺丝孔 1.7mm）→ 拉伸穿透 → 螺丝孔
- 步骤 4：自动 verify + 写到文件 + 弹窗
"""
import json, uuid

code = r'''
import adsk.core, adsk.fusion, traceback
import json as _json
import math

app = adsk.core.Application.get()
rootComp = app.activeProduct.rootComponent

result = {"steps": [], "verify": [], "success": False, "judgment": "?", "error": None}

try:
    # 0. 清空文档
    del_f = sum(1 for i in range(rootComp.features.count - 1, -1, -1)
                if (lambda: (rootComp.features.item(i).deleteMe(), True)[1])())
    del_s = sum(1 for i in range(rootComp.sketches.count - 1, -1, -1)
                if (lambda: (rootComp.sketches.item(i).deleteMe(), True)[1])())
    result["steps"].append(f"清空: features={del_f}, sketches={del_s}, 残留 body={rootComp.bRepBodies.count}")

    # ===== 步骤 1: 外壳（嵌套轮廓 - 板+洞） =====
    sketch1 = rootComp.sketches.add(rootComp.xYConstructionPlane)
    lines1 = sketch1.sketchCurves.sketchLines

    # 外轮廓 30x25mm（中心在原点）
    lines1.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.5, -1.25, 0),
        adsk.core.Point3D.create(1.5, 1.25, 0)
    )
    # 内腔 24x13mm（嵌套 - Fusion 拉伸时识别为洞）
    lines1.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.2, -0.65, 0),
        adsk.core.Point3D.create(1.2, 0.65, 0)
    )
    # 注意：Z 方向高度 = 14mm 用拉伸距离控制

    result["steps"].append(f"草图1: {sketch1.profiles.count} profiles")
    for j in range(sketch1.profiles.count):
        a = abs(sketch1.profiles.item(j).areaProperties().area) * 100
        result["steps"].append(f"  profile[{j}]: {a:.1f} mm2")

    # 选最大 profile（外轮廓或外-内净面积）拉伸 14mm
    chosen = max(range(sketch1.profiles.count),
                 key=lambda j: abs(sketch1.profiles.item(j).areaProperties().area))
    chosen_area = abs(sketch1.profiles.item(chosen).areaProperties().area) * 100
    result["steps"].append(f"拉伸 profile[{chosen}] = {chosen_area:.1f} mm2 (高 14mm)")

    extrudes = rootComp.features.extrudeFeatures
    ext_in = extrudes.createInput(sketch1.profiles.item(chosen),
                                   adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.4))  # 14mm
    ext1 = extrudes.add(ext_in)
    result["steps"].append(f"步骤1后 body={rootComp.bRepBodies.count}")

    # ===== 步骤 2: SG90 输出轴孔（5mm 圆穿透） =====
    # 在远端面（X+ 方向）开一个 5mm 圆孔，让 SG90 输出轴穿出
    # 用 ExtrudeFeature 的 cut，需要一个面作为草图平面
    # 先获取远端面
    body1 = rootComp.bRepBodies.item(0)
    faces = body1.faces
    target_face = None
    for i in range(faces.count):
        f = faces.item(i)
        bbox = f.boundingBox
        # 找 X+ 方向的面（maxX 最大）
        if abs(bbox.maxPoint.x - 1.5) < 0.01 and abs(bbox.minPoint.y - (-1.25)) < 0.01:
            target_face = f
            break
    if target_face is None:
        # fallback: 找垂直于 X 的最大面
        for i in range(faces.count):
            f = faces.item(i)
            bbox = f.boundingBox
            if abs(bbox.maxPoint.x - 1.5) < 0.05:
                target_face = f
                break
    if target_face is None:
        # 再 fallback: 直接用 XY 平面，X+ 方向的拉伸
        # 用 XY 平面画一个 5mm 圆，Z=0 到 Z=1.4
        sketch2 = rootComp.sketches.add(rootComp.xYConstructionPlane)
        circles2 = sketch2.sketchCurves.sketchCircles
        circles2.addByCenterRadius(adsk.core.Point3D.create(1.5, 0, 0), 0.25)  # 在 X+ 端面
        # 拉伸 1.4cm 穿透
        cut_in = extrudes.createInput(sketch2.profiles.item(0),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = body1
        cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.5))
        extrudes.add(cut_in)
    else:
        sketch2 = rootComp.sketches.add(target_face)
        circles2 = sketch2.sketchCurves.sketchCircles
        # 圆心在面中心
        circles2.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 0.25)  # 5mm
        cut_in = extrudes.createInput(sketch2.profiles.item(0),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = body1
        cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.5))
        extrudes.add(cut_in)
    result["steps"].append(f"步骤2(输出轴孔)后 body={rootComp.bRepBodies.count}")

    # ===== 步骤 3: 6 个 M2 螺丝孔 =====
    # 2 个 SG90 螺丝孔（Y- 和 Y+ 方向，穿过 SG90 螺丝耳位置）
    # 4 个手掌螺丝孔（4 个角）
    # 用 XZ 平面作为草图平面
    sketch3 = rootComp.sketches.add(rootComp.xZConstructionPlane)
    circles3 = sketch3.sketchCurves.sketchCircles

    # SG90 螺丝孔（Y- 和 Y+ 方向中心，Z=SG90 螺丝耳高度 ~10mm，X=中心）
    circles3.addByCenterRadius(adsk.core.Point3D.create(0, 0, 1.0), 0.085)  # Y- 方向
    circles3.addByCenterRadius(adsk.core.Point3D.create(0, 0, -1.0), 0.085)  # Y+ 方向
    # 手掌螺丝孔（4 个角：XY 平面上 4 个角在 Z=0）
    for x, y in [(-1.3, -1.05), (1.3, -1.05), (-1.3, 1.05), (1.3, 1.05)]:
        circles3.addByCenterRadius(adsk.core.Point3D.create(x, y, 0), 0.085)

    result["steps"].append(f"草图3: {sketch3.profiles.count} circles")

    for j in range(sketch3.profiles.count):
        cut_in = extrudes.createInput(sketch3.profiles.item(j),
                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_in.targetBody = rootComp.bRepBodies.item(0)
        cut_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(3.0))
        extrudes.add(cut_in)
    result["steps"].append(f"步骤3(6螺丝孔)后 body={rootComp.bRepBodies.count}")

    # ===== 步骤 4: 自动 verify =====
    for i, b in enumerate(rootComp.bRepBodies):
        bbox = b.boundingBox
        sx = (bbox.maxPoint.x - bbox.minPoint.x) * 10
        sy = (bbox.maxPoint.y - bbox.minPoint.y) * 10
        sz = (bbox.maxPoint.z - bbox.minPoint.z) * 10
        result["verify"].append({
            "id": i,
            "size_mm": [round(sx, 1), round(sy, 1), round(sz, 1)],
            "volume_cm3": round(b.volume, 2)
        })

    n = rootComp.bRepBodies.count
    if n == 1:
        v = rootComp.bRepBodies.item(0).volume
        sz_list = result["verify"][0]["size_mm"]
        # 理论: 外壳 30x25x14=10.5cm3，内腔 24x13x14=4.37cm3，净 ~6.13cm3（嵌套轮廓方案）
        # 实际嵌套轮廓算出来: 6.0-6.5 cm3 都算正常
        if 5.5 < v < 7.0 and abs(sz_list[0]-30) < 2 and abs(sz_list[1]-25) < 2 and abs(sz_list[2]-14) < 2:
            result["success"] = True
            result["judgment"] = f"OK 外壳尺寸对 (V={v:.2f}, 尺寸{sz_list}, 期望 30x25x14 净6.13)"
        elif abs(sz_list[0]-30) < 2 and abs(sz_list[1]-25) < 2 and abs(sz_list[2]-14) < 2:
            result["judgment"] = f"? 尺寸对但体积异常 (V={v:.2f}, 尺寸{sz_list})"
        else:
            result["judgment"] = f"NO 尺寸不对 (尺寸{sz_list}, 期望 30x25x14)"
    elif n == 2:
        result["judgment"] = f"NO 两个独立 body (切没合并)"
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
    "description": "指段 1 建模 + 自动 verify"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"指段1 建模+verify 已发送！command_id: {data['command_id']}")
