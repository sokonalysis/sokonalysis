<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

include('../config.php');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);

if (!isset($input['video_id'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Video ID is required']);
    exit;
}

$video_id = intval($input['video_id']);

try {
    $sql = "UPDATE videos SET views = views + 1 WHERE id = ?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("i", $video_id);
    
    if ($stmt->execute()) {
        echo json_encode(['success' => true, 'message' => 'View count updated']);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to update view count']);
    }
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error']);
}

$conn->close();
?>