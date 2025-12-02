// Test data for SLD Bot functionality
import { TextElement } from '../../contexts/SLDContext';

export const mockSLDData = {
  document_path: "test_sld.pdf",
  document_type: "Single Line Diagram",
  page_count: 1,
  processing_time: 2.5,
  total_text_length: 450,
  text_elements: [
    {
      text: "CB-1 630A 11kV",
      confidence: 0.95,
      polygon: [[100, 100], [200, 100], [200, 150], [100, 150]],
      bounding_box: {
        left: 100,
        top: 100,
        width: 100,
        height: 50,
        x1: 100,
        y1: 100,
        x2: 200,
        y2: 150
      },
      page_number: 1,
      center: { x: 150, y: 125 },
      area: 5000
    },
    {
      text: "CT 1000/5A Class 1",
      confidence: 0.92,
      polygon: [[250, 100], [350, 100], [350, 150], [250, 150]],
      bounding_box: {
        left: 250,
        top: 100,
        width: 100,
        height: 50,
        x1: 250,
        y1: 100,
        x2: 350,
        y2: 150
      },
      page_number: 1,
      center: { x: 300, y: 125 },
      area: 5000
    },
    {
      text: "PT 11kV/110V 50VA",
      confidence: 0.88,
      polygon: [[400, 100], [500, 100], [500, 150], [400, 150]],
      bounding_box: {
        left: 400,
        top: 100,
        width: 100,
        height: 50,
        x1: 400,
        y1: 100,
        x2: 500,
        y2: 150
      },
      page_number: 1,
      center: { x: 450, y: 125 },
      area: 5000
    },
    {
      text: "TR 25MVA 132/11kV",
      confidence: 0.94,
      polygon: [[100, 200], [250, 200], [250, 280], [100, 280]],
      bounding_box: {
        left: 100,
        top: 200,
        width: 150,
        height: 80,
        x1: 100,
        y1: 200,
        x2: 250,
        y2: 280
      },
      page_number: 1,
      center: { x: 175, y: 240 },
      area: 12000
    },
    {
      text: "GEN 50MW 11kV 50Hz",
      confidence: 0.91,
      polygon: [[300, 200], [450, 200], [450, 280], [300, 280]],
      bounding_box: {
        left: 300,
        top: 200,
        width: 150,
        height: 80,
        x1: 300,
        y1: 200,
        x2: 450,
        y2: 280
      },
      page_number: 1,
      center: { x: 375, y: 240 },
      area: 12000
    },
    {
      text: "Bus Bar 11kV 2000A",
      confidence: 0.89,
      polygon: [[100, 300], [500, 300], [500, 320], [100, 320]],
      bounding_box: {
        left: 100,
        top: 300,
        width: 400,
        height: 20,
        x1: 100,
        y1: 300,
        x2: 500,
        y2: 320
      },
      page_number: 1,
      center: { x: 300, y: 310 },
      area: 8000
    },
    {
      text: "Motor 500kW 11kV 50Hz",
      confidence: 0.87,
      polygon: [[100, 400], [250, 400], [250, 480], [100, 480]],
      bounding_box: {
        left: 100,
        top: 400,
        width: 150,
        height: 80,
        x1: 100,
        y1: 400,
        x2: 250,
        y2: 480
      },
      page_number: 1,
      center: { x: 175, y: 440 },
      area: 12000
    },
    {
      text: "Cable 3x240mm² 11kV",
      confidence: 0.93,
      polygon: [[300, 400], [450, 400], [450, 430], [300, 430]],
      bounding_box: {
        left: 300,
        top: 400,
        width: 150,
        height: 30,
        x1: 300,
        y1: 400,
        x2: 450,
        y2: 430
      },
      page_number: 1,
      center: { x: 375, y: 415 },
      area: 4500
    },
    {
      text: "Relay 51/50 7SJ80",
      confidence: 0.86,
      polygon: [[500, 100], [600, 100], [600, 150], [500, 150]],
      bounding_box: {
        left: 500,
        top: 100,
        width: 100,
        height: 50,
        x1: 500,
        y1: 100,
        x2: 600,
        y2: 150
      },
      page_number: 1,
      center: { x: 550, y: 125 },
      area: 5000
    },
    {
      text: "Capacitor 5MVAR 11kV",
      confidence: 0.90,
      polygon: [[500, 200], [650, 200], [650, 280], [500, 280]],
      bounding_box: {
        left: 500,
        top: 200,
        width: 150,
        height: 80,
        x1: 500,
        y1: 200,
        x2: 650,
        y2: 280
      },
      page_number: 1,
      center: { x: 575, y: 240 },
      area: 12000
    }
  ] as TextElement[],
  image_dimensions: {
    width: 800,
    height: 600
  },
  service_info: {
    endpoint: "https://test-endpoint.cognitiveservices.azure.com/",
    model_id: "prebuilt-document",
    api_version: "2023-07-31"
  }
};

export const mockMarkdownResponse = `# SLD Analysis Results

## Component Summary

I've analyzed your Single Line Diagram and found **10 electrical components** with high confidence levels.

### Protection Equipment
- **Circuit Breaker (CB-1)**: 630A, 11kV rating
- **Relay (51/50)**: Siemens 7SJ80 protection relay

### Measurement Equipment  
- **Current Transformer**: 1000/5A, Class 1 accuracy
- **Potential Transformer**: 11kV/110V, 50VA rating

### Power Equipment
| Component | Rating | Specifications |
|-----------|--------|----------------|
| Transformer | 25MVA | 132/11kV |
| Generator | 50MW | 11kV, 50Hz |
| Motor | 500kW | 11kV, 50Hz |

### Distribution
- **Bus Bar**: 11kV, 2000A capacity
- **Cable**: 3x240mm², 11kV rated

### Compensation
- **Capacitor Bank**: 5MVAR, 11kV

## Technical Specifications

\`\`\`
Voltage Level: 11kV
Frequency: 50Hz
Total Power: 75MW (50MW Gen + 25MVA Transformer)
Protection: Overcurrent (51/50)
\`\`\`

## Confidence Analysis

The text detection achieved an **average confidence of 90.5%**, indicating high-quality OCR results.

**High Confidence (>90%)**:
- Circuit Breaker: 95%
- Transformer: 94%  
- Cable: 93%
- Current Transformer: 92%

**Medium Confidence (85-90%)**:
- Capacitor: 90%
- Bus Bar: 89%
- Potential Transformer: 88%
- Motor: 87%
- Relay: 86%

> 💡 **Tip**: All components show reliable detection confidence levels suitable for engineering analysis.`;

export const sampleQuestions = [
  "What electrical components did you find?",
  "Can you show me the technical specifications?", 
  "Please generate a Bill of Materials",
  "How confident are you about the text detection?",
  "What's the spatial layout of components?",
  "Show me the protection equipment details",
  "What are the voltage levels in this SLD?",
  "Analyze the power ratings of all equipment"
];

export const mockBOMData = {
  components: [
    {
      id: "Circuit Breaker_0",
      itemNumber: 1,
      componentType: "Circuit Breaker",
      description: "Circuit Breaker (630A, 11kV) - CB-1 630A 11kV",
      quantity: 1,
      specifications: ["630A", "11kV"],
      location: "Position (150, 125)",
      confidence: 0.95,
      textElements: [mockSLDData.text_elements[0]]
    },
    {
      id: "Current Transformer_1", 
      itemNumber: 2,
      componentType: "Current Transformer",
      description: "Current Transformer (1000/5A, Class 1) - CT 1000/5A Class 1",
      quantity: 1,
      specifications: ["1000/5A", "class 1"],
      location: "Position (300, 125)",
      confidence: 0.92,
      textElements: [mockSLDData.text_elements[1]]
    },
    {
      id: "Potential Transformer_2",
      itemNumber: 3, 
      componentType: "Potential Transformer",
      description: "Potential Transformer (11kV/110V, 50VA) - PT 11kV/110V 50VA",
      quantity: 1,
      specifications: ["11kV/110V", "50VA"],
      location: "Position (450, 125)",
      confidence: 0.88,
      textElements: [mockSLDData.text_elements[2]]
    }
  ],
  summary: {
    totalComponents: 3,
    uniqueTypes: 3,
    averageConfidence: 0.92,
    processingDate: new Date().toISOString()
  },
  metadata: {
    documentType: "Single Line Diagram",
    totalTextElements: 10,
    processingTime: Date.now()
  }
};
