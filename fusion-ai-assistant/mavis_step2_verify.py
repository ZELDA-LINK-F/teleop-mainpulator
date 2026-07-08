"""Mavis 发送：两步法 + 自动 verify 脚本
- 步骤 1：草图（外+内矩形）
- 步骤 2：拉伸外矩形成板（createInput + NewBodyFeatureOperation）
- 步骤 3：切内矩形成洞（createInput + CutFeatureOperation + targetBody）
- 步骤 4：自动 verify（算 body 数量 + 体积 + bounding box）
- 步骤 5：判断形状（有洞？无洞？两个 body？）
- 步骤 6：写 result.json（Mavis 读取）+ 弹窗（用户看）
"""
import json, uuid

code = r'''
import adsk.core, adsk.fusion, traceback
import json as _json

app = adsk.core.Application.get()
rootComp = app.activeProduct.rootComponent

result = {"steps": [], "verify": [], "success": False, "judgment": "?", "error": None}

try:
    # 1. 草图（XY 平面）
    sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines

    # 外矩形 35x22 mm
    lines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.75, -1.1, 0),
        adsk.core.Point3D.create(1.75, 1.1, 0)
    )
    # 内矩形 22x12 mm
    lines.addTwoPointRectangle(
        adsk.core.Point3D.create(-1.1, -0.6, 0),
        adsk.core.Point3D.create(1.1, 0.6, 0)
    )

    result["steps"].append(f"草图: {sketch.profiles.count} profiles")
    for j in range(sketch.profiles.count):
        p = sketch.profiles.item(j)
        area_mm2 = abs(p.areaProperties().area) * 100
        result["steps"].append(f"  profile[{j}]: area={area_mm2:.1f} mm2")

    # 2. 拉伸外矩形成板（createInput + NewBodyFeatureOperation）
    profile_outer = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    ext_input = extrudes.createInput(profile_outer, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(0.4))  # 4mm
    ext1 = extrudes.add(ext_input)
    body = ext1.bodies.item(0)
    result["steps"].append(f"外拉伸 → 板 (body={rootComp.bRepBodies.count})")

    # 3. 切内矩形成洞（createInput + CutFeatureOperation + targetBody）
    profile_inner = sketch.profiles.item(1)
    cut_input = extrudes.createInput(profile_inner, adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_input.targetBody = body  # 关键：明确指定目标 body
    cut_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(0.4))  # 4mm = 板厚
    cut1 = extrudes.add(cut_input)
    result["steps"].append(f"切内拉伸 → 洞 (body={rootComp.bRepBodies.count})")

    # 4. 自动 verify（算每个 body 的尺寸 + 体积）
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

    # 5. 形状判断
    # 理论：板 3.5*2.2*0.4=3.08 cm3，洞 2.2*1.2*0.4=1.06 cm3，净 2.02 cm3
    n = rootComp.bRepBodies.count
    if n == 1:
        v = rootComp.bRepBodies.item(0).volume
        if 1.5 < v < 2.5:
            result["success"] = True
            result["judgment"] = f"OK 穿透洞成功 (V={v:.2f}, 期望 2.02)"
        elif 2.8 < v < 3.3:
            result["judgment"] = f"NO 实心板, 没洞 (V={v:.2f}, 期望 3.08 板/2.02 板+洞)"
        else:
            result["judgment"] = f"? 体积异常 (V={v:.2f})"
    elif n == 2:
        v0 = rootComp.bRepBodies.item(0).volume
        v1 = rootComp.bRepBodies.item(1).volume
        result["judgment"] = f"NO 两个独立 body (V0={v0:.2f}, V1={v1:.2f})"
    else:
        result["judgment"] = f"? {n} 个 body (异常)"

except Exception as e:
    result["error"] = traceback.format_exc()
    result["judgment"] = f"ERROR: {e}"

# 6. 写文件（Mavis 读取判断成功/失败）
with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\last_result.json", "w", encoding="utf-8") as f:
    _json.dump(result, f, ensure_ascii=False, indent=2)

# 7. 弹窗（用户看）
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
    "description": "两步法 + 自动 verify (外拉伸 + 切内 + 体积判断)"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"两步法+verify 已发送！command_id: {data['command_id']}")
print("等几秒后 Fusion 弹窗显示：步骤 + 判断 + body 列表")
