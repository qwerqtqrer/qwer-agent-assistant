-- 智慧校园 AI 智能体助手 - MySQL 初始化脚本
-- 执行：mysql -u root -p < scripts/init_db.sql

CREATE DATABASE IF NOT EXISTS school DEFAULT CHARACTER SET utf8mb4;
CREATE DATABASE IF NOT EXISTS oa_demo DEFAULT CHARACTER SET utf8mb4;
CREATE DATABASE IF NOT EXISTS abc DEFAULT CHARACTER SET utf8mb4;
CREATE DATABASE IF NOT EXISTS fruitdb DEFAULT CHARACTER SET utf8mb4;
CREATE DATABASE IF NOT EXISTS newsdb DEFAULT CHARACTER SET utf8mb4;

USE school;

CREATE TABLE IF NOT EXISTS student (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL,
    password VARCHAR(128) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_name VARCHAR(64) NOT NULL,
    course_name VARCHAR(128) NOT NULL,
    weekday VARCHAR(16) NOT NULL,
    start_time VARCHAR(16) NOT NULL,
    end_time VARCHAR(16) NOT NULL,
    location VARCHAR(128)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS grades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_name VARCHAR(64) NOT NULL,
    course_name VARCHAR(128) NOT NULL,
    score DECIMAL(5,1) NOT NULL,
    semester VARCHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    publish_time DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO student (username, password) VALUES ('2024001', 'demo123') ON DUPLICATE KEY UPDATE username=username;
INSERT INTO courses (student_name, course_name, weekday, start_time, end_time, location) VALUES
    ('张三', '高等数学', '星期一', '08:00', '09:40', '教一 101'),
    ('张三', '大学英语', '星期三', '10:00', '11:40', '外语楼 203'),
    ('张三', '数据结构', '星期五', '14:00', '15:40', '信息楼 305')
ON DUPLICATE KEY UPDATE course_name=course_name;
INSERT INTO grades (student_name, course_name, score, semester) VALUES
    ('张三', '高等数学', 88.0, '2025-2026-1'),
    ('张三', '大学英语', 92.0, '2025-2026-1'),
    ('张三', '数据结构', 85.0, '2025-2026-2')
ON DUPLICATE KEY UPDATE course_name=course_name;
INSERT INTO notices (title, content, publish_time) VALUES
    ('关于2026年秋季学期选课的通知', '选课预选阶段将于8月20日开始，请同学们及时关注教务系统。', '2026-08-10 09:00:00'),
    ('图书馆暑假开放安排', '暑假期间图书馆周一至周五开放，周末闭馆。', '2026-07-05 10:30:00')
ON DUPLICATE KEY UPDATE title=title;

USE oa_demo;

CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(200) NOT NULL DEFAULT '新会话',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT,
    extra_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS leaves (
    id INT PRIMARY KEY AUTO_INCREMENT,
    applicant VARCHAR(64) NOT NULL,
    leave_type VARCHAR(32) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status VARCHAR(32) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    review_comment TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reimbursements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    applicant VARCHAR(64) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    category VARCHAR(64),
    description TEXT,
    status VARCHAR(32) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    review_comment TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

USE abc;

CREATE TABLE IF NOT EXISTS student (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(64) NOT NULL,
    age VARCHAR(16)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS students_age (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ault VARCHAR(16)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO student (name, age) VALUES ('李四', '20'), ('王五', '21') ON DUPLICATE KEY UPDATE name=name;

USE fruitdb;

CREATE TABLE IF NOT EXISTS fruit (
    id INT PRIMARY KEY AUTO_INCREMENT,
    fruit_name VARCHAR(64) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    weight DECIMAL(10,2),
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO fruit (fruit_name, price, weight) VALUES
    ('苹果', 5.50, 0.20),
    ('香蕉', 4.00, 0.15),
    ('橙子', 6.80, 0.18)
ON DUPLICATE KEY UPDATE fruit_name=fruit_name;

USE newsdb;

CREATE TABLE IF NOT EXISTS category (
    id INT PRIMARY KEY AUTO_INCREMENT,
    NAME VARCHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS news (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    category_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO category (NAME) VALUES ('校园'), ('科技'), ('体育') ON DUPLICATE KEY UPDATE NAME=NAME;
