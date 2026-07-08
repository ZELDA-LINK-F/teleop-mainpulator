"""Mavis 发送 SG90 固定座代码（无清空版本）"""
import json, uuid

code = r'''
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
rootComp = app.activeProduct.rootComponent

# 不清空！直接画嵌套轮廓
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
lines = sketch.sketchCurves.sketchLines

# 外矩形 35x22 mm
lines.addTwoPointRectangle(
    adsk.core.Point3D.create(-1.75, -1.1, 0),
    adsk.core.Point3D.create(1.75, 1.1, 0)
)

# 内矩形 22x12 mm（嵌套 - Fusion 自动识别为洞）
lines.addTwoPointRectangle(
    adsk.core.Point3D.create(-1.1, -0.6, 0),
    adsk.core.Point3D.create(1.1, 0.6, 0)
)

# 拉伸
profile = sketch.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
input1 = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
input1.setDistanceExtent(False, adsk.core.ValueInput.createByString("4 mm"))
extrudes.add(input1)

cam = app.activeViewport.camera
cam.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
app.activeViewport.camera = cam
'''

data = {
    "command_id": str(uuid.uuid4()),
    "code": code,
    "description": "SG90 舵机固定座（无清空）"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"无清空版已发送！command_id: {data['command_id']}")