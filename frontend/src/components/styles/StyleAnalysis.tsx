'use client';

// Style analysis component for displaying AI-generated style insights

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { StyleAnalysis as StyleAnalysisType } from '@/types/api';
import {
  TrendingUp,
  Target,
  MessageSquare,
  BookOpen,
  Users,
  FileText,
  Zap,
  BarChart3,
} from 'lucide-react';

interface StyleAnalysisProps {
  analysis: StyleAnalysisType;
  processingTime?: number;
  className?: string;
}

const StyleAnalysis: React.FC<StyleAnalysisProps> = ({
  analysis,
  processingTime,
  className,
}) => {
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400';
    if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getConfidenceBgColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-600';
    if (score >= 0.6) return 'bg-yellow-600';
    return 'bg-red-600';
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Обзор анализа</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {Math.round(analysis.confidence_score * 100)}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Уверенность
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {analysis.vocabulary?.length || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Ключевые слова
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {analysis.key_phrases?.length || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Ключевые фразы
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {processingTime ? `${processingTime}s` : 'N/A'}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Время анализа
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Core Characteristics */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5" />
              <span>Тон и голос</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Тон
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {analysis.tone}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Голос
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {analysis.voice}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Целевая аудитория
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {analysis.target_audience}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BookOpen className="h-5 w-5" />
              <span>Структура и формат</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Структура
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {analysis.structure}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Длина предложений
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {analysis.sentence_length}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Тип контента
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {analysis.content_type}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Vocabulary */}
      {analysis.vocabulary && analysis.vocabulary.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Ключевые слова</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {analysis.vocabulary.map((word, index) => (
                <Badge key={index} variant="outline" className="text-sm">
                  {word}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Key Phrases */}
      {analysis.key_phrases && analysis.key_phrases.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Zap className="h-5 w-5" />
              <span>Ключевые фразы</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {analysis.key_phrases.map((phrase, index) => (
                <Badge key={index} variant="secondary" className="text-sm">
                  {phrase}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Formatting Preferences */}
      {analysis.formatting_preferences && analysis.formatting_preferences.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Target className="h-5 w-5" />
              <span>Предпочтения форматирования</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analysis.formatting_preferences.map((preference, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {preference}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Confidence Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5" />
            <span>Уверенность анализа</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Общая точность
              </span>
              <span className={cn('text-sm font-medium', getConfidenceColor(analysis.confidence_score))}>
                {Math.round(analysis.confidence_score * 100)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div 
                className={cn('h-3 rounded-full transition-all duration-300', getConfidenceBgColor(analysis.confidence_score))}
                style={{ width: `${analysis.confidence_score * 100}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {analysis.confidence_score >= 0.8 
                ? 'Высокая уверенность в анализе' 
                : analysis.confidence_score >= 0.6 
                ? 'Средняя уверенность в анализе' 
                : 'Низкая уверенность в анализе. Рекомендуется добавить больше референсных материалов.'
              }
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export { StyleAnalysis };
