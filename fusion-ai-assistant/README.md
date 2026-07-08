# Fusion AI 助手 - Mavis Edition

> 在 Fusion 360 里直接调用 Mavis（我）来建模。**工具栏原生按钮，输入自然语言，AI 自动建模型**。

## 这是什么

一个 **Fusion 360 Add-In 插件**，把 Mavis 深度集成到 Fusion 里：

```
┌─────────────────────────────────────────┐
│  Fusion 360                              │
│  [文件] [实体] [曲面] ... [🤖 Mavis AI]  │ ← 工具栏原生按钮
└─────────────────────────────────────────┘
         ↓ 点击
┌─────────────────────────────────────────┐
│  输入: "画一个舵机固定座，SG90 用的"     │
│              [取消] [发送到 Mavis]       │
└─────────────────────────────────────────┘
         ↓
   Mavis 收到请求 → 用 LLM 生成代码 → 自动执行
         ↓
   🎉 模型出现在画布上
```

---

## 工作原理

```
Fusion 插件                    Mavis (我)                 你
─────────────                  ─────────                  ──
点 [🤖 AI 助手] 按钮
       ↓
弹输入框
       ↓
输入"画 50×30×20 方块"
       ↓
写入 queue/pending_request.json
       ↓
调用 mavis communication send ─────→  收到 prompt
                                              ↓
                                         读 pending_request.json
                                              ↓
                                         生成 Fusion Python 代码
                                              ↓
                                         写入 queue/completed_response.json
       ↓                                         ↓
后台线程轮询 completed_response.json ←──────────┘
       ↓
收到代码 → exec() 执行
       ↓
🎉 模型出现
```

**通信方式**：JSON 文件 + `mavis communication` CLI 命令。

**AI 部分**：就是 Mavis（我），**不需要 OpenAI / Claude / 任何 API key**。

---

## 安装步骤

### 1. 运行安装脚本

打开 PowerShell，进入项目目录：

```powershell
cd D:\ESP\遥操作机械\fusion-ai-assistant
.\install.ps1
```

脚本会**自动**：
- 找到 Fusion AddIns 目录
- 创建符号链接（修改代码不用重装）

> 如果提示权限不足，用**管理员身份运行 PowerShell**。

### 2. 在 Fusion 里加载插件

1. 打开 Fusion 360
2. 菜单栏 → **工具** → **脚本和添加剂**
3. 点左上角 **"+"** 添加按钮
4. 选 **"我的电脑上的脚本/插件"** → **"文件夹"**
5. 浏览到 `C:\Users\<你>\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\FusionAIAssistant`
6. 选中 `FusionAIAssistant` → 点 **"运行"**

### 3. 配置 Mavis Session ID

第一次安装后，编辑 `config.json`：

```json
{
  "mavis_session_id": "mvs_xxxxxxxxxx",
  "auto_notify": true
}
```

把 `mavis_session_id` 改成你自己的 session ID（在 Mavis Code 顶部能看到）。

### 4. 测试

工具栏会出现 **"🤖 Mavis AI 助手"** 按钮，点击 → 输入"画一个 50×30×20 mm 的方块" → 点"发送到 Mavis" → 等几秒 → 模型出现 🎉

---

## 卸载

### 方法 A：用脚本

```powershell
.\uninstall.ps1
```

### 方法 B：手动

```powershell
Remove-Item "$env:APPDATA\Autodesk\Autodesk Fusion 360\API\AddIns\FusionAIAssistant"
```

---

## 使用示例

在输入框里输入任意自然语言描述，AI 会自动建模型：

| 输入 | 输出 |
|---|---|
| `画一个 50×30×20 mm 的方块` | 一个 50×30×20 mm 长方体 |
| `画舵机固定座，SG90 用的` | SG90 舵机的固定座（带螺丝孔） |
| `画一个 M3 螺丝孔，直径 3.2，深 10` | 一个圆柱孔 |
| `做一个机械手连杆，长 50，宽 10，厚 5，两端各一个 M3 孔` | 带孔的连杆 |
| `画指尖，圆弧半径 20，厚 8` | 指尖零件 |

---

## 项目结构

```
fusion-ai-assistant/
├── FusionAIAssistant.manifest    # Fusion 插件清单
├── FusionAIAssistant.py          # 插件主入口（按钮 + 输入框 + 轮询）
├── config.json                   # 配置文件（Mavis session ID）
├── install.ps1                   # 安装脚本（创建符号链接）
├── uninstall.ps1                 # 卸载脚本
├── README.md                     # 本文件
└── queue/                        # 通信队列
    ├── pending_request.json      # 插件写入 → Mavis 读取
    └── completed_response.json   # Mavis 写入 → 插件读取
```

---

## 故障排查

### 工具栏没有按钮
- 检查 Fusion 版本是否 ≥ 2.0.10000
- 检查 `install.ps1` 是否成功执行
- Fusion → 工具 → 脚本和添加剂，确认 `FusionAIAssistant` 在列表里且**已运行**

### 点按钮没反应
- 打开 Fusion 的 **"文本命令"窗口**（视图 → 文本命令）→ 看 `[Mavis AI]` 开头的日志
- 检查 Fusion 是不是新版本（PyComponent 格式）

### 点了按钮但模型没出现
- 检查 `config.json` 里的 `mavis_session_id` 对不对
- 检查 `mavis CLI` 能不能在 PowerShell 里直接调用
- 看 `queue/` 目录里有没有 `pending_request.json` 或 `completed_response.json`
- **手动触发**：切到 Mavis 对话窗口，说"检查 Fusion 请求"

### 代码执行失败
- Fusion 的 Python 上下文里可能缺少某些模块
- 看 Fusion 弹的错误消息，里面有堆栈跟踪
- 把错误消息发给 Mavis，AI 会修复代码

---

## 开发者

**Fusion API 参考**：
- [Fusion 360 Python API 文档](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-A92A4B10-3781-4925-94C6-2DA45CF25292)
- [Fusion 脚本示例](https://github.com/AutodeskFusion360/Fusion360ScriptExamples)

**关键 API 调用**：
- `adsk.core.Application.get()` - 获取应用实例
- `app.activeProduct` - 当前产品（设计/CAM 等）
- `design.rootComponent` - 根组件
- `comp.sketches.add(plane)` - 创建草图
- `sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)` - 画矩形
- `comp.features.extrudeFeatures.add(input)` - 拉伸

**注意**：Fusion Python 默认单位是 **cm**，不是 mm！50mm = 5cm。

---

## License

MIT - 用得开心。