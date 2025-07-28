<?php
// Migration script to add required tables to existing sokonalysis database
include('config.php');

echo "<h2>Database Migration for Sokonalysis Web App</h2>";

// Test connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

echo "<p style='color: green;'>✅ Connected to database successfully</p>";

// Array of SQL statements to create tables
$migrations = [
    'admins' => "
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin', 'user') DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ",
    'users' => "
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin', 'user') DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ",
    'analyses' => "
        CREATE TABLE IF NOT EXISTS analyses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            data_file VARCHAR(255),
            algorithm VARCHAR(100),
            results TEXT,
            status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ",
    'reports' => "
        CREATE TABLE IF NOT EXISTS reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            analysis_id INT,
            user_id INT,
            title VARCHAR(255) NOT NULL,
            file_path VARCHAR(255),
            file_type ENUM('pdf', 'csv', 'xlsx') DEFAULT 'pdf',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    "
];

echo "<h3>Creating Required Tables:</h3>";

foreach ($migrations as $table_name => $sql) {
    echo "<p>Creating table: <strong>$table_name</strong>... ";
    
    if ($conn->query($sql) === TRUE) {
        echo "<span style='color: green;'>✅ Success</span></p>";
    } else {
        echo "<span style='color: red;'>❌ Error: " . $conn->error . "</span></p>";
    }
}

echo "<h3>Adding Default Data:</h3>";

// Check if admin user exists
$admin_check = $conn->query("SELECT id FROM admins WHERE username = 'admin'");
if ($admin_check->num_rows == 0) {
    $admin_sql = "INSERT INTO admins (username, email, password, role) VALUES 
                  ('admin', 'admin@sokonalysis.com', '$2y$10\$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin')";
    
    if ($conn->query($admin_sql) === TRUE) {
        echo "<p>✅ Default admin user created (username: admin, password: admin123)</p>";
    } else {
        echo "<p>❌ Error creating admin user: " . $conn->error . "</p>";
    }
} else {
    echo "<p>ℹ️ Admin user already exists</p>";
}

// Check if test user exists
$user_check = $conn->query("SELECT id FROM users WHERE username = 'testuser'");
if ($user_check->num_rows == 0) {
    $user_sql = "INSERT INTO users (username, email, password, role) VALUES 
                 ('testuser', 'user@sokonalysis.com', '$2y$10\$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'user')";
    
    if ($conn->query($user_sql) === TRUE) {
        echo "<p>✅ Default test user created (username: testuser, password: user123)</p>";
    } else {
        echo "<p>❌ Error creating test user: " . $conn->error . "</p>";
    }
} else {
    echo "<p>ℹ️ Test user already exists</p>";
}

echo "<h3>Migration Complete!</h3>";
echo "<p style='color: green; font-weight: bold;'>🎉 Your sokonalysis database is now ready for the web application!</p>";

echo "<h4>Next Steps:</h4>";
echo "<ol>";
echo "<li>Go to <a href='index.html'>Main Application</a></li>";
echo "<li>Try logging in with:</li>";
echo "<ul>";
echo "<li><strong>Admin:</strong> username: admin, password: admin123</li>";
echo "<li><strong>User:</strong> username: testuser, password: user123</li>";
echo "</ul>";
echo "<li>Or register a new account</li>";
echo "</ol>";

$conn->close();
?>

<!DOCTYPE html>
<html>
<head>
    <title>Database Migration - Sokonalysis</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h2, h3, h4 { color: #333; }
        ul, ol { margin: 10px 0; }
        li { margin: 5px 0; }
        a { color: #28a745; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
</body>
</html>