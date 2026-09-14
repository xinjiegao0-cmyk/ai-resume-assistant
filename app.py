import os
import re
import json
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from docx import Document


# =========================================================
# 基础配置
# =========================================================

load_dotenv()

st.set_page_config(
    page_title="AI 简历优化助手",
    page_icon="📄",
    layout="wide"
)

HISTORY_FILE = "analysis_history.json"


# =========================================================
# Kimi API
# =========================================================

client = None

if os.getenv("MOONSHOT_API_KEY"):
    client = OpenAI(
        api_key=os.getenv("MOONSHOT_API_KEY"),
        base_url="https://api.moonshot.cn/v1"
    )


# =========================================================
# 历史记录
# =========================================================

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except Exception:
        return []


def save_history(history):
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


# =========================================================
# PDF 读取
# =========================================================

def read_pdf(file):

    reader = PdfReader(file)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# =========================================================
# Word 读取
# =========================================================

def read_docx(file):

    document = Document(file)

    text = ""

    for paragraph in document.paragraphs:

        if paragraph.text.strip():

            text += paragraph.text + "\n"

    return text


# =========================================================
# 文本清理
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    text = re.sub(
        r"[ \t]{2,}",
        " ",
        text
    )

    return text.strip()


# =========================================================
# 自动识别简历 + JD + 岗位名称
# =========================================================

def auto_detect_content(text):

    text = text.strip()

    resume = ""
    job = ""
    job_title = ""

    # 岗位名称
    title_match = re.search(
        r"【(?:岗位名称|职位名称|岗位|职位)】\s*(.*?)(?=\n|【|$)",
        text,
        re.S
    )

    if title_match:

        job_title = title_match.group(1).strip()

    # 简历
    resume_match = re.search(
        r"【(?:我的简历|简历|个人简历)】"
        r"(.*?)"
        r"(?=【(?:目标岗位|岗位 JD|JD|岗位|职位)】|$)",
        text,
        re.S
    )

    if resume_match:

        resume = clean_text(
            resume_match.group(1)
        )

    # JD
    job_match = re.search(
        r"【(?:目标岗位|岗位 JD|JD|岗位|职位)】"
        r"(.*)$",
        text,
        re.S
    )

    if job_match:

        job = clean_text(
            job_match.group(1)
        )

    return resume, job, job_title


# =========================================================
# AI：岗位分析
# =========================================================

def analyze_resume(resume, job):

    prompt = f"""
你是一名专业的互联网招聘顾问、HR和简历优化专家。

请分析用户真实简历与目标岗位 JD。

第一行必须严格输出：

MATCH_SCORE: 数字

然后输出：

SKILL_SCORE: 数字
EXPERIENCE_SCORE: 数字
EDUCATION_SCORE: 数字
JOB_SCORE: 数字
AI_SCORE: 数字
OPERATIONS_SCORE: 数字

所有分数范围为 0-100。

评分含义：

SKILL_SCORE = 专业技能匹配度
EXPERIENCE_SCORE = 经历匹配度
EDUCATION_SCORE = 学历/专业匹配度
JOB_SCORE = 与岗位核心要求匹配度
AI_SCORE = AI/技术能力匹配度
OPERATIONS_SCORE = 运营能力匹配度


然后按照以下结构输出：

# 📊 综合分析

解释为什么给出这个综合匹配度。

# ✅ 我的优势

结合用户真实简历，
找出与岗位最匹配的能力、经历和项目。

# ❌ 我的不足

指出用户简历与岗位要求之间的主要差距。

# 🔧 优化建议

给出具体、可执行的修改建议。

# 🎯 最终建议

告诉用户：

1. 是否值得投递
2. 当前最大优势
3. 当前最大短板
4. 最应该提升的 3 件事情

严格要求：

- 不允许编造经历。
- 不允许虚构数据。
- 不允许增加用户没有的技能。
- 必须基于用户提供的真实信息。
- 如果用户没有相关经历，要明确指出。


【我的简历】

{resume}


【目标岗位 JD】

{job}
"""

    response = client.chat.completions.create(

        model="kimi-k2.6",

        messages=[
            {
                "role": "system",
                "content": "你是一名专业的互联网招聘顾问。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        extra_body={
            "thinking": {
                "type": "disabled"
            }
        }
    )

    return response.choices[0].message.content


# =========================================================
# AI：优化简历
# =========================================================

def optimize_resume(resume, job):

    prompt = f"""
你是一名专业的互联网招聘顾问和简历优化专家。

请根据用户真实简历和目标岗位 JD，
重新组织一份更适合该岗位的简历。

必须严格遵守：

1. 不允许编造经历。
2. 不允许虚构数据。
3. 不允许增加不存在的技能。
4. 只能优化表达方式、结构和重点。
5. 突出与目标岗位相关的真实经历。
6. 如果某项经历不存在，不要强行添加。


请输出：

# ✨ 优化后的简历

## 个人简介

## 教育经历

## 专业技能

## 项目经历

## 实习/实践经历

## 校园经历

## 其他信息


要求：

- 表达专业。
- 简洁清晰。
- 尽量使用“做了什么 + 怎么做 + 结果”的表达方式。
- 不能虚构结果。
- 不能夸大经历。


【原始简历】

{resume}


【目标岗位 JD】

{job}
"""

    response = client.chat.completions.create(

        model="kimi-k2.6",

        messages=[
            {
                "role": "system",
                "content": "你是一名专业的互联网简历优化专家。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        extra_body={
            "thinking": {
                "type": "disabled"
            }
        }
    )

    return response.choices[0].message.content


# =========================================================
# 页面标题
# =========================================================

st.title("📄 AI 简历优化助手")

st.caption(
    "分析简历与目标岗位匹配度，并生成针对性的优化建议"
)

st.divider()


# =========================================================
# Session State 初始化
# =========================================================

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "job_text" not in st.session_state:
    st.session_state.job_text = ""

if "job_title" not in st.session_state:
    st.session_state.job_title = ""

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""

if "clean_result" not in st.session_state:
    st.session_state.clean_result = ""

if "score" not in st.session_state:
    st.session_state.score = None

if "dimensions" not in st.session_state:
    st.session_state.dimensions = {}

if "optimized_resume" not in st.session_state:
    st.session_state.optimized_resume = ""

if "auto_text" not in st.session_state:
    st.session_state.auto_text = ""


# =========================================================
# 侧边栏
# =========================================================

history = load_history()

with st.sidebar:

    st.header("🗂️ 历史记录")

    if not history:

        st.caption("暂无分析记录")

    else:

        st.caption(
            f"共 {len(history)} 条分析记录"
        )

        for item in reversed(history):

            title = item.get(
                "job_title",
                "未命名岗位"
            )

            score = item.get(
                "score",
                "--"
            )

            time = item.get(
                "time",
                ""
            )

            st.write(
                f"**{title}** · {score}分"
            )

            st.caption(time)


# =========================================================
# 一键识别区域
# =========================================================

st.subheader("🧠 一键识别并自动填充")

st.caption(
    "一次性粘贴简历、岗位名称和 JD，AI 简历助手会自动识别并填入对应区域。"
)

auto_text = st.text_area(
    "粘贴信息",
    height=180,
    placeholder="""例如：

【岗位名称】
产品运营实习生

【我的简历】
姓名：高新杰
专业：计算机应用
……

【目标岗位】
岗位职责：
……
任职要求：
……
""",
    key="auto_text"
)


if st.button(
    "🧠 自动识别并填充",
    use_container_width=True
):

    if not auto_text.strip():

        st.warning(
            "⚠️ 请先粘贴需要识别的信息"
        )

    else:

        detected_resume, detected_job, detected_title = (
            auto_detect_content(auto_text)
        )

        if detected_resume:

            st.session_state.resume_text = (
                detected_resume
            )

        if detected_job:

            st.session_state.job_text = (
                detected_job
            )

        if detected_title:

            st.session_state.job_title = (
                detected_title
            )

        if (
            detected_resume
            or detected_job
            or detected_title
        ):

            st.success(
                "✅ 已自动识别并填充成功！"
            )

            st.rerun()

        else:

            st.warning(
                "⚠️ 没有识别到内容，请检查格式。"
            )


st.divider()


# =========================================================
# 输入区域
# =========================================================

col1, col2 = st.columns(2)


# =========================================================
# 简历
# =========================================================

with col1:

    st.subheader("📋 我的简历")

    uploaded_file = st.file_uploader(
        "上传 PDF / Word 简历",
        type=["pdf", "docx"]
    )

    if uploaded_file:

        try:

            if uploaded_file.name.endswith(".pdf"):

                uploaded_text = read_pdf(
                    uploaded_file
                )

            else:

                uploaded_text = read_docx(
                    uploaded_file
                )

            uploaded_text = clean_text(
                uploaded_text
            )

            if uploaded_text:

                st.session_state.resume_text = (
                    uploaded_text
                )

                st.success(
                    f"✅ 已成功读取：{uploaded_file.name}"
                )

                with st.expander(
                    "查看提取的简历文字"
                ):

                    st.text(
                        uploaded_text
                    )

            else:

                st.warning(
                    "⚠️ 没有读取到文字，请检查文件。"
                )

        except Exception as e:

            st.error(
                f"❌ 文件读取失败：{e}"
            )

    resume = st.text_area(
        "简历内容",
        height=300,
        placeholder="也可以直接把简历粘贴到这里……",
        key="resume_text"
    )


# =========================================================
# JD
# =========================================================

with col2:

    st.subheader("🎯 目标岗位")

    job_title = st.text_input(
        "岗位名称",
        placeholder="例如：产品运营实习生",
        key="job_title"
    )

    job = st.text_area(
        "岗位 JD",
        height=300,
        placeholder="把招聘岗位职责和任职要求粘贴到这里……",
        key="job_text"
    )


st.divider()


# =========================================================
# 第一步：分析
# =========================================================

st.subheader("🚀 第一步：岗位匹配分析")

analyze_button = st.button(
    "开始智能分析",
    use_container_width=True
)


if analyze_button:

    if not resume.strip():

        st.warning(
            "⚠️ 请先上传或粘贴简历。"
        )

    elif not job.strip():

        st.warning(
            "⚠️ 请先填写岗位 JD。"
        )

    elif not client:

        st.error(
            "❌ 没有检测到 Kimi API Key，请检查 .env 文件。"
        )

    else:

        with st.spinner(
            "🤖 AI 正在分析，请稍候……"
        ):

            try:

                result = analyze_resume(
                    resume,
                    job
                )

                st.session_state.analysis_result = (
                    result
                )

                # -----------------------------------------
                # 综合评分
                # -----------------------------------------

                score_match = re.search(
                    r"MATCH_SCORE:\s*(\d+)",
                    result
                )

                score = None

                if score_match:

                    score = min(
                        100,
                        max(
                            0,
                            int(
                                score_match.group(1)
                            )
                        )
                    )

                st.session_state.score = score

                # -----------------------------------------
                # 多维度评分
                # -----------------------------------------

                dimensions = {}

                score_patterns = {

                    "技能匹配": "SKILL_SCORE",

                    "经历匹配": "EXPERIENCE_SCORE",

                    "学历匹配": "EDUCATION_SCORE",

                    "岗位匹配": "JOB_SCORE",

                    "AI能力": "AI_SCORE",

                    "运营能力": "OPERATIONS_SCORE"
                }

                for name, pattern in score_patterns.items():

                    match = re.search(
                        rf"{pattern}:\s*(\d+)",
                        result
                    )

                    if match:

                        dimensions[name] = min(
                            100,
                            max(
                                0,
                                int(
                                    match.group(1)
                                )
                            )
                        )

                st.session_state.dimensions = (
                    dimensions
                )

                # -----------------------------------------
                # 清理内部评分
                # -----------------------------------------

                clean_result = re.sub(

                    r"(MATCH_SCORE|"
                    r"SKILL_SCORE|"
                    r"EXPERIENCE_SCORE|"
                    r"EDUCATION_SCORE|"
                    r"JOB_SCORE|"
                    r"AI_SCORE|"
                    r"OPERATIONS_SCORE)"
                    r":\s*\d+\s*",

                    "",

                    result
                )

                st.session_state.clean_result = (
                    clean_result
                )

                # -----------------------------------------
                # 保存历史
                # -----------------------------------------

                history = load_history()

                history.append(
                    {
                        "job_title": (
                            job_title
                            if job_title
                            else "未命名岗位"
                        ),

                        "score": score,

                        "time": datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        ),

                        "analysis": clean_result
                    }
                )

                save_history(history)

            except Exception as e:

                st.error(
                    f"❌ AI 分析失败：{e}"
                )


# =========================================================
# 显示分析结果
# =========================================================

if st.session_state.score is not None:

    score = st.session_state.score

    dimensions = st.session_state.dimensions

    st.subheader("📊 岗位匹配度")

    score_col1, score_col2 = st.columns(
        [1, 3]
    )

    with score_col1:

        st.metric(
            "综合匹配度",
            f"{score} / 100"
        )

    with score_col2:

        st.progress(
            score / 100
        )

        if score >= 80:

            st.success(
                "🎉 匹配度较高，可以重点投递！"
            )

        elif score >= 60:

            st.warning(
                "👍 有一定匹配度，优化后建议投递。"
            )

        else:

            st.error(
                "⚠️ 当前匹配度较低，建议针对 JD 重点优化。"
            )


    # =====================================================
    # 多维度评分
    # =====================================================

    if dimensions:

        st.subheader(
            "📈 多维度能力分析"
        )

        score_cols = st.columns(3)

        for index, (name, value) in enumerate(
            dimensions.items()
        ):

            with score_cols[index % 3]:

                st.metric(
                    name,
                    f"{value} / 100"
                )

                st.progress(
                    value / 100
                )


    st.divider()


    # =====================================================
    # AI 深度分析
    # =====================================================

    st.subheader(
        "🤖 AI 深度分析"
    )

    st.markdown(
        st.session_state.clean_result
    )


# =========================================================
# 第二步：生成优化简历
# =========================================================

st.divider()

st.subheader(
    "✨ 第二步：生成优化简历"
)

st.caption(
    "分析完成后再生成优化简历，可以减少不必要的 API 调用。"
)

optimize_button = st.button(
    "✨ 一键生成优化简历",
    use_container_width=True
)


if optimize_button:

    if not resume.strip():

        st.warning(
            "⚠️ 请先上传或粘贴简历。"
        )

    elif not job.strip():

        st.warning(
            "⚠️ 请先填写岗位 JD。"
        )

    elif not client:

        st.error(
            "❌ 没有检测到 Kimi API Key。"
        )

    else:

        with st.spinner(
            "✍️ AI 正在生成优化简历……"
        ):

            try:

                optimized = optimize_resume(
                    resume,
                    job
                )

                st.session_state.optimized_resume = (
                    optimized
                )

            except Exception as e:

                st.error(
                    f"❌ 简历优化失败：{e}"
                )


# =========================================================
# 优化后的简历
# =========================================================

if st.session_state.optimized_resume:

    st.divider()

    st.subheader(
        "📝 优化后的简历"
    )

    st.info(
        "以下内容根据你提供的真实经历生成，"
        "投递前请自行核对。"
    )

    optimized_text = (
        st.session_state.optimized_resume
    )

    st.text_area(
        "优化结果",
        value=optimized_text,
        height=650,
        key="optimized_resume_display"
    )

    # =====================================================
    # 一键复制
    # =====================================================

    # 转成安全的 JavaScript 字符串
    copy_data = json.dumps(
        optimized_text,
        ensure_ascii=False
    )

    st.html(
        f"""
        <button
            onclick='
                navigator.clipboard.writeText(
                    {copy_data}
                ).then(() => {{
                    this.innerText = "✅ 已复制到剪贴板";
                }}).catch(() => {{
                    this.innerText = "❌ 复制失败，请手动复制";
                }})
            '
            style="
                width: 100%;
                padding: 12px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
            "
        >
            📋 一键复制优化后的简历
        </button>
        """,
        unsafe_allow_javascript=True
    )

    st.success(
        "🎉 简历优化完成！"
    )