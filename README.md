# ASR-Ultimate

<div align="center">

**Windows 系统音频录制 + ASR 转录 + AI 分析工具**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-6.7.0-green?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

</div>

---

## 功能特性

- **系统音频录制**: 通过 WASAPI Loopback 捕获 Windows 系统音频
- **离线 ASR 转录**: 使用 FunASR (paraformer-zh) 进行语音识别，支持长音频分段处理
- **AI 分析**: 调用 OpenAI 兼容 API 对转录文本进行智能分析
- **赛博朋克风格 UI**: 现代化深色主题界面，流式输出显示

## 工作流程

```
开始录制 → 持续录制系统音频 → 停止录制 → ASR 离线处理（每10分钟切分）→ AI 分析 → 显示结果
```

---

## 环境要求

- **操作系统**: Windows 10/11
- **Python**: 3.10 或更高版本
- **GPU（可选）**: NVIDIA GPU + CUDA，用于加速 ASR 推理

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/ASR-Ultimate.git
cd ASR-Ultimate
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 安装 PyTorch (CPU 版本)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# 安装其他依赖
pip install -r requirements.txt
```

> **GPU 用户**: 如果需要 CUDA 加速，请安装对应版本的 PyTorch：
> ```bash
> pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
> ```

### 4. 运行程序

```bash
python main.py
```

---

## 使用说明

### 基本操作

1. **配置 AI**
   - 在左侧边栏输入 API Key
   - 设置 Base URL（默认: `https://api.openai.com/v1`）
   - 设置 Model（默认: `gpt-4o-mini`）

2. **选择 ASR 设备**
   - `cpu`: 使用 CPU 进行推理（默认，兼容性好）
   - `cuda`: 使用 GPU 进行推理（需要 NVIDIA GPU + CUDA）

3. **开始录制**
   - 点击 `START REC` 按钮
   - 程序将开始录制系统音频
   - 底部音量条显示实时音量

4. **停止并分析**
   - 点击 `STOP & ANALYZE` 按钮
   - 程序自动进行 ASR 转录
   - 转录完成后自动进行 AI 分析
   - 结果以聊天气泡形式显示

5. **清空记录**
   - 点击 `CLEAR` 按钮清空所有聊天记录

### 注意事项

- 首次运行时，FunASR 会自动下载模型（约 1GB），请耐心等待
- 录制期间请确保系统有音频输出（如播放音乐、视频等）
- 长时间录制会占用较多内存，建议单次录制不超过 1 小时

---

## 打包为 EXE

### 方法一：使用打包脚本

```bash
python build.py
```

### 方法二：手动打包

```bash
pyinstaller --clean --noconfirm build.spec
```

### 打包结果

- 输出目录: `dist/`
- 生成文件: `dist/ASR-Ultimate.exe`
- 单文件 EXE，无需 Python 环境即可运行

### 打包注意事项

1. 打包后的 EXE 文件较大（包含 Python 运行时和依赖库）
2. 首次运行时仍需下载 ASR 模型
3. 如需 CUDA 支持，请在有 GPU 的机器上打包

---

## 项目结构

```
ASR-Ultimate/
├── main.py                 # 程序入口
├── requirements.txt        # Python 依赖
├── build.py                # 打包脚本
├── build.spec              # PyInstaller 配置
├── CLAUDE.md               # 项目文档
├── README.md               # 本文件
└── src/
    ├── audio/
    │   └── capture.py      # 音频捕获模块 (WASAPI Loopback)
    ├── asr/
    │   └── engine.py       # ASR 引擎 (FunASR)
    ├── ai/
    │   └── analyzer.py     # AI 分析模块 (OpenAI API)
    ├── ui/
    │   └── main_window.py  # 主界面 (PySide6)
    └── utils/
        └── __init__.py
```

---

## 配置说明

### AI 配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| API Key | OpenAI 兼容 API 的密钥 | 无 |
| Base URL | API 端点地址 | `https://api.openai.com/v1` |
| Model | 使用的模型名称 | `gpt-4o-mini` |

### ASR 配置（硬编码）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| model | FunASR 模型 | `paraformer-zh` |
| vad_model | VAD 模型 | `fsmn-vad` |
| punc_model | 标点模型 | `ct-punc` |
| segment_duration | 分段时长（秒） | `600`（10分钟） |

### 音频配置（硬编码）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| sample_rate | 采样率 | `16000` |
| channels | 声道数 | `1` |
| chunk_size | 每次读取帧数 | `9600` |

---

## 常见问题

### Q: 提示 "No module named 'torchaudio'"

```bash
pip install torchaudio
```

### Q: PySide6 导入失败

```bash
pip install PySide6==6.7.0
```

### Q: 找不到 Loopback 设备

请确保：
1. 系统有音频输出设备
2. 有音频正在播放
3. 使用的是 Windows 10/11

### Q: ASR 模型下载失败

可以手动下载模型：
```python
from funasr import AutoModel
model = AutoModel(model="paraformer-zh", hub="ms")
```

### Q: CUDA 内存不足

- 减小 `segment_duration` 配置值
- 或切换到 CPU 模式

---

## 技术栈

- **音频捕获**: [pyaudiowpatch](https://github.com/s0d3s/pyaudiowpatch) (WASAPI Loopback)
- **ASR 引擎**: [FunASR](https://github.com/modelscope/FunASR) (paraformer-zh)
- **AI 分析**: [OpenAI Python SDK](https://github.com/openai/openai-python)
- **UI 框架**: [PySide6](https://wiki.qt.io/Qt_for_Python)

---

## 许可证

MIT License

---

## 致谢

- [FunASR](https://github.com/modelscope/FunASR) - 语音识别引擎
- [pyaudiowpatch](https://github.com/s0d3s/pyaudiowpatch) - Windows 音频捕获
- [Qt for Python](https://wiki.qt.io/Qt_for_Python) - UI 框架
