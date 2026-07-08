"""
Mavis AI 助手 - 自动守护模式
============================
启动后常驻运行，监听 Mavis 写的指令文件
你在 Mavis 对话里说"画 XX"，模型自动出现在 Fusion

使用方法：
1. 复制本文件到 Fusion 脚本编辑器
2. Ctrl+S 保存
3. 点"运行"（只需要这一次！）
4. 之后你只用在 Mavis 对话里说"画 XX"，全自动
"""
import adsk.core, adsk.fusion, traceback
import os, json, time, threading, subprocess

# 文件路径
ADDIN_DIR = r'D:\ESP\遥操作机械\fusion-ai-assistant'
QUEUE_DIR = os.path.join(ADDIN_DIR, 'queue')
COMMAND_FILE = os.path.join(QUEUE_DIR, 'mavis_command.json')  # Mavis 写，Fusion 读
RESPONSE_FILE = os.path.join(QUEUE_DIR, 'fusion_response.json')  # Fusion 写，Mavis 读
CONFIG_FILE = os.path.join(ADDIN_DIR, 'config.json')


def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def notify_mavis(cfg, message):
    """通过 mavis CLI 发消息给 Mavis"""
    try:
        subprocess.run([
            'mavis', 'communication', 'send',
            '--from', 'fusion-ai-daemon',
            '--to', cfg['mavis_session_id'],
            '--command', 'prompt',
            '--content', message
        ], capture_output=True, text=True, encoding='utf-8', timeout=10)
    except Exception as e:
        print(f'[Mavis AI] 通知 Mavis 失败: {e}')


def execute_command(code, description):
    """执行 Mavis 生成的 Fusion 代码（不调用清空，避免依赖错误）"""
    app = adsk.core.Application.get()

    # 不清空！让 Mavis 代码自己管理（已经自带清空逻辑）

    # 执行 Mavis 代码
    if 'def run(' in code:
        namespace = {'adsk': adsk, 'fusion': adsk.fusion}
        exec(code, namespace)
        run_fn = namespace.get('run')
        if run_fn:
            run_fn(None)
    else:
        exec(code, {'adsk': adsk, 'fusion': adsk.fusion})

    # 切到等轴测视角
    cam = app.activeViewport.camera
    cam.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
    app.activeViewport.camera = cam

    return True


def listener():
    """守护线程：持续监听 Mavis 的指令文件"""
    cfg = load_config()
    last_command_id = None
    fail_count = 0

    while True:
        try:
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
                    cmd = json.load(f)

                command_id = cmd.get('command_id')
                if command_id == last_command_id:
                    time.sleep(2)
                    continue

                code = cmd.get('code', '')
                description = cmd.get('description', '')

                if not code:
                    time.sleep(2)
                    continue

                # 执行
                success, error = False, None
                try:
                    execute_command(code, description)
                    success = True
                except Exception as e:
                    error = traceback.format_exc()

                # 反馈
                resp = {
                    'command_id': command_id,
                    'status': 'success' if success else 'error',
                    'description': description
                }
                if error:
                    resp['error'] = error

                with open(RESPONSE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(resp, f, ensure_ascii=False, indent=2)

                # 通知 Mavis 完成
                msg = f'[Fusion] 完成: {description}\n状态: {"成功" if success else "失败"}'
                if error:
                    msg += f'\n错误: {error[:500]}'
                notify_mavis(cfg, msg)

                # 删命令文件 + 标记
                last_command_id = command_id
                try:
                    os.remove(COMMAND_FILE)
                except:
                    pass

                fail_count = 0
            else:
                time.sleep(2)
        except Exception as e:
            fail_count += 1
            if fail_count > 10:
                print(f'[Mavis AI] listener 多次失败: {e}')
                fail_count = 0
            time.sleep(2)


def run(context):
    """Fusion 脚本入口 - 用户点运行后启动 daemon"""
    ui = adsk.core.Application.get().userInterface
    try:
        cfg = load_config()

        # 确保 queue 目录存在
        os.makedirs(QUEUE_DIR, exist_ok=True)

        # 启动 daemon 线程
        thread = threading.Thread(target=listener, daemon=True)
        thread.start()

        # 通知 Mavis 助手已启动，请求第一个示范零件
        notify_mavis(
            cfg,
            f'[Fusion AI 助手] ✅ 启动成功！\n\n'
            f'守护进程已就绪。请生成第一个示范零件：SG90 舵机固定座（35×22×4 mm 板 + 22×12×2 mm 中央凹槽）。\n\n'
            f'生成代码后写入: {COMMAND_FILE}\n\n'
            f'之后用户每次说"画 XX"，请把代码写入这个文件，我会自动执行。'
        )

        ui.messageBox(
            '✅ Mavis AI 助手已启动！\n\n'
            '你现在直接在 Mavis 对话里说"画 XX"，\n'
            '模型会自动出现在画布上。\n\n'
            '🎁 第一个示范零件（SG90 舵机固定座）正在生成...\n\n'
            '几秒后看画布。'
        )
    except Exception as e:
        ui.messageBox(f'启动失败：{traceback.format_exc()}')