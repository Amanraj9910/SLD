# SLD Bot - AI Assistant for Single Line Diagram Processing

## Overview

The SLD Bot is an intelligent AI assistant designed to help users analyze and interact with Single Line Diagram (SLD) processing results. It provides natural language querying capabilities, automated Bill of Materials (BOM) generation, and comprehensive analysis of text detection data from Azure Document Intelligence.

## Features

### 🤖 **AI Chat Interface**
- **Natural Language Processing**: Ask questions about your SLD in plain English
- **Context-Aware Responses**: Bot understands the specific SLD data you've processed
- **Interactive Suggestions**: Provides sample questions to guide users
- **Real-time Typing Indicators**: Smooth chat experience with visual feedback

### 📊 **Comprehensive Analysis**
- **Component Detection**: Identifies electrical components (circuit breakers, transformers, etc.)
- **Technical Specifications**: Extracts voltage, current, power ratings, and other specs
- **Confidence Assessment**: Analyzes text detection quality and reliability
- **Spatial Relationships**: Understands component positioning and layout
- **Search Functionality**: Find specific text elements or components

### 📋 **Bill of Materials (BOM) Generation**
- **Automated Component Extraction**: Identifies and categorizes electrical components
- **Quantity Calculation**: Groups similar components and counts instances
- **Specification Extraction**: Pulls technical ratings and part numbers
- **Multiple Export Formats**: CSV and summary text files
- **Professional Formatting**: Industry-standard BOM structure

### 🎨 **User Interface**
- **Floating Widget**: Non-intrusive bottom-right positioning
- **Collapsible Design**: Chat bubble expands to full interface
- **Theme Consistency**: Matches application design language
- **Responsive Layout**: Works on different screen sizes
- **Accessibility**: Proper ARIA labels and keyboard navigation

## Technical Implementation

### Architecture
```
SLD Bot Component
├── Chat Interface (React Component)
├── AI Response Engine (Pattern Matching + Analysis)
├── BOM Generator (Component Extraction + Export)
├── Context Integration (Global State Management)
└── UI Components (Floating Widget + Chat Window)
```

### Key Components

#### 1. **SLDBot.tsx** - Main Component
- Manages chat state and user interactions
- Handles message flow and typing indicators
- Integrates with global SLD context
- Provides BOM generation interface

#### 2. **SLDContext.tsx** - State Management
- Global state for SLD data sharing
- Synchronizes data between pages and bot
- Manages processing states
- Provides React context for data access

#### 3. **AI Response Engine**
- Pattern-based natural language understanding
- Component identification algorithms
- Technical specification extraction
- Spatial analysis capabilities

#### 4. **BOM Generation System**
- Component pattern matching
- Quantity aggregation
- Specification parsing
- Multi-format export (CSV, TXT)

### Data Flow
```
Text Detection Page → Process SLD → Update Context → SLD Bot Access
                                        ↓
User Query → AI Analysis → Pattern Matching → Response Generation
                                        ↓
BOM Request → Component Extraction → Export Generation → File Download
```

## Usage Guide

### Getting Started
1. **Upload SLD**: Use the Text Detection page to upload and process an SLD image
2. **Open Bot**: Click the floating chat bubble in the bottom-right corner
3. **Ask Questions**: Type natural language queries about your SLD
4. **Generate BOM**: Use the "Generate BOM" button for automated material lists

### Sample Queries
- "What components are detected in this SLD?"
- "Show me all high-confidence text elements"
- "Generate a Bill of Materials"
- "What technical specifications are found?"
- "Analyze the spatial relationships between components"
- "Search for circuit breakers"
- "Show confidence statistics"

### BOM Generation
1. Process an SLD with text detection
2. Open the SLD Bot
3. Click "Generate BOM" button
4. Downloads include:
   - **CSV File**: Detailed component list with specifications
   - **Summary File**: Human-readable analysis and recommendations

## Component Recognition

### Supported Component Types
- **Protection**: Circuit Breakers (CB, MCB, MCCB), Relays
- **Measurement**: Current Transformers (CT), Potential Transformers (PT/VT), Meters
- **Power**: Transformers (TR), Generators (GEN)
- **Distribution**: Bus Bars, Switches, Isolators
- **Load**: Motors, Loads
- **Compensation**: Capacitors, Reactors
- **Connection**: Cables, Feeders

### Specification Extraction
- **Electrical Ratings**: Voltage (V, kV), Current (A, kA), Power (W, kW, MVA)
- **Frequency**: Hz ratings
- **Impedance**: Ohm, percentage values
- **Ratios**: Transformer and CT/PT ratios
- **Physical**: Cable sizes (mm², AWG)

## Integration Points

### Global Context
The SLD Bot integrates with the application's global state management:
```typescript
// Context provides SLD data to bot
const { sldData, setSLDData, currentImageUrl } = useSLD();

// Bot receives processed text detection results
<SLDBot sldData={sldData} isVisible={true} />
```

### Text Detection Integration
Automatically receives data when SLD processing completes:
- Text elements with confidence scores
- Bounding box coordinates
- Image dimensions
- Processing metadata

## Customization

### Adding New Component Types
```typescript
const componentPatterns = {
  'New Component': {
    pattern: /\b(NEW|COMP)\b/i,
    category: 'Custom'
  }
};
```

### Extending AI Responses
```typescript
// Add new query patterns in generateBotResponse function
if (input.includes('custom query')) {
  return "Custom response logic here";
}
```

### BOM Format Customization
Modify the `generateExcelBOM` function to change export formats or add new fields.

## Performance Considerations

- **Lazy Loading**: Bot only processes data when expanded
- **Efficient Pattern Matching**: Optimized regex patterns for component detection
- **Memory Management**: Proper cleanup of blob URLs and event listeners
- **Responsive Design**: Smooth animations and interactions

## Future Enhancements

### Planned Features
- **Real AI Integration**: Replace pattern matching with actual AI/ML models
- **Advanced BOM Features**: Excel export with formulas and formatting
- **Component Visualization**: Highlight components on SLD image
- **Multi-language Support**: Internationalization for global use
- **Learning Capabilities**: Improve responses based on user feedback

### Integration Opportunities
- **External APIs**: Connect to component databases and pricing services
- **CAD Integration**: Export to electrical design software
- **Project Management**: Integration with procurement and project tools
- **Collaboration**: Share analysis results with team members

## Troubleshooting

### Common Issues
1. **Bot Not Responding**: Ensure SLD data is processed first
2. **Empty BOM**: Check if components are properly labeled in SLD
3. **Low Confidence**: Improve image quality or manual verification needed
4. **Missing Components**: Add custom patterns for specific naming conventions

### Debug Information
The bot provides detailed console logging for troubleshooting:
- Coordinate system detection
- Component pattern matching
- Specification extraction results
- BOM generation process

## Contributing

To extend the SLD Bot functionality:
1. Add new component patterns in `extractComponentsFromSLD`
2. Extend AI responses in `generateBotResponse`
3. Enhance BOM generation in `generateExcelBOM`
4. Update UI components for new features
5. Test with various SLD formats and layouts

---

**Note**: This implementation provides a foundation for AI-powered SLD analysis. For production use, consider integrating with actual AI/ML services for more sophisticated natural language understanding and component recognition.
