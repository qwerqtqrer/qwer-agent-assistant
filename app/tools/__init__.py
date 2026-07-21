"""所有工具的统一注册入口"""

from app.tools.calculator import calculator
from app.tools.campus import query_campus_notice, query_course_schedule, query_grade
from app.tools.email_tool import send_email
from app.tools.sql_query import execute_sql_query
from app.tools.translation import translate_text
from app.tools.weather import get_weather

ALL_TOOLS = [
    get_weather,
    send_email,
    execute_sql_query,
    query_course_schedule,
    query_grade,
    query_campus_notice,
    translate_text,
    calculator,
]
