<?php
// Simple database setup script
include('config.php');

echo "<h2>Database Setup</h2>";

// Create the correct users table structure
$users_table_sql = "
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
)";

if ($conn->query($users_table_sql)) {
    echo "<p style='color: green;'>✓ Users table created/verified successfully</p>";
} else {
    echo "<p style='color: red;'>✗ Error creating users table: " . $conn->error . "</p>";
}

// Check if admin user exists, if not create one
$admin_check = $conn->query("SELECT id FROM users WHERE username = 'admin' AND role = 'admin'");
if ($admin_check->num_rows == 0) {
    $admin_password = password_hash('admin123', PASSWORD_DEFAULT);
    $admin_sql = "INSERT INTO users (username, email, password, role, full_name) VALUES 
                  ('admin', 'admin@sokonalysis.com', '$admin_password', 'admin', 'System Administrator')";
    
    if ($conn->query($admin_sql)) {
        echo "<p style='color: green;'>✓ Default admin user created</p>";
        echo "<p><strong>Admin Login:</strong> username: admin, password: admin123</p>";
    } else {
        echo "<p style='color: red;'>✗ Error creating admin user: " . $conn->error . "</p>";
    }
} else {
    echo "<p style='color: blue;'>ℹ Admin user already exists</p>";
}

// Create videos table for tutorials
$videos_table_sql = "
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
)";

if ($conn->query($videos_table_sql)) {
    echo "<p style='color: green;'>✓ Videos table created/verified successfully</p>";
} else {
    echo "<p style='color: red;'>✗ Error creating videos table: " . $conn->error . "</p>";
}

// Insert sample videos if none exist
$video_check = $conn->query("SELECT COUNT(*) as count FROM videos");
$video_count = $video_check->fetch_assoc()['count'];

if ($video_count == 0) {
    $sample_videos = [
        ['Advanced SQL Injection Techniques', 'Learn advanced SQL injection methods for penetration testing', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg', 'Hacking', '15:30'],
        ['Network Reconnaissance with Nmap', 'Master network scanning and reconnaissance techniques', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg', 'Network', '12:45'],
        ['Social Engineering Fundamentals', 'Psychological manipulation techniques for security testing', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg', 'Social', '18:20']
    ];
    
    foreach ($sample_videos as $video) {
        $stmt = $conn->prepare("INSERT INTO videos (title, description, video_url, thumbnail_url, uploaded_by, category, duration) VALUES (?, ?, ?, ?, 1, ?, ?)");
        $stmt->bind_param("ssssss", $video[0], $video[1], $video[2], $video[3], $video[4], $video[5]);
        $stmt->execute();
    }
    echo "<p style='color: green;'>✓ Sample hacking tutorials added</p>";
}

echo "<h3>Current Users:</h3>";
$result = $conn->query("SELECT id, username, email, role, full_name, created_at FROM users");
if ($result) {
    echo "<table border='1' style='border-collapse: collapse; width: 100%;'>";
    echo "<tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Full Name</th><th>Created</th></tr>";
    while ($row = $result->fetch_assoc()) {
        echo "<tr>";
        echo "<td>" . $row['id'] . "</td>";
        echo "<td>" . $row['username'] . "</td>";
        echo "<td>" . $row['email'] . "</td>";
        echo "<td>" . $row['role'] . "</td>";
        echo "<td>" . $row['full_name'] . "</td>";
        echo "<td>" . $row['created_at'] . "</td>";
        echo "</tr>";
    }
    echo "</table>";
}

$conn->close();
echo "<br><p><strong>Setup complete!</strong></p>";
echo "<p><a href='login.php' style='color: #00ff41; text-decoration: none;'>→ Go to Login Page</a></p>";
echo "<p><a href='index.html' style='color: #00ff41; text-decoration: none;'>→ Go to Home Page</a></p>";
?>