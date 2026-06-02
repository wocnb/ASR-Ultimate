"""FunASR 语音识别引擎"""

import threading
import time
import numpy as np
from typing import Callable, Optional
from dataclasses import dataclass, field


@dataclass
class TranscriptSegment:
    """转录片段"""
    text: str
    timestamp: float  # 相对开始时间的秒数
    duration: float = 0.0


class ASREngine:
    """FunASR 实时语音识别引擎"""

    def __init__(
        self,
        model: str = "paraformer-zh",
        vad_model: str = "fsmn-vad",
        punc_model: str = "ct-punc",
        device: str = "cpu",
        sample_rate: int = 16000,
        segment_duration: int = 600,
    ):
        self.model_name = model
        self.vad_model = vad_model
        self.punc_model = punc_model
        self.device = device
        self.sample_rate = sample_rate
        self.segment_duration = segment_duration

        self._model = None
        self._on_result: Optional[Callable[[TranscriptSegment], None]] = None
        self._buffer: list[np.ndarray] = []
        self._buffer_lock = threading.Lock()
        self._start_time: float = 0
        self._processing = False
        self._init_lock = threading.Lock()

    def on_result(self, callback: Callable[[TranscriptSegment], None]):
        """注册识别结果回调"""
        self._on_result = callback

    def _ensure_model(self):
        """延迟加载模型，如果本地没有则自动下载"""
        if self._model is not None:
            return

        with self._init_lock:
            if self._model is not None:
                return

            from funasr import AutoModel

            self._model = AutoModel(
                model=self.model_name,
                vad_model=self.vad_model,
                punc_model=self.punc_model,
                device=self.device,
                hub="ms",  # 使用 ModelScope 下载模型
            )

    def feed_audio(self, audio_data: np.ndarray):
        """喂入音频数据 (float32, 单声道)"""
        if not self._processing:
            return

        with self._buffer_lock:
            self._buffer.append(audio_data.copy())

    def _process_loop(self):
        """处理线程: 定期从缓冲区取出音频进行识别"""
        self._ensure_model()
        self._start_time = time.time()

        while self._processing:
            # 等待足够的音频数据 (约 2 秒)
            time.sleep(2.0)

            if not self._processing:
                break

            # 取出缓冲区数据
            with self._buffer_lock:
                if not self._buffer:
                    continue
                audio_chunk = np.concatenate(self._buffer)
                self._buffer.clear()

            if len(audio_chunk) < self.sample_rate * 0.5:
                # 太短，放回缓冲区
                with self._buffer_lock:
                    self._buffer.insert(0, audio_chunk)
                continue

            # 执行识别
            try:
                # FunASR 需要 int16 或 float32，确保格式正确
                if audio_chunk.dtype != np.float32:
                    audio_chunk = audio_chunk.astype(np.float32)

                result = self._model.generate(
                    input=audio_chunk,
                    batch_size_s=300,
                )

                if result and len(result) > 0:
                    text = ""
                    for item in result:
                        if "text" in item:
                            text += item["text"]

                    if text.strip():
                        segment = TranscriptSegment(
                            text=text.strip(),
                            timestamp=time.time() - self._start_time,
                        )
                        if self._on_result:
                            self._on_result(segment)

            except Exception as e:
                print(f"ASR 识别错误: {e}")

    def start(self):
        """开始识别"""
        if self._processing:
            return

        self._processing = True
        self._buffer.clear()
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()

    def stop(self) -> list[TranscriptSegment]:
        """停止识别，返回所有已识别的文本"""
        self._processing = False

        # 处理剩余缓冲区
        with self._buffer_lock:
            remaining = self._buffer.copy()
            self._buffer.clear()

        if remaining and self._model:
            try:
                audio_chunk = np.concatenate(remaining)
                if len(audio_chunk) >= self.sample_rate * 0.3:
                    result = self._model.generate(
                        input=audio_chunk.astype(np.float32),
                        batch_size_s=300,
                    )
                    if result and len(result) > 0:
                        text = ""
                        for item in result:
                            if "text" in item:
                                text += item["text"]
                        if text.strip() and self._on_result:
                            self._on_result(
                                TranscriptSegment(
                                    text=text.strip(),
                                    timestamp=time.time() - self._start_time,
                                )
                            )
            except Exception as e:
                print(f"ASR 最终处理错误: {e}")

        if hasattr(self, "_thread"):
            self._thread.join(timeout=3.0)

    def transcribe_audio(
        self,
        audio_data: np.ndarray,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> list[TranscriptSegment]:
        """
        离线转录音频数据，每 segment_duration 秒切分一段处理

        Args:
            audio_data: 完整音频数据 (float32, 单声道)
            on_progress: 进度回调 (当前段索引, 总段数, 当前段转录文本)

        Returns:
            所有转录片段列表
        """
        self._ensure_model()

        total_samples = len(audio_data)
        samples_per_segment = int(self.sample_rate * self.segment_duration)

        # 计算总段数
        num_segments = max(1, (total_samples + samples_per_segment - 1) // samples_per_segment)

        all_segments: list[TranscriptSegment] = []
        current_time = 0.0

        for i in range(num_segments):
            start_idx = i * samples_per_segment
            end_idx = min((i + 1) * samples_per_segment, total_samples)
            segment_audio = audio_data[start_idx:end_idx]

            # 跳过太短的片段
            if len(segment_audio) < self.sample_rate * 0.5:
                continue

            try:
                # 确保格式正确
                if segment_audio.dtype != np.float32:
                    segment_audio = segment_audio.astype(np.float32)

                result = self._model.generate(
                    input=segment_audio,
                    batch_size_s=300,
                )

                segment_text = ""
                if result and len(result) > 0:
                    for item in result:
                        if "text" in item:
                            segment_text += item["text"]

                if segment_text.strip():
                    segment = TranscriptSegment(
                        text=segment_text.strip(),
                        timestamp=current_time,
                        duration=len(segment_audio) / self.sample_rate,
                    )
                    all_segments.append(segment)

                # 回调进度
                if on_progress:
                    on_progress(i + 1, num_segments, segment_text.strip())

            except Exception as e:
                print(f"ASR 离线处理错误 (段 {i+1}/{num_segments}): {e}")

            current_time += len(segment_audio) / self.sample_rate

        return all_segments

    @property
    def is_running(self) -> bool:
        return self._processing
