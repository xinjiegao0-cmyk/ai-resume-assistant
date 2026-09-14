import os
import re

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

st.set_page_config(
    page_title="AI 简历优化助手",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI 简历优化助手")
st.caption("让 AI 帮你分析简历与目标岗位的匹配度")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 我的简历")
    resume = st.text_area(
        "粘贴你的简历内容",
        height=350,
        placeholder="例如：我是计算机应用专业大三学生……"
    )

with col2:
    st.subheader("🎯 目标岗位")
    job = st.text_area(
        "粘贴招聘岗位 JD",
        height=350,
        placeholder="例如：岗位职责……\n任职要求……"
    )

st.divider()

if st.button("🚀 开始智能分析", use_container_width=True):

    if not resume or not job:
        st.warning("⚠️ 请先填写简历和目标岗位 JD")

    elif not os.getenv("MOONSHOT_API_KEY"):
        st.error("❌ 没有检测到 Kimi API Key，请检查 .env 文件")

    else:
        client = OpenAI(
            api_key=os.getenv("MOONSHOT_API_KEY"),
            base_url="https://api.moonshot.cn/v1"
        )

        with st.spinner("🤖 AI 正在分析，请稍候……"):

            try:
                response = client.chat.completions.create(
                    model="kimi-k2.6",
                    messages=[
                        {
                            "role": "system",
                            "content": """
你是一名专业的互联网招聘顾问和简历优化专家。

请分析用户简历和目标岗位 JD。

第一行必须严格输出：
MATCH_SCORE: 数字

数字范围 0-100，例如：
MATCH_SCORE: 78

然后按照以下结构输出：

# 📊 综合分析
解释这个分数为什么是这个水平。

# ✅ 我的优势
列出与岗位最匹配的能力和经历。

# ❌ 我的不足
指出简历与岗位要求之间的主要差距。

# 🔧 优化建议
给出具体、可执行的修改建议。

# ✍️ 简历优化示例
把用户现有经历改写成更适合目标岗位的表达。

# 🎯 最终建议
告诉用户是否值得投递，以及最应该优先提升的 3 件事情。

请使用中文，具体、真实，不要编造用户没有的经历。
"""
                        },
                        {
                            "role": "user",
                            "content": f"""
【我的简历】

{resume}

【目标岗位 JD】

{job}
"""
                        }
                    ],
                    extra_body={
                        "thinking": {
                            "type": "disabled"
                        }
                    }
                )

                result = response.choices[0].message.content

                # 提取 AI 返回的匹配度
                score_match = re.search(
                    r"MATCH_SCORE:\s*(\d+)",
                    result
                )

                score = None

                if score_match:
                    score = min(100, max(0, int(score_match.group(1))))

                # 隐藏内部评分标记
                result = re.sub(
                    r"MATCH_SCORE:\s*\d+\s*",
                    "",
                    result,
                    count=1
                )

                # 显示评分
                if score is not None:
                    st.subheader("📊 岗位匹配度")

                    score_col1, score_col2 = st.columns([1, 3])

                    with score_col1:
                        st.metric(
                            label="综合匹配度",
                            value=f"{score} / 100"
                        )

                    with score_col2:
                        st.progress(score / 100)

                        if score >= 80:
                            st.success("🎉 匹配度较高，可以重点投递！")
                        elif score >= 60:
                            st.warning("👍 有一定匹配度，建议优化简历后投递。")
                        else:
                            st.error("⚠️ 当前匹配度较低，建议针对 JD 进行重点优化。")

                st.divider()

                st.subheader("🤖 AI 深度分析")
                st.markdown(result)

            except Exception as e:
                st.error(f"❌ AI 调用失败：{e}")