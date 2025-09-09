'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/auth';
import { ArrowRight, Sparkles, FileText, Zap, Users, Shield, Clock } from 'lucide-react';

const HomePage: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Sparkles className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">AI Writer PRO</span>
            </div>
            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <Link href="/dashboard">
                  <Button>Панель управления</Button>
                </Link>
              ) : (
                <>
                  <Link href="/login">
                    <Button variant="ghost">Войти</Button>
                  </Link>
                  <Link href="/register">
                    <Button>Начать</Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Создавайте{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                ИИ-контент
              </span>{' '}
              за секунды
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Создавайте высококачественные, увлекательные статьи за минуты с помощью нашей передовой ИИ-технологии. 
              Идеально для контент-мейкеров, маркетологов и бизнеса.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {isAuthenticated ? (
                <Link href="/dashboard/content/new">
                  <Button size="lg" className="group">
                    Создать статью
                    <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
              ) : (
                <Link href="/register">
                  <Button size="lg" className="group">
                    Начать бесплатно
                    <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
              )}
              <Button variant="outline" size="lg">
                Посмотреть демо
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Почему выбирают AI Writer PRO?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Наша платформа сочетает передовой ИИ с интуитивным дизайном для достижения исключительных результатов.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-lg shadow-md text-center hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Zap className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Молниеносно быстро</h3>
              <p className="text-gray-600">
                Создавайте полные статьи менее чем за 60 секунд. Больше никаких часов ожидания создания контента.
              </p>
            </div>

            <div className="bg-white p-8 rounded-lg shadow-md text-center hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <FileText className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Высокое качество</h3>
              <p className="text-gray-600">
                Наш ИИ создает увлекательный, хорошо структурированный контент, который читается естественно и привлекает аудиторию.
              </p>
            </div>

            <div className="bg-white p-8 rounded-lg shadow-md text-center hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Sparkles className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Настраиваемый</h3>
              <p className="text-gray-600">
                Легко адаптируйте контент под голос вашего бренда, целевую аудиторию и конкретные требования.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Готовы трансформировать ваш контент?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Присоединяйтесь к тысячам создателей контента, которые уже используют AI Writer PRO для масштабирования производства контента.
          </p>
          {isAuthenticated ? (
            <Link href="/dashboard/content/new">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100">
                Создать статью
              </Button>
            </Link>
          ) : (
            <Link href="/register">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100">
                Начать бесплатно
              </Button>
            </Link>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <Sparkles className="h-8 w-8 text-blue-400" />
              <span className="ml-2 text-xl font-bold">AI Writer PRO</span>
            </div>
            <div className="text-gray-400 text-sm">
              © 2024 AI Writer PRO. Все права защищены.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
