// Form Validation Schemas using Zod

import { z } from 'zod';

// Authentication Forms
export const loginSchema = z.object({
  email: z.string().email('Введите корректный email адрес'),
  password: z.string().min(6, 'Пароль должен содержать минимум 6 символов'),
});

export const registerSchema = z.object({
  email: z.string().email('Введите корректный email адрес'),
  password: z.string()
    .min(8, 'Пароль должен содержать минимум 8 символов')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Пароль должен содержать заглавные и строчные буквы, а также цифры'),
  confirmPassword: z.string(),
  full_name: z.string().min(2, 'Имя должно содержать минимум 2 символа'),
  organization_name: z.string().min(2, 'Название организации должно содержать минимум 2 символа'),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Пароли не совпадают',
  path: ['confirmPassword'],
});

export const passwordResetSchema = z.object({
  email: z.string().email('Введите корректный email адрес'),
});

export const passwordResetConfirmSchema = z.object({
  token: z.string().min(1, 'Токен обязателен'),
  new_password: z.string()
    .min(8, 'Пароль должен содержать минимум 8 символов')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Пароль должен содержать заглавные и строчные буквы, а также цифры'),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'Пароли не совпадают',
  path: ['confirm_password'],
});

// Style Management Forms
export const styleCreationSchema = z.object({
  name: z.string().min(2, 'Название стиля должно содержать минимум 2 символа'),
  description: z.string().optional(),
  reference_articles: z.array(z.instanceof(File))
    .min(1, 'Загрузите минимум один референсный файл')
    .max(10, 'Максимум 10 файлов'),
});

export const styleUpdateSchema = z.object({
  name: z.string().min(2, 'Название стиля должно содержать минимум 2 символа').optional(),
  description: z.string().optional(),
  is_active: z.boolean().optional(),
});

// Content Generation Forms
export const contentGenerationSchema = z.object({
  brief: z.string().min(10, 'Бриф должен содержать минимум 10 символов'),
  style_profile_id: z.string().min(1, 'Выберите стиль'),
  max_tokens: z.number().min(100).max(4000).optional(),
  temperature: z.number().min(0).max(2).optional(),
  additional_instructions: z.string().optional(),
});

export const contentEditSchema = z.object({
  edit_prompt: z.string().min(5, 'Промпт для редактирования должен содержать минимум 5 символов'),
  max_tokens: z.number().min(100).max(4000).optional(),
  temperature: z.number().min(0).max(2).optional(),
});

// File Upload Forms
export const fileUploadSchema = z.object({
  file: z.instanceof(File)
    .refine((file) => file.size <= 10 * 1024 * 1024, 'Размер файла не должен превышать 10MB')
    .refine(
      (file) => ['text/plain', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type),
      'Поддерживаются только файлы: .txt, .pdf, .doc, .docx'
    ),
});

// Organization Forms
export const organizationUpdateSchema = z.object({
  name: z.string().min(2, 'Название организации должно содержать минимум 2 символа').optional(),
  description: z.string().optional(),
  settings: z.object({
    ai_model: z.string().optional(),
    max_tokens_per_month: z.number().min(1000).optional(),
    default_style_id: z.string().optional(),
  }).optional(),
});

export const organizationMemberSchema = z.object({
  email: z.string().email('Введите корректный email адрес'),
  role: z.enum(['admin', 'member'], {
    errorMap: () => ({ message: 'Выберите роль: admin или member' }),
  }),
});

// User Profile Forms
export const userProfileSchema = z.object({
  full_name: z.string().min(2, 'Имя должно содержать минимум 2 символа'),
  email: z.string().email('Введите корректный email адрес'),
  timezone: z.string().optional(),
  language: z.string().optional(),
});

export const userSettingsSchema = z.object({
  theme: z.enum(['light', 'dark', 'system']),
  language: z.string(),
  timezone: z.string(),
  notifications: z.object({
    email_notifications: z.boolean(),
    push_notifications: z.boolean(),
    content_generated: z.boolean(),
    style_analyzed: z.boolean(),
    usage_alerts: z.boolean(),
  }),
});

// Search and Filter Forms
export const contentSearchSchema = z.object({
  query: z.string().optional(),
  status: z.enum(['draft', 'generated', 'edited', 'published']).optional(),
  style_profile_id: z.string().optional(),
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  page: z.number().min(1).optional(),
  per_page: z.number().min(1).max(100).optional(),
  sort_by: z.string().optional(),
  sort_order: z.enum(['asc', 'desc']).optional(),
});

export const styleSearchSchema = z.object({
  query: z.string().optional(),
  is_active: z.boolean().optional(),
  created_by: z.string().optional(),
  page: z.number().min(1).optional(),
  per_page: z.number().min(1).max(100).optional(),
  sort_by: z.string().optional(),
  sort_order: z.enum(['asc', 'desc']).optional(),
});

// Type exports for form data
export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type PasswordResetFormData = z.infer<typeof passwordResetSchema>;
export type PasswordResetConfirmFormData = z.infer<typeof passwordResetConfirmSchema>;
export type StyleCreationFormData = z.infer<typeof styleCreationSchema>;
export type StyleUpdateFormData = z.infer<typeof styleUpdateSchema>;
export type ContentGenerationFormData = z.infer<typeof contentGenerationSchema>;
export type ContentEditFormData = z.infer<typeof contentEditSchema>;
export type FileUploadFormData = z.infer<typeof fileUploadSchema>;
export type OrganizationUpdateFormData = z.infer<typeof organizationUpdateSchema>;
export type OrganizationMemberFormData = z.infer<typeof organizationMemberSchema>;
export type UserProfileFormData = z.infer<typeof userProfileSchema>;
export type UserSettingsFormData = z.infer<typeof userSettingsSchema>;
export type ContentSearchFormData = z.infer<typeof contentSearchSchema>;
export type StyleSearchFormData = z.infer<typeof styleSearchSchema>;
