<?php
// Script to check existing database structure
include('config.php');

echo "<h2>Database Connection Test</h2>";

// Test connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
} else {
    echo "<p style='color: green;'>✅ Successfully connected to database: " . $conn->server_info . "</p>";
}

echo "<h3>Existing Tables in 'sokonalysis' database:</h3>";

// Get list of tables
$result = $conn->query("SHOW TABLES");
if ($result->num_rows > 0) {
    echo "<ul>";
    while($row = $result->fetch_array()) {
        $table_name = $row[0];
        echo "<li><strong>$table_name</strong>";
        
        // Get table structure
        $desc_result = $conn->query("DESCRIBE $table_name");
        if ($desc_result->num_rows > 0) {
            echo "<ul>";
            while($desc_row = $desc_result->fetch_assoc()) {
                echo "<li>" . $desc_row['Field'] . " (" . $desc_row['Type'] . ")</li>";
            }
            echo "</ul>";
        }
        echo "</li>";
    }
    echo "</ul>";
} else {
    echo "<p style='color: orange;'>⚠️ No tables found in the database.</p>";
}

echo "<h3>Required Tables for Web Application:</h3>";
echo "<ul>";
echo "<li><strong>admins</strong> - For admin user authentication</li>";
echo "<li><strong>users</strong> - For regular user authentication</li>";
echo "<li><strong>analyses</strong> - For storing user analysis data</li>";
echo "<li><strong>reports</strong> - For storing generated reports</li>";
echo "</ul>";

// Check if required tables exist
$required_tables = ['admins', 'users', 'analyses', 'reports'];
$missing_tables = [];

foreach ($required_tables as $table) {
    $check_result = $conn->query("SHOW TABLES LIKE '$table'");
    if ($check_result->num_rows == 0) {
        $missing_tables[] = $table;
    }
}

if (!empty($missing_tables)) {
    echo "<h3 style='color: red;'>❌ Missing Tables:</h3>";
    echo "<ul>";
    foreach ($missing_tables as $table) {
        echo "<li style='color: red;'>$table</li>";
    }
    echo "</ul>";
    echo "<p><strong>Action needed:</strong> Run the setup_database.sql script to create missing tables.</p>";
} else {
    echo "<h3 style='color: green;'>✅ All required tables exist!</h3>";
}

$conn->close();
?>

<!DOCTYPE html>
<html>
<head>
    <title>Database Check - Sokonalysis</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h2, h3 { color: #333; }
        ul { margin: 10px 0; }
        li { margin: 5px 0; }
    </style>
</head>
<body>
    <hr>
    <p><a href="index.html">← Back to Main Application</a></p>
</body>
</html>