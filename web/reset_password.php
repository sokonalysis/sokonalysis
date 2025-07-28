<?php
session_start();

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    include('config.php');
    
    $email = $_POST['email'];
    
    if (empty($email)) {
        $error = "Email is required.";
    } else {
        // Check if email exists in either table
        $stmt_admin = $conn->prepare("SELECT id, username FROM admins WHERE email = ?");
        $stmt_admin->bind_param("s", $email);
        $stmt_admin->execute();
        $result_admin = $stmt_admin->get_result();
        
        $stmt_user = $conn->prepare("SELECT id, username FROM users WHERE email = ?");
        $stmt_user->bind_param("s", $email);
        $stmt_user->execute();
        $result_user = $stmt_user->get_result();
        
        if ($result_admin->num_rows > 0 || $result_user->num_rows > 0) {
            // In a real application, you would:
            // 1. Generate a unique reset token
            // 2. Store it in the database with expiration
            // 3. Send an email with the reset link
            
            // For demo purposes, we'll just show a success message
            $success = "If an account with that email exists, a password reset link has been sent.";
        } else {
            // Don't reveal if email exists or not for security
            $success = "If an account with that email exists, a password reset link has been sent.";
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset - sokonalysis</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="login-container">
        <div class="login-card">
            <h2>Password Reset</h2>
            
            <?php if (isset($error)): ?>
                <div style="color: red; margin-bottom: 15px; text-align: center;">
                    <?php echo htmlspecialchars($error); ?>
                </div>
            <?php endif; ?>
            
            <?php if (isset($success)): ?>
                <div style="color: green; margin-bottom: 15px; text-align: center;">
                    <?php echo htmlspecialchars($success); ?>
                </div>
            <?php endif; ?>
            
            <form method="post">
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" placeholder="Enter your email" required>
                </div>
                
                <button type="submit" class="primary-btn">Send Reset Link</button>
            </form>
            
            <div style="text-align: center; margin-top: 20px;">
                <a href="index.html" style="color: var(--green); text-decoration: none;">
                    ← Back to Login
                </a>
            </div>
        </div>
    </div>
</body>
</html>