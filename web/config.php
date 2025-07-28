<?php
$host = "localhost";
$user = "root";
$password = ""; // No password for default XAMPP setup
$database = "sokonalysisWeb";

$conn = new mysqli($host, $user, $password, $database, 3306); 
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
?>
