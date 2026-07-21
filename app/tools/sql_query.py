"""SQL 查询工具——大模型生成 SQL 后执行"""

import re

from langchain.tools import tool
from langchain_core.messages import HumanMessage

from app.config import config
from app.database import execute_raw

TABLE_SCHEMA = """
abc.student (学生信息):
    id (int, 主键), name (varchar, 姓名), age (varchar, 年龄)

abc.students_age:
    id (int, 主键), ault (varchar)

fruitdb.fruit (水果):
    id (int, 主键), fruit_name (varchar, 水果名), price (decimal, 价格),
    weight (decimal, 重量), created_time (timestamp, 创建时间)

newsdb.category (新闻分类):
    id (int, 主键), NAME (varchar, 分类名称)

newsdb.news (新闻):
    id (int, 主键), title (varchar, 标题), category_id (int, 分类ID),
    created_at (timestamp, 发布时间)

oa_demo.leaves (请假表):
    id (int, 主键), applicant (varchar, 申请人), leave_type (varchar, 请假类型),
    start_date (date, 开始日期), end_date (date, 结束日期),
    reason (text, 原因), status (varchar, 状态),
    created_at (datetime, 创建时间), review_comment (text, 审核意见)

oa_demo.reimbursements (报销表):
    id (int, 主键), applicant (varchar, 申请人), amount (decimal, 金额),
    category (varchar, 类别), description (text, 说明),
    status (varchar, 状态), created_at (datetime, 创建时间),
    review_comment (text, 审核意见)

school.student (学校账号):
    id (int, 主键), username (varchar, 用户名), password (varchar, 密码)

school.courses (课程表):
    id (int, 主键), student_name (varchar, 学生姓名), course_name (varchar, 课程名称),
    weekday (varchar, 星期几), start_time (varchar, 上课时间), end_time (varchar, 下课时间),
    location (varchar, 上课地点)

school.grades (考试成绩表):
    id (int, 主键), student_name (varchar, 学生姓名), course_name (varchar, 课程名称),
    score (decimal, 分数), semester (varchar, 所属学期)

school.notices (通知公告表):
    id (int, 主键), title (varchar, 标题), content (text, 内容),
    publish_time (datetime, 发布时间)
"""

SQL_SYSTEM_PROMPT = f"""你是一个专业的MySQL 8.0 SQL生成器，**只返回合法的SQL语句**。

数据库所有表结构（使用 `数据库名.表名` 访问）：

{TABLE_SCHEMA}

规则：
1. 跨库查询时使用完整表名，如 `SELECT * FROM abc.student`
2. 绝对不返回任何自然语言解释、注释或说明
3. 禁止返回中文内容
"""


def _generate_sql(user_query: str):
    """让大模型根据用户描述生成 SQL"""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        api_key=config.ZHIPUAI_API_KEY,
        base_url=config.ZHIPUAI_BASE_URL,
        temperature=0.1,
        timeout=config.LLM_TIMEOUT,
    )
    response = llm.invoke([("system", SQL_SYSTEM_PROMPT), ("user", user_query)])
    sql = response.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    sql_match = re.search(r"(SELECT|INSERT|UPDATE|DELETE).*", sql, re.I | re.DOTALL)
    if sql_match:
        sql = sql_match.group(0).strip()

    return sql


@tool
def execute_sql_query(query: str) -> str:
    """执行 SQL 查询并返回结果，支持 SELECT / INSERT / UPDATE / DELETE"""
    print(f"[工具调用] 执行SQL查询: {query}")

    sql = _generate_sql(query)

    if not sql or not sql.upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE")):
        return "错误:无法生成合法的SQL语句,请重新描述您的问题。"

    print(f"[生成SQL] {sql}")
    return execute_raw(sql)
