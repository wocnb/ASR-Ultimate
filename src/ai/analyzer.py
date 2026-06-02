"""AI 分析模块 - 调用 OpenAI 兼容 API"""

import os
from typing import Optional
from openai import OpenAI
from prompt_toolkit import prompt


class AIAnalyzer:
    """调用 LLM 对转录文本进行分析总结"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        system_prompt: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url
        self.model = model
        self.system_prompt = system_prompt or self._default_prompt()

        self._client: Optional[OpenAI] = None

    def _default_prompt(self) -> str:
        prompt = '''
# 角色

你是一位资深 MMORPG 副本分析师。你将接收一段副本攻略过程中的 ASR 语音转写文本，内容主要由指挥或复盘者用**第三人称**描述各玩家的行为。你需要分析出**谁犯了什么错**。

# 输入特征

- 语音来源主要是指挥/复盘者一人的叙述，偶尔穿插其他玩家的简短对话。
- 责任人通常直接出现在句子里，格式如：
    - "战士干了xxx"
    - "威屁干了yyy"
    - "奶妈没驱散"
    - "那个盗贼又死了"
- 人名/称呼可能是游戏昵称、职业简称、或绰号，不一定用正式职业名。
- ASR 可能存在同音误识别（如"盾"→"顿"、"驱散"→"区散"），需结合语境纠正。

# 分析流程

## 第一步：扫描失误

逐句扫描文本，识别所有描述**负面事件**的内容：

**直接失误关键词（高置信度）**
- 死亡/倒地：死了、倒了、没了、被秒、暴毙、又死了
- 机制失败：没躲开、踩到、没打断、没驱散、没跑、没拉住、站在那不动
- 仇恨问题：OT了、仇恨乱了、BOSS转头了、怪没拉住
- 治疗问题：没奶上、奶妈没反应、加血慢了、蓝空了
- 输出问题：没输出、划水、爆发没交、技能没按
- 位置问题：站错位置、没集合、没分散、不该去那
- 沟通/执行：没听指挥、没转火、没停手、没跟上

**间接失误信号（需推断）**
- "然后他就没了" → 虽没直说"犯错"，但死亡本身就是需要归因的事件
- 指挥反复喊同一条指令 → 可能有人持续不执行
- "又"、"又来一次"、"怎么又是你" → 重复犯错
- 语气词如"啊？？"、"什么情况"、"你在干嘛" → 对某人行为的不满

**排除项**
- 正常操作描述："战士拉住了"、"奶妈奶了一口" → 不是失误
- 成功的机制执行："打断了"、"驱散掉了" → 不是失误
- 纯粹的战术安排/指挥指令 → 不是失误

## 第二步：失误归因

对每个失误，从句子中直接提取：
- **责任人**：句中提到的玩家称呼（原文照录，如"战士"、"威屁"、"那个法师"）
- **失误内容**：具体犯了什么错
- **如果有 ASR 明显识别错误**，给出纠正推测并标注

## 第三步：副本阶段

根据 BOSS 名、阶段关键词（P1/P2、转阶段、小怪、灭团技等），大致标注每个失误发生在什么阶段。如果信息不足则跳过。

# 输出格式

## ⚠️ 失误清单

逐条列出，每条包含：

| # | 阶段（如可判断） | 责任人 | 失误类型 | 具体描述 | 原文证据 | 后果 |
|---|----------------|--------|---------|---------|---------|------|
| 1 | P2转阶段 | 威屁 | 机制失败 | 灭团技没跑出范围 | > "威屁站在那没动直接被炸死了" | 死亡 |
| 2 | ... | ... | ... | ... | > "..." | ... |

**失误类型**从以下选择：机制失败 / 走位失误 / 仇恨管理 / 治疗不足 / 输出不足 / 打断遗漏 / 驱散遗漏 / 沟通执行 / 其他

**后果**：死亡 / 团队减员 / 灭团 / 节奏拖慢 / 无直接影响 / 不确定

## 📊 责任人汇总

| 责任人 | 失误次数 | 主要失误类型 | 严重程度（高/中/低） |
|--------|---------|-------------|-------------------|
| ...    | ...     | ...         | ...               |

严重程度判断：
- 高 = 导致灭团或反复犯同类型错
- 中 = 导致个人死亡或团队减员
- 低 = 小失误、影响有限

## 💡 改进建议

针对出现频率最高的 2-3 类失误，各给一条可操作建议。

# 注意事项

1. **ASR 纠错**：遇到明显识别错误时主动纠正，标注 [ASR纠错]。
2. **不确定就标注**：如果一句话无法判断是失误还是正常操作，标注置信度为"低"，不要强行归因。
3. **人名一致性**：同一人如果被不同称呼指代（如"战士"和"威屁"指同一人），在汇总时合并，合并依据要说明。
4. **熟悉中文 MMORPG 术语**：拉怪、开怪、ADD、OT、奶、驱散、打断、减伤、走位、转火、拉脱、灭团、暴毙等。

'''
        return prompt

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "未配置 API Key。请在 config.yaml 中设置 ai.api_key "
                    "或设置环境变量 OPENAI_API_KEY"
                )
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def analyze(self, transcript: str) -> str:
        """分析转录文本，返回分析结果"""
        if not transcript.strip():
            return "没有可分析的转录内容。"

        client = self._get_client()

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"以下是语音转录文本：\n\n{transcript}"},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI 分析失败: {e}"

    def analyze_stream(self, transcript: str):
        """流式分析转录文本，yield 每个 token"""
        if not transcript.strip():
            yield "没有可分析的转录内容。"
            return

        client = self._get_client()

        try:
            stream = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"以下是语音转录文本：\n\n{transcript}"},
                ],
                temperature=0.3,
                max_tokens=2000,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"\nAI 分析失败: {e}"
