// API Types - Comprehensive TypeScript interfaces for all backend schemas

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  avatar_url?: string;
  timezone?: string;
  language?: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  created_at: string;
  updated_at: string;
  owner_id: string;
  settings?: OrganizationSettings;
}

export interface OrganizationSettings {
  ai_model?: string;
  max_tokens_per_month?: number;
  default_style_id?: string;
  features?: string[];
}

export interface OrganizationMember {
  id: string;
  organization_id: string;
  user_id: string;
  role: 'owner' | 'admin' | 'member';
  joined_at: string;
  user: User;
}

export interface StyleProfile {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  analysis_result?: StyleAnalysis;
  created_at: string;
  updated_at: string;
  created_by: string;
  is_active: boolean;
  reference_articles: ReferenceArticle[];
}

export interface StyleAnalysis {
  tone: string;
  voice: string;
  structure: string;
  vocabulary: string[];
  sentence_length: string;
  formatting_preferences: string[];
  key_phrases: string[];
  target_audience: string;
  content_type: string;
  confidence_score: number;
}

export interface ReferenceArticle {
  id: string;
  style_profile_id: string;
  title: string;
  content: string;
  file_path?: string;
  file_size?: number;
  file_type?: string;
  created_at: string;
  updated_at: string;
}

export interface GeneratedContent {
  id: string;
  organization_id: string;
  title: string;
  content: string;
  brief: string;
  style_profile_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  status: 'draft' | 'generated' | 'edited' | 'published';
  token_count: number;
  cost: number;
  iterations: ContentIteration[];
  style_profile?: StyleProfile;
}

export interface ContentIteration {
  id: string;
  content_id: string;
  content: string;
  edit_prompt?: string;
  created_at: string;
  created_by: string;
  diff_lines?: DiffLine[];
}

export interface DiffLine {
  id: string;
  iteration_id: string;
  line_number: number;
  old_content?: string;
  new_content?: string;
  change_type: 'added' | 'removed' | 'modified';
}

export interface ApiUsage {
  id: string;
  organization_id: string;
  user_id: string;
  endpoint: string;
  method: string;
  status_code: number;
  response_time: number;
  token_count: number;
  cost: number;
  created_at: string;
}

export interface UsageStats {
  total_tokens: number;
  total_cost: number;
  requests_count: number;
  period_start: string;
  period_end: string;
  daily_usage: DailyUsage[];
}

export interface DailyUsage {
  date: string;
  tokens: number;
  cost: number;
  requests: number;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

// Authentication Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  organization: Organization;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
}

export interface RegisterResponse {
  user: User;
  organization: Organization;
  message: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  new_password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// OAuth Types
export interface OAuthProvider {
  name: string;
  url: string;
  icon: string;
}

export interface OAuthCallbackRequest {
  code: string;
  state: string;
  provider: 'google' | 'github';
}

// Content Generation Types
export interface ContentGenerationRequest {
  brief: string;
  style_profile_id: string;
  max_tokens?: number;
  temperature?: number;
  additional_instructions?: string;
}

export interface ContentGenerationResponse {
  content: GeneratedContent;
  tokens_used: number;
  cost: number;
  generation_time: number;
}

export interface ContentEditRequest {
  edit_prompt: string;
  max_tokens?: number;
  temperature?: number;
}

export interface ContentEditResponse {
  iteration: ContentIteration;
  tokens_used: number;
  cost: number;
  generation_time: number;
}

// Style Management Types
export interface StyleCreationRequest {
  name: string;
  description?: string;
  reference_article_ids: string[];
}

export interface StyleUpdateRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface StyleAnalysisRequest {
  reference_articles: string[];
}

export interface StyleAnalysisResponse {
  analysis: StyleAnalysis;
  processing_time: number;
}

// File Upload Types
export interface FileUploadRequest {
  file: File;
  organization_id: string;
}

export interface FileUploadResponse {
  file_id: string;
  file_path: string;
  file_size: number;
  file_type: string;
  upload_time: number;
}

// Search and Filter Types
export interface SearchParams {
  query?: string;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface ContentSearchParams extends SearchParams {
  status?: string;
  style_profile_id?: string;
  date_from?: string;
  date_to?: string;
}

export interface StyleSearchParams extends SearchParams {
  is_active?: boolean;
  created_by?: string;
}

// Dashboard Types
export interface DashboardStats {
  total_content: number;
  total_styles: number;
  total_tokens: number;
  total_cost: number;
  monthly_usage: UsageStats;
  recent_content: GeneratedContent[];
  popular_styles: StyleProfile[];
}

// Notification Types
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  created_at: string;
  read: boolean;
  action_url?: string;
}

// Settings Types
export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  notifications: NotificationSettings;
}

export interface NotificationSettings {
  email_notifications: boolean;
  push_notifications: boolean;
  content_generated: boolean;
  style_analyzed: boolean;
  usage_alerts: boolean;
}
