<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');

include('../config.php');

if (!isset($_GET['user_id'])) {
    http_response_code(400);
    echo json_encode(['error' => 'User ID is required']);
    exit;
}

$user_id = intval($_GET['user_id']);
$limit = isset($_GET['limit']) ? intval($_GET['limit']) : 50;
$offset = isset($_GET['offset']) ? intval($_GET['offset']) : 0;

try {
    $sql = "SELECT ua.*, u.username 
            FROM user_activities ua 
            LEFT JOIN users u ON ua.user_id = u.id 
            WHERE ua.user_id = ? 
            ORDER BY ua.created_at DESC 
            LIMIT ? OFFSET ?";
    
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("iii", $user_id, $limit, $offset);
    $stmt->execute();
    $result = $stmt->get_result();
    
    $activities = [];
    
    if ($result->num_rows > 0) {
        while($row = $result->fetch_assoc()) {
            $activities[] = [
                'id' => $row['id'],
                'activity_type' => $row['activity_type'],
                'activity_description' => $row['activity_description'],
                'tool_command' => $row['tool_command'],
                'input_data' => $row['input_data'],
                'output_data' => $row['output_data'],
                'execution_time' => $row['execution_time'],
                'status' => $row['status'],
                'ip_address' => $row['ip_address'],
                'created_at' => $row['created_at'],
                'username' => $row['username']
            ];
        }
    }
    
    // Get total count for pagination
    $count_sql = "SELECT COUNT(*) as total FROM user_activities WHERE user_id = ?";
    $count_stmt = $conn->prepare($count_sql);
    $count_stmt->bind_param("i", $user_id);
    $count_stmt->execute();
    $count_result = $count_stmt->get_result();
    $total = $count_result->fetch_assoc()['total'];
    
    echo json_encode([
        'activities' => $activities,
        'total' => $total,
        'limit' => $limit,
        'offset' => $offset
    ]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to fetch activities']);
}

$conn->close();
?>