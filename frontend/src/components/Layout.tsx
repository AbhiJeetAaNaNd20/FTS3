import React, { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { 
  HomeIcon, 
  UsersIcon, 
  ClockIcon, 
  CameraIcon, 
  CogIcon,
  LogOutIcon,
  UserIcon
} from 'lucide-react'
import clsx from 'clsx'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth()
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon, roles: ['employee', 'admin', 'super_admin'] },
    { name: 'Employees', href: '/employees', icon: UsersIcon, roles: ['employee', 'admin', 'super_admin'] },
    { name: 'Attendance', href: '/attendance', icon: ClockIcon, roles: ['employee', 'admin', 'super_admin'] },
    { name: 'Camera', href: '/camera', icon: CameraIcon, roles: ['admin', 'super_admin'] },
    { name: 'Admin', href: '/admin', icon: CogIcon, roles: ['admin', 'super_admin'] },
  ]

  const filteredNavigation = navigation.filter(item => 
    item.roles.includes(user?.role_name || '')
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg">
        <div className="flex h-16 items-center justify-center border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">Face Recognition</h1>
        </div>
        
        <nav className="mt-8 px-4">
          <ul className="space-y-2">
            {filteredNavigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={clsx(
                      'flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
                      isActive
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    )}
                  >
                    <item.icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* User info and logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
          <div className="flex items-center mb-3">
            <UserIcon className="h-8 w-8 text-gray-400" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">{user?.username}</p>
              <p className="text-xs text-gray-500 capitalize">{user?.role_name?.replace('_', ' ')}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors duration-200"
          >
            <LogOutIcon className="mr-3 h-4 w-4" />
            Sign out
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <main className="py-8 px-8">
          {children}
        </main>
      </div>
    </div>
  )
}