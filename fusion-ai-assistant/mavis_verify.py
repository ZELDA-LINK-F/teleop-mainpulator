"""验证当前模型的实际尺寸"""
import json, uuid

code = r'''
import adsk.core, adsk.fusion, traceback

app = adsk.core.Application.get()
ui = app.userInterface
rootComp = app.activeProduct.rootComponent

info = []
for i, body in enumerate(rootComp.bRepBodies):
    bbox = body.boundingBox
    sx_mm = (bbox.maxPoint.x - bbox.minPoint.x) * 10
    sy_mm = (bbox.maxPoint.y - bbox.minPoint.y) * 10
    sz_mm = (bbox.maxPoint.z - bbox.minPoint.z) * 10
    info.append(f"Body {i}: {sx_mm:.1f} x {sy_mm:.1f} x {sz_mm:.1f} mm")
    info.append(f"  体积: {body.volume:.2f} cm3")

ui.messageBox("\n".join(info) if info else "没有 body!")
'''

data = {
    "command_id": str(uuid.uuid4()),
    "code": code,
    "description": "验证尺寸"
}

with open(r"D:\ESP\遥操作机械\fusion-ai-assistant\queue\mavis_command.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("验证脚本已发送")