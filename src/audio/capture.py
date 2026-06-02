"""Windows 系统音频捕获模块 (WASAPI loopback)"""

import threading
import numpy as np
from typing import Callable, Optional

try:
    import pyaudiowpatch as pyaudio
except ImportError:
    import pyaudio


class AudioCapture:
    """捕获 Windows 系统音频输出 (loopback)"""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 9600,
        silence_threshold: float = 0.01,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.silence_threshold = silence_threshold

        self._pa: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._on_audio: Optional[Callable[[np.ndarray], None]] = None
        self._on_volume: Optional[Callable[[float], None]] = None

        # 录制缓冲区
        self._record_buffer: list[np.ndarray] = []
        self._record_lock = threading.Lock()

    def on_audio(self, callback: Callable[[np.ndarray], None]):
        """注册音频数据回调 (numpy float32 array)"""
        self._on_audio = callback

    def on_volume(self, callback: Callable[[float], None]):
        """注册音量回调 (0.0 ~ 1.0)"""
        self._on_volume = callback

    def clear_record_buffer(self):
        """清空录制缓冲区"""
        with self._record_lock:
            self._record_buffer.clear()

    def get_recorded_audio(self) -> Optional[np.ndarray]:
        """获取录制的完整音频数据"""
        with self._record_lock:
            if not self._record_buffer:
                return None
            return np.concatenate(self._record_buffer)

    def _find_loopback_device(self) -> dict:
        """查找 WASAPI loopback 设备 (系统默认输出的 loopback)"""
        self._pa = pyaudio.PyAudio()

        try:
            wasapi_info = self._pa.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            raise RuntimeError("当前系统不支持 WASAPI")

        default_speakers = self._pa.get_device_info_by_index(
            wasapi_info["defaultOutputDevice"]
        )

        # 查找对应的 loopback 设备
        for i in range(self._pa.get_device_count()):
            dev = self._pa.get_device_info_by_index(i)
            if dev["name"].startswith(default_speakers["name"]) and dev["isLoopbackDevice"]:
                return dev

        raise RuntimeError(
            f"未找到 loopback 设备。默认输出: {default_speakers['name']}\n"
            "请确保有音频输出设备正在播放。"
        )

    def _audio_thread(self, device_info: dict):
        """音频采集线程"""
        try:
            self._stream = self._pa.open(
                format=pyaudio.paFloat32,
                channels=int(device_info["maxInputChannels"]),
                rate=int(device_info["defaultSampleRate"]),
                frames_per_buffer=self.chunk_size,
                input=True,
                input_device_index=device_info["index"],
                stream_callback=self._stream_callback,
            )
            self._stream.start_stream()

            while self._running:
                threading.Event().wait(0.1)

        except Exception as e:
            print(f"音频采集错误: {e}")
        finally:
            self._cleanup_stream()

    def _stream_callback(
        self, in_data: bytes, frame_count: int, time_info, status
    ) -> tuple:
        """PyAudio 流回调"""
        if not self._running:
            return (None, pyaudio.paComplete)

        # 转换为 numpy 数组
        audio_data = np.frombuffer(in_data, dtype=np.float32)

        # 多声道转单声道
        channels = int(self._stream._channels) if hasattr(self._stream, '_channels') else self.channels
        if channels > 1:
            audio_data = audio_data.reshape(-1, channels).mean(axis=1)

        # 重采样到目标采样率 (如果需要)
        # pyaudiowpatch 会自动处理，这里简化处理

        # 计算音量 (RMS)
        if self._on_volume:
            rms = float(np.sqrt(np.mean(audio_data ** 2)))
            self._on_volume(min(rms, 1.0))

        # 保存到录制缓冲区
        with self._record_lock:
            self._record_buffer.append(audio_data.copy())

        # 回调音频数据
        if self._on_audio:
            self._on_audio(audio_data)

        return (None, pyaudio.paContinue)

    def start(self):
        """开始捕获"""
        if self._running:
            return

        # 清空录制缓冲区
        self.clear_record_buffer()

        device_info = self._find_loopback_device()
        self._running = True
        self._thread = threading.Thread(
            target=self._audio_thread, args=(device_info,), daemon=True
        )
        self._thread.start()

    def stop(self):
        """停止捕获"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        self._cleanup()

    def _cleanup_stream(self):
        """清理流资源"""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _cleanup(self):
        """清理所有资源"""
        self._cleanup_stream()
        if self._pa:
            self._pa.terminate()
            self._pa = None

    @property
    def is_running(self) -> bool:
        return self._running

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
