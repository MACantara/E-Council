export interface User {
  users_id: number;
  users_first_name: string;
  users_last_name: string;
  users_username: string;
  users_email: string;
  users_role: string;
  users_department_name: string;
  users_email_verified: number;
  users_student_organization?: number | null;
  users_student_organization_position?: string | null;
  profile_picture?: { url: string } | null;
  signature?: { url: string } | null;
}

export interface PaginationMetadata {
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface PaginatedList<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: {
    items: T[];
    pagination: PaginationMetadata;
  };
}

export interface SingleResponse<T> {
  success: boolean;
  data: T;
}

export interface MessageResponse {
  message: string;
}

export interface ImageItem {
  url: string;
  public_id?: string | null;
}

export interface Resource {
  [key: string]: unknown;
}

export interface AuditLog {
  audit_log_id: number;
  audit_log_timestamp: string;
  audit_log_user_id?: number | null;
  audit_log_action: string;
  audit_log_entity_type: string;
  audit_log_entity_id?: number | null;
  user?: User | null;
}

export interface DashboardStats {
  user_stats: {
    total: number;
    verified: number;
    by_role: Record<string, number>;
  };
  resource_counts: Record<string, number>;
  recent_activity: AuditLog[];
}
