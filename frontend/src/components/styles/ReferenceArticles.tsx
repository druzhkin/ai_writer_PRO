'use client';

// Reference articles component for managing style reference materials

import React, { useState } from 'react';
import { useUploadFile, useDeleteFile } from '@/hooks/api';
import { useAuth } from '@/hooks/auth';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { FileUpload } from './FileUpload';
import { cn } from '@/lib/utils';
import { ReferenceArticle } from '@/types/api';
import {
  FileText,
  Upload,
  Trash2,
  Download,
  Eye,
  AlertCircle,
} from 'lucide-react';

interface ReferenceArticlesProps {
  styleId: string;
  articles: ReferenceArticle[];
  onArticlesChange?: (articles: ReferenceArticle[]) => void;
  className?: string;
}

const ReferenceArticles: React.FC<ReferenceArticlesProps> = ({
  styleId,
  articles = [],
  onArticlesChange,
  className,
}) => {
  const { organization } = useAuth();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  
  const uploadFileMutation = useUploadFile(organization?.id || '');
  const deleteFileMutation = useDeleteFile(organization?.id || '');

  const handleFilesChange = (files: File[]) => {
    setSelectedFiles(files);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    try {
      const uploadPromises = selectedFiles.map(file => 
        uploadFileMutation.mutateAsync(file)
      );
      
      const results = await Promise.all(uploadPromises);
      
      // Convert upload results to reference articles
      const newArticles: ReferenceArticle[] = results.map(result => ({
        id: result.file_id,
        style_profile_id: styleId,
        title: result.file_path.split('/').pop() || 'Unknown',
        content: '', // Will be extracted by backend
        file_path: result.file_path,
        file_size: result.file_size,
        file_type: result.file_type,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }));

      onArticlesChange?.([...articles, ...newArticles]);
      setSelectedFiles([]);
    } catch (error) {
      console.error('Error uploading files:', error);
    }
  };

  const handleDelete = async (articleId: string) => {
    try {
      await deleteFileMutation.mutateAsync(articleId);
      onArticlesChange?.(articles.filter(article => article.id !== articleId));
    } catch (error) {
      console.error('Error deleting file:', error);
    }
  };

  const handleDownload = (article: ReferenceArticle) => {
    // TODO: Implement file download
    console.log('Download file:', article);
  };

  const handlePreview = (article: ReferenceArticle) => {
    // TODO: Implement file preview
    console.log('Preview file:', article);
  };

  const isLoading = uploadFileMutation.isPending || deleteFileMutation.isPending;
  const error = uploadFileMutation.error || deleteFileMutation.error;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <FileText className="h-5 w-5" />
          <span>Референсные статьи</span>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Error message */}
        {error && (
          <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Ошибка загрузки
                </h3>
                <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                  {error.message || 'Произошла ошибка при загрузке файлов'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* File upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Добавить файлы
          </label>
          <FileUpload
            onFilesChange={handleFilesChange}
            maxFiles={10}
            acceptedTypes={['text/plain', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']}
          />
          
          {selectedFiles.length > 0 && (
            <div className="mt-3">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                Выбрано файлов: {selectedFiles.length}
              </p>
              <div className="space-y-1">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                    <Upload className="h-4 w-4" />
                    <span className="truncate">{file.name}</span>
                    <span className="text-gray-400">
                      ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                ))}
              </div>
              <Button
                onClick={handleUpload}
                disabled={isLoading}
                className="mt-3"
                size="sm"
              >
                {isLoading ? 'Загружаем...' : 'Загрузить файлы'}
              </Button>
            </div>
          )}
        </div>

        {/* Articles list */}
        {articles.length > 0 ? (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Загруженные файлы
            </h4>
            {articles.map((article) => (
              <div key={article.id} className="flex items-center space-x-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                <FileText className="h-4 w-4 text-gray-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {article.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {article.file_type} • {(article.file_size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <div className="flex items-center space-x-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handlePreview(article)}
                    title="Предпросмотр"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDownload(article)}
                    title="Скачать"
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(article.id)}
                    title="Удалить"
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <FileText className="mx-auto h-8 w-8 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Нет референсных статей
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500">
              Загрузите файлы для анализа стиля
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export { ReferenceArticles };
