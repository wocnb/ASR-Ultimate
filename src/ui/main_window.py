"""PySide6 主界面 - 简洁风格设计"""

import threading
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QProgressBar,
    QStatusBar, QMessageBox, QSystemTrayIcon,
    QMenu, QApplication, QGroupBox, QLineEdit, QComboBox,
    QFormLayout, QFrame, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QAction

from src.audio.capture import AudioCapture
from src.asr.engine import ASREngine, TranscriptSegment
from src.ai.analyzer import AIAnalyzer


# 硬编码配置
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "channels": 1,
    "chunk_size": 9600,
    "silence_threshold": 0.01,
}

ASR_CONFIG = {
    "model": "paraformer-zh",
    "vad_model": "fsmn-vad",
    "punc_model": "ct-punc",
    "segment_duration": 600,
}

DEFAULT_AI_CONFIG = {
    "api_key": "",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
}

# 配色方案
COLORS = {
    "bg_main": "#faf8f5",
    "bg_sidebar": "#2d2a26",
    "bg_card": "#3a3632",
    "bg_input": "#4a4642",
    "accent": "#ff7b5c",
    "accent_hover": "#ff6b4a",
    "accent_light": "#3d2f2a",
    "text_primary": "#ffffff",
    "text_secondary": "#b5b0aa",
    "text_muted": "#8a8580",
    "border": "#4a4642",
}

# 样式表
STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS["bg_main"]};
}}

/* 侧边栏 */
QWidget#sidebar {{
    background-color: {COLORS["bg_sidebar"]};
    border-right: 1px solid {COLORS["border"]};
}}

QLabel#logo {{
    color: {COLORS["accent"]};
    font-size: 32px;
    font-weight: bold;
    padding: 32px 24px 4px 24px;
}}

QLabel#logo_sub {{
    color: {COLORS["text_muted"]};
    font-size: 10px;
    letter-spacing: 4px;
    padding: 0 24px 28px 24px;
}}

QGroupBox#config_group {{
    color: {COLORS["accent"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    margin-top: 16px;
    padding-top: 20px;
    background-color: {COLORS["bg_card"]};
}}

QGroupBox#config_group::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: {COLORS["accent"]};
}}

QLineEdit#light_input {{
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 12px;
    font-size: 13px;
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
}}
QLineEdit#light_input:focus {{
    border-color: {COLORS["accent"]};
    background-color: {COLORS["bg_card"]};
}}

QComboBox#light_combo {{
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 12px;
    font-size: 13px;
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
}}
QComboBox#light_combo:focus {{
    border-color: {COLORS["accent"]};
}}
QComboBox#light_combo::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox#light_combo::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS["accent"]};
    margin-right: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    selection-background-color: {COLORS["accent_light"]};
}}

QLabel#label {{
    color: {COLORS["text_secondary"]};
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

QLabel#status_active {{
    color: {COLORS["accent"]};
    font-size: 14px;
    font-weight: bold;
    padding: 8px;
    background-color: {COLORS["accent_light"]};
    border-radius: 8px;
}}

QLabel#status_idle {{
    color: {COLORS["text_muted"]};
    font-size: 14px;
    padding: 8px;
}}

/* 主内容区 */
QWidget#main_area {{
    background-color: {COLORS["bg_main"]};
}}

QLabel#result_title {{
    color: #2d2a26;
    font-size: 18px;
    font-weight: bold;
    padding: 24px 32px 8px 32px;
}}

QTextEdit#result_display {{
    border: 1px solid #e8e3dd;
    border-radius: 12px;
    padding: 20px;
    font-size: 14px;
    background-color: #ffffff;
    color: #2d2a26;
    margin: 8px 32px 24px 32px;
}}

/* 底部控制栏 */
QWidget#control_bar {{
    background-color: {COLORS["bg_sidebar"]};
    border-top: 1px solid {COLORS["border"]};
}}

QPushButton#btn_start {{
    background-color: {COLORS["accent"]};
    color: white;
    border: none;
    border-radius: 10px;
    padding: 14px 28px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#btn_start:hover {{
    background-color: {COLORS["accent_hover"]};
}}
QPushButton#btn_start:disabled {{
    background-color: {COLORS["border"]};
    color: {COLORS["text_muted"]};
}}

QPushButton#btn_stop {{
    background-color: transparent;
    color: {COLORS["accent"]};
    border: 2px solid {COLORS["accent"]};
    border-radius: 10px;
    padding: 14px 28px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#btn_stop:hover {{
    background-color: {COLORS["accent_light"]};
}}
QPushButton#btn_stop:disabled {{
    color: {COLORS["text_muted"]};
    border-color: {COLORS["border"]};
}}

QPushButton#btn_clear {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["text_secondary"]};
    border-radius: 10px;
    padding: 14px 28px;
    font-size: 14px;
}}
QPushButton#btn_clear:hover {{
    border-color: {COLORS["text_primary"]};
    color: {COLORS["text_primary"]};
}}

/* 音量条 */
QProgressBar#volume_bar {{
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    text-align: center;
    background-color: {COLORS["bg_input"]};
}}
QProgressBar#volume_bar::chunk {{
    background-color: {COLORS["accent"]};
    border-radius: 5px;
}}

/* 状态栏 */
QStatusBar {{
    background-color: {COLORS["bg_sidebar"]};
    border-top: 1px solid {COLORS["border"]};
    color: {COLORS["text_secondary"]};
    font-size: 11px;
}}
"""


class MainWindow(QMainWindow):
    """ASR-Ultimate 主窗口"""

    # 跨线程信号
    volume_update = Signal(float)
    ai_result_ready = Signal(str)
    ai_token_ready = Signal(str)
    status_update = Signal(str)
    asr_progress = Signal(int, int, str)

    def __init__(self):
        super().__init__()
        self._transcripts: list[TranscriptSegment] = []
        self._is_recording = False
        self._current_ai_text = ""

        # 初始化组件
        self._init_audio()
        self._init_ui()
        self._init_tray()
        self._connect_signals()

        # ASR 和 AI 延迟初始化
        self._asr: ASREngine | None = None
        self._ai: AIAnalyzer | None = None

    def _init_audio(self):
        self._audio = AudioCapture(
            sample_rate=AUDIO_CONFIG["sample_rate"],
            channels=AUDIO_CONFIG["channels"],
            chunk_size=AUDIO_CONFIG["chunk_size"],
            silence_threshold=AUDIO_CONFIG["silence_threshold"],
        )
        self._audio.on_audio(lambda x: None)
        self._audio.on_volume(self._on_volume_data)

    def _init_ui(self):
        self.setWindowTitle("ASR-Ultimate")
        self.resize(1280, 860)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(STYLESHEET)

        # 主布局
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 左侧边栏 ===
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 32, 0, 24)

        logo = QLabel("ASR")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo)

        logo_sub = QLabel("U L T I M A T E")
        logo_sub.setObjectName("logo_sub")
        logo_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_sub)

        sidebar_layout.addWidget(logo_container)

        # 分隔线
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px; margin: 0 24px;")
        sidebar_layout.addWidget(line1)

        # 配置区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        config_container = QWidget()
        config_layout = QVBoxLayout(config_container)
        config_layout.setContentsMargins(20, 20, 20, 20)
        config_layout.setSpacing(12)

        # AI 配置组
        ai_group = QGroupBox("AI CONFIG")
        ai_group.setObjectName("config_group")
        ai_form = QFormLayout(ai_group)
        ai_form.setSpacing(12)
        ai_form.setContentsMargins(16, 24, 16, 16)

        lbl_key = QLabel("API KEY")
        lbl_key.setObjectName("label")
        self._inp_api_key = QLineEdit()
        self._inp_api_key.setObjectName("light_input")
        self._inp_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._inp_api_key.setPlaceholderText("sk-...")
        ai_form.addRow(lbl_key, self._inp_api_key)

        lbl_url = QLabel("BASE URL")
        lbl_url.setObjectName("label")
        self._inp_base_url = QLineEdit()
        self._inp_base_url.setObjectName("light_input")
        self._inp_base_url.setText(DEFAULT_AI_CONFIG["base_url"])
        ai_form.addRow(lbl_url, self._inp_base_url)

        lbl_model = QLabel("MODEL")
        lbl_model.setObjectName("label")
        self._inp_model = QLineEdit()
        self._inp_model.setObjectName("light_input")
        self._inp_model.setText(DEFAULT_AI_CONFIG["model"])
        ai_form.addRow(lbl_model, self._inp_model)

        config_layout.addWidget(ai_group)

        # ASR 配置组
        asr_group = QGroupBox("ASR ENGINE")
        asr_group.setObjectName("config_group")
        asr_layout = QVBoxLayout(asr_group)
        asr_layout.setContentsMargins(16, 24, 16, 16)

        device_row = QHBoxLayout()
        lbl_device = QLabel("DEVICE")
        lbl_device.setObjectName("label")
        self._combo_device = QComboBox()
        self._combo_device.setObjectName("light_combo")
        self._combo_device.addItems(["cpu", "cuda"])
        device_row.addWidget(lbl_device)
        device_row.addWidget(self._combo_device)
        asr_layout.addLayout(device_row)

        config_layout.addWidget(asr_group)

        # 状态组
        status_group = QGroupBox("STATUS")
        status_group.setObjectName("config_group")
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(16, 24, 16, 16)

        self._lbl_status_sidebar = QLabel("IDLE")
        self._lbl_status_sidebar.setObjectName("status_idle")
        self._lbl_status_sidebar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self._lbl_status_sidebar)

        self._lbl_time_sidebar = QLabel("00:00")
        self._lbl_time_sidebar.setObjectName("label")
        self._lbl_time_sidebar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self._lbl_time_sidebar)

        config_layout.addWidget(status_group)

        config_layout.addStretch()
        scroll.setWidget(config_container)
        sidebar_layout.addWidget(scroll)

        main_layout.addWidget(sidebar)

        # === 右侧主区域 ===
        main_area = QWidget()
        main_area.setObjectName("main_area")
        main_area_layout = QVBoxLayout(main_area)
        main_area_layout.setContentsMargins(0, 0, 0, 0)
        main_area_layout.setSpacing(0)

        # 标题
        result_title = QLabel("AI Analysis Result")
        result_title.setObjectName("result_title")
        main_area_layout.addWidget(result_title)

        # 结果显示区域
        self._txt_result = QTextEdit()
        self._txt_result.setObjectName("result_display")
        self._txt_result.setReadOnly(True)
        self._txt_result.setPlaceholderText("录制并分析后，结果将显示在这里...")
        main_area_layout.addWidget(self._txt_result)

        # 底部控制栏
        control_bar = QWidget()
        control_bar.setObjectName("control_bar")
        control_layout = QVBoxLayout(control_bar)
        control_layout.setContentsMargins(32, 20, 32, 20)
        control_layout.setSpacing(16)

        # 音量条
        vol_layout = QHBoxLayout()
        vol_layout.setSpacing(12)

        lbl_vol = QLabel("VOL")
        lbl_vol.setObjectName("label")
        lbl_vol.setFixedWidth(30)
        vol_layout.addWidget(lbl_vol)

        self._volume_bar = QProgressBar()
        self._volume_bar.setObjectName("volume_bar")
        self._volume_bar.setRange(0, 100)
        self._volume_bar.setValue(0)
        self._volume_bar.setMaximumHeight(8)
        vol_layout.addWidget(self._volume_bar)

        self._lbl_volume = QLabel("0%")
        self._lbl_volume.setObjectName("label")
        self._lbl_volume.setFixedWidth(40)
        vol_layout.addWidget(self._lbl_volume)

        control_layout.addLayout(vol_layout)

        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)

        self._btn_start = QPushButton("START REC")
        self._btn_start.setObjectName("btn_start")

        self._btn_stop = QPushButton("STOP & ANALYZE")
        self._btn_stop.setObjectName("btn_stop")
        self._btn_stop.setEnabled(False)

        self._btn_clear = QPushButton("CLEAR")
        self._btn_clear.setObjectName("btn_clear")

        btn_layout.addWidget(self._btn_start)
        btn_layout.addWidget(self._btn_stop)
        btn_layout.addWidget(self._btn_clear)
        control_layout.addLayout(btn_layout)

        main_area_layout.addWidget(control_bar)

        main_layout.addWidget(main_area)

        # 状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._lbl_status = QLabel("SYSTEM READY")
        self._status_bar.addWidget(self._lbl_status)

        # 计时器
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_time)
        self._start_timestamp: float = 0

    def _init_tray(self):
        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("ASR-Ultimate")

        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.showNormal)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _connect_signals(self):
        self._btn_start.clicked.connect(self._start_recording)
        self._btn_stop.clicked.connect(self._stop_recording)
        self._btn_clear.clicked.connect(self._clear_all)
        self.volume_update.connect(self._update_volume)
        self.ai_result_ready.connect(self._show_ai_result)
        self.ai_token_ready.connect(self._append_ai_token)
        self.status_update.connect(self._on_status_update)
        self.asr_progress.connect(self._on_asr_progress)

    def _init_asr_if_needed(self):
        if self._asr is None:
            device = self._combo_device.currentText()
            self._asr = ASREngine(
                model=ASR_CONFIG["model"],
                vad_model=ASR_CONFIG["vad_model"],
                punc_model=ASR_CONFIG["punc_model"],
                device=device,
                sample_rate=AUDIO_CONFIG["sample_rate"],
                segment_duration=ASR_CONFIG["segment_duration"],
            )

    def _init_ai_if_needed(self):
        if self._ai is None:
            api_key = self._inp_api_key.text().strip()
            base_url = self._inp_base_url.text().strip() or DEFAULT_AI_CONFIG["base_url"]
            model = self._inp_model.text().strip() or DEFAULT_AI_CONFIG["model"]

            if not api_key:
                raise ValueError("Please enter API Key")

            self._ai = AIAnalyzer(
                api_key=api_key,
                base_url=base_url,
                model=model,
            )

    # --- 音频回调 ---
    def _on_volume_data(self, volume: float):
        self.volume_update.emit(volume)

    # --- 槽函数 ---
    @Slot(float)
    def _update_volume(self, volume: float):
        pct = int(min(volume * 500, 100))
        self._volume_bar.setValue(pct)
        self._lbl_volume.setText(f"{pct}%")

    @Slot(str)
    def _show_ai_result(self, text: str):
        self._txt_result.setPlainText(text)
        self._current_ai_text = ""

    @Slot(str)
    def _append_ai_token(self, token: str):
        self._current_ai_text += token
        self._txt_result.setPlainText(self._current_ai_text)
        # 滚动到底部
        cursor = self._txt_result.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._txt_result.setTextCursor(cursor)

    @Slot(str)
    def _on_status_update(self, status: str):
        self._lbl_status.setText(status.upper())
        self._lbl_status_sidebar.setText(status.upper())

        if "录制" in status or "ASR" in status or "分析" in status:
            self._lbl_status_sidebar.setObjectName("status_active")
        else:
            self._lbl_status_sidebar.setObjectName("status_idle")
        self._lbl_status_sidebar.style().unpolish(self._lbl_status_sidebar)
        self._lbl_status_sidebar.style().polish(self._lbl_status_sidebar)

    @Slot(int, int, str)
    def _on_asr_progress(self, current: int, total: int, text: str):
        self._lbl_status.setText(f"ASR PROCESSING: {current}/{total}")
        self._lbl_status_sidebar.setText(f"ASR: {current}/{total}")

    def _update_time(self):
        if self._start_timestamp:
            elapsed = int(datetime.now().timestamp() - self._start_timestamp)
            mins, secs = divmod(elapsed, 60)
            self._lbl_time_sidebar.setText(f"{mins:02d}:{secs:02d}")

    # --- 控制逻辑 ---
    def _start_recording(self):
        try:
            self._transcripts.clear()
            self._txt_result.clear()
            self._current_ai_text = ""

            self._audio.start()

            self._is_recording = True
            self._start_timestamp = datetime.now().timestamp()
            self._timer.start(1000)

            self._btn_start.setEnabled(False)
            self._btn_stop.setEnabled(True)
            self._combo_device.setEnabled(False)
            self.status_update.emit("Recording system audio...")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start audio capture:\n{e}")

    def _stop_recording(self):
        self._is_recording = False
        self._timer.stop()

        self._audio.stop()

        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._combo_device.setEnabled(True)

        self.status_update.emit("Processing audio...")

        recorded_audio = self._audio.get_recorded_audio()

        if recorded_audio is None or len(recorded_audio) == 0:
            self._txt_result.setPlainText("No audio data recorded.")
            self.status_update.emit("Idle")
            return

        threading.Thread(
            target=self._run_offline_processing, args=(recorded_audio,), daemon=True
        ).start()

    def _run_offline_processing(self, audio_data):
        try:
            # ASR
            self._init_asr_if_needed()
            self.status_update.emit("ASR transcribing...")

            def on_asr_progress(current, total, text):
                self.asr_progress.emit(current, total, text)

            segments = self._asr.transcribe_audio(audio_data, on_progress=on_asr_progress)

            for seg in segments:
                self._transcripts.append(seg)

            full_text = "\n".join(seg.text for seg in self._transcripts)

            if not full_text.strip():
                self.ai_result_ready.emit("No valid speech detected.")
                self.status_update.emit("Idle")
                return

            # AI 分析
            self._init_ai_if_needed()
            self.status_update.emit("AI analyzing...")
            for token in self._ai.analyze_stream(full_text):
                self.ai_token_ready.emit(token)
            self.status_update.emit("Analysis complete")

        except ValueError as e:
            self.ai_result_ready.emit(f"Config error: {e}")
            self.status_update.emit("Config error")
        except Exception as e:
            self.ai_result_ready.emit(f"Error: {e}")
            self.status_update.emit("Error")

    def _clear_all(self):
        self._transcripts.clear()
        self._txt_result.clear()
        self._current_ai_text = ""
        self._lbl_time_sidebar.setText("00:00")
        self._start_timestamp = 0
        self.status_update.emit("Cleared")

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showNormal()
            self.activateWindow()

    def closeEvent(self, event):
        if self._is_recording:
            self._audio.stop()
        self._tray.hide()
        event.accept()

    def _cleanup_and_exit(self, event):
        if self._is_recording:
            self._audio.stop()
        self._tray.hide()
        event.accept()
