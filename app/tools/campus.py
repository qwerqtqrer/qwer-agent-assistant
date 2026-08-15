"""校园相关工具：课程表、成绩、通知公告。"""

from langchain.tools import tool

from app.core.config import config
from app.core.llm import build_llm
from app.core.logging import get_logger
from app.database import execute_query

logger = get_logger("app.tools.campus")


def _beautify(prompt: str, fallback: str = "") -> str:
    """调用 LLM 把原始数据整理为美观输出，失败时回退到原始数据。"""
    try:
        resp = build_llm().invoke([("user", prompt)])
        return str(resp.content)
    except Exception:
        logger.exception("LLM 格式化失败，回退为原始数据")
        return fallback or "查询成功，但格式化输出失败。"


def _demo_notice(feature: str) -> str:
    return f"演示模式未接入 MySQL，暂时无法查询{feature}；配置 DB_HOST/DB_USER/DB_PASSWORD 后即可使用。"


@tool
def query_course_schedule(student_name: str) -> str:
    """
    查询指定学生的课程表
    :param student_name: 学生姓名
    """
    if config.is_demo_mode:
        return _demo_notice("课程表")
    sql = (
        "SELECT course_name, weekday, start_time, end_time, location "
        "FROM school.courses WHERE student_name = %s"
    )
    result = execute_query(sql, (student_name,))

    if not result or " | " not in result:
        return f"未找到学生「{student_name}」的课程信息，请确认姓名是否正确。"

    return _beautify(
        f"以下是学生 {student_name} 的课程表原始数据，请将其整理为美观的课程表格式：\n\n{result}\n\n"
        '请按「星期X」分组，格式：\n📅 星期一\n  1. 课程名 (08:00-09:40 @ 教室)\n',
        fallback=result,
    )


@tool
def query_grade(student_name: str) -> str:
    """
    查询指定学生的考试成绩
    :param student_name: 学生姓名
    """
    if config.is_demo_mode:
        return _demo_notice("成绩")
    sql = (
        "SELECT course_name, score, semester FROM school.grades "
        "WHERE student_name = %s"
    )
    result = execute_query(sql, (student_name,))

    if not result or " | " not in result:
        return f"未找到学生「{student_name}」的成绩信息，请确认姓名是否正确。"

    return _beautify(
        f"以下是学生 {student_name} 的成绩原始数据，请整理为美观的格式：\n\n{result}\n\n"
        "要求：\n- 按学期分组\n- 显示每门课分数\n- 计算平均分\n",
        fallback=result,
    )


@tool
def query_campus_notice(keyword: str = "") -> str:
    """
    查询校园通知公告
    :param keyword: 可选关键词，用于筛选通知标题
    """
    if config.is_demo_mode:
        return _demo_notice("校园公告")
    if keyword:
        sql = (
            "SELECT title, content, publish_time FROM school.notices "
            "WHERE title LIKE %s OR content LIKE %s ORDER BY publish_time DESC LIMIT 10"
        )
        params = (f"%{keyword}%", f"%{keyword}%")
    else:
        sql = "SELECT title, content, publish_time FROM school.notices ORDER BY publish_time DESC LIMIT 10"
        params = None

    result = execute_query(sql, params)
    if not result or " | " not in result:
        return f"未找到相关通知公告{f'(关键词: {keyword})' if keyword else ''}。"

    return _beautify(
        f"以下是校园公告原始数据，请整理为美观的列表：\n\n{result}\n\n"
        "格式要求：\n📢 [标题]\n   内容概要：...\n   发布时间：...\n",
        fallback=result,
    )
