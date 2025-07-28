<?php
include('session_check.php');
checkSession('admin');
$user = getUserInfo();
?>
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Admin Dashboard - Sokonalysis</title>
  <link rel="stylesheet" href="styles.css" />
  <link rel="stylesheet" href="modern-styles.css" />
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
  <!-- Header -->
  <header class="dashboard-header">
    <div class="header-content">
      <h1 class="dashboard-title">
        <i class="fas fa-chart-line"></i>
        Admin Dashboard
      </h1>
      <div class="header-actions">
        <div class="user-info">
          <span class="welcome-text">Welcome, <?php echo htmlspecialchars($user['full_name'] ?: $user['username']); ?></span>
          <span class="user-role"><?php echo ucfirst($user['role']); ?></span>
        </div>
        <button class="logout-btn" onclick="logout()">
          <i class="fas fa-sign-out-alt"></i>
          Logout
        </button>
      </div>
    </div>
  </header>

  <!-- Sidebar -->
  <div class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <h3><i class="fas fa-cog"></i> Admin Panel</h3>
    </div>
    <nav class="sidebar-nav">
      <a href="#" onclick="showSection('overview')" class="nav-item active" data-section="overview">
        <i class="fas fa-tachometer-alt"></i> Overview
      </a>
      <a href="#" onclick="showSection('users')" class="nav-item" data-section="users">
        <i class="fas fa-users"></i> Users Management
      </a>
      <a href="#" onclick="showSection('videos')" class="nav-item" data-section="videos">
        <i class="fas fa-video"></i> Video Management
      </a>
      <a href="#" onclick="showSection('activities')" class="nav-item" data-section="activities">
        <i class="fas fa-chart-bar"></i> User Activities
      </a>
      <a href="#" onclick="showSection('settings')" class="nav-item" data-section="settings">
        <i class="fas fa-cog"></i> Settings
      </a>
    </nav>
  </div>

  <!-- Main Content -->
  <div class="main-content">
    
    <!-- Overview Section -->
    <div id="overview" class="content-section active">
      <div class="section-header">
        <h2>Dashboard Overview</h2>
        <p>System statistics and quick actions</p>
      </div>
      
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-users"></i>
          </div>
          <div class="stat-info">
            <h3 id="totalUsers">Loading...</h3>
            <p>Total Users</p>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-video"></i>
          </div>
          <div class="stat-info">
            <h3 id="totalVideos">Loading...</h3>
            <p>Tutorial Videos</p>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-chart-line"></i>
          </div>
          <div class="stat-info">
            <h3 id="totalActivities">Loading...</h3>
            <p>User Activities</p>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-eye"></i>
          </div>
          <div class="stat-info">
            <h3 id="totalViews">Loading...</h3>
            <p>Video Views</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Users Management Section -->
    <div id="users" class="content-section">
      <div class="section-header">
        <h2>Users Management</h2>
        <p>Manage user accounts and permissions</p>
      </div>
      
      <div class="users-table-container">
        <table class="data-table" id="usersTable">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <!-- Users will be loaded dynamically -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- Video Management Section -->
    <div id="videos" class="content-section">
      <div class="section-header">
        <h2>Video Management</h2>
        <button class="btn-primary" onclick="showAddVideoForm()">
          <i class="fas fa-plus"></i> Add New Video
        </button>
      </div>
      
      <div class="videos-grid" id="adminVideosGrid">
        <!-- Videos will be loaded dynamically -->
      </div>
    </div>

    <!-- User Activities Section -->
    <div id="activities" class="content-section">
      <div class="section-header">
        <h2>User Activities</h2>
        <p>Monitor CLI tool usage and user interactions</p>
      </div>
      
      <div class="activities-table-container">
        <table class="data-table" id="activitiesTable">
          <thead>
            <tr>
              <th>User</th>
              <th>Activity</th>
              <th>Command</th>
              <th>Status</th>
              <th>Execution Time</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            <!-- Activities will be loaded dynamically -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- Settings Section -->
    <div id="settings" class="content-section">
      <div class="section-header">
        <h2>System Settings</h2>
        <p>Configure application settings</p>
      </div>
      
      <div class="settings-grid">
        <div class="setting-card">
          <h3>Database Management</h3>
          <p>Backup and restore database</p>
          <button class="btn-secondary">Backup Database</button>
        </div>
        
        <div class="setting-card">
          <h3>User Registration</h3>
          <p>Control user registration settings</p>
          <label class="toggle">
            <input type="checkbox" id="allowRegistration" checked>
            <span class="slider"></span>
          </label>
        </div>
        
        <div class="setting-card">
          <h3>System Logs</h3>
          <p>View and manage system logs</p>
          <button class="btn-secondary">View Logs</button>
        </div>
      </div>
    </div>

  </div>

  <!-- Add Video Modal -->
  <div id="addVideoModal" class="modal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Add New Tutorial Video</h3>
        <span class="close" onclick="closeAddVideoForm()">&times;</span>
      </div>
      <form id="addVideoForm">
        <div class="form-group">
          <label for="videoTitle">Title</label>
          <input type="text" id="videoTitle" name="title" required>
        </div>
        
        <div class="form-group">
          <label for="videoDescription">Description</label>
          <textarea id="videoDescription" name="description" rows="3"></textarea>
        </div>
        
        <div class="form-group">
          <label for="videoUrl">Video URL</label>
          <input type="url" id="videoUrl" name="video_url" required>
        </div>
        
        <div class="form-group">
          <label for="thumbnailUrl">Thumbnail URL</label>
          <input type="url" id="thumbnailUrl" name="thumbnail_url">
        </div>
        
        <div class="form-group">
          <label for="videoCategory">Category</label>
          <select id="videoCategory" name="category">
            <option value="Tutorial">Tutorial</option>
            <option value="Advanced">Advanced</option>
            <option value="Reference">Reference</option>
            <option value="Tips">Tips & Tricks</option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="videoDuration">Duration</label>
          <input type="text" id="videoDuration" name="duration" placeholder="e.g., 10:30">
        </div>
        
        <div class="modal-actions">
          <button type="button" class="btn-secondary" onclick="closeAddVideoForm()">Cancel</button>
          <button type="submit" class="btn-primary">Add Video</button>
        </div>
      </form>
    </div>
  </div>

  <script>
    // Navigation
    function showSection(sectionId) {
      // Hide all sections
      document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
      });
      
      // Remove active class from nav items
      document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
      });
      
      // Show selected section
      document.getElementById(sectionId).classList.add('active');
      
      // Add active class to nav item
      document.querySelector(`[data-section="${sectionId}"]`).classList.add('active');
      
      // Load section-specific data
      loadSectionData(sectionId);
    }

    // Load section data
    function loadSectionData(section) {
      switch(section) {
        case 'overview':
          loadDashboardStats();
          break;
        case 'users':
          loadUsers();
          break;
        case 'videos':
          loadAdminVideos();
          break;
        case 'activities':
          loadUserActivities();
          break;
      }
    }

    // Load dashboard statistics
    async function loadDashboardStats() {
      try {
        const response = await fetch('api/get_dashboard_stats.php');
        const stats = await response.json();
        
        document.getElementById('totalUsers').textContent = stats.total_users || '0';
        document.getElementById('totalVideos').textContent = stats.total_videos || '0';
        document.getElementById('totalActivities').textContent = stats.total_activities || '0';
        document.getElementById('totalViews').textContent = stats.total_views || '0';
      } catch (error) {
        console.error('Error loading stats:', error);
      }
    }

    // Load users
    async function loadUsers() {
      try {
        const response = await fetch('api/get_users.php');
        const users = await response.json();
        
        const tbody = document.querySelector('#usersTable tbody');
        tbody.innerHTML = users.map(user => `
          <tr>
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.full_name || 'N/A'}</td>
            <td>${user.email}</td>
            <td><span class="role-badge ${user.role}">${user.role}</span></td>
            <td>${new Date(user.created_at).toLocaleDateString()}</td>
            <td>
              <button class="btn-small btn-danger" onclick="deleteUser(${user.id})">
                <i class="fas fa-trash"></i>
              </button>
            </td>
          </tr>
        `).join('');
      } catch (error) {
        console.error('Error loading users:', error);
      }
    }

    // Load admin videos
    async function loadAdminVideos() {
      try {
        const response = await fetch('api/get_videos.php');
        const videos = await response.json();
        
        const container = document.getElementById('adminVideosGrid');
        container.innerHTML = videos.map(video => `
          <div class="admin-video-card">
            <div class="video-thumbnail">
              <img src="${video.thumbnail_url}" alt="${video.title}" />
            </div>
            <div class="video-info">
              <h4>${video.title}</h4>
              <p>${video.description}</p>
              <div class="video-meta">
                <span class="category">${video.category}</span>
                <span class="duration">${video.duration}</span>
                <span class="views">${video.views} views</span>
              </div>
              <div class="video-actions">
                <button class="btn-small btn-primary" onclick="editVideo(${video.id})">
                  <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-small btn-danger" onclick="deleteVideo(${video.id})">
                  <i class="fas fa-trash"></i> Delete
                </button>
              </div>
            </div>
          </div>
        `).join('');
      } catch (error) {
        console.error('Error loading videos:', error);
      }
    }

    // Load user activities
    async function loadUserActivities() {
      try {
        const response = await fetch('api/get_user_activities.php');
        const activities = await response.json();
        
        const tbody = document.querySelector('#activitiesTable tbody');
        tbody.innerHTML = activities.map(activity => `
          <tr>
            <td>${activity.username}</td>
            <td>${activity.activity_type}</td>
            <td><code>${activity.tool_command || 'N/A'}</code></td>
            <td><span class="status-badge ${activity.status}">${activity.status}</span></td>
            <td>${activity.execution_time}s</td>
            <td>${new Date(activity.created_at).toLocaleDateString()}</td>
          </tr>
        `).join('');
      } catch (error) {
        console.error('Error loading activities:', error);
      }
    }

    // Video management
    function showAddVideoForm() {
      document.getElementById('addVideoModal').style.display = 'block';
    }

    function closeAddVideoForm() {
      document.getElementById('addVideoModal').style.display = 'none';
      document.getElementById('addVideoForm').reset();
    }

    // Handle add video form submission
    document.getElementById('addVideoForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const formData = new FormData(this);
      
      try {
        const response = await fetch('api/add_video.php', {
          method: 'POST',
          body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
          alert('Video added successfully!');
          closeAddVideoForm();
          loadAdminVideos();
        } else {
          alert('Error adding video: ' + result.message);
        }
      } catch (error) {
        console.error('Error adding video:', error);
        alert('Error adding video');
      }
    });

    // Delete functions
    async function deleteUser(userId) {
      if (confirm('Are you sure you want to delete this user?')) {
        try {
          const response = await fetch('api/delete_user.php', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: userId })
          });
          
          const result = await response.json();
          
          if (result.success) {
            alert('User deleted successfully!');
            loadUsers();
          } else {
            alert('Error deleting user: ' + result.message);
          }
        } catch (error) {
          console.error('Error deleting user:', error);
          alert('Error deleting user');
        }
      }
    }

    async function deleteVideo(videoId) {
      if (confirm('Are you sure you want to delete this video?')) {
        try {
          const response = await fetch('api/delete_video.php', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ video_id: videoId })
          });
          
          const result = await response.json();
          
          if (result.success) {
            alert('Video deleted successfully!');
            loadAdminVideos();
          } else {
            alert('Error deleting video: ' + result.message);
          }
        } catch (error) {
          console.error('Error deleting video:', error);
          alert('Error deleting video');
        }
      }
    }

    // Logout function
    function logout() {
      if (confirm('Are you sure you want to log out?')) {
        window.location.href = 'logout.php';
      }
    }

    // Initialize dashboard
    document.addEventListener('DOMContentLoaded', function() {
      loadDashboardStats();
    });

    // Close modal when clicking outside
    window.onclick = function(event) {
      const modal = document.getElementById('addVideoModal');
      if (event.target == modal) {
        closeAddVideoForm();
      }
    }
  </script>
</body>
</html>