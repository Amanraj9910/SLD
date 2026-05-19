import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  className?: string;
}

export interface TableProps {
  headers: string[];
  rows: string[][];
  className?: string;
}

export interface CodeBlockProps {
  code: string;
  language?: string;
  className?: string;
}

// Collapsible Section Component
export const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  children,
  defaultExpanded = false,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className={`border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between text-left transition-colors duration-200"
      >
        <span className="font-medium text-gray-900">{title}</span>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        )}
      </button>
      {isExpanded && (
        <div className="p-4 bg-white border-t border-gray-200 animate-fade-in">
          {children}
        </div>
      )}
    </div>
  );
};

// Enhanced Table Component
export const EnhancedTable: React.FC<TableProps> = ({
  headers,
  rows,
  className = ''
}) => {
  return (
    <div className={`overflow-x-auto rounded-lg border border-gray-200 ${className}`}>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {headers.map((header, index) => (
              <th
                key={index}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {rows.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              className={`${
                rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'
              } hover:bg-red-50 transition-colors duration-150`}
            >
              {row.map((cell, cellIndex) => (
                <td
                  key={cellIndex}
                  className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Code Block Component with Copy Functionality
export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'text',
  className = ''
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  return (
    <div className={`relative rounded-lg border border-gray-200 ${className}`}>
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
        <span className="text-xs font-medium text-gray-500 uppercase">
          {language}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3" />
              <span>Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 bg-white overflow-x-auto">
        <code className="text-sm text-gray-800 font-mono">{code}</code>
      </pre>
    </div>
  );
};

// Main Markdown Renderer Component
const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = ''
}) => {
  // Parse markdown content and convert to structured elements
  const parseMarkdown = (text: string) => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let currentSection: string[] = [];
    let inCodeBlock = false;
    let codeLanguage = '';
    let codeContent: string[] = [];

    const flushCurrentSection = () => {
      if (currentSection.length > 0) {
        elements.push(
          <div key={elements.length} className="mb-4">
            {currentSection.map((line, index) => (
              <p key={index} className="mb-2 text-gray-800 leading-relaxed">
                {parseInlineMarkdown(line)}
              </p>
            ))}
          </div>
        );
        currentSection = [];
      }
    };

    const flushCodeBlock = () => {
      if (codeContent.length > 0) {
        elements.push(
          <CodeBlock
            key={elements.length}
            code={codeContent.join('\n')}
            language={codeLanguage}
            className="mb-4"
          />
        );
        codeContent = [];
        codeLanguage = '';
      }
    };

    lines.forEach((line, index) => {
      // Handle code blocks
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          flushCodeBlock();
          inCodeBlock = false;
        } else {
          flushCurrentSection();
          inCodeBlock = true;
          codeLanguage = line.slice(3).trim() || 'text';
        }
        return;
      }

      if (inCodeBlock) {
        codeContent.push(line);
        return;
      }

      // Handle headers
      if (line.startsWith('#')) {
        flushCurrentSection();
        const level = line.match(/^#+/)?.[0].length || 1;
        const text = line.replace(/^#+\s*/, '');
        const HeaderTag = `h${Math.min(level, 6)}` as keyof JSX.IntrinsicElements;
        
        elements.push(
          <HeaderTag
            key={elements.length}
            className={`font-bold text-gray-900 mb-3 ${
              level === 1 ? 'text-2xl' :
              level === 2 ? 'text-xl' :
              level === 3 ? 'text-lg' :
              'text-base'
            }`}
          >
            {parseInlineMarkdown(text)}
          </HeaderTag>
        );
        return;
      }

      // Handle tables
      if (line.includes('|') && line.trim().startsWith('|')) {
        flushCurrentSection();
        const tableLines = [line];
        let nextIndex = index + 1;
        
        // Collect all table rows
        while (nextIndex < lines.length && lines[nextIndex].includes('|')) {
          tableLines.push(lines[nextIndex]);
          nextIndex++;
        }

        if (tableLines.length >= 2) {
          const headers = tableLines[0]
            .split('|')
            .slice(1, -1)
            .map(h => h.trim());
          
          const rows = tableLines
            .slice(2) // Skip header separator
            .map(row => 
              row.split('|')
                .slice(1, -1)
                .map(cell => cell.trim())
            );

          elements.push(
            <EnhancedTable
              key={elements.length}
              headers={headers}
              rows={rows}
              className="mb-4"
            />
          );
        }
        return;
      }

      // Handle empty lines
      if (line.trim() === '') {
        flushCurrentSection();
        return;
      }

      // Regular content
      currentSection.push(line);
    });

    // Flush remaining content
    flushCurrentSection();
    flushCodeBlock();

    return elements;
  };

  // Parse inline markdown (bold, italic, links, etc.)
  const parseInlineMarkdown = (text: string): React.ReactNode => {
    // Handle bold text
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic text
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Handle inline code
    text = text.replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>');
    
    // Handle links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-red-500 hover:text-red-600 underline">$1</a>');

    return <span dangerouslySetInnerHTML={{ __html: text }} />;
  };

  const parsedElements = parseMarkdown(content);

  return (
    <div className={`markdown-content ${className}`}>
      {parsedElements}
    </div>
  );
};

export default MarkdownRenderer;
