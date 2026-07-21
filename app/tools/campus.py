"""校园相关工具：课程表、成绩、通知公告"""

from langchain.tools import tool

from app.database import execute_query


@tool
def query_course_schedule(student_name: str) -> str:
    """
    查询指定学生的课程表
    :param student_name: 学生姓名
    """
    sql = f"SELECT course_name, weekday, start_time, end_time, location FROM school.courses WHERE student_name = '{student_name}'"
    result = execute_query(sql)

    if not result or " | " not in result:
        return f"未找到学生「{student_name}」的课程信息，请确认姓名是否正确。"

    return _beautify(
        f"以下是学生 {student_name} 的课程表原始数据，请将其整理为美观的课程表格式：\n\n{result}\n\n"
        '请按「星期X」分组，格式：\n📅 星期一\n  1. 课程名 (08:00-09:40 @ 教室)\n'
    )


@tool
def query_grade(student_name: str) -> str:
    """
    查询指定学生的考试成绩
    :param student_name: 学生姓名
    """
    sql = f"SELECT course_name, score, semester FROM school.grades WHERE student_name = '{student_name}'"
    result = execute_query(sql)

    if not result or " | " not in result:
        return f"未找到学生「{student_name}」的成绩信息，请确认姓名是否正确。"

    return _beautify(
        f"以下是学生 {student_name} 的成绩原始数据，请整理为美观的格式：\n\n{result}\n\n"
        "要求：\n- 按学期分组\n- 显示每门课分数\n- 计算平均分\n"
    )


@tool
def query_campus_notice(keyword: str = "") -> str:
    """
    查询校园通知公告
    :param keyword: 可选关键词，用于筛选通知标题
    """
    if keyword:
        sql = f"SELECT title, content, publish_time FROM school.notices WHERE title LIKE '%{keyword}%' OR content LIKE '%{keyword}%' ORDER BY publish_time DESC LIMIT 10"
    else:
        sql = "SELECT title, content, publish_time FROM school.notices ORDER BY publish_time DESC LIMIT 10"

    result = execute_query(sql)

    if not result or " | " not in result:
        return f"未找到相关通知公告{f'(关键词: {keyword})' if keyword else ''}。"

    return _beautify(
        f"以下是校园公告原始数据，请整理为美观的列表：\n\n{result}\n\n"
        "格式要求：\n📢 [标题]\n   内容概要：...\n   发布时间：...\n"
    )


def _beautify(prompt: str) -> str:
    """调用 ZhipuAI 美化输出"""
    from zhipuai import ZhipuAI

    client = ZhipuAI()
    resp = client.chat.completions.create(
        model="glm-5.2",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content
