import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, FileSpreadsheet, Bot, Loader2, Maximize2, Minimize2 } from 'lucide-react';
// import MarkdownRenderer from './MarkdownRenderer';
// import BOMPreview from './bot/BOMPreview';
// import SampleQuestions from './bot/SampleQuestions';
// Temporarily define types locally to avoid import issues
interface BOMComponent {
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

interface BOMData {
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

interface TextElement {
  text: string;
  confidence: number;
  bounding_box: {
    left: number;
    top: number;
    width: number;
    height: number;
  };
}

interface SLDData {
  text_elements: TextElement[];
  document_type: string;
  processing_time: number;
  image_dimensions?: {
    width: number;
    height: number;
  };
  service_info: {
    model_id: string;
    api_version: string;
  };
}

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
}

interface SLDBotProps {
  sldData?: SLDData | null;
  isVisible?: boolean;
}

// Azure OpenAI API configuration
const AZURE_OPENAI_CONFIG = {
  endpoint: 'https://ai-diagramanalysis709756132870.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2025-01-01-preview',
  apiKey: '9oaTfptIYncr9vUe1JegGBXBXVF7VCVXi4pntMJGuUj2C84GxJexJQQJ99BEACYeBjFXJ3w3AAAAACOGvCqX'
};

// Analyze user intent to determine response style
const analyzeUserIntent = (query: string) => {
  const lowerQuery = query.toLowerCase().trim();

  // Greeting patterns
  const greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening'];
  const isGreeting = greetings.some(greeting => lowerQuery === greeting || lowerQuery.startsWith(greeting));

  // Simple question patterns
  const simpleQuestions = [
    /^what.*found/i,
    /^how many/i,
    /^do you have/i,
    /^can you/i,
    /^is there/i,
    /^are there/i
  ];
  const isSimpleQuestion = simpleQuestions.some(pattern => pattern.test(lowerQuery));

  // Detail request patterns
  const detailRequests = [
    /tell me (everything|all|more|details)/i,
    /explain.*detail/i,
    /show me.*complete/i,
    /full.*analysis/i,
    /comprehensive/i,
    /specifications/i,
    /technical.*info/i
  ];
  const wantsDetails = detailRequests.some(pattern => pattern.test(lowerQuery));

  // Help/guidance patterns
  const helpRequests = [
    /help/i,
    /how.*do/i,
    /guide/i,
    /step.*by.*step/i,
    /tutorial/i
  ];
  const needsGuidance = helpRequests.some(pattern => pattern.test(lowerQuery));

  return {
    isGreeting,
    isSimpleQuestion,
    wantsDetails,
    needsGuidance,
    isBrief: isGreeting || (isSimpleQuestion && !wantsDetails)
  };
};

// Categorize the type of query for better AI context
const categorizeQuery = (query: string): string => {
  const lowerQuery = query.toLowerCase();

  if (lowerQuery.includes('component') || lowerQuery.includes('element')) {
    return 'component_analysis';
  }
  if (lowerQuery.includes('bom') || lowerQuery.includes('bill of materials')) {
    return 'bom_generation';
  }
  if (lowerQuery.includes('confidence') || lowerQuery.includes('quality') || lowerQuery.includes('accuracy')) {
    return 'quality_assessment';
  }
  if (lowerQuery.includes('specification') || lowerQuery.includes('rating') || lowerQuery.includes('voltage') || lowerQuery.includes('current')) {
    return 'technical_specs';
  }
  if (lowerQuery.includes('location') || lowerQuery.includes('position') || lowerQuery.includes('layout')) {
    return 'spatial_analysis';
  }
  if (lowerQuery.includes('help') || lowerQuery.includes('how') || lowerQuery.includes('guide')) {
    return 'help_guidance';
  }

  return 'general_inquiry';
};

// Generate response when no SLD data is available
const generateNoDataResponse = async (userQuery: string): Promise<string> => {
  const intent = analyzeUserIntent(userQuery);

  // For simple cases, provide direct responses
  if (intent.isGreeting) {
    return "Hello! I'm here to help you analyze your SLD. To get started, please upload and process an SLD document first.";
  }

  if (intent.isBrief) {
    return "I'd love to help, but I don't have any SLD data to analyze yet. Please upload an SLD document first, then I can answer your questions!";
  }

  // For more complex queries, use AI to generate contextual responses
  try {
    const systemPrompt = `You are a helpful SLD analysis assistant. The user has asked a question but hasn't uploaded any SLD data yet.

Respond conversationally and helpfully, explaining that they need to upload an SLD first. Tailor your response to their specific question while being encouraging and helpful.

User Intent: ${JSON.stringify({
      isGreeting: intent.isGreeting,
      wantsBriefResponse: intent.isBrief,
      wantsDetailedInfo: intent.wantsDetails,
      needsGuidance: intent.needsGuidance,
      queryType: categorizeQuery(userQuery)
    })}`;

    const response = await fetch(AZURE_OPENAI_CONFIG.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'api-key': AZURE_OPENAI_CONFIG.apiKey
      },
      body: JSON.stringify({
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userQuery }
        ],
        max_tokens: 200,
        temperature: 0.8
      })
    });

    if (response.ok) {
      const data = await response.json();
      return data.choices?.[0]?.message?.content || "I'd be happy to help you analyze your SLD! Please upload and process an SLD document first, and then I'll be able to assist you with your questions.";
    }
  } catch (error) {
    console.error('AI response error for no-data case:', error);
  }

  // Fallback response
  return "I'd be happy to help you analyze your SLD! However, I don't currently have any SLD data to work with. Please upload and process an SLD document first, and then I'll be able to assist you with component analysis, technical specifications, BOM generation, and more. Once you've processed an SLD, feel free to ask me anything about it!";
};

// Generate AI-powered response using Azure OpenAI
const generateAIResponse = async (userQuery: string, sldData: SLDData | null): Promise<string> => {
  if (!sldData) {
    return await generateNoDataResponse(userQuery);
  }

  try {
    const sldContext = {
      summary: {
        totalElements: sldData.text_elements.length,
        averageConfidence: (sldData.text_elements.reduce((sum, el) => sum + el.confidence, 0) / sldData.text_elements.length * 100).toFixed(1),
        documentType: sldData.document_type,
        processingTime: sldData.processing_time,
        imageDimensions: sldData.image_dimensions
      },
      textElements: sldData.text_elements.slice(0, 20).map(el => ({
        text: el.text.trim(),
        confidence: Math.round(el.confidence * 100),
        position: {
          x: Math.round(el.bounding_box.left),
          y: Math.round(el.bounding_box.top)
        }
      }))
    };

    // Analyze user intent for response guidance
    const intent = analyzeUserIntent(userQuery);

    const systemPrompt = `You are a helpful, friendly SLD (Single Line Diagram) analysis assistant. Respond like a knowledgeable human colleague who is polite and conversational.

**Your Expertise:**
- Electrical component identification (circuit breakers, transformers, generators, switchgear)
- Power system analysis and electrical specifications
- Bill of Materials generation
- Spatial layout analysis
- Electrical safety and compliance

**CONVERSATIONAL RESPONSE GUIDELINES:**
${intent.isGreeting ? '- User is greeting you: Respond warmly and briefly, ask what they\'d like to know' : ''}
${intent.isBrief ? '- User wants a quick answer: Keep response brief (1-3 sentences), offer to provide more details' : ''}
${intent.wantsDetails ? '- User wants detailed information: Provide comprehensive technical analysis with specifics' : ''}
${intent.needsGuidance ? '- User needs help: Offer step-by-step guidance and explain options clearly' : ''}

**TONE GUIDELINES:**
- Use natural, conversational language (not formal documentation style)
- Be friendly and approachable like a helpful colleague
- Include polite elements like "I can see...", "Let me help you with...", "Would you like me to..."
- Offer follow-up questions or additional help
- Use "I" and "you" to make it personal and conversational

**Current SLD Context:**
- Total elements: ${sldContext.summary.totalElements}
- Average confidence: ${sldContext.summary.averageConfidence}%
- Document type: ${sldContext.summary.documentType}

Respond with detailed electrical engineering knowledge while referencing the specific SLD data.`;

    const response = await fetch(AZURE_OPENAI_CONFIG.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'api-key': AZURE_OPENAI_CONFIG.apiKey
      },
      body: JSON.stringify({
        messages: [
          {
            role: 'system',
            content: systemPrompt
          },
          {
            role: 'user',
            content: `User Question: "${userQuery}"\n\nUser Intent: ${JSON.stringify({
              isGreeting: intent.isGreeting,
              wantsBriefResponse: intent.isBrief,
              wantsDetailedInfo: intent.wantsDetails,
              needsGuidance: intent.needsGuidance,
              queryType: categorizeQuery(userQuery)
            }, null, 2)}\n\nSLD Data: ${JSON.stringify(sldContext, null, 2)}`
          }
        ],
        max_tokens: intent.isBrief ? 300 : intent.wantsDetails ? 2000 : 1000,
        temperature: 0.7, // More conversational
        top_p: 0.9
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data.choices?.[0]?.message?.content || 'Sorry, I could not generate a response.';

  } catch (error) {
    console.error('AI response error:', error);
    // Return a simple error message - no mock responses
    return "I'm having trouble connecting to my AI service right now. Please try again in a moment, or check your connection.";
  }
};

// All responses now go through the AI - no more mock responses

const SLDBot: React.FC<SLDBotProps> = ({ sldData, isVisible = true }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showBOMPreview, setShowBOMPreview] = useState(false);
  const [bomData, setBomData] = useState<BOMData | null>(null);
  const [isGeneratingBOM, setIsGeneratingBOM] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Sample questions for future use
  // const sampleQuestions = [
  //   "What electrical components did you find?",
  //   "Can you show me the technical specifications?",
  //   "Please generate a Bill of Materials",
  //   "How confident are you about the text detection?",
  //   "What's the spatial layout of components?"
  // ];

  // Initialize with welcome message
  useEffect(() => {
    if (sldData && messages.length === 0) {
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        type: 'bot',
        content: `👋 **Hello! I'm your SLD Bot assistant.**\n\nI've analyzed your Single Line Diagram and found **${sldData.text_elements.length} text elements** with an average confidence of **${((sldData.text_elements.reduce((sum, el) => sum + el.confidence, 0) / sldData.text_elements.length) * 100).toFixed(1)}%**.\n\n🤖 **I can help you with:**\n• Component identification and analysis\n• Technical specifications extraction\n• Bill of Materials generation\n• Spatial relationship analysis\n• Quality assessment of text detection\n\n💡 **What would you like to explore first?**`,
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);
    }
  }, [sldData, messages.length]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Focus input when expanded
  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isExpanded]);

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const botResponse = await generateAIResponse(userMessage.content, sldData || null);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: botResponse,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Message error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  // const handleSampleQuestion = (question: string) => {
  //   setInputValue(question);
  //   setTimeout(() => handleSendMessage(), 100);
  // };



  // Format BOM response using AI for conversational tone
  const formatBOMResponse = async (bomData: BOMData): Promise<string> => {
    try {
      const systemPrompt = `You are a helpful SLD analysis assistant. A Bill of Materials has just been generated successfully. Create a brief, conversational response summarizing the results.

GUIDELINES:
- Be friendly and conversational
- Highlight key statistics
- Mention that download options are available
- Keep it brief but informative
- Use natural language, not formal documentation style`;

      const response = await fetch(AZURE_OPENAI_CONFIG.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'api-key': AZURE_OPENAI_CONFIG.apiKey
        },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: `BOM generated with: ${bomData.summary.totalComponents} total components, ${bomData.summary.uniqueTypes} unique types, ${Math.round(bomData.summary.averageConfidence * 100)}% average confidence. Main component types: ${bomData.components.slice(0, 3).map(c => c.componentType).join(', ')}` }
          ],
          max_tokens: 200,
          temperature: 0.7
        })
      });

      if (response.ok) {
        const data = await response.json();
        return data.choices?.[0]?.message?.content || `Great! I've generated your BOM with ${bomData.summary.totalComponents} components. Download options are available above.`;
      }
    } catch (error) {
      console.error('AI BOM response formatting failed:', error);
    }

    // Simple fallback
    return `BOM generated successfully with ${bomData.summary.totalComponents} components. Download options are available above.`;
  };

  const handleGenerateBOM = async () => {
    if (!sldData || !sldData.text_elements) {
      console.error('No SLD data available for BOM generation');
      return;
    }

    setIsGeneratingBOM(true);

    try {
      // Simulate processing time for better UX
      await new Promise(resolve => setTimeout(resolve, 1000));

      const generatedBOM = await generateAIBOM(sldData.text_elements);
      setBomData(generatedBOM);
      setShowBOMPreview(true);

      // Add structured BOM generation message to chat
      const bomMessage: Message = {
        id: Date.now().toString(),
        type: 'bot',
        content: await formatBOMResponse(generatedBOM),
        timestamp: new Date()
      };
      setMessages(prev => [...prev, bomMessage]);
    } catch (error) {
      console.error('BOM generation failed:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'bot',
        content: 'BOM Generation Failed\n\nI encountered an error while generating the Bill of Materials. Please ensure your SLD has been properly processed and try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsGeneratingBOM(false);
    }
  };

  // Generate download success message using AI
  const generateDownloadSuccessMessage = async (format: string, bomData: BOMData): Promise<string> => {
    try {
      const systemPrompt = `You are a helpful assistant. A user has just successfully downloaded a BOM file. Create a brief, friendly confirmation message.

GUIDELINES:
- Be conversational and positive
- Mention the file format
- Keep it brief (1-2 sentences)
- Offer additional help if needed`;

      const response = await fetch(AZURE_OPENAI_CONFIG.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'api-key': AZURE_OPENAI_CONFIG.apiKey
        },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: `User downloaded ${format.toUpperCase()} file with ${bomData.summary.totalComponents} components` }
          ],
          max_tokens: 100,
          temperature: 0.7
        })
      });

      if (response.ok) {
        const data = await response.json();
        return data.choices?.[0]?.message?.content || `Your ${format.toUpperCase()} file is downloading now!`;
      }
    } catch (error) {
      console.error('AI download message generation failed:', error);
    }

    return `Your ${format.toUpperCase()} file is downloading now!`;
  };

  // Download functionality for different formats
  const handleDownload = async (format: 'txt' | 'csv' | 'xlsx' | 'pdf') => {
    if (!bomData) return;

    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const filename = `BOM_${timestamp}`;

    try {
      switch (format) {
        case 'txt':
          downloadTXT(bomData, `${filename}.txt`);
          break;
        case 'csv':
          downloadCSV(bomData, `${filename}.csv`);
          break;
        case 'xlsx':
          downloadExcel(bomData, `${filename}.xlsx`);
          break;
        case 'pdf':
          downloadPDF(bomData, `${filename}.pdf`);
          break;
      }

      // Generate AI success message
      const successContent = await generateDownloadSuccessMessage(format, bomData);
      const successMessage: Message = {
        id: Date.now().toString(),
        type: 'bot',
        content: successContent,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, successMessage]);

    } catch (error) {
      console.error('Download failed:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'bot',
        content: `I'm sorry, there was an issue downloading your ${format.toUpperCase()} file. Please try again in a moment.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Download utility functions
  const downloadFile = (content: string, filename: string, mimeType: string) => {
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

  const downloadTXT = (bomData: BOMData, filename: string) => {
    const content = generateTXTContent(bomData);
    downloadFile(content, filename, 'text/plain');
  };

  const downloadCSV = (bomData: BOMData, filename: string) => {
    const content = generateCSVContent(bomData);
    downloadFile(content, filename, 'text/csv');
  };

  const downloadExcel = (bomData: BOMData, filename: string) => {
    // For now, use CSV format for Excel compatibility
    const content = generateCSVContent(bomData);
    downloadFile(content, filename, 'application/vnd.ms-excel');
  };

  const downloadPDF = (bomData: BOMData, filename: string) => {
    // For now, use TXT format as PDF generation requires additional libraries
    const content = generateTXTContent(bomData);
    downloadFile(content, filename.replace('.pdf', '.txt'), 'text/plain');
  };

  const generateTXTContent = (bomData: BOMData): string => {
    const { components, summary, metadata } = bomData;

    let content = `BILL OF MATERIALS - SINGLE LINE DIAGRAM\n`;
    content += `Generated: ${new Date().toLocaleString()}\n`;
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

  const generateCSVContent = (bomData: BOMData): string => {
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

  // AI-powered BOM generator function
  const generateAIBOM = async (textElements: TextElement[]): Promise<BOMData> => {
    try {
      const systemPrompt = `You are an expert electrical engineer specializing in Single Line Diagram (SLD) analysis. Your role is to:

1. **Educational Support**: Act as a mentor and teacher, providing clear insights about SLD components and electrical systems in simple, concise language
2. **Component Analysis**: Analyze text elements from SLD images to identify electrical components and their relationships
3. **BOM Generation**: Generate comprehensive Bill of Materials (BOM) in both tabular and JSON formats

CORE RESPONSIBILITIES:
1. Analyze each text element to identify electrical components from the SLD
2. Extract technical specifications (voltage, current, power ratings, frequency, etc.)
3. Group similar components and calculate total quantities
4. Identify electrical relationships and connections between components
5. Provide educational explanations about component functions and purposes
6. Return structured data in the specified JSON format

COMPONENT TYPES TO IDENTIFY (23 Categories):
**Protection & Control:**
- HRC FUSE, CIRCUIT BREAKER, ISOLATOR, CONTACTOR
- TIME DELAY RELAY, EARTH FAULT RELAY, OVER CURRENT RELAY
- INVERSE DEFINITE MINIMUM TIME LAG OVERCURRENT RELAY
- RIPPLE CONTROL RECEIVER RELAY SWITCH

**Measurement & Monitoring:**
- VOLTMETER, AMMETER, MAXIMUM DEMAND AMMETER
- CURRENT TRANSFORMER, PUB kWh METER
- PHASE INDICATOR LIGHTS, PHASE SELECTOR SWITCH

**Distribution & Connection:**
- CABLE TERMINATION BOX, HOUSE SERVICE/METER BOARD
- THREE FUSED TAP-OFF UNIT, SINGLE PHASE TAP-OFF UNIT
- SINGLE PHASE UNFUSED TAP-OFF UNIT
- KEY INTERLOCK BETWEEN COUPLER, EARTH ELECTRODE

ANALYSIS REQUIREMENTS:
- Identify component specifications (kV, A, kW, MVA, Hz, etc.)
- Determine component locations using coordinate data
- Assess detection confidence levels
- Establish electrical connections and system hierarchy
- Group identical components for quantity calculation

RESPONSE FORMAT:
- Provide brief educational context about identified components
- Present BOM in clear tabular format for readability
- Include complete JSON structure for data processing
- Explain component relationships and system functionality

REQUIRED JSON STRUCTURE:
{
  "components": [
    {
      "id": "unique_identifier",
      "itemNumber": 1,
      "componentType": "CIRCUIT BREAKER",
      "description": "11kV Circuit Breaker - CB1",
      "quantity": 1,
      "specifications": ["11kV", "630A", "25kA"],
      "location": "Position (x, y)",
      "confidence": 0.95,
      "textElements": [...],
      "function": "Primary protection device",
      "connections": ["upstream_component", "downstream_component"]
    }
  ],
  "summary": {
    "totalComponents": 15,
    "uniqueTypes": 6,
    "averageConfidence": 0.87,
    "processingDate": "ISO_DATE"
  },
  "metadata": {
    "documentType": "Single Line Diagram",
    "totalTextElements": 25,
    "processingTime": timestamp
  },
  "systemAnalysis": {
    "voltageLevel": "11kV",
    "systemType": "Distribution",
    "protectionScheme": "Overcurrent + Earth Fault"
  }
}

Keep responses concise, educational, and technically accurate.`;

      const response = await fetch(AZURE_OPENAI_CONFIG.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'api-key': AZURE_OPENAI_CONFIG.apiKey
        },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: systemPrompt },
            {
              role: 'user', content: `Generate BOM from these text elements: ${JSON.stringify(textElements.map(el => ({
                text: el.text.trim(),
                confidence: el.confidence,
                position: { x: Math.round(el.bounding_box.left), y: Math.round(el.bounding_box.top) }
              })), null, 2)}`
            }
          ],
          max_tokens: 3000,
          temperature: 0.1 // Low temperature for structured data
        })
      });

      if (response.ok) {
        const data = await response.json();
        const bomContent = data.choices?.[0]?.message?.content;

        if (bomContent) {
          try {
            // Try to parse the AI response as JSON
            const bomData = JSON.parse(bomContent);
            return bomData;
          } catch (parseError) {
            console.error('Failed to parse AI BOM response:', parseError);
          }
        }
      }
    } catch (error) {
      console.error('AI BOM generation failed:', error);
    }

    // Fallback: return minimal BOM structure
    return {
      components: [],
      summary: {
        totalComponents: 0,
        uniqueTypes: 0,
        averageConfidence: 0,
        processingDate: new Date().toISOString()
      },
      metadata: {
        documentType: 'Single Line Diagram',
        totalTextElements: textElements.length,
        processingTime: Date.now()
      }
    };
  };

  // Enhanced bot message rendering with tables and structured formatting
  const renderBotMessage = (content: string) => {
    const lines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let currentSection: string[] = [];
    let inTable = false;
    let tableData: string[][] = [];

    const flushCurrentSection = () => {
      if (currentSection.length > 0) {
        elements.push(
          <div key={elements.length} className="space-y-2">
            {currentSection.map((line, index) => {
              if (line.startsWith('• ')) {
                return (
                  <div key={index} className="flex items-start space-x-2">
                    <span className="text-red-500 mt-1">•</span>
                    <span>{line.substring(2)}</span>
                  </div>
                );
              } else if (line.startsWith('  - ')) {
                return (
                  <div key={index} className="flex items-start space-x-2 ml-4">
                    <span className="text-gray-400 mt-1">-</span>
                    <span className="text-gray-700">{line.substring(4)}</span>
                  </div>
                );
              } else if (line.startsWith('    ')) {
                return (
                  <div key={index} className="ml-8 text-sm text-gray-600">
                    {line.substring(4)}
                  </div>
                );
              } else if (line.trim() && !line.includes(':') && line === line.toUpperCase()) {
                return (
                  <h3 key={index} className="text-lg font-semibold text-gray-900 mt-4 mb-2">
                    {line}
                  </h3>
                );
              } else if (line.endsWith(':') && line.trim().length > 1) {
                return (
                  <h4 key={index} className="text-md font-medium text-gray-800 mt-3 mb-1">
                    {line}
                  </h4>
                );
              } else {
                return (
                  <p key={index} className="text-gray-800">
                    {line}
                  </p>
                );
              }
            })}
          </div>
        );
        currentSection = [];
      }
    };

    const flushTable = () => {
      if (tableData.length > 1) {
        const headers = tableData[0];
        const rows = tableData.slice(1);

        elements.push(
          <div key={elements.length} className="overflow-x-auto rounded-lg border border-gray-200 my-4">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-red-50">
                <tr>
                  {headers.map((header, index) => (
                    <th
                      key={index}
                      className="px-4 py-3 text-left text-xs font-medium text-red-700 uppercase tracking-wider"
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
                    className={`${rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'
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
      }
      tableData = [];
      inTable = false;
    };

    lines.forEach((line) => {
      // Check for table format (contains | characters)
      if (line.includes('|') && line.trim().startsWith('|')) {
        if (!inTable) {
          flushCurrentSection();
          inTable = true;
        }
        const cells = line.split('|').slice(1, -1).map(cell => cell.trim());
        tableData.push(cells);
      } else {
        if (inTable) {
          flushTable();
        }
        if (line.trim() === '') {
          flushCurrentSection();
        } else {
          currentSection.push(line);
        }
      }
    });

    // Flush remaining content
    flushCurrentSection();
    flushTable();

    return elements;
  };

  if (!isVisible) return null;

  // Responsive container classes - ensure bot header stays above navbar
  const containerClasses = isFullscreen
    ? "fixed inset-0 z-[60] bg-white" // z-[60] to stay above navbar (z-50)
    : "fixed bottom-6 right-6 z-50";

  const chatWindowClasses = isFullscreen
    ? "w-full h-full flex flex-col" // Remove pt-16 since we're above navbar now
    : `bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col transition-all duration-300 ease-out
       w-96 h-[650px]
       sm:w-80 sm:h-[600px]
       md:w-96 md:h-[650px]
       lg:w-[400px] lg:h-[650px]
       max-w-[calc(100vw-3rem)] max-h-[calc(100vh-3rem)]`;

  return (
    <div className={containerClasses}>
      {/* Chat Bubble */}
      {!isExpanded && !isFullscreen && (
        <button
          onClick={handleToggle}
          className="group bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 focus:outline-none focus:ring-4 focus:ring-red-500/30"
          aria-label="Open SLD Bot"
        >
          <MessageCircle className="w-6 h-6 transition-transform group-hover:scale-110" />
          {sldData && (
            <div className="absolute -top-2 -right-2 bg-gradient-to-r from-green-400 to-green-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center font-bold shadow-lg animate-pulse">
              !
            </div>
          )}
        </button>
      )}

      {/* Expanded Chat Window */}
      {(isExpanded || isFullscreen) && (
        <div className={chatWindowClasses}>
          {/* Header */}
          <div className={`bg-gradient-to-r from-red-500 via-red-600 to-red-700 text-white p-6 ${isFullscreen ? '' : 'rounded-t-2xl'} flex items-center justify-between shadow-xl border-b border-red-800/20`}>
            <div className="flex items-center space-x-4">
              <div className="bg-white/25 backdrop-blur-sm rounded-xl p-3 shadow-lg ring-1 ring-white/20">
                <Bot className="w-6 h-6 text-white drop-shadow-sm" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white drop-shadow-sm">
                  SLD Bot
                </h1>
                <div className="flex items-center space-x-2 mt-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse shadow-sm"></div>
                  <span className="text-red-100 text-sm font-medium">Ready to assist</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {!isFullscreen && (
                <button
                  onClick={() => setIsFullscreen(true)}
                  className="text-white/80 hover:text-white transition-colors p-2 rounded-lg hover:bg-white/10"
                  aria-label="Expand to fullscreen"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
              )}
              {isFullscreen && (
                <button
                  onClick={() => setIsFullscreen(false)}
                  className="text-white/80 hover:text-white transition-colors p-2 rounded-lg hover:bg-white/10"
                  aria-label="Exit fullscreen"
                >
                  <Minimize2 className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => {
                  setIsExpanded(false);
                  setIsFullscreen(false);
                }}
                className="text-white/80 hover:text-white transition-colors p-2 rounded-lg hover:bg-white/10"
                aria-label="Close chat"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* BOM Preview and Download Section */}
          {showBOMPreview && bomData && (
            <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-green-50 to-green-100">
              <div className="bg-white rounded-lg shadow-lg border border-green-200 p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="bg-green-500 rounded-full p-2">
                      <FileSpreadsheet className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Bill of Materials</h3>
                      <p className="text-sm text-gray-600">
                        {bomData.components.length} unique components • {bomData.summary.totalComponents} total items
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowBOMPreview(false)}
                    className="text-gray-400 hover:text-gray-600 p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Summary Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {bomData.summary.totalComponents}
                    </div>
                    <div className="text-sm text-blue-800">Total Components</div>
                  </div>
                  <div className="bg-purple-50 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {bomData.summary.uniqueTypes}
                    </div>
                    <div className="text-sm text-purple-800">Unique Types</div>
                  </div>
                  <div className="bg-green-50 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {Math.round(bomData.summary.averageConfidence * 100)}%
                    </div>
                    <div className="text-sm text-green-800">Avg Confidence</div>
                  </div>
                  <div className="bg-orange-50 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {bomData.metadata.totalTextElements}
                    </div>
                    <div className="text-sm text-orange-800">Text Elements</div>
                  </div>
                </div>

                {/* Download Buttons */}
                <div className="border-t border-gray-200 pt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Download Options:</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <button
                      onClick={() => handleDownload('txt')}
                      className="bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-center space-x-1"
                    >
                      <span>📄</span>
                      <span>TXT</span>
                    </button>
                    <button
                      onClick={() => handleDownload('csv')}
                      className="bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-center space-x-1"
                    >
                      <span>📊</span>
                      <span>CSV</span>
                    </button>
                    <button
                      onClick={() => handleDownload('xlsx')}
                      className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-center space-x-1"
                    >
                      <span>📈</span>
                      <span>Excel</span>
                    </button>
                    <button
                      onClick={() => handleDownload('pdf')}
                      className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-center space-x-1"
                    >
                      <span>📋</span>
                      <span>PDF</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Messages Area */}
          <div className={`flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-gray-50 to-gray-100 ${isFullscreen ? 'h-full' : ''}`}>
            {messages.length === 0 && !sldData && (
              <div className="text-center text-gray-500 py-12">
                <div className="bg-white rounded-full p-6 w-24 h-24 mx-auto mb-6 shadow-lg">
                  <Bot className="w-12 h-12 text-gray-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Welcome to SLD Bot!</h3>
                <p className="text-sm text-gray-500 max-w-xs mx-auto">Upload and process an SLD to start our conversation. I'm here to help analyze your diagrams!</p>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm transition-all duration-200 hover:shadow-md ${message.type === 'user'
                      ? 'bg-gradient-to-r from-red-500 to-red-600 text-white'
                      : 'bg-white text-gray-800 border border-gray-200/50 backdrop-blur-sm'
                    }`}
                >
                  <div className="flex items-start space-x-3">
                    {message.type === 'bot' && (
                      <div className="bg-red-50 rounded-full p-1.5 mt-0.5">
                        <Bot className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                      </div>
                    )}
                    <div className="flex-1">
                      <div className="text-sm leading-relaxed font-medium">
                        {message.type === 'bot' ? (
                          <div className="space-y-3">
                            {renderBotMessage(message.content)}
                          </div>
                        ) : (
                          <div className="whitespace-pre-wrap">{message.content}</div>
                        )}
                      </div>
                      <p className={`text-xs mt-2 font-medium ${message.type === 'user' ? 'text-red-100' : 'text-gray-400'
                        }`}>
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start animate-fade-in">
                <div className="bg-white text-gray-800 border border-gray-200/50 rounded-2xl px-4 py-3 max-w-[85%] shadow-sm backdrop-blur-sm">
                  <div className="flex items-center space-x-3">
                    <div className="bg-red-50 rounded-full p-1.5">
                      <Bot className="w-3.5 h-3.5 text-red-500" />
                    </div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-red-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-red-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-red-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-xs text-gray-500 font-medium">SLD Bot is thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Sample Questions */}
          {/* {messages.length <= 1 && sldData && (
            <SampleQuestions
              questions={sampleQuestions.slice(0, 5)}
              onQuestionSelect={handleSampleQuestion}
            />
          )} */}

          {/* Input Area */}
          <div className={`p-4 border-t border-gray-200/50 bg-white ${isFullscreen ? '' : 'rounded-b-2xl'} shadow-inner`}>
            {/* BOM Generation Button */}
            {sldData && (
              <div className="mb-4">
                <button
                  onClick={handleGenerateBOM}
                  disabled={isGeneratingBOM}
                  className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 disabled:from-gray-400 disabled:to-gray-500 text-white text-sm py-3 px-4 rounded-xl transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg hover:shadow-xl font-medium disabled:cursor-not-allowed"
                >
                  {isGeneratingBOM ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Generating BOM...</span>
                    </>
                  ) : (
                    <>
                      <FileSpreadsheet className="w-4 h-4" />
                      <span>Generate Bill of Materials</span>
                    </>
                  )}
                </button>
              </div>
            )}

            <div className="flex space-x-3">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder={sldData ? "Ask me anything about your SLD..." : "Upload an SLD first to start chatting..."}
                disabled={!sldData || isTyping}
                className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed shadow-sm transition-all duration-200 placeholder-gray-400"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || !sldData || isTyping}
                className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white p-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none"
                aria-label="Send message"
              >
                {isTyping ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SLDBot;
