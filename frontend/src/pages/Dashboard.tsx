import React from 'react'
import { useQuery } from 'react-query'
import { useAuth } from '../hooks/useAuth'
import { attendanceApi, adminApi } from '../services/api'
import { UsersIcon, ClockIcon, CheckCircleIcon, XCircleIcon } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import { format } from 'date-fns'

export default function Dashboard() {
  const { user } = useAuth()
  const isAdmin = user?.role_name === 'admin' || user?.role_name === 'super_admin'

  // Get present employees for all users
  const { data: presentData, isLoading: presentLoading } = useQuery(
    'present-employees',
    attendanceApi.getPresentEmployees,
    { refetchInterval: 30000 } // Refresh every 30 seconds
  )

  // Get admin dashboard data for admins
  const { data: adminData, isLoading: adminLoading } = useQuery(
    'admin-dashboard',
    adminApi.getDashboard,
    { 
      enabled: isAdmin,
      refetchInterval: 60000 // Refresh every minute
    }
  )

  // Get user's own attendance for employees
  const { data: userAttendance, isLoading: attendanceLoading } = useQuery(
    ['user-attendance', user?.username],
    () => attendanceApi.getEmployeeAttendance(user!.username, { per_page: 5 }),
    { 
      enabled: !isAdmin && !!user?.username,
      refetchInterval: 60000
    }
  )

  if (presentLoading || (isAdmin && adminLoading) || (!isAdmin && attendanceLoading)) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome back, {user?.username}
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {isAdmin && adminData && (
          <>
            <div className="card">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <UsersIcon className="h-8 w-8 text-primary-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Employees</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {adminData.statistics.total_employees}
                  </p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckCircleIcon className="h-8 w-8 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Today's Check-ins</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {adminData.statistics.today_checkins}
                  </p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <XCircleIcon className="h-8 w-8 text-red-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Today's Check-outs</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {adminData.statistics.today_checkouts}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Present Now</p>
              <p className="text-2xl font-bold text-gray-900">
                {presentData?.total_present || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Present Employees */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Currently Present</h3>
          <div className="space-y-3">
            {presentData?.present_employees
              ?.filter(emp => emp.is_present)
              ?.slice(0, 5)
              ?.map((employee) => (
                <div key={employee.employee_id} className="flex items-center justify-between py-2">
                  <div>
                    <p className="font-medium text-gray-900">{employee.employee_name}</p>
                    <p className="text-sm text-gray-500">ID: {employee.employee_id}</p>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Present
                    </span>
                    {employee.last_timestamp && (
                      <p className="text-xs text-gray-500 mt-1">
                        Since {format(new Date(employee.last_timestamp), 'HH:mm')}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            
            {(!presentData?.present_employees?.some(emp => emp.is_present)) && (
              <p className="text-gray-500 text-center py-4">No employees currently present</p>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {isAdmin ? 'Recent Activity' : 'Your Recent Activity'}
          </h3>
          <div className="space-y-3">
            {isAdmin && adminData?.recent_activity?.slice(0, 5).map((activity, index) => (
              <div key={index} className="flex items-center justify-between py-2">
                <div>
                  <p className="font-medium text-gray-900">{activity.employee_name}</p>
                  <p className="text-sm text-gray-500">
                    {activity.event_type === 'check_in' ? 'Checked in' : 'Checked out'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-900">
                    {format(new Date(activity.timestamp), 'MMM dd, HH:mm')}
                  </p>
                  {activity.confidence_score && (
                    <p className="text-xs text-gray-500">
                      {Math.round(activity.confidence_score * 100)}% confidence
                    </p>
                  )}
                </div>
              </div>
            ))}

            {!isAdmin && userAttendance?.records?.slice(0, 5).map((record) => (
              <div key={record.id} className="flex items-center justify-between py-2">
                <div>
                  <p className="font-medium text-gray-900">
                    {record.event_type === 'check_in' ? 'Checked in' : 'Checked out'}
                  </p>
                  <p className="text-sm text-gray-500">Camera {record.camera_id}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-900">
                    {format(new Date(record.timestamp), 'MMM dd, HH:mm')}
                  </p>
                  {record.confidence_score && (
                    <p className="text-xs text-gray-500">
                      {Math.round(record.confidence_score * 100)}% confidence
                    </p>
                  )}
                </div>
              </div>
            ))}

            {isAdmin && (!adminData?.recent_activity?.length) && (
              <p className="text-gray-500 text-center py-4">No recent activity</p>
            )}

            {!isAdmin && (!userAttendance?.records?.length) && (
              <p className="text-gray-500 text-center py-4">No recent activity</p>
            )}
          </div>
        </div>
      </div>

      {/* System Health (Admin only) */}
      {isAdmin && adminData && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {adminData.system_health.total_logs_24h}
              </p>
              <p className="text-sm text-gray-500">Total Logs (24h)</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">
                {adminData.system_health.error_logs_24h}
              </p>
              <p className="text-sm text-gray-500">Error Logs (24h)</p>
            </div>
            <div className="text-center">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                adminData.system_health.system_status === 'healthy' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {adminData.system_health.system_status}
              </span>
              <p className="text-sm text-gray-500 mt-1">System Status</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}