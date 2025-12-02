import { TextElement } from '../contexts/SLDContext';

export interface BOMComponent {
  id: string;
  itemNumber: number;
  componentType: string;
  description: string;
  quantity: number;
  specifications: string[];
  location: string;
  confidence: number;
  textElements: TextElement[];
}

export interface BOMData {
  components: BOMComponent[];
  summary: {
    totalComponents: number;
    uniqueTypes: number;
    averageConfidence: number;
    processingDate: string;
  };
  metadata: {
    documentType: string;
    totalTextElements: number;
    processingTime: number;
  };
}

// Component patterns for electrical equipment
const COMPONENT_PATTERNS = {
  'Circuit Breaker': {
    patterns: [
      /\b(CB|MCB|MCCB|ACB|VCB|SF6|OCB)\b/i,
      /\bcircuit\s*breaker\b/i,
      /\bbreaker\b/i
    ],
    category: 'Protection',
    specifications: [/\d+A/i, /\d+kV/i, /\d+kA/i]
  },
  'Current Transformer': {
    patterns: [
      /\b(CT|C\.T\.)\b/i,
      /\bcurrent\s*transformer\b/i
    ],
    category: 'Measurement',
    specifications: [/\d+\/\d+A/i, /\d+VA/i, /class\s*\d+/i]
  },
  'Potential Transformer': {
    patterns: [
      /\b(PT|VT|P\.T\.)\b/i,
      /\bpotential\s*transformer\b/i,
      /\bvoltage\s*transformer\b/i
    ],
    category: 'Measurement',
    specifications: [/\d+\/\d+V/i, /\d+kV/i, /\d+VA/i]
  },
  'Transformer': {
    patterns: [
      /\b(TR|T|XFMR)\b/i,
      /\btransformer\b/i,
      /\d+MVA/i
    ],
    category: 'Power',
    specifications: [/\d+MVA/i, /\d+kV/i, /\d+%/i]
  },
  'Generator': {
    patterns: [
      /\b(GEN|G)\b/i,
      /\bgenerator\b/i
    ],
    category: 'Generation',
    specifications: [/\d+MW/i, /\d+kV/i, /\d+Hz/i]
  },
  'Motor': {
    patterns: [
      /\b(M|MOT)\b/i,
      /\bmotor\b/i
    ],
    category: 'Load',
    specifications: [/\d+kW/i, /\d+HP/i, /\d+V/i, /\d+Hz/i]
  },
  'Bus Bar': {
    patterns: [
      /\bbus\s*bar\b/i,
      /\bbus\b/i,
      /\bmain\s*bus\b/i
    ],
    category: 'Distribution',
    specifications: [/\d+kV/i, /\d+A/i]
  },
  'Isolator': {
    patterns: [
      /\bisolator\b/i,
      /\bdisconnector\b/i,
      /\bISO\b/i
    ],
    category: 'Switching',
    specifications: [/\d+kV/i, /\d+A/i]
  },
  'Relay': {
    patterns: [
      /\brelay\b/i,
      /\b\d+\w*\s*relay\b/i
    ],
    category: 'Protection',
    specifications: [/\d+V/i, /\d+A/i]
  },
  'Capacitor': {
    patterns: [
      /\bcapacitor\b/i,
      /\bcap\b/i,
      /\bkVAR\b/i
    ],
    category: 'Compensation',
    specifications: [/\d+kVAR/i, /\d+kV/i]
  },
  'Cable': {
    patterns: [
      /\bcable\b/i,
      /\bfeeder\b/i,
      /\d+mm²/i,
      /\d+AWG/i
    ],
    category: 'Connection',
    specifications: [/\d+mm²/i, /\d+AWG/i, /\d+kV/i]
  },
  'Load': {
    patterns: [
      /\bload\b/i,
      /\bkW\b/i,
      /\bMW\b/i
    ],
    category: 'Load',
    specifications: [/\d+kW/i, /\d+MW/i, /\d+kV/i]
  }
};

export class BOMGenerator {
  private textElements: TextElement[];
  private components: BOMComponent[] = [];

  constructor(textElements: TextElement[]) {
    this.textElements = textElements;
  }

  generateBOM(): BOMData {
    this.extractComponents();
    this.aggregateComponents();
    
    return {
      components: this.components,
      summary: this.generateSummary(),
      metadata: {
        documentType: 'Single Line Diagram',
        totalTextElements: this.textElements.length,
        processingTime: Date.now()
      }
    };
  }

  private extractComponents(): void {
    const detectedComponents: Map<string, BOMComponent> = new Map();
    let itemNumber = 1;

    this.textElements.forEach((element, index) => {
      const text = element.text.trim();
      if (!text || text.length < 2) return;

      // Check against all component patterns
      for (const [componentType, config] of Object.entries(COMPONENT_PATTERNS)) {
        const isMatch = config.patterns.some(pattern => pattern.test(text));
        
        if (isMatch) {
          const componentId = `${componentType}_${index}`;
          const specifications = this.extractSpecifications(text, config.specifications);
          
          const component: BOMComponent = {
            id: componentId,
            itemNumber: itemNumber++,
            componentType,
            description: this.generateDescription(componentType, text, specifications),
            quantity: 1,
            specifications,
            location: this.getLocationDescription(element),
            confidence: element.confidence,
            textElements: [element]
          };

          detectedComponents.set(componentId, component);
          break; // Only match first pattern to avoid duplicates
        }
      }
    });

    this.components = Array.from(detectedComponents.values());
  }

  private extractSpecifications(text: string, specPatterns: RegExp[]): string[] {
    const specifications: string[] = [];
    
    specPatterns.forEach(pattern => {
      const matches = text.match(pattern);
      if (matches) {
        specifications.push(...matches);
      }
    });

    // Extract additional common specifications
    const additionalPatterns = [
      /\d+\s*Hz/i,
      /\d+\s*V/i,
      /\d+\s*A/i,
      /\d+\s*W/i,
      /\d+\s*VA/i,
      /\d+\s*Ω/i,
      /\d+\s*%/i,
      /class\s*\d+/i,
      /IP\d+/i
    ];

    additionalPatterns.forEach(pattern => {
      const matches = text.match(pattern);
      if (matches && !specifications.includes(matches[0])) {
        specifications.push(matches[0]);
      }
    });

    return [...new Set(specifications)]; // Remove duplicates
  }

  private generateDescription(componentType: string, originalText: string, specifications: string[]): string {
    let description = componentType;
    
    if (specifications.length > 0) {
      description += ` (${specifications.join(', ')})`;
    }
    
    // Add original text if it contains additional useful information
    const cleanText = originalText.replace(/[^\w\s\-\.\/]/g, '').trim();
    if (cleanText.length > 0 && !description.toLowerCase().includes(cleanText.toLowerCase())) {
      description += ` - ${cleanText}`;
    }
    
    return description;
  }

  private getLocationDescription(element: TextElement): string {
    const { bounding_box } = element;
    const x = Math.round(bounding_box.left + bounding_box.width / 2);
    const y = Math.round(bounding_box.top + bounding_box.height / 2);
    
    return `Position (${x}, ${y})`;
  }

  private aggregateComponents(): void {
    // Group similar components and aggregate quantities
    const groupedComponents: Map<string, BOMComponent> = new Map();

    this.components.forEach(component => {
      const key = `${component.componentType}_${component.specifications.join('_')}`;
      
      if (groupedComponents.has(key)) {
        const existing = groupedComponents.get(key)!;
        existing.quantity += 1;
        existing.textElements.push(...component.textElements);
        existing.confidence = (existing.confidence + component.confidence) / 2;
        existing.location += `, ${component.location}`;
      } else {
        groupedComponents.set(key, { ...component });
      }
    });

    // Reassign item numbers
    this.components = Array.from(groupedComponents.values())
      .sort((a, b) => a.componentType.localeCompare(b.componentType))
      .map((component, index) => ({
        ...component,
        itemNumber: index + 1
      }));
  }

  private generateSummary() {
    const totalComponents = this.components.reduce((sum, comp) => sum + comp.quantity, 0);
    const uniqueTypes = new Set(this.components.map(comp => comp.componentType)).size;
    const averageConfidence = this.components.reduce((sum, comp) => sum + comp.confidence, 0) / this.components.length;

    return {
      totalComponents,
      uniqueTypes,
      averageConfidence: Math.round(averageConfidence * 100) / 100,
      processingDate: new Date().toISOString()
    };
  }
}

// Export utilities
export const exportBOMToCSV = (bomData: BOMData): string => {
  const headers = ['Item#', 'Component Type', 'Description', 'Quantity', 'Specifications', 'Location', 'Confidence'];
  const rows = bomData.components.map(comp => [
    comp.itemNumber.toString(),
    comp.componentType,
    comp.description,
    comp.quantity.toString(),
    comp.specifications.join('; '),
    comp.location,
    `${Math.round(comp.confidence * 100)}%`
  ]);

  const csvContent = [headers, ...rows]
    .map(row => row.map(cell => `"${cell}"`).join(','))
    .join('\n');

  return csvContent;
};

export const exportBOMToTXT = (bomData: BOMData): string => {
  const { components, summary, metadata } = bomData;
  
  let content = `BILL OF MATERIALS - SINGLE LINE DIAGRAM\n`;
  content += `Generated: ${new Date(summary.processingDate).toLocaleString()}\n`;
  content += `Document Type: ${metadata.documentType}\n`;
  content += `Total Text Elements: ${metadata.totalTextElements}\n\n`;
  
  content += `SUMMARY:\n`;
  content += `- Total Components: ${summary.totalComponents}\n`;
  content += `- Unique Types: ${summary.uniqueTypes}\n`;
  content += `- Average Confidence: ${Math.round(summary.averageConfidence * 100)}%\n\n`;
  
  content += `COMPONENT LIST:\n`;
  content += `${'='.repeat(80)}\n`;
  
  components.forEach(comp => {
    content += `${comp.itemNumber}. ${comp.componentType}\n`;
    content += `   Description: ${comp.description}\n`;
    content += `   Quantity: ${comp.quantity}\n`;
    content += `   Specifications: ${comp.specifications.join(', ') || 'None specified'}\n`;
    content += `   Location: ${comp.location}\n`;
    content += `   Confidence: ${Math.round(comp.confidence * 100)}%\n\n`;
  });
  
  return content;
};

export const downloadFile = (content: string, filename: string, mimeType: string): void => {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
