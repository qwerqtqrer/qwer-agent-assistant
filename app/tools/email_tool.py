"""邮件发送工具"""

import smtplib
from email.mime.text import MIMEText

from langchain.tools import tool

from app.config import config


@tool
def send_email(subject: str, content: str, receiver: str) -> str:
    """
    发送邮件的工具
    :param subject: 邮件主题
    :param content: 邮件内容
    :param receiver: 收件人邮箱
    """
    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = config.MAIL_SENDER
    msg["To"] = receiver
    msg["Subject"] = subject

    try:
        smtp = smtplib.SMTP_SSL(config.MAIL_HOST, 465)
        smtp.login(config.MAIL_USER, config.MAIL_PASS)
        smtp.sendmail(config.MAIL_SENDER, [receiver], msg.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException as e:
        print("Error: 无法发送邮件", e)
    finally:
        return "邮件发送成功！"
