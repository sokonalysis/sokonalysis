-- Database setup for sokonalysisWeb application
-- Run this script in phpMyAdmin or MySQL command line

CREATE DATABASE IF NOT EXISTS sokonalysisWeb;
USE sokonalysisWeb;

-- Create users table (combined admin and regular users)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    full_name VARCHAR(100),
    profile_image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create videos table for admin uploaded videos
CREATE TABLE IF NOT EXISTS videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    video_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    uploaded_by INT,
    category VARCHAR(100),
    duration VARCHAR(20),
    views INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE
);

-- Create user_activities table to track CLI tool activities
CREATE TABLE IF NOT EXISTS user_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    activity_description TEXT,
    tool_command VARCHAR(500),
    input_data TEXT,
    output_data TEXT,
    execution_time DECIMAL(10,3),
    status ENUM('success', 'error', 'pending') DEFAULT 'pending',
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create api_logs table for CLI integration tracking
CREATE TABLE IF NOT EXISTS api_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    request_data TEXT,
    response_data TEXT,
    status_code INT,
    execution_time DECIMAL(10,3),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create sessions table for user session management
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password, role, full_name) VALUES 
('admin', 'admin@sokonalysis.com', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin', 'System Administrator');

-- Insert sample videos
INSERT INTO videos (title, description, video_url, thumbnail_url, uploaded_by, category, duration) VALUES 
('Getting Started with Sokonalysis', 'Learn the basics of using the Sokonalysis CLI tool', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg', 1, 'Tutorial', '10:30'),
('Advanced Data Analysis', 'Deep dive into advanced analysis features', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg', 1, 'Advanced', '15:45'),
('CLI Commands Overview', 'Complete guide to all available CLI commands', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg', 1, 'Reference', '8:20');