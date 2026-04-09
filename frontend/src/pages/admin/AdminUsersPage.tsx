/**
 * User management page for administrators. Lists users with role information.
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import type { User, PaginatedResponse } from '../../types/api';

export default function AdminUsersPage() {
  const { data, isLoading, isError } = useQuery<PaginatedResponse<User>>({
    queryKey: ['admin', 'users'],
    queryFn: () => apiClient.get('/users', { params: { per_page: 50 } }).then((r) => r.data),
  });

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">User Management</h1>
        <Link to="/admin/users/new"
          className="min-h-[44px] inline-flex items-center px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          Add User
        </Link>
      </div>

      {isLoading && <div className="flex items-center justify-center py-16"><Spinner label="Loading users" /></div>}
      {isError && <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load users.</div>}

      {data && data.items.length === 0 && <p className="text-gray-500 dark:text-gray-400 text-center py-16">No users found.</p>}

      {data && data.items.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Name</th>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Email</th>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Roles</th>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Status</th>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Last Login</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {data.items.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{user.display_name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{user.email}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {user.roles.map((role) => (
                        <span key={role.id} className="inline-block px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">{role.name}</span>
                      ))}
                      {user.is_superadmin && <span className="inline-block px-2 py-0.5 rounded text-xs bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300">superadmin</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {user.is_active
                      ? <span className="text-xs text-green-700 dark:text-green-400">Active</span>
                      : <span className="text-xs text-red-600 dark:text-red-400">Inactive</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400 text-xs">
                    {user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
