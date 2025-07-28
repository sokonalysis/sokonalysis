# Sokonalysis - Elite Hacker Data Analysis Platform

A cyberpunk-themed web application for data analysis with a hacker aesthetic and advanced security features.

## Features

- **User Authentication**: Login/Register system with role-based access (Admin/User)
- **Responsive Design**: Mobile-friendly interface with dark/light theme support
- **Dashboard System**: Separate dashboards for admins and users
- **Modern UI**: Clean, professional design with smooth animations
- **Database Integration**: MySQL backend for user management and data storage

## Installation

### Prerequisites

- XAMPP (Apache + MySQL + PHP)
- Web browser
- Text editor (optional)

### Setup Instructions

1. **Install XAMPP**
   - Download and install XAMPP from [https://www.apachefriends.org/](https://www.apachefriends.org/)
   - Start Apache and MySQL services

2. **Database Setup**
   - Open phpMyAdmin (http://localhost/phpmyadmin)
   - Import the `setup_database.sql` file to create the database and tables
   - Or run the SQL commands manually

3. **File Placement**
   - Ensure all files are in the `c:/xampp/XAMPP/htdocs/sokonalysisWEB/` directory
   - Verify file permissions are set correctly

4. **Configuration**
   - Check `config.php` for database connection settings
   - Default settings should work with standard XAMPP installation

### Default Login Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`
- Role: Admin

**User Account:**
- Username: `testuser`
- Password: `user123`
- Role: User

## File Structure

```
sokonalysisWEB/
├── index.html              # Main landing page with login/register
├── admin-dashboard.html    # Admin dashboard
├── user-dashboard.html     # User dashboard
├── styles.css             # Main stylesheet
├── config.php             # Database configuration
├── login.php              # Login processing
├── register.php           # Registration processing
├── reset_password.php     # Password reset
├── setup_database.sql     # Database setup script
└── README.md              # This file
```

## Usage

1. **Access the Application**
   - Open your browser and go to `http://localhost/sokonalysisWEB/`

2. **Register New Account**
   - Click "Sign Up" tab
   - Fill in username, email, password
   - Select role (Admin or User)
   - Submit form

3. **Login**
   - Use existing credentials or newly created account
   - Select appropriate role
   - You'll be redirected to the corresponding dashboard

4. **Features**
   - Toggle between light/dark themes
   - Navigate using the sidebar menu
   - Access role-specific features

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure MySQL is running in XAMPP
   - Check database name in `config.php`
   - Verify database was created properly

2. **Login Not Working**
   - Check if database tables exist
   - Verify default users were inserted
   - Check browser console for JavaScript errors

3. **Pages Not Loading**
   - Ensure Apache is running
   - Check file paths are correct
   - Verify all files are in the correct directory

### Error Messages

- **"Connection failed"**: MySQL service not running
- **"Invalid username or password"**: Check credentials or database data
- **"Page not found"**: Check file paths and Apache configuration

## Development

### Adding New Features

1. **Database Changes**
   - Update `setup_database.sql`
   - Add new tables or columns as needed

2. **Frontend Changes**
   - Modify HTML files for new pages
   - Update `styles.css` for styling
   - Add JavaScript for interactivity

3. **Backend Changes**
   - Create new PHP files for processing
   - Update existing PHP files for new functionality

### Security Considerations

- Passwords are hashed using PHP's `password_hash()`
- SQL injection protection using prepared statements
- Session management for user authentication
- Input validation and sanitization

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers

## License

This project is open source and available under the MIT License.

## Support

For issues or questions, please check the troubleshooting section or create an issue in the project repository.