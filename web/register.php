<?php
session_start();

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    include('config.php');

    
    $username = trim($_POST['username']);
    $email = trim($_POST['email']);
    $password = $_POST['password'];
    $confirm_password = $_POST['confirm_password'];
    $full_name = trim($_POST['full_name']);
    $role = 'user'; // Default to user role for public registration
    
    // Validate input
    if (empty($username) || empty($email) || empty($password) || empty($full_name)) {
        header("Location: index.html?error=" . urlencode("All fields are required."));
        exit;
    } elseif ($password !== $confirm_password) {
        header("Location: index.html?error=" . urlencode("Passwords do not match."));
        exit;
    } elseif (strlen($password) < 6) {
        header("Location: index.html?error=" . urlencode("Password must be at least 6 characters long."));
        exit;
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        header("Location: index.html?error=" . urlencode("Please enter a valid email address."));
        exit;
    } elseif (strlen($username) < 3) {
        header("Location: index.html?error=" . urlencode("Username must be at least 3 characters long."));
        exit;
    } else {
        // Hash password
        $hashed_password = password_hash($password, PASSWORD_DEFAULT);
        
        // Check if username or email already exists
        $check_stmt = $conn->prepare("SELECT id FROM users WHERE username = ? OR email = ?");
        if ($check_stmt) {
            $check_stmt->bind_param("ss", $username, $email);
            $check_stmt->execute();
            $check_result = $check_stmt->get_result();
            
            if ($check_result->num_rows > 0) {
                header("Location: index.html?error=" . urlencode("Username or email already exists."));
                exit;
            } else {
                // Insert new user
                $stmt = $conn->prepare("INSERT INTO users (username, email, password, full_name, role) VALUES (?, ?, ?, ?, ?)");
                if ($stmt) {
                    $stmt->bind_param("sssss", $username, $email, $hashed_password, $full_name, $role);
                    
                    if ($stmt->execute()) {
                        header("Location: index.html?success=" . urlencode("Registration successful! You can now log in."));
                        exit;
                    } else {
                        header("Location: index.html?error=" . urlencode("Registration failed. Please try again."));
                        exit;
                    }
                    $stmt->close();
                } else {
                    header("Location: index.html?error=" . urlencode("Database error. Please try again."));
                    exit;
                }
            }
            $check_stmt->close();
        } else {
            header("Location: index.html?error=" . urlencode("Database error. Please try again."));
            exit;
        }
    }
}
?>