-- Initialize database with default roles and admin user
-- This will be executed when the database container starts

-- Create default roles
INSERT INTO roles (role_name, permissions) VALUES 
('employee', '{"view_own_attendance": true, "view_present_employees": true}'),
('admin', '{"view_all_attendance": true, "enroll_employees": true, "manage_embeddings": true, "delete_employees": true, "view_camera_feed": true}'),
('super_admin', '{"view_all_attendance": true, "enroll_employees": true, "manage_embeddings": true, "delete_employees": true, "view_camera_feed": true, "manage_users": true, "manage_roles": true}')
ON CONFLICT (role_name) DO NOTHING;

-- Create default super admin user (password: admin123)
-- Password hash for 'admin123' using bcrypt
INSERT INTO users (username, password_hash, role_id) 
SELECT 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXzgVjHUxrLW', r.id 
FROM roles r WHERE r.role_name = 'super_admin'
ON CONFLICT (username) DO NOTHING;