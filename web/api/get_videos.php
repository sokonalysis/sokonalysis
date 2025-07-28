<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');

include('../config.php');

try {
    $sql = "SELECT v.*, u.username as uploader_name 
            FROM videos v 
            LEFT JOIN users u ON v.uploaded_by = u.id 
            ORDER BY v.created_at DESC";
    
    $result = $conn->query($sql);
    $videos = [];
    
    if ($result->num_rows > 0) {
        while($row = $result->fetch_assoc()) {
            $videos[] = [
                'id' => $row['id'],
                'title' => $row['title'],
                'description' => $row['description'],
                'video_url' => $row['video_url'],
                'thumbnail_url' => $row['thumbnail_url'],
                'category' => $row['category'],
                'duration' => $row['duration'],
                'views' => $row['views'],
                'uploader_name' => $row['uploader_name'],
                'created_at' => $row['created_at']
            ];
        }
    }
    
    echo json_encode($videos);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to fetch videos']);
}

$conn->close();
?>