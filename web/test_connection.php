<?php
// Test database connection and table structure
include('config.php');

echo "<h2>Database Connection Test</h2>";

// Test connection
if ($conn->connect_error) {
    echo "<p style='color: red;'>Connection failed: " . $conn->connect_error . "</p>";
    exit;
} else {
    echo "<p style='color: green;'>Database connection successful!</p>";
}

// Check if users table exists and show structure
$result = $conn->query("DESCRIBE users");
if ($result) {
    echo "<h3>Users table structure:</h3>";
    echo "<table border='1' style='border-collapse: collapse;'>";
    echo "<tr><th>Field</th><th>Type</th><th>Null</th><th>Key</th><th>Default</th><th>Extra</th></tr>";
    while ($row = $result->fetch_assoc()) {
        echo "<tr>";
        echo "<td>" . $row['Field'] . "</td>";
        echo "<td>" . $row['Type'] . "</td>";
        echo "<td>" . $row['Null'] . "</td>";
        echo "<td>" . $row['Key'] . "</td>";
        echo "<td>" . $row['Default'] . "</td>";
        echo "<td>" . $row['Extra'] . "</td>";
        echo "</tr>";
    }
    echo "</table>";
} else {
    echo "<p style='color: red;'>Users table does not exist or error occurred: " . $conn->error . "</p>";
}

// Count existing users
$result = $conn->query("SELECT COUNT(*) as count FROM users");
if ($result) {
    $row = $result->fetch_assoc();
    echo "<p>Total users in database: " . $row['count'] . "</p>";
}

$conn->close();
?>