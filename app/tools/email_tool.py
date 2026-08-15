"""邮件发送工具：QQ SMTP，失败时返回真实错误而非伪成功。"""

import re
import smtplib
from email.mime.text import MIMEText

from langchain.tools import tool

from app.core.config import config
from app.core.logging import get_logger

logger = get_logger("app.tools.email")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@tool
def send_email(subject: str, content: str, receiver: str) -> str:
    """
    发送邮件的工具
    :param subject: 邮件主题
    :param content: 邮件内容
    :param receiver: 收件人邮箱
    """
    if not (config.mail_user and config.mail_pass and config.mail_sender):
        return "邮件服务未配置（MAIL_USER/MAIL_PASS/MAIL_SENDER），请先配置后再发送。"
    if not _EMAIL_RE.match(receiver):
        return f"收件人邮箱格式不正确：{receiver}"
    if not subject.strip():
        return "错误：邮件主题不能为空。"

    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = config.mail_sender
    msg["To"] = receiver
    msg["Subject"] = subject

    try:
        smtp = smtplib.SMTP_SSL(config.mail_host, config.mail_port, timeout=10)
        smtp.login(config.mail_user, config.mail_pass)
        smtp.sendmail(config.mail_sender, [receiver], msg.as_string())
        smtp.quit()
        logger.info("邮件发送成功：%s", receiver)
        return f"邮件已成功发送给 {receiver}。"
    except Exception as exc:
        logger.error("邮件发送失败：%s", exc)
        return f"邮件发送失败：{exc}"
