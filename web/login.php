<?php
session_start();

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    include('config.php');
    $username = trim($_POST['username']);
    $password = $_POST['password'];
    $role = $_POST['role'] ?? 'user';

    // Validate input
    if (empty($username) || empty($password)) {
        header("Location: index.html?error=" . urlencode("Username and password are required."));
        exit;
    } else {
        // Check user in unified users table
        $stmt = $conn->prepare("SELECT * FROM users WHERE username = ? AND role = ?");
        if ($stmt) {
            $stmt->bind_param("ss", $username, $role);
            $stmt->execute();
            $result = $stmt->get_result();
            $user = $result->fetch_assoc();

            if ($user && password_verify($password, $user['password'])) {
                $_SESSION['user_id'] = $user['id'];
                $_SESSION['username'] = $user['username'];
                $_SESSION['role'] = $user['role'];
                $_SESSION['full_name'] = $user['full_name'];
                $_SESSION['email'] = $user['email'];
                
                if ($user['role'] === 'admin') {
                    header("Location: admin-dashboard.php");
                } else {
                    header("Location: dashboard.php");
                }
                exit;
            } else {
                // Redirect back to index.html with error
                header("Location: index.html?error=" . urlencode("Invalid username, password, or role."));
                exit;
            }
            $stmt->close();
        } else {
            header("Location: index.html?error=" . urlencode("Database error. Please try again."));
            exit;
        }
    }
}
?>
