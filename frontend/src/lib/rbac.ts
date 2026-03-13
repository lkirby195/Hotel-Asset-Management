import type { UserRole } from '@/types/users';

const ROLE_HIERARCHY: Record<UserRole, number> = {
  executive: 3,
  operator: 2,
  manager: 1,
};

export function hasAccess(userRole: UserRole, requiredRole: UserRole): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
}

export function isAdmin(user: { role: string }): boolean {
  return user.role === 'admin';
}
