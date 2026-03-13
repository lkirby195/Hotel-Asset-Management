export type UserRole = 'executive' | 'operator' | 'manager';

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: UserRole;
  is_active: boolean;
  property_ids: string[];
}

export type DepartmentType = 'rooms' | 'fb' | 'spa' | 'golf' | 'retail' | 'mountain' | 'other';

export interface Property {
  id: string;
  tenant_id?: string;
  name: string;
  code: string;
  departments: { id: string; type: DepartmentType; name: string; is_active: boolean }[];
  timezone: string;
  is_active?: boolean;
}
