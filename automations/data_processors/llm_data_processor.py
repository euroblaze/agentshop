#!/usr/bin/env python3
"""
LLM Data Processor - Processes data using LLM capabilities
Analyzes scraped data, generates insights, and creates summaries
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import aiofiles

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from services.llm_orm_service import llm_orm_service


@dataclass
class ProcessingResult:
    """Result from data processing operation"""
    success: bool
    processed_items: int
    output_file: Optional[str] = None
    summary: Optional[str] = None
    insights: List[str] = None
    error: Optional[str] = None
    processing_time_ms: int = 0


class LLMDataProcessor:
    """Processes data using LLM capabilities for analysis and insights"""
    
    def __init__(self):
        self.default_provider = "openai"  # Can be configured
        self.default_model = "gpt-3.5-turbo"
        self.processing_session = f"data_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def process_batch(
        self,
        input_path: str,
        output_path: str,
        processing_type: str,
        config: Dict[str, Any]
    ) -> ProcessingResult:
        """Process a batch of data files"""
        
        start_time = datetime.now()
        processed_items = 0
        
        try:
            # Ensure output directory exists
            os.makedirs(output_path, exist_ok=True)
            
            # Get input files
            input_files = self._get_input_files(input_path, config)
            
            if not input_files:
                return ProcessingResult(
                    success=False,
                    processed_items=0,
                    error="No input files found"
                )
            
            # Process each file
            results = []
            for file_path in input_files:
                result = await self._process_file(file_path, processing_type, config)
                if result:
                    results.append(result)
                    processed_items += 1
            
            # Generate summary
            summary = await self._generate_batch_summary(results, processing_type)
            
            # Save results
            output_file = await self._save_batch_results(
                results, output_path, processing_type, summary
            )
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return ProcessingResult(
                success=True,
                processed_items=processed_items,
                output_file=output_file,
                summary=summary,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return ProcessingResult(
                success=False,
                processed_items=processed_items,
                error=str(e),
                processing_time_ms=processing_time
            )
    
    def _get_input_files(self, input_path: str, config: Dict[str, Any]) -> List[str]:
        """Get list of input files to process"""
        files = []
        
        if os.path.isfile(input_path):
            files.append(input_path)
        elif os.path.isdir(input_path):
            # Get files based on config filters
            file_extension = config.get('file_extension', '.json')
            max_files = config.get('max_files', 100)
            
            for filename in os.listdir(input_path):
                if filename.endswith(file_extension):
                    files.append(os.path.join(input_path, filename))
                    
                    if len(files) >= max_files:
                        break
        
        return sorted(files)
    
    async def _process_file(
        self,
        file_path: str,
        processing_type: str,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process a single file"""
        
        try:
            # Load file content
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
            
            # Process based on type
            if processing_type == 'content_analysis':
                return await self._analyze_content(data, config)
            elif processing_type == 'sentiment_analysis':
                return await self._analyze_sentiment(data, config)
            elif processing_type == 'summarization':
                return await self._summarize_content(data, config)
            elif processing_type == 'keyword_extraction':
                return await self._extract_keywords(data, config)
            elif processing_type == 'cleanup_and_normalize':
                return await self._cleanup_data(data, config)
            else:
                raise ValueError(f"Unknown processing type: {processing_type}")
                
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return None
    
    async def _analyze_content(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content using LLM"""
        
        content = self._extract_text_content(data)
        if not content:
            return {"error": "No content to analyze"}
        
        prompt = f"""
        Analyze the following content and provide insights:
        
        Content: {content[:2000]}...
        
        Please provide:
        1. Main topics and themes
        2. Key insights or findings
        3. Potential business value
        4. Content quality assessment
        5. Recommendations for action
        
        Format as JSON with keys: topics, insights, business_value, quality_score, recommendations
        """
        
        try:
            result = await llm_orm_service.generate_text(
                prompt=prompt,
                provider=config.get('llm_provider', self.default_provider),
                model=config.get('llm_model', self.default_model),
                session_id=self.processing_session,
                request_type='content_analysis',
                max_tokens=800,
                temperature=0.3
            )
            
            # Try to parse JSON response
            try:
                analysis = json.loads(result['content'])
            except:
                # If not valid JSON, create structured response
                analysis = {
                    "raw_analysis": result['content'],
                    "cost": result['cost'],
                    "provider": result['provider']
                }
            
            return {
                "file_content": content[:500],
                "analysis": analysis,
                "processing_metadata": {
                    "provider": result['provider'],
                    "model": result['model'],
                    "cost": result['cost'],
                    "tokens": result['tokens_used']
                }
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def _analyze_sentiment(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of content"""
        
        content = self._extract_text_content(data)
        if not content:
            return {"error": "No content for sentiment analysis"}
        
        prompt = f"""
        Analyze the sentiment of the following content:
        
        Content: {content[:1500]}
        
        Provide:
        1. Overall sentiment (positive/negative/neutral)
        2. Sentiment score (-1 to 1)
        3. Key emotional indicators
        4. Confidence level (0-1)
        
        Format as JSON: {{"sentiment": "positive/negative/neutral", "score": 0.5, "indicators": [], "confidence": 0.9}}
        """
        
        try:
            result = await llm_orm_service.generate_text(
                prompt=prompt,
                provider=config.get('llm_provider', self.default_provider),
                model=config.get('llm_model', self.default_model),
                session_id=self.processing_session,
                request_type='sentiment_analysis',
                max_tokens=300,
                temperature=0.1
            )
            
            try:
                sentiment = json.loads(result['content'])
            except:
                sentiment = {"raw_response": result['content']}
            
            return {
                "content_preview": content[:200],
                "sentiment_analysis": sentiment,
                "processing_cost": result['cost']
            }
            
        except Exception as e:
            return {"error": f"Sentiment analysis failed: {str(e)}"}
    
    async def _summarize_content(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of content"""
        
        content = self._extract_text_content(data)
        if not content:
            return {"error": "No content to summarize"}
        
        summary_length = config.get('summary_length', 'medium')
        length_instruction = {
            'short': 'in 1-2 sentences',
            'medium': 'in 3-5 sentences', 
            'long': 'in 1-2 paragraphs'
        }.get(summary_length, 'in 3-5 sentences')
        
        prompt = f"""
        Summarize the following content {length_instruction}:
        
        Content: {content[:3000]}
        
        Provide a clear, concise summary that captures the main points and key information.
        """
        
        try:
            result = await llm_orm_service.generate_text(
                prompt=prompt,
                provider=config.get('llm_provider', self.default_provider),
                model=config.get('llm_model', self.default_model),
                session_id=self.processing_session,
                request_type='summarization',
                max_tokens=400,
                temperature=0.3
            )
            
            return {
                "original_length": len(content),
                "summary": result['content'],
                "compression_ratio": len(result['content']) / len(content),
                "processing_cost": result['cost']
            }
            
        except Exception as e:
            return {"error": f"Summarization failed: {str(e)}"}
    
    async def _extract_keywords(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract keywords and key phrases"""
        
        content = self._extract_text_content(data)
        if not content:
            return {"error": "No content for keyword extraction"}
        
        num_keywords = config.get('num_keywords', 10)
        
        prompt = f"""
        Extract the {num_keywords} most important keywords and key phrases from the following content:
        
        Content: {content[:2000]}
        
        Provide keywords as a JSON array, ordered by relevance: ["keyword1", "keyword2", ...]
        """
        
        try:
            result = await llm_orm_service.generate_text(
                prompt=prompt,
                provider=config.get('llm_provider', self.default_provider),
                model=config.get('llm_model', self.default_model),
                session_id=self.processing_session,
                request_type='keyword_extraction',
                max_tokens=200,
                temperature=0.2
            )
            
            try:
                keywords = json.loads(result['content'])
            except:
                # Extract keywords from text response
                keywords = [word.strip() for word in result['content'].split(',')]
            
            return {
                "keywords": keywords,
                "content_preview": content[:300],
                "processing_cost": result['cost']
            }
            
        except Exception as e:
            return {"error": f"Keyword extraction failed: {str(e)}"}
    
    async def _cleanup_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up and normalize data"""
        
        # Basic data cleanup without LLM
        cleaned_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Clean up text
                cleaned_value = value.strip()
                cleaned_value = ' '.join(cleaned_value.split())  # Normalize whitespace
                cleaned_data[key] = cleaned_value
            elif isinstance(value, list):
                # Clean up lists
                cleaned_data[key] = [item for item in value if item and str(item).strip()]
            else:
                cleaned_data[key] = value
        
        return {
            "cleaned_data": cleaned_data,
            "original_keys": len(data),
            "cleaned_keys": len(cleaned_data),
            "processing_type": "data_cleanup"
        }
    
    def _extract_text_content(self, data: Dict[str, Any]) -> str:
        """Extract text content from data structure"""
        content_parts = []
        
        # Common fields that contain text content
        text_fields = ['content', 'text', 'title', 'description', 'body', 'article']
        
        for field in text_fields:
            if field in data and data[field]:
                content_parts.append(str(data[field]))
        
        # If no standard fields, try to extract any string values
        if not content_parts:
            for value in data.values():
                if isinstance(value, str) and len(value) > 50:
                    content_parts.append(value)
        
        return ' '.join(content_parts)
    
    async def _generate_batch_summary(
        self,
        results: List[Dict[str, Any]],
        processing_type: str
    ) -> str:
        """Generate summary of batch processing results"""
        
        if not results:
            return "No results to summarize"
        
        # Create summary based on processing type
        if processing_type == 'content_analysis':
            return self._summarize_content_analysis(results)
        elif processing_type == 'sentiment_analysis':
            return self._summarize_sentiment_analysis(results)
        else:
            return f"Processed {len(results)} items using {processing_type}"
    
    def _summarize_content_analysis(self, results: List[Dict[str, Any]]) -> str:
        """Summarize content analysis results"""
        total_items = len(results)
        successful_analyses = len([r for r in results if 'analysis' in r])
        
        # Extract common themes if available
        themes = []
        for result in results:
            if 'analysis' in result and isinstance(result['analysis'], dict):
                topics = result['analysis'].get('topics', [])
                if isinstance(topics, list):
                    themes.extend(topics)
        
        return f"Content Analysis Summary: {successful_analyses}/{total_items} items analyzed successfully."
    
    def _summarize_sentiment_analysis(self, results: List[Dict[str, Any]]) -> str:
        """Summarize sentiment analysis results"""
        sentiments = []
        for result in results:
            if 'sentiment_analysis' in result:
                sentiment = result['sentiment_analysis'].get('sentiment')
                if sentiment:
                    sentiments.append(sentiment)
        
        if sentiments:
            positive = sentiments.count('positive')
            negative = sentiments.count('negative')
            neutral = sentiments.count('neutral')
            
            return f"Sentiment Analysis: {positive} positive, {negative} negative, {neutral} neutral out of {len(sentiments)} items"
        
        return f"Sentiment analysis completed for {len(results)} items"
    
    async def _save_batch_results(
        self,
        results: List[Dict[str, Any]],
        output_path: str,
        processing_type: str,
        summary: str
    ) -> str:
        """Save batch processing results to file"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{processing_type}_results_{timestamp}.json"
        output_file = os.path.join(output_path, filename)
        
        output_data = {
            "processing_type": processing_type,
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "total_items": len(results),
            "results": results
        }
        
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(output_data, indent=2, ensure_ascii=False))
        
        return output_file
    
    async def analyze_data(
        self,
        data_source: str,
        analysis_type: str,
        config: Dict[str, Any]
    ) -> ProcessingResult:
        """Analyze data from various sources"""
        
        try:
            if data_source == 'llm_usage_stats':
                return await self._analyze_llm_usage(analysis_type, config)
            elif data_source == 'scraped_data':
                return await self._analyze_scraped_data(analysis_type, config)
            else:
                return ProcessingResult(
                    success=False,
                    processed_items=0,
                    error=f"Unknown data source: {data_source}"
                )
        
        except Exception as e:
            return ProcessingResult(
                success=False,
                processed_items=0,
                error=str(e)
            )
    
    async def _analyze_llm_usage(self, analysis_type: str, config: Dict[str, Any]) -> ProcessingResult:
        """Analyze LLM usage patterns"""
        
        # This would query the database for LLM usage stats
        # For now, return a mock result
        
        insights = [
            "Peak usage occurs during business hours (9 AM - 5 PM)",
            "GPT-3.5-turbo is the most cost-effective model for general tasks",
            "Claude performs better for complex reasoning tasks",
            "Average response time is under 2 seconds across all providers"
        ]
        
        return ProcessingResult(
            success=True,
            processed_items=1,
            summary="LLM usage analysis completed",
            insights=insights
        )
    
    async def _analyze_scraped_data(self, analysis_type: str, config: Dict[str, Any]) -> ProcessingResult:
        """Analyze scraped data patterns"""
        
        # This would process files from datalake/scraped_data
        # For now, return a mock result
        
        insights = [
            "Competitor pricing has increased by 15% over the last month",
            "New AI agent categories are emerging in the market",
            "Customer reviews mention 'ease of use' as the top priority",
            "Mobile-first design is becoming standard across competitors"
        ]
        
        return ProcessingResult(
            success=True,
            processed_items=1,
            summary="Scraped data analysis completed",
            insights=insights
        )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

async def example_usage():
    """Example of how to use the LLM data processor"""
    
    processor = LLMDataProcessor()
    
    # Example: Process scraped content
    sample_data = {
        "url": "https://example.com/article",
        "title": "The Future of AI Agents",
        "content": "AI agents are becoming increasingly sophisticated and are being deployed across various industries...",
        "scraped_at": "2024-01-15T10:30:00Z"
    }
    
    # Save sample data to test processing
    test_dir = "datalake/scraped_data/test"
    os.makedirs(test_dir, exist_ok=True)
    
    test_file = os.path.join(test_dir, "test_article.json")
    with open(test_file, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    # Process the data
    config = {
        'llm_provider': 'openai',
        'llm_model': 'gpt-3.5-turbo',
        'max_files': 10
    }
    
    # Content analysis
    result = await processor.process_batch(
        input_path=test_dir,
        output_path="datalake/processed_data/test",
        processing_type="content_analysis",
        config=config
    )
    
    print(f"Processing result: {result}")


if __name__ == "__main__":
    asyncio.run(example_usage())