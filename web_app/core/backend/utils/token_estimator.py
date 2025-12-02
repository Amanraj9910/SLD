"""
Token Estimation Tool for SLD Chat Bot
Estimates input and output tokens for GPT-4o-mini when processing SLD files and chat interactions.
"""

import json
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TokenEstimate:
    """Token estimation result"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_estimate: float  # USD
    

class TokenEstimator:
    """Estimates token usage for SLD chat bot interactions"""
    
    # GPT-4o-mini pricing (as of 2024)
    INPUT_TOKEN_COST = 0.00015 / 1000  # $0.15 per 1M input tokens
    OUTPUT_TOKEN_COST = 0.0006 / 1000  # $0.60 per 1M output tokens
    
    # Average token counts based on analysis of the SLDBot implementation
    SYSTEM_PROMPT_TOKENS = {
        'chat_response': 450,  # System prompt for regular chat responses
        'bom_generation': 850,  # System prompt for BOM generation
        'no_data_response': 200,  # System prompt when no SLD data available
        'bom_formatting': 150   # System prompt for BOM response formatting
    }
    
    def __init__(self):
        self.conversation_history = []
        
    def estimate_tokens_from_text(self, text: str) -> int:
        """
        Estimate token count from text using a simple approximation.
        GPT models typically use ~4 characters per token for English text.
        """
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Rough estimation: 4 characters per token
        # JSON and structured data tends to be more token-dense
        if self._is_json_like(text):
            return len(text) // 3  # JSON is more token-dense
        else:
            return len(text) // 4  # Regular text
    
    def _is_json_like(self, text: str) -> bool:
        """Check if text appears to be JSON or structured data"""
        json_indicators = ['{', '}', '[', ']', '":', '","', 'null', 'true', 'false']
        return any(indicator in text for indicator in json_indicators)
    
    def estimate_sld_data_tokens(self, text_elements_count: int) -> int:
        """Estimate tokens for SLD data context"""
        # Based on the SLDBot implementation, it sends:
        # - Summary data (totalElements, averageConfidence, etc.)
        # - First 20 text elements with position data
        
        base_summary_tokens = 100  # Summary metadata
        per_element_tokens = 25    # Each text element with position data
        
        # Limit to first 20 elements as per implementation
        elements_to_include = min(text_elements_count, 20)
        
        return base_summary_tokens + (elements_to_include * per_element_tokens)
    
    def estimate_chat_interaction(self, 
                                user_question: str, 
                                sld_data_elements: int = 0,
                                response_type: str = 'brief') -> TokenEstimate:
        """
        Estimate tokens for a single chat interaction
        
        Args:
            user_question: The user's question
            sld_data_elements: Number of text elements in SLD data
            response_type: 'brief', 'detailed', or 'greeting'
        """
        # Input tokens calculation
        system_prompt_tokens = self.SYSTEM_PROMPT_TOKENS['chat_response']
        user_question_tokens = self.estimate_tokens_from_text(user_question)
        sld_context_tokens = self.estimate_sld_data_tokens(sld_data_elements) if sld_data_elements > 0 else 0
        
        # Add conversation history (previous messages in context)
        history_tokens = sum(msg['tokens'] for msg in self.conversation_history[-10:])  # Last 10 messages
        
        input_tokens = system_prompt_tokens + user_question_tokens + sld_context_tokens + history_tokens
        
        # Output tokens estimation based on response type
        output_tokens_map = {
            'greeting': 50,
            'brief': 200,
            'detailed': 800,
            'help': 400
        }
        output_tokens = output_tokens_map.get(response_type, 300)
        
        total_tokens = input_tokens + output_tokens
        cost = (input_tokens * self.INPUT_TOKEN_COST) + (output_tokens * self.OUTPUT_TOKEN_COST)
        
        # Store in conversation history
        self.conversation_history.append({
            'user_tokens': user_question_tokens,
            'bot_tokens': output_tokens,
            'tokens': user_question_tokens + output_tokens,
            'timestamp': datetime.now()
        })
        
        return TokenEstimate(input_tokens, output_tokens, total_tokens, cost)
    
    def estimate_bom_generation(self, text_elements_count: int) -> TokenEstimate:
        """Estimate tokens for BOM generation"""
        system_prompt_tokens = self.SYSTEM_PROMPT_TOKENS['bom_generation']
        
        # BOM generation includes all text elements (not limited to 20)
        text_elements_tokens = text_elements_count * 30  # Each element with full data
        
        input_tokens = system_prompt_tokens + text_elements_tokens
        output_tokens = 3000  # Max tokens set in implementation
        
        total_tokens = input_tokens + output_tokens
        cost = (input_tokens * self.INPUT_TOKEN_COST) + (output_tokens * self.OUTPUT_TOKEN_COST)
        
        return TokenEstimate(input_tokens, output_tokens, total_tokens, cost)
    
    def estimate_session_with_20_questions(self, 
                                         sld_elements_count: int,
                                         include_bom_generation: bool = True) -> Dict[str, Any]:
        """
        Estimate token usage for a complete session with 1 SLD file and 20 questions
        """
        # Reset conversation history
        self.conversation_history = []
        
        # Sample question distribution based on typical user behavior
        question_types = [
            ('greeting', 1),           # "Hi, what did you find?"
            ('brief', 12),             # Quick questions about components
            ('detailed', 5),           # Detailed analysis requests
            ('help', 2)                # Help/guidance questions
        ]
        
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        interaction_details = []
        
        # Process each question type
        question_num = 1
        for response_type, count in question_types:
            for _ in range(count):
                # Sample questions for estimation
                sample_questions = {
                    'greeting': "Hi, what components did you find in this SLD?",
                    'brief': f"What is the voltage rating of component {question_num}?",
                    'detailed': f"Can you provide detailed specifications and analysis of all protection devices?",
                    'help': "How do I interpret the spatial layout of these components?"
                }
                
                question = sample_questions[response_type]
                estimate = self.estimate_chat_interaction(question, sld_elements_count, response_type)
                
                total_input_tokens += estimate.input_tokens
                total_output_tokens += estimate.output_tokens
                total_cost += estimate.cost_estimate
                
                interaction_details.append({
                    'question_num': question_num,
                    'type': response_type,
                    'question': question,
                    'input_tokens': estimate.input_tokens,
                    'output_tokens': estimate.output_tokens,
                    'cost': estimate.cost_estimate
                })
                
                question_num += 1
        
        # Add BOM generation if requested
        bom_estimate = None
        if include_bom_generation:
            bom_estimate = self.estimate_bom_generation(sld_elements_count)
            total_input_tokens += bom_estimate.input_tokens
            total_output_tokens += bom_estimate.output_tokens
            total_cost += bom_estimate.cost_estimate
        
        return {
            'session_summary': {
                'sld_elements_count': sld_elements_count,
                'total_questions': 20,
                'bom_generation_included': include_bom_generation,
                'total_input_tokens': total_input_tokens,
                'total_output_tokens': total_output_tokens,
                'total_tokens': total_input_tokens + total_output_tokens,
                'estimated_cost_usd': round(total_cost, 4),
                'cost_breakdown': {
                    'input_cost': round(total_input_tokens * self.INPUT_TOKEN_COST, 4),
                    'output_cost': round(total_output_tokens * self.OUTPUT_TOKEN_COST, 4)
                }
            },
            'bom_generation': {
                'input_tokens': bom_estimate.input_tokens if bom_estimate else 0,
                'output_tokens': bom_estimate.output_tokens if bom_estimate else 0,
                'cost': bom_estimate.cost_estimate if bom_estimate else 0
            } if bom_estimate else None,
            'question_breakdown': interaction_details,
            'conversation_growth': self._analyze_conversation_growth()
        }
    
    def _analyze_conversation_growth(self) -> Dict[str, Any]:
        """Analyze how conversation context grows over time"""
        if not self.conversation_history:
            return {}
        
        context_sizes = []
        cumulative_tokens = 0
        
        for i, msg in enumerate(self.conversation_history):
            cumulative_tokens += msg['tokens']
            # Context window includes last 10 messages
            context_size = sum(m['tokens'] for m in self.conversation_history[max(0, i-9):i+1])
            context_sizes.append(context_size)
        
        return {
            'context_growth_pattern': context_sizes,
            'max_context_size': max(context_sizes) if context_sizes else 0,
            'average_context_size': sum(context_sizes) / len(context_sizes) if context_sizes else 0,
            'total_conversation_tokens': cumulative_tokens
        }


def run_estimation_example():
    """Run example estimation for different SLD sizes"""
    estimator = TokenEstimator()
    
    # Test different SLD sizes
    sld_sizes = [
        ('Small SLD', 25),      # 25 text elements
        ('Medium SLD', 75),     # 75 text elements  
        ('Large SLD', 150),     # 150 text elements
        ('Very Large SLD', 300) # 300 text elements
    ]
    
    print("🔍 SLD Chat Bot Token Usage Estimation")
    print("=" * 60)
    print(f"Model: GPT-4o-mini")
    print(f"Input cost: ${TokenEstimator.INPUT_TOKEN_COST * 1000:.3f} per 1K tokens")
    print(f"Output cost: ${TokenEstimator.OUTPUT_TOKEN_COST * 1000:.3f} per 1K tokens")
    print()
    
    for sld_name, element_count in sld_sizes:
        print(f"📊 {sld_name} ({element_count} text elements)")
        print("-" * 40)
        
        # Estimate session with BOM generation
        result = estimator.estimate_session_with_20_questions(element_count, include_bom_generation=True)
        summary = result['session_summary']
        
        print(f"Total Input Tokens:  {summary['total_input_tokens']:,}")
        print(f"Total Output Tokens: {summary['total_output_tokens']:,}")
        print(f"Total Tokens:        {summary['total_tokens']:,}")
        print(f"Estimated Cost:      ${summary['estimated_cost_usd']:.4f}")
        
        if result['bom_generation']:
            bom = result['bom_generation']
            print(f"BOM Generation:      {bom['input_tokens'] + bom['output_tokens']:,} tokens (${bom['cost']:.4f})")
        
        print(f"Cost per Question:   ${summary['estimated_cost_usd']/20:.4f}")
        print()


if __name__ == "__main__":
    run_estimation_example()