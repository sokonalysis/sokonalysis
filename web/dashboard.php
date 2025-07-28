<?php
session_start();

if (!isset($_SESSION['user_id'])) {
    header("Location: login.php");
    exit;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - sokonalysis</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <h1>Welcome, <?php echo htmlspecialchars($_SESSION['full_name'] ?? $_SESSION['username']); ?>!</h1>
            <div class="user-info">
                <span>Role: <?php echo ucfirst($_SESSION['role']); ?></span>
                <a href="logout.php" class="logout-btn">Logout</a>
            </div>
        </header>
        
        <main class="dashboard-content">
            <div class="dashboard-grid">
                <div class="dashboard-card">
                    <h3>Profile Information</h3>
                    <p><strong>Username:</strong> <?php echo htmlspecialchars($_SESSION['username']); ?></p>
                    <p><strong>Email:</strong> <?php echo htmlspecialchars($_SESSION['email']); ?></p>
                    <p><strong>Role:</strong> <?php echo ucfirst($_SESSION['role']); ?></p>
                </div>
                
                <?php if ($_SESSION['role'] === 'admin'): ?>
                <div class="dashboard-card">
                    <h3>Admin Functions</h3>
                    <p>Access to admin-specific features</p>
                    <a href="admin-dashboard.php" class="primary-btn">Go to Admin Dashboard</a>
                </div>
                <?php endif; ?>
                
                <div class="dashboard-card">
                    <h3>Quick Actions</h3>
                    <p>Common tasks and features</p>
                    <div class="action-buttons">
                        <button class="secondary-btn">View Reports</button>
                        <button class="secondary-btn">Settings</button>
                    </div>
                </div>
            </div>
        </main>
    </div>
</body>
</html>
