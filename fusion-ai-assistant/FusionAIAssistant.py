"""
Fusion AI Assistant - 主入口
============================
功能：在 Fusion 360 工具栏添加 [🤖 AI 助手] 按钮
点击后弹出输入框，用户输入建模需求
需求通过 JSON 文件发送到 Mavis，Mavis 生成 Fusion Python 代码后写回
插件后台线程轮询响应，收到代码后在 Fusion 里执行，建模自动完成
"""
import adsk.core
import adsk.fusion
import traceback
import os
import json
import threading
import time
import queue
import uuid
import subprocess

# ============================================================================
# 全局状态
# ============================================================================
_app = None
_ui = None
_cmd_defs = []  # 命令定义列表（用于清理）
_panel_controls = []  # 工具栏控件（用于清理）

# 文件桥接路径
ADDIN_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_DIR = os.path.join(ADDIN_DIR, 'queue')
PENDING_FILE = os.path.join(QUEUE_DIR, 'pending_request.json')
RESPONSE_FILE = os.path.join(QUEUE_DIR, 'completed_response.json')
CONFIG_FILE = os.path.join(ADDIN_DIR, 'config.json')

# 配置（从 config.json 读取）
CONFIG = {
    'mavis_session_id': '',
    'auto_notify': True
}


def load_config():
    """读取配置文件"""
    global CONFIG
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_cfg = json.load(f)
            CONFIG.update(user_cfg)
    except Exception as e:
        print(f'[Mavis AI] 读取配置失败: {e}')


def notify_mavis(prompt_text: str, request_id: str):
    """通过 mavis CLI 把请求发给 Mavis session"""
    if not CONFIG.get('mavis_session_id'):
        print('[Mavis AI] 未配置 mavis_session_id，跳过通知')
        return False
    if not CONFIG.get('auto_notify', True):
        return False

    try:
        # 构造消息内容
        msg = (
            f'[Fusion AI 助手] 收到用户建模指令\n\n'
            f'指令：{prompt_text}\n'
            f'请求 ID：{request_id}\n\n'
            f'请按以下步骤处理：\n'
            f'1. 读取 {PENDING_FILE} 获取完整请求\n'
            f'2. 用 LLM 生成 Fusion 360 Python API 代码\n'
            f'3. 把代码写入 {RESPONSE_FILE}（JSON 格式）\n'
            f'4. 删除 {PENDING_FILE}\n\n'
            f'Fusion 插件会轮询 {RESPONSE_FILE} 并自动执行代码'
        )

        # 调用 mavis CLI
        result = subprocess.run(
            [
                'mavis', 'communication', 'send',
                '--from', 'fusion-ai-assistant',
                '--to', CONFIG['mavis_session_id'],
                '--command', 'prompt',
                '--content', msg
            ],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8'
        )

        if result.returncode == 0:
            print(f'[Mavis AI] 已通知 Mavis session: {CONFIG["mavis_session_id"][:12]}...')
            return True
        else:
            print(f'[Mavis AI] 通知失败: {result.stderr}')
            return False

    except subprocess.TimeoutExpired:
        print('[Mavis AI] 通知超时')
        return False
    except Exception as e:
        print(f'[Mavis AI] 通知异常: {e}')
        return False

# ============================================================================
# 插件生命周期
# ============================================================================
def run(context):
    """Fusion 加载插件时调用"""
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        # 读取配置
        load_config()

        # 确保 queue 目录存在
        os.makedirs(QUEUE_DIR, exist_ok=True)

        # 创建命令定义（按钮）
        cmd_def = _ui.commandDefinitions.addButtonDefinition(
            'FusionAIAssistantBtn',
            'Mavis AI 助手',
            '通过 Mavis AI 直接建模（输入自然语言描述）'
        )

        # 绑定按钮点击事件
        on_command_created = CommandCreatedHandler()
        cmd_def.commandCreated.add(on_command_created)
        _cmd_defs.append(cmd_def)

        # 添加到工具栏
        # Fusion 2702 的实体创建面板 ID
        target_panel_ids = ['SolidCreatePanel', 'SolidModifyPanel', 'ToolsPanel']
        for panel_id in target_panel_ids:
            panel = _ui.allToolbarPanels.itemById(panel_id)
            if panel:
                try:
                    control = panel.controls.addCommand(cmd_def)
                    _panel_controls.append(control)
                    print(f'[Mavis AI] 按钮已添加到 {panel_id}')
                    break
                except Exception as e:
                    print(f'[Mavis AI] 添加到 {panel_id} 失败: {e}')
                    continue

        # 启动响应监听线程（后台）
        start_response_watcher()

        # 在文本命令窗口打印启动信息
        if _app:
            text_palette = _ui.palettes.itemById('TextCommandsPanel')
            if text_palette:
                text_palette.writeText('[Mavis AI 助手] 启动成功！工具栏找到 [🤖 AI 助手] 按钮即可使用\n')

    except Exception as e:
        if _ui:
            _ui.messageBox(f'AI 助手启动失败:\n{traceback.format_exc()}')


def stop(context):
    """Fusion 卸载插件时调用"""
    try:
        # 清理工具栏控件
        for control in _panel_controls:
            try:
                control.deleteMe()
            except:
                pass
        # 清理命令定义
        for cmd_def in _cmd_defs:
            try:
                cmd_def.deleteMe()
            except:
                pass
    except:
        pass


# ============================================================================
# 事件处理器
# ============================================================================
class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """用户点击 [🤖 AI 助手] 按钮时触发 - 配置输入对话框"""

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isAutoExecute = False
            cmd.okButtonText = '发送到 Mavis'
            cmd.cancelButtonText = '取消'

            inputs = cmd.commandInputs

            # 主输入框：建模指令
            prompt_input = inputs.addTextBoxCommandInput(
                'prompt',
                'AI 指令（自然语言描述）',
                '例如：画一个 50×30×20 mm 的方块',
                6,    # 显示行数
                True  # 多行模式
            )

            # 提示信息
            inputs.addTextBoxCommandInput(
                'hint',
                '',
                '💡 提示：用自然语言描述你想要的零件\n' +
                '   例如："画一个舵机固定座，SG90 用的"\n' +
                '   指令会发送到 Mavis，AI 会自动生成代码并执行',
                4,
                False
            )

            # OK 按钮事件
            on_execute = ExecuteHandler()
            cmd.execute.add(on_execute)

            # 输入变化事件（实时校验）
            on_input_changed = InputChangedHandler()
            cmd.inputChanged.add(on_input_changed)

        except Exception as e:
            if _ui:
                _ui.messageBox(f'创建对话框失败:\n{traceback.format_exc()}')


class InputChangedHandler(adsk.core.CommandInputChangedEventHandler):
    """用户修改输入时触发"""
    def notify(self, args):
        pass  # 暂不处理


class ExecuteHandler(adsk.core.CommandExecuteEventHandler):
    """用户点击 [发送到 Mavis] 按钮时触发"""

    def notify(self, args):
        try:
            cmd = args.command
            prompt_input = cmd.commandInputs.itemById('prompt')
            prompt_text = prompt_input.text.strip() if prompt_input.text else ''

            # 校验
            if not prompt_text:
                if _ui:
                    _ui.messageBox('请输入建模指令！\n\n例如：画一个 50×30×20 mm 的方块')
                return

            # 构造请求
            request_id = str(uuid.uuid4())
            request = {
                'request_id': request_id,
                'prompt': prompt_text,
                'timestamp': time.time(),
                'source': 'fusion-plugin'
            }

            # 写入 pending_request.json（Mavis 会轮询这个文件）
            with open(PENDING_FILE, 'w', encoding='utf-8') as f:
                json.dump(request, f, ensure_ascii=False, indent=2)

            # 通过 mavis CLI 通知 Mavis session
            notified = notify_mavis(prompt_text, request_id)

            if _ui:
                if notified:
                    _ui.messageBox(
                        f'✅ 指令已发送到 Mavis\n\n'
                        f'指令：{prompt_text}\n\n'
                        f'请求 ID：{request_id[:8]}\n\n'
                        f'Mavis 正在生成代码...\n'
                        f'完成后模型会自动出现在画布上'
                    )
                else:
                    _ui.messageBox(
                        f'⚠️ 指令已写入队列文件\n\n'
                        f'指令：{prompt_text}\n\n'
                        f'请求 ID：{request_id[:8]}\n\n'
                        f'自动通知失败（请检查 config.json 里的 mavis_session_id）。\n'
                        f'你可以手动切到 Mavis 对话窗口说"检查 Fusion 请求"'
                    )

        except Exception as e:
            if _ui:
                _ui.messageBox(f'发送失败:\n{traceback.format_exc()}')


# ============================================================================
# 后台响应监听
# ============================================================================
def start_response_watcher():
    """启动后台线程，每 2 秒检查一次 completed_response.json"""
    def watcher():
        while True:
            try:
                if os.path.exists(RESPONSE_FILE):
                    # 读取响应
                    with open(RESPONSE_FILE, 'r', encoding='utf-8') as f:
                        response = json.load(f)

                    code = response.get('code', '')
                    error = response.get('error', '')
                    description = response.get('description', '')
                    request_id = response.get('request_id', '')

                    if error:
                        # Mavis 返回错误
                        _ui.messageBox(
                            f'❌ Mavis 返回错误\n\n'
                            f'请求 ID：{request_id[:8]}\n'
                            f'错误：{error}'
                        )
                    elif code:
                        # Mavis 返回代码 → 执行
                        success, exec_error = execute_code(code)
                        if success:
                            _ui.messageBox(
                                f'✅ 模型创建成功！\n\n'
                                f'请求 ID：{request_id[:8]}\n'
                                f'说明：{description}'
                            )
                        else:
                            _ui.messageBox(
                                f'❌ 代码执行失败\n\n'
                                f'请求 ID：{request_id[:8]}\n'
                                f'错误：{exec_error}\n\n'
                                f'--- 生成的代码 ---\n{code[:500]}...'
                            )

                    # 删除响应文件（避免重复处理）
                    os.remove(RESPONSE_FILE)

            except Exception as e:
                # 静默处理异常，继续轮询
                pass

            time.sleep(2)

    # 启动 daemon 线程
    thread = threading.Thread(target=watcher, daemon=True)
    thread.start()


def execute_code(code: str):
    """执行 Mavis 返回的 Python 代码"""
    try:
        # 在 Fusion 的 Python 上下文里执行
        # 提供 adsk 和 fusion 两个模块
        exec(code, {'adsk': adsk, 'fusion': adsk.fusion, '__name__': '__fusion_exec__'})
        return True, None
    except Exception as e:
        return False, traceback.format_exc()