/** Permission check hook. Returns boolean for a given action. */
import { useAuth } from './useAuth';
import { checkPermission } from '../services/permissions';

export function usePermission(action: string, resource?: string): boolean {
  const { user } = useAuth();
  if (!user) return false;
  const roles = user.is_superadmin
    ? ['superadmin']
    : user.roles.map((r) => r.name);
  return checkPermission(roles, action, resource);
}
