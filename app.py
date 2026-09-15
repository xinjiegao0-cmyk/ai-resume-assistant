import streamlit as st
import os
import re
import json
from pathlib import Path
from collections import Counter
from html import escape
from dotenv import load_dotenv

# ============================================================
# 基础配置
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="AI Resume Assistant",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
HISTORY_FILE = BASE_DIR / "analysis_history.json"

BASE_URL = "https://api.moonshot.cn/v1"
MODEL = "kimi-k2.6"
APP_VERSION = "V10.0"


def get_api_key():
    """Use a local .env during development and Streamlit secrets in Cloud."""
    local_key = os.getenv("MOONSHOT_API_KEY")
    if local_key:
        return local_key

    try:
        return st.secrets.get("MOONSHOT_API_KEY", "")
    except Exception:
        return ""


API_KEY = get_api_key()


# ============================================================
# Session State
# ============================================================

defaults = {
    "page": "home",
    "resume_text": "",
    "job_text": "",
    "analysis_result": None,
    "optimized_resume": "",
    "uploaded_filename": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# Liquid Glass UI
# ============================================================

st.html(
    """
<style>

/* =========================================================
   全局
   ========================================================= */

html,
body,
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(
            circle at 20% 10%,
            rgba(80,95,180,0.10),
            transparent 35%
        ),
        radial-gradient(
            circle at 85% 80%,
            rgba(130,70,180,0.08),
            transparent 35%
        ),
        #07080c !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

* {
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "SF Pro Text",
        "Helvetica Neue",
        Arial,
        sans-serif;
}

.block-container {
    max-width: 1160px;
    padding-top: 48px;
    padding-bottom: 100px;
    padding-left: 35px;
    padding-right: 110px;
}


/* =========================================================
   标题
   ========================================================= */

.hero-title {
    font-size: 46px;
    line-height: 1.05;
    font-weight: 720;
    letter-spacing: -2.4px;
    color: rgba(255,255,255,0.96);
    margin-bottom: 10px;
}

.hero-subtitle {
    font-size: 15px;
    color: rgba(255,255,255,0.45);
    margin-bottom: 35px;
}


/* =========================================================
   Glass Card
   ========================================================= */

.glass-card {

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,0.075),
            rgba(255,255,255,0.025)
        );

    border:
        1px solid rgba(255,255,255,0.095);

    border-radius: 24px;

    padding: 25px;

    backdrop-filter:
        blur(32px)
        saturate(150%);

    -webkit-backdrop-filter:
        blur(32px)
        saturate(150%);

    box-shadow:
        0 20px 70px rgba(0,0,0,0.34),
        inset 0 1px rgba(255,255,255,0.07);
}

.section-title {
    color: rgba(255,255,255,0.93);
    font-size: 21px;
    font-weight: 650;
    margin-bottom: 7px;
}

.section-subtitle {
    color: rgba(255,255,255,0.42);
    font-size: 13px;
    margin-bottom: 18px;
}


/* =========================================================
   输入框
   ========================================================= */

[data-baseweb="textarea"],
[data-baseweb="input"] {

    background:
        rgba(255,255,255,0.035) !important;

    border:
        1px solid rgba(255,255,255,0.075) !important;

    border-radius:
        16px !important;
}

[data-baseweb="textarea"]:focus-within,
[data-baseweb="input"]:focus-within {

    border-color:
        rgba(120,145,255,0.65) !important;

    box-shadow:
        0 0 0 1px rgba(120,145,255,0.18) !important;
}

textarea,
input {
    color:
        rgba(255,255,255,0.92) !important;
}


/* =========================================================
   普通按钮
   ========================================================= */

.stButton > button {

    border:
        1px solid rgba(255,255,255,0.10) !important;

    border-radius:
        14px !important;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,0.075),
            rgba(255,255,255,0.025)
        ) !important;

    color:
        rgba(255,255,255,0.90) !important;

    transition:
        transform .20s ease,
        box-shadow .20s ease,
        border-color .20s ease !important;
}

.stButton > button:hover {

    transform:
        translateY(-1px);

    border-color:
        rgba(255,255,255,0.22) !important;

    box-shadow:
        0 8px 30px rgba(0,0,0,0.28);
}


/* =========================================================
   Primary
   ========================================================= */

button[kind="primary"] {

    background:
        linear-gradient(
            135deg,
            rgba(105,125,255,0.85),
            rgba(150,90,255,0.82)
        ) !important;

    border:
        1px solid rgba(255,255,255,0.18) !important;

    box-shadow:
        0 10px 35px rgba(100,100,255,0.18),
        inset 0 1px rgba(255,255,255,0.20);
}


/* =========================================================
   数据指标
   ========================================================= */

.metric-card {

    background:
        rgba(255,255,255,0.045);

    border:
        1px solid rgba(255,255,255,0.075);

    border-radius:
        18px;

    padding:
        18px;
}

.metric-value {

    font-size:
        28px;

    font-weight:
        700;

    color:
        white;
}

.metric-label {

    font-size:
        12px;

    color:
        rgba(255,255,255,0.42);
}


/* =========================================================
   分数
   ========================================================= */

.score-number {

    font-size:
        68px;

    line-height:
        1;

    font-weight:
        750;

    letter-spacing:
        -4px;

    color:
        white;
}

.score-label {

    font-size:
        13px;

    color:
        rgba(255,255,255,0.42);
}


/* =========================================================
   标签
   ========================================================= */

.tag {

    display:
        inline-block;

    padding:
        6px 11px;

    margin:
        3px;

    border-radius:
        999px;

    background:
        rgba(255,255,255,0.055);

    border:
        1px solid rgba(255,255,255,0.08);

    color:
        rgba(255,255,255,0.72);

    font-size:
        12px;
}

.tag-success {

    background:
        rgba(70,220,160,0.10);

    border-color:
        rgba(70,220,160,0.20);
}

.tag-danger {

    background:
        rgba(255,90,120,0.10);

    border-color:
        rgba(255,90,120,0.20);
}


/* =========================================================
   分割线
   ========================================================= */

hr {
    border-color:
        rgba(255,255,255,0.07) !important;
}


/* =========================================================
   文件上传
   ========================================================= */

[data-testid="stFileUploader"] {

    border-radius:
        18px;
}


/* =========================================================
   Expander
   ========================================================= */

[data-testid="stExpander"] {

    background:
        rgba(255,255,255,0.025) !important;

    border:
        1px solid rgba(255,255,255,0.075) !important;

    border-radius:
        16px !important;
}

</style>
""",
)

st.html(BASE_DIR / "styles.css")


# ============================================================
# 文本处理
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = str(text)

    text = re.sub(
        r"\r\n?",
        "\n",
        text
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    return text.strip()


def tokenize(text):

    text = text.lower()

    english = re.findall(
        r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,30}",
        text
    )

    chinese = re.findall(
        r"[\u4e00-\u9fff]{2,8}",
        text
    )

    tokens = english + chinese

    stop_words = {
        "负责",
        "进行",
        "具有",
        "相关",
        "工作",
        "岗位",
        "要求",
        "能够",
        "以及",
        "熟悉",
        "了解",
        "参与",
        "完成",
        "团队",
        "能力",
        "优先",
        "以上",
        "公司",
        "项目",
        "经验",
    }

    return [
        x for x in tokens
        if x not in stop_words
        and len(x) >= 2
    ]


# ============================================================
# 技能库
# ============================================================

SKILL_LIBRARY = {

    "编程语言": [
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "go",
        "rust",
        "php",
        "kotlin",
        "swift",
    ],

    "前端": [
        "html",
        "css",
        "react",
        "vue",
        "next.js",
        "webpack",
        "vite",
        "uniapp",
    ],

    "后端": [
        "spring",
        "spring boot",
        "django",
        "flask",
        "fastapi",
        "node.js",
        "express",
    ],

    "数据库": [
        "mysql",
        "redis",
        "mongodb",
        "postgresql",
        "sql",
        "oracle",
    ],

    "AI": [
        "人工智能",
        "ai",
        "机器学习",
        "深度学习",
        "大模型",
        "llm",
        "gpt",
        "kimi",
        "prompt",
        "提示词",
        "rag",
        "向量数据库",
        "langchain",
        "agent",
        "智能体",
    ],

    "开发工具": [
        "git",
        "github",
        "docker",
        "linux",
        "vscode",
        "api",
        "restful",
    ],

    "运营": [
        "用户运营",
        "产品运营",
        "内容运营",
        "活动运营",
        "数据运营",
        "新媒体运营",
        "社群运营",
        "增长",
        "转化",
        "用户增长",
        "数据分析",
        "excel",
    ],

    "设计": [
        "figma",
        "photoshop",
        "ps",
        "ui",
        "ux",
        "交互设计",
    ],
}


def extract_skills(text):

    text_lower = text.lower()

    result = {}

    for category, skills in SKILL_LIBRARY.items():

        found = []

        for skill in skills:

            if skill.lower() in text_lower:
                found.append(skill)

        if found:
            result[category] = list(
                dict.fromkeys(found)
            )

    return result


# ============================================================
# 关键词匹配算法
# ============================================================

def keyword_similarity(resume, job):

    resume_tokens = tokenize(resume)
    job_tokens = tokenize(job)

    if not resume_tokens or not job_tokens:
        return 0

    resume_counter = Counter(
        resume_tokens
    )

    job_counter = Counter(
        job_tokens
    )

    score = 0
    total = 0

    high_value_words = {
        "python",
        "java",
        "javascript",
        "typescript",
        "mysql",
        "redis",
        "git",
        "docker",
        "ai",
        "大模型",
        "机器学习",
        "数据分析",
        "用户运营",
        "产品运营",
        "内容运营",
        "增长",
    }

    for token, count in job_counter.items():

        weight = 1.0

        if token in high_value_words:
            weight = 2.2

        elif len(token) >= 4:
            weight = 1.4

        total += count * weight

        if token in resume_counter:

            score += (
                min(
                    resume_counter[token],
                    count
                )
                * weight
            )

    if total <= 0:
        return 0

    return min(
        100,
        round(
            score / total * 100
        )
    )


# ============================================================
# 技能匹配
# ============================================================

def skill_match_score(resume, job):

    resume_skills = extract_skills(
        resume
    )

    job_skills = extract_skills(
        job
    )

    resume_all = []

    job_all = []

    for items in resume_skills.values():
        resume_all.extend(items)

    for items in job_skills.values():
        job_all.extend(items)

    resume_set = {
        x.lower()
        for x in resume_all
    }

    matched = []
    missing = []

    for skill in job_all:

        if skill.lower() in resume_set:
            matched.append(skill)

        else:
            missing.append(skill)

    if job_all:

        score = round(
            len(matched)
            /
            len(job_all)
            * 100
        )

    else:

        score = 50

    return (
        score,
        list(dict.fromkeys(matched)),
        list(dict.fromkeys(missing)),
        resume_skills,
        job_skills,
    )


# ============================================================
# 核心岗位要求识别
# ============================================================

def detect_core_requirements(job):

    text = job.lower()

    core_words = [
        "必须",
        "要求",
        "任职要求",
        "岗位要求",
        "熟练",
        "掌握",
        "负责",
        "需要",
        "至少",
        "核心",
        "优先",
    ]

    core = []
    bonus = []

    for category, skills in SKILL_LIBRARY.items():

        for skill in skills:

            skill_lower = skill.lower()

            if skill_lower not in text:
                continue

            index = text.find(
                skill_lower
            )

            nearby = text[
                max(0, index - 90):
                min(len(text), index + 120)
            ]

            if any(
                word in nearby
                for word in core_words
            ):

                core.append(skill)

            else:

                bonus.append(skill)

    return (
        list(dict.fromkeys(core)),
        list(dict.fromkeys(bonus)),
    )


# ============================================================
# 本地算法
# ============================================================

def local_analysis(resume, job):

    (
        skill_score,
        matched,
        missing,
        resume_skills,
        job_skills,
    ) = skill_match_score(
        resume,
        job
    )

    keyword_score = keyword_similarity(
        resume,
        job
    )

    core_requirements, bonus_requirements = (
        detect_core_requirements(job)
    )

    matched_set = {
        x.lower()
        for x in matched
    }

    core_matched = sum(
        1
        for x in core_requirements
        if x.lower() in matched_set
    )

    if core_requirements:

        core_score = round(
            core_matched
            /
            len(core_requirements)
            * 100
        )

    else:

        core_score = skill_score

    completeness = min(
        100,
        round(
            len(resume)
            /
            800
            * 100
        )
    )

    final_score = round(
        skill_score * 0.40
        +
        core_score * 0.30
        +
        keyword_score * 0.20
        +
        completeness * 0.10
    )

    return {

        "score": min(
            100,
            max(
                0,
                final_score
            )
        ),

        "skill_score":
            skill_score,

        "core_score":
            core_score,

        "keyword_score":
            keyword_score,

        "completeness":
            completeness,

        "matched":
            matched,

        "missing":
            missing,

        "resume_skills":
            resume_skills,

        "job_skills":
            job_skills,

        "core_requirements":
            core_requirements,

        "bonus_requirements":
            bonus_requirements,
    }


# ============================================================
# Kimi API
# ============================================================

def ask_ai(prompt, temperature=0.2):

    if not API_KEY:
        return None

    try:

        from openai import OpenAI

        client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
        )

        response = client.chat.completions.create(

            model=MODEL,

            messages=[

                {
                    "role": "system",

                    "content": """
你是一名专业的互联网招聘分析助手。

请严格基于用户真实提供的信息进行判断。

禁止：
- 编造实习经历
- 编造工作经历
- 编造项目
- 编造学历
- 编造技能
- 编造数据
- 编造成果

允许：
- 优化表达
- 调整结构
- 提炼关键词
- 将已有经历用更专业的方式描述
- 分析岗位匹配程度
""",
                },

                {
                    "role":
                        "user",

                    "content":
                        prompt,
                },
            ],

            temperature=
                temperature,

            extra_body={
                "thinking": {
                    "type":
                        "disabled"
                }
            },
        )

        return (
            response
            .choices[0]
            .message
            .content
        )

    except Exception as e:

        return (
            "AI_ERROR:"
            +
            str(e)
        )


# ============================================================
# JSON 提取
# ============================================================

def extract_json(text):

    if not text:
        return None

    text = text.strip()

    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.I
    )

    text = text.replace(
        "```",
        ""
    ).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    try:

        return json.loads(
            text[
                start:
                end + 1
            ]
        )

    except Exception:

        return None


# ============================================================
# AI 语义分析
# ============================================================

def ai_analyze(
    resume,
    job,
    local
):

    prompt = f"""
请分析下面的简历和目标岗位。

【简历】
{resume}

【岗位JD】
{job}

【本地算法】
本地综合评分：
{local["score"]}

技能匹配：
{local["skill_score"]}

核心要求：
{local["core_score"]}

关键词匹配：
{local["keyword_score"]}

已匹配技能：
{", ".join(local["matched"])}

缺失技能：
{", ".join(local["missing"])}

核心要求：
{", ".join(local["core_requirements"])}

请进行第二层语义分析。

重点判断：

1. 简历经历与JD职责是否真正相关
2. 是否存在同义表达
3. 项目经验是否可以迁移到岗位
4. 简历中有没有隐藏能力
5. 哪些要求是真正核心要求
6. 哪些能力缺失
7. 如果进入面试，最大风险是什么

请严格返回以下JSON：

{{
    "semantic_score": 0,
    "final_ai_score": 0,
    "summary": "",
    "strengths": [],
    "weaknesses": [],
    "missing_skills": [],
    "suggestions": [],
    "interview_risk": "",
    "reason": ""
}}

不要输出JSON以外的内容。
"""

    result = ask_ai(
        prompt
    )

    data = extract_json(
        result
    )

    if not data:

        return {

            "semantic_score":
                local["score"],

            "final_ai_score":
                local["score"],

            "summary":
                "AI分析暂时不可用，当前使用本地算法结果。",

            "strengths": [],

            "weaknesses": [],

            "missing_skills":
                local["missing"],

            "suggestions": [],

            "interview_risk":
                "AI分析不可用",

            "reason":
                "",
        }

    return data


# ============================================================
# 混合算法
# ============================================================

def hybrid_analysis(
    resume,
    job
):

    local = local_analysis(
        resume,
        job
    )

    ai = ai_analyze(
        resume,
        job,
        local
    )

    semantic_score = int(
        ai.get(
            "semantic_score",
            local["score"]
        )
    )

    ai_score = int(
        ai.get(
            "final_ai_score",
            local["score"]
        )
    )

    final_score = round(

        local["score"] * 0.45

        +

        semantic_score * 0.35

        +

        ai_score * 0.20

    )

    final_score = min(
        100,
        max(
            0,
            final_score
        )
    )

    return {
        **local,
        **ai,
        "final_score":
            final_score,
    }


# ============================================================
# AI 简历优化
# ============================================================

def optimize_resume(
    resume,
    job,
    analysis
):

    prompt = f"""
请根据目标岗位JD优化这份简历。

【原始简历】
{resume}

【目标岗位】
{job}

【分析结果】
{json.dumps(
    analysis,
    ensure_ascii=False
)}

要求：

1. 不能编造任何经历。
2. 不能编造公司。
3. 不能编造项目。
4. 不能编造技能。
5. 不能编造数据。
6. 不能改变学历。
7. 可以优化语言。
8. 可以调整结构。
9. 可以突出岗位相关经历。
10. 可以自然加入JD中的关键词。
11. 优先使用“动作 + 方法 + 结果”的表达。
12. 没有数据时不要自行创造数据。
13. 最终内容应该适合互联网公司招聘。

只输出完整优化后的简历正文。
不要解释。
"""

    return ask_ai(
        prompt,
        temperature=0.15
    )


# ============================================================
# 文件读取
# ============================================================

def read_uploaded_file(
    uploaded_file
):

    if uploaded_file is None:
        return ""

    filename = (
        uploaded_file
        .name
        .lower()
    )

    try:

        if filename.endswith(
            ".txt"
        ):

            return (
                uploaded_file
                .read()
                .decode(
                    "utf-8",
                    errors="ignore"
                )
            )

        if filename.endswith(
            ".pdf"
        ):

            from pypdf import PdfReader

            reader = PdfReader(
                uploaded_file
            )

            text = ""

            for page in reader.pages:

                text += (
                    page.extract_text()
                    or ""
                )

            return text

        if filename.endswith(
            ".docx"
        ):

            from docx import Document

            document = Document(
                uploaded_file
            )

            return "\n".join(
                p.text
                for p in document.paragraphs
            )

    except Exception as e:

        st.error(
            f"文件读取失败：{e}"
        )

    return ""


# ============================================================
# 历史记录
# ============================================================

def load_history():

    if not HISTORY_FILE.exists():
        return []

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            history = json.load(f)
            return history if isinstance(history, list) else []

    except Exception:

        return []


def save_history(
    item
):

    history = load_history()

    history.insert(
        0,
        item
    )

    history = history[:30]

    try:
        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                history,
                f,
                ensure_ascii=False,
                indent=2
            )
    except OSError:
        # Streamlit Cloud storage is ephemeral. The current analysis still works.
        pass


# ============================================================
# 一键复制
# ============================================================

def copy_button(
    text,
    label="一键复制"
):
    st.caption(f"{label}：点击下方内容右上角的复制图标即可复制。")
    st.code(text, language=None)


# ============================================================
# 页面标题
# ============================================================

def page_header(
    title,
    subtitle
):

    st.html(
        f"""
        <div class="hero-title">
            {title}
        </div>

        <div class="hero-subtitle">
            {subtitle}
        </div>
        """,
    )


# ============================================================
# Dock
# ============================================================

def render_dock():
    """Render navigation with native Streamlit buttons, not injected HTML."""
    pages = [

            (
                "⌂",
                "home",
                "首页"
            ),

            (
                "▣",
                "resume",
                "我的简历"
            ),

            (
                "⌁",
                "job",
                "目标岗位"
            ),

            (
                "✦",
                "analysis",
                "AI分析"
            ),

            (
                "◈",
                "optimize",
                "优化简历"
            ),

            (
                "◷",
                "history",
                "历史记录"
            ),

            (
                "⚙",
                "settings",
                "设置"
            ),
    ]

    with st.sidebar:
        for (
            icon,
            key,
            label
        ) in pages:

            if st.button(

                icon,

                key=
                    f"dock_{key}",

                help=
                    label,

                type=
                    (
                        "primary"
                        if
                        st.session_state.page
                        == key
                        else
                        "secondary"
                    ),
            ):

                st.session_state.page = key

                st.rerun()


# ============================================================
# 首页
# ============================================================

def render_home():

    page_header(
        "AI Resume Assistant",
        f"{APP_VERSION} · 让简历和岗位真正匹配。"
    )

    c1, c2, c3 = st.columns(3)

    cards = [
        (
            "01",
            "简历解析"
        ),
        (
            "02",
            "岗位匹配"
        ),
        (
            "03",
            "AI优化"
        ),
    ]

    for col, (
        number,
        label
    ) in zip(
        [c1, c2, c3],
        cards
    ):

        with col:

            st.html(
                f"""
                <div class="metric-card">

                    <div class="metric-value">
                        {number}
                    </div>

                    <div class="metric-label">
                        {label}
                    </div>

                </div>
                """,
            )

    st.write("")

    st.html(
        """
        <div class="glass-card">

            <div class="section-title">
                开始你的第一次岗位匹配
            </div>

            <div class="section-subtitle">
                上传简历 → 输入岗位JD → AI分析 → 优化简历
            </div>

        </div>
        """,
    )

    st.write("")

    if st.button(
        "开始分析 →",
        type="primary",
        use_container_width=True
    ):

        st.session_state.page = "resume"

        st.rerun()


# ============================================================
# 简历页面
# ============================================================

def render_resume():

    page_header(
        "我的简历",
        "上传或者直接粘贴你的简历。"
    )

    uploaded = st.file_uploader(
        "上传简历",
        type=[
            "pdf",
            "docx",
            "txt"
        ],
        label_visibility="collapsed"
    )

    if uploaded:

        text = read_uploaded_file(
            uploaded
        )

        if text:

            st.session_state.resume_text = text

            st.session_state.uploaded_filename = (
                uploaded.name
            )

            st.success(
                f"已识别：{uploaded.name}"
            )

    resume = st.text_area(
        "简历内容",
        value=
            st.session_state.resume_text,
        height=500,
        placeholder="""
请粘贴你的简历内容：

教育经历
项目经历
技能
实习经历
校园经历
获奖经历
自我评价
""",
    )

    st.session_state.resume_text = resume

    if resume:

        skills = extract_skills(
            resume
        )

        if skills:

            st.markdown(
                "### 已识别技能"
            )

            for category, items in skills.items():

                tags = "".join(
                    f'<span class="tag">{escape(str(x))}</span>'
                    for x in items
                )

                st.html(
                    f"""
                    <div style="margin-bottom:10px">

                        <b style="color:white">
                            {category}
                        </b>

                        <br>

                        {tags}

                    </div>
                    """,
                )


# ============================================================
# JD 页面
# ============================================================

def render_job():

    page_header(
        "目标岗位",
        "复制你真正想申请的岗位JD。"
    )

    job = st.text_area(
        "岗位JD",
        value=
            st.session_state.job_text,
        height=500,
        placeholder="""
把Boss直聘、字节、腾讯、美团等岗位JD复制到这里。
""",
    )

    st.session_state.job_text = job

    if job:

        skills = extract_skills(
            job
        )

        if skills:

            st.markdown(
                "### 岗位技能画像"
            )

            for category, items in skills.items():

                tags = "".join(
                    f'<span class="tag">{escape(str(x))}</span>'
                    for x in items
                )

                st.html(
                    f"""
                    <div style="margin-bottom:10px">

                        <b style="color:white">
                            {category}
                        </b>

                        <br>

                        {tags}

                    </div>
                    """,
                )

    st.write("")

    if st.button(
        "开始 AI 分析",
        type="primary",
        use_container_width=True
    ):

        if not st.session_state.resume_text:

            st.error(
                "请先填写简历。"
            )

            return

        if not st.session_state.job_text:

            st.error(
                "请先填写岗位JD。"
            )

            return

        with st.spinner(
            "正在进行本地算法 + AI语义分析..."
        ):

            result = hybrid_analysis(

                st.session_state.resume_text,

                st.session_state.job_text,
            )

        st.session_state.analysis_result = result

        save_history(
            {
                "resume":
                    st.session_state.resume_text,

                "job":
                    st.session_state.job_text,

                "score":
                    result["final_score"],

                "analysis":
                    result,
            }
        )

        st.session_state.page = "analysis"

        st.rerun()


# ============================================================
# 分析页面
# ============================================================

def render_analysis():

    page_header(
        "AI 分析",
        "本地算法 + 大模型语义理解。"
    )

    result = (
        st.session_state.analysis_result
    )

    if not result:

        st.info(
            "还没有分析结果。"
        )

        if st.button(
            "去分析 →",
            type="primary"
        ):

            st.session_state.page = "job"

            st.rerun()

        return

    score = result[
        "final_score"
    ]

    st.html(
        f"""
        <div class="glass-card">

            <div class="score-label">
                综合岗位匹配度
            </div>

            <div class="score-number">
                {score}
            </div>

            <div class="score-label">
                / 100
            </div>

        </div>
        """,
    )

    st.write("")

    cols = st.columns(4)

    metrics = [

        (
            "技能匹配",
            result["skill_score"]
        ),

        (
            "核心要求",
            result["core_score"]
        ),

        (
            "关键词",
            result["keyword_score"]
        ),

        (
            "AI语义",
            result.get(
                "semantic_score",
                0
            )
        ),
    ]

    for col, (
        label,
        value
    ) in zip(
        cols,
        metrics
    ):

        with col:

            st.html(
                f"""
                <div class="metric-card">

                    <div class="metric-value">
                        {value}
                    </div>

                    <div class="metric-label">
                        {label}
                    </div>

                </div>
                """,
            )

    st.write("")

    # 匹配技能

    st.markdown(
        "### ✓ 已匹配技能"
    )

    matched = result.get(
        "matched",
        []
    )

    if matched:

        tags = "".join(
            f'<span class="tag tag-success">{escape(str(x))}</span>'
            for x in matched
        )

        st.html(tags)

    else:

        st.caption(
            "暂未识别到明显匹配技能。"
        )

    # 缺失技能

    st.markdown(
        "### △ 建议补强"
    )

    missing = list(
        dict.fromkeys(

            result.get(
                "missing",
                []
            )

            +

            result.get(
                "missing_skills",
                []
            )
        )
    )

    if missing:

        tags = "".join(
            f'<span class="tag tag-danger">{escape(str(x))}</span>'
            for x in missing
        )

        st.html(tags)

    # AI总结

    st.markdown(
        "### AI 招聘判断"
    )

    with st.container(border=True):
        st.write(result.get("summary", "暂无分析"))

    strengths = result.get(
        "strengths",
        []
    )

    if strengths:

        st.markdown(
            "### 你的优势"
        )

        for item in strengths:

            st.markdown(
                f"- {item}"
            )

    weaknesses = result.get(
        "weaknesses",
        []
    )

    if weaknesses:

        st.markdown(
            "### 你的短板"
        )

        for item in weaknesses:

            st.markdown(
                f"- {item}"
            )

    suggestions = result.get(
        "suggestions",
        []
    )

    if suggestions:

        st.markdown(
            "### 优化建议"
        )

        for item in suggestions:

            st.markdown(
                f"- {item}"
            )

    st.write("")

    if st.button(
        "生成优化简历 →",
        type="primary",
        use_container_width=True
    ):

        st.session_state.page = "optimize"

        st.rerun()


# ============================================================
# 优化页面
# ============================================================

def render_optimize():

    page_header(
        "优化简历",
        "优化表达，不伪造经历。"
    )

    resume = (
        st.session_state.resume_text
    )

    job = (
        st.session_state.job_text
    )

    analysis = (
        st.session_state.analysis_result
    )

    if not resume:

        st.warning(
            "请先准备简历。"
        )

        return

    if not job:

        st.warning(
            "请先准备目标岗位JD。"
        )

        return

    if st.button(
        "重新生成优化简历",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "AI正在优化简历..."
        ):

            optimized = optimize_resume(

                resume,

                job,

                analysis or {}
            )

        if optimized:

            st.session_state.optimized_resume = optimized

    if st.session_state.optimized_resume:

        optimized = (
            st.session_state.optimized_resume
        )

        st.markdown(
            "### 优化后的简历"
        )

        copy_button(
            optimized,
            "一键复制优化后的简历"
        )

    else:

        st.info(
            "点击上方按钮生成优化版本。"
        )


# ============================================================
# 历史页面
# ============================================================

def render_history():

    page_header(
        "历史记录",
        "保存最近的岗位分析结果。"
    )

    history = load_history()

    if not history:

        st.info(
            "暂时没有历史记录。"
        )

        return

    for index, item in enumerate(history):

        if not isinstance(item, dict):
            continue

        score = item.get(
            "score",
            0
        )

        job = item.get(
            "job",
            ""
        )

        preview = clean_text(
            job
        )[:100]

        with st.expander(
            f"匹配度 {score} · {preview}"
        ):

            st.markdown(
                f"**匹配度：{score}/100**"
            )

            analysis = item.get("analysis", {})
            if not isinstance(analysis, dict):
                analysis = {}
                st.caption("这条旧记录缺少可加载的分析详情。")

            st.write(
                analysis.get(
                    "summary",
                    ""
                )
            )

            if analysis and st.button(
                "加载这次分析",
                key=
                    f"load_{index}"
            ):

                st.session_state.resume_text = (
                    item.get(
                        "resume",
                        ""
                    )
                )

                st.session_state.job_text = (
                    item.get(
                        "job",
                        ""
                    )
                )

                st.session_state.analysis_result = (
                    analysis
                )

                st.session_state.page = (
                    "analysis"
                )

                st.rerun()


# ============================================================
# 设置页面
# ============================================================

def render_settings():

    page_header(
        "设置",
        f"AI Resume Assistant · {APP_VERSION}"
    )

    st.html(
        f"""
        <div class="glass-card">

            <div class="section-title">
                AI 模型
            </div>

            <div class="section-subtitle">
                当前使用 Kimi API
            </div>

            <p style="color:rgba(255,255,255,.7)">
                Model：{MODEL}
            </p>

        </div>
        """,
    )

    st.write("")

    if API_KEY:

        st.success(
            "API Key 已配置"
        )

    else:

        st.error(
            "没有检测到 MOONSHOT_API_KEY"
        )

    st.write("")

    if st.button(
        "清空当前分析数据"
    ):

        st.session_state.resume_text = ""
        st.session_state.job_text = ""
        st.session_state.analysis_result = None
        st.session_state.optimized_resume = ""

        st.success(
            "当前数据已清空。"
        )


# ============================================================
# 主程序
# ============================================================

render_dock()

current_page = st.session_state.page

if current_page == "home":
    render_home()
elif current_page == "resume":
    render_resume()
elif current_page == "job":
    render_job()
elif current_page == "analysis":
    render_analysis()
elif current_page == "optimize":
    render_optimize()
elif current_page == "history":
    render_history()
elif current_page == "settings":
    render_settings()
else:
    st.session_state.page = "home"
    st.rerun()
