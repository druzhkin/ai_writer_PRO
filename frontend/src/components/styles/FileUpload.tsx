'use client';

// File upload component with drag and drop support

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { cn } from '@/lib/utils';
import { Upload, File, X } from 'lucide-react';

interface FileUploadProps {
  onFilesChange: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
  maxSize?: number;
  className?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFilesChange,
  maxFiles = 10,
  acceptedTypes = ['text/plain', 'application/pdf'],
  maxSize = 10 * 1024 * 1024, // 10MB
  className,
}) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    onFilesChange(acceptedFiles);
  }, [onFilesChange]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    maxFiles,
    accept: acceptedTypes.reduce((acc, type) => {
      acc[type] = [];
      return acc;
    }, {} as Record<string, string[]>),
    maxSize,
  });

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={cn('w-full', className)}>
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center space-y-2">
          <Upload className="h-8 w-8 text-gray-400" />
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {isDragActive ? (
              <p>Отпустите файлы здесь...</p>
            ) : (
              <div>
                <p className="font-medium">Перетащите файлы сюда или нажмите для выбора</p>
                <p className="text-xs mt-1">
                  Максимум {maxFiles} файлов, до {formatFileSize(maxSize)} каждый
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* File rejection errors */}
      {fileRejections.length > 0 && (
        <div className="mt-4 space-y-2">
          {fileRejections.map(({ file, errors }) => (
            <div key={file.name} className="flex items-center space-x-2 p-2 bg-red-50 dark:bg-red-900/20 rounded-md">
              <X className="h-4 w-4 text-red-500" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  {file.name}
                </p>
                <div className="text-xs text-red-600 dark:text-red-400">
                  {errors.map((error, index) => (
                    <div key={index}>
                      {error.code === 'file-too-large' && 'Файл слишком большой'}
                      {error.code === 'file-invalid-type' && 'Неподдерживаемый тип файла'}
                      {error.code === 'too-many-files' && 'Слишком много файлов'}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export { FileUpload };