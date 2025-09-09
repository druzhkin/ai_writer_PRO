'use client';

// Rich text editor component using Tiptap with AI integration

import React, { useCallback } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import TextAlign from '@tiptap/extension-text-align';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import {
  Bold,
  Italic,
  Underline,
  Strikethrough,
  List,
  ListOrdered,
  Quote,
  Code,
  Link as LinkIcon,
  Image as ImageIcon,
  Undo,
  Redo,
  Save,
  Zap,
  Type,
  AlignLeft,
  AlignCenter,
  AlignRight,
} from 'lucide-react';

interface RichTextEditorProps {
  content?: string;
  onChange?: (content: string) => void;
  onSave?: (content: string) => void;
  placeholder?: string;
  className?: string;
  editable?: boolean;
  showToolbar?: boolean;
  showAIAssistant?: boolean;
  onAIAssist?: (prompt: string) => void;
}

const RichTextEditor: React.FC<RichTextEditorProps> = ({
  content = '',
  onChange,
  onSave,
  placeholder = 'Начните писать...',
  className,
  editable = true,
  showToolbar = true,
  showAIAssistant = true,
  onAIAssist,
}) => {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder,
      }),
      TextAlign.configure({ 
        types: ['heading', 'paragraph'] 
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-blue-600 underline cursor-pointer',
        },
      }),
      Image.configure({
        HTMLAttributes: {
          class: 'max-w-full h-auto rounded-lg',
        },
      }),
    ],
    content,
    editable,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML());
    },
  });

  const handleSave = useCallback(() => {
    if (editor && onSave) {
      onSave(editor.getHTML());
    }
  }, [editor, onSave]);

  const handleAIAssist = useCallback(() => {
    if (onAIAssist && editor) {
      const selectedText = editor.state.doc.textBetween(
        editor.state.selection.from,
        editor.state.selection.to
      );
      onAIAssist(selectedText || 'Улучшить текст');
    }
  }, [editor, onAIAssist]);

  if (!editor) {
    return null;
  }

  const ToolbarButton: React.FC<{
    onClick: () => void;
    isActive?: boolean;
    disabled?: boolean;
    children: React.ReactNode;
    title?: string;
  }> = ({ onClick, isActive, disabled, children, title }) => (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={cn(
        'p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors',
        isActive && 'bg-gray-200 dark:bg-gray-600',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      {children}
    </button>
  );

  return (
    <div className={cn('border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden', className)}>
      {/* Toolbar */}
      {showToolbar && (
        <div className="border-b border-gray-200 dark:border-gray-700 p-2 bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center space-x-1 flex-wrap gap-1">
            {/* Text formatting */}
            <div className="flex items-center space-x-1 border-r border-gray-300 dark:border-gray-600 pr-2 mr-2">
              <ToolbarButton
                onClick={() => editor.chain().focus().toggleBold().run()}
                isActive={editor.isActive('bold')}
                title="Жирный"
              >
                <Bold className="h-4 w-4" />
              </ToolbarButton>
              
              <ToolbarButton
                onClick={() => editor.chain().focus().toggleItalic().run()}
                isActive={editor.isActive('italic')}
                title="Курсив"
              >
                <Italic className="h-4 w-4" />
              </ToolbarButton>
              
              <ToolbarButton
                onClick={() => editor.chain().focus().toggleStrike().run()}
                isActive={editor.isActive('strike')}
                title="Зачеркнутый"
              >
                <Strikethrough className="h-4 w-4" />
              </ToolbarButton>
              
              <ToolbarButton
                onClick={() => editor.chain().focus().toggleCode().run()}
                isActive={editor.isActive('code')}
                title="Код"
              >
                <Code className="h-4 w-4" />
              </ToolbarButton>
            </div>

            {/* Lists */}
            <div className="flex items-center space-x-1 border-r border-gray-300 dark:border-gray-600 pr-2 mr-2">
              <ToolbarButton
                onClick={() => editor.chain().focus().toggleBulletList().run()}
                isActive={editor.isActive('bulletList')}
                title="Маркированный список"
              >
                <List className="h-4 w-4" />
              </ToolbarButton>
              
              <ToolbarButton
                onClick={() => editor.chain().focus().toggleOrderedList().run()}
                isActive={editor.isActive('orderedList')}
                title="Нумерованный список"
              >
                <ListOrdered className="h-4 w-4" />
              </ToolbarButton>
              
              <ToolbarButton
                onClick={() => editor.chain().focus().toggleBlockquote().run()}
                isActive={editor.isActive('blockquote')}
                title="Цитата"
              >
                <Quote className="h-4 w-4" />
              </ToolbarButton>
            </div>

            {/* Alignment */}
            <div className="flex items-center space-x-1 border-r border-gray-300 dark:border-gray-600 pr-2 mr-2">
              <ToolbarButton
                onClick={() => editor.chain().focus().setTextAlign('left').run()}
                isActive={editor.isActive({ textAlign: 'left' })}
                title="Выровнять по левому краю"
              >
                <AlignLeft className="h-4 w-4" />
              </ToolbarButton>
              
              <ToolbarButton
                onClick={() => editor.chain().focus().setTextAlign('center').run()}
                isActive={editor.isActive({ textAlign: 'center' })}
                title="Выровнять по центру"
              >
                <AlignCenter className="h-4 w-4" />
              </ToolbarButton>
              
              <ToolbarButton
                onClick={() => editor.chain().focus().setTextAlign('right').run()}
                isActive={editor.isActive({ textAlign: 'right' })}
                title="Выровнять по правому краю"
              >
                <AlignRight className="h-4 w-4" />
              </ToolbarButton>
            </div>

            {/* Links and images */}
            <div className="flex items-center space-x-1 border-r border-gray-300 dark:border-gray-600 pr-2 mr-2">
              <ToolbarButton
                onClick={() => {
                  const url = window.prompt('Введите URL:');
                  if (url) {
                    editor.chain().focus().setLink({ href: url }).run();
                  }
                }}
                isActive={editor.isActive('link')}
                title="Добавить ссылку"
              >
                <LinkIcon className="h-4 w-4" />
              </ToolbarButton>
              
              <ToolbarButton
                onClick={() => {
                  const url = window.prompt('Введите URL изображения:');
                  if (url) {
                    editor.chain().focus().setImage({ src: url }).run();
                  }
                }}
                title="Добавить изображение"
              >
                <ImageIcon className="h-4 w-4" />
              </ToolbarButton>
            </div>

            {/* History */}
            <div className="flex items-center space-x-1 border-r border-gray-300 dark:border-gray-600 pr-2 mr-2">
              <ToolbarButton
                onClick={() => editor.chain().focus().undo().run()}
                disabled={!editor.can().undo()}
                title="Отменить"
              >
                <Undo className="h-4 w-4" />
              </ToolbarButton>
              
              <ToolbarButton
                onClick={() => editor.chain().focus().redo().run()}
                disabled={!editor.can().redo()}
                title="Повторить"
              >
                <Redo className="h-4 w-4" />
              </ToolbarButton>
            </div>

            {/* AI Assistant */}
            {showAIAssistant && onAIAssist && (
              <div className="flex items-center space-x-1">
                <ToolbarButton
                  onClick={handleAIAssist}
                  title="ИИ-помощник"
                >
                  <Zap className="h-4 w-4" />
                </ToolbarButton>
              </div>
            )}

            {/* Save */}
            {onSave && (
              <div className="flex items-center space-x-1 ml-auto">
                <ToolbarButton
                  onClick={handleSave}
                  title="Сохранить"
                >
                  <Save className="h-4 w-4" />
                </ToolbarButton>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Editor content */}
      <div className="min-h-[300px] p-4">
        <EditorContent
          editor={editor}
          className="prose prose-sm max-w-none dark:prose-invert focus:outline-none"
        />
      </div>

      {/* Character count */}
      <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-2 bg-gray-50 dark:bg-gray-800 text-xs text-gray-500 dark:text-gray-400">
        {editor.storage.characterCount?.characters() || 0} символов
      </div>
    </div>
  );
};

export { RichTextEditor };
