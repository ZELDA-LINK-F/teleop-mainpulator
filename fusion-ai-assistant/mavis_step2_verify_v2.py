"""Mavis 发送：清空 + 两步法 + 自动 verify v2
- 步骤 0：清空所有 features + sketches（避免残留）
- 步骤 1：画外+内矩形
- 步骤 2：拉伸外-内净面积 = 板带洞（一步到位，避开 profile 排序坑）
- 步骤 3：verify + 写到文件 + 弹窗
"""
import json, uuid

code = r'''
import adsk.core, adsk.fusion, traceback
import json as _json

app = adsk.core.Application.get()
rootComp = app.activeProduct.rootComponent

result = {"steps": [], "verify": [], "success": False, "judgment": "?", "error": None}

try:
    # 0. 清空所有 features 和 sketches（解决残留 body 问题）
    del_count = 0
    for i in range(rootComp.features.count - 1, -1, -1):
        try:
            rootComp.features.item(i).deleteMe()
            del_count += 1
        except:
            pass
    sk_count = 0
    for i in range(rootComp.sketches.count - 1, -1, -1):
        try:
            rootComp.sketches.item(i).deleteMe()
            sk_count += 1
        except:
            pass
    result["steps"].append(f"清空: features={del_count}, sketches={sk_count}, 残留 body={rootComp.bRepBodies.count}")

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

    # 2. 拉伸：选面积最大的 profile（外轮廓 = 35x22=770 mm2 或外-内=506 mm2）
    #    用 NewBodyFeatureOperation + 板厚 4mm
    extrudes = rootComp.features.extrudeFeatures
    chosen_profile = None
    chosen_area = 0
    for j in range(sketch.profiles.count):
        p = sketch.profiles.item(j)
        a = abs(p.areaProperties().area) * 100
        if a > chosen_area:
            chosen_area = a
            chosen_profile = p
    result["steps"].append(f"选面积最大 profile: {chosen_area:.1f} mm2 (外轮廓=770 或外-内=506)")

    ext_input = extrudes.createInput(chosen_profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(0.4))  # 4mm
    ext1 = extrudes.add(ext_input)
    result["steps"].append(f"拉伸后 body={rootComp.bRepBodies.count}")
    for i in range(rootComp.bRepBodies.count):
        b = rootComp.bRepBodies.item(i)
        result["steps"].append(f"  body[{i}]: V={b.volume:.2f} cm3")

    # 3. verify + 形状判断
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
        # 板 3.08 / 板带洞 2.02 / 板+独立洞块 3.08+1.06=4.14
        if 1.8 < v < 2.3:
            result["success"] = True
            result["judgment"] = f"OK 板带洞 (V={v:.2f}, 期望 2.02)"
        elif 2.9 < v < 3.2:
            result["judgment"] = f"NO 实心板没洞 (V={v:.2f}, 期望 3.08 板/2.02 板+洞)"
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

# 写文件（Mavis 读取）
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
    "description": "清空 + 单步拉伸(选最大 profile) + 自动 verify v2"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"v2 已发送！command_id: {data['command_id']}")
