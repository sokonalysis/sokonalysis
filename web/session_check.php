<?php
session_start();

function checkSession($required_role = null) {
    if (!isset($_SESSION['user_id']) || !isset($_SESSION['username'])) {
        header("Location: index.html");
        exit;
    }
    
    if ($required_role && $_SESSION['role'] !== $required_role) {
        header("Location: index.html");
        exit;
    }
    
    return true;
}

function getUserInfo() {
    if (!isset($_SESSION['user_id'])) {
        return null;
    }
    
    return [
        'id' => $_SESSION['user_id'],
        'username' => $_SESSION['username'],
        'role' => $_SESSION['role'],
        'full_name' => $_SESSION['full_name'] ?? '',
        'email' => $_SESSION['email'] ?? ''
    ];
}
?>