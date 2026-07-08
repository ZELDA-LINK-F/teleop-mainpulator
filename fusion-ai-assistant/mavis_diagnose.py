"""Mavis 发送：详细诊断脚本 - 看实际 body 尺寸 + 特征数 + profile 列表"""
import json, uuid

code = r'''
import adsk.core, adsk.fusion, traceback

try:
    app = adsk.core.Application.get()
    rootComp = app.activeProduct.rootComponent

    info = []
    info.append("=" * 50)
    info.append(f"Body 数量: {rootComp.bRepBodies.count}")
    for i, b in enumerate(rootComp.bRepBodies):
        bbox = b.boundingBox
        sx = (bbox.maxPoint.x - bbox.minPoint.x) * 10
        sy = (bbox.maxPoint.y - bbox.minPoint.y) * 10
        sz = (bbox.maxPoint.z - bbox.minPoint.z) * 10
        info.append(f"  Body {i}: {sx:.1f} x {sy:.1f} x {sz:.1f} mm")
        info.append(f"    体积: {b.volume:.2f} cm3")

    info.append("=" * 50)
    info.append(f"Extrude 特征数: {rootComp.features.extrudeFeatures.count}")
    for i in range(rootComp.features.extrudeFeatures.count):
        e = rootComp.features.extrudeFeatures.item(i)
        try:
            dist_cm = e.extentOne.distance.value
            info.append(f"  Extrude {i}: op={e.operationType}, 距离={dist_cm*10:.1f}mm")
        except:
            info.append(f"  Extrude {i}: op={e.operationType}")

    info.append("=" * 50)
    info.append(f"Sketch 数量: {rootComp.sketches.count}")
    for i, s in enumerate(rootComp.sketches):
        info.append(f"  Sketch {i}: profiles={s.profiles.count}")
        for j in range(s.profiles.count):
            p = s.profiles.item(j)
            area_mm2 = abs(p.areaProperties().area) * 100
            info.append(f"    profile[{j}]: area={area_mm2:.1f} mm2")

    msg = "\n".join(info)
    with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\last_result.txt", "w", encoding="utf-8") as f:
        f.write(msg)
    app.userInterface.messageBox(msg)
except Exception as e:
    err = traceback.format_exc()
    with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\last_result.txt", "w", encoding="utf-8") as f:
        f.write("ERROR:\n" + err)
    try:
        app.userInterface.messageBox("失败:\n" + err)
    except:
        pass
'''

data = {
    "command_id": str(uuid.uuid4()),
    "code": code,
    "description": "详细诊断 - 实际 body 尺寸 + 特征数 + profile 列表"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"诊断脚本已发送！command_id: {data['command_id']}")
print("等用户截图 Fusion 弹出的对话框")
