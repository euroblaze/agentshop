#!/usr/bin/env python3
"""
Scoup Client - Integration with Scoup Microservice
https://github.com/euroblaze/scoup/

Provides web crawling capabilities for AgentShop automations
"""

import aiohttp
import asyncio
import json
import os
import sys
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

# Add backend to path for database integration
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from models.llm_models import WebcrawlerJob, ScrapedData


@dataclass
class ScoupConfig:
    """Configuration for Scoup microservice"""
    base_url: str = "http://localhost:3001"
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 10  # requests per second


@dataclass
class ScrapeRequest:
    """Request configuration for web scraping"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None
    proxy: Optional[str] = None
    user_agent: Optional[str] = None
    wait_for: Optional[str] = None  # CSS selector to wait for
    screenshot: bool = False
    extract_links: bool = True
    extract_images: bool = True
    extract_text: bool = True
    custom_selectors: Optional[Dict[str, str]] = None
    javascript: bool = False
    mobile: bool = False


@dataclass
class ScrapeResult:
    """Result from web scraping operation"""
    url: str
    status_code: int
    success: bool
    content: str
    html: str
    text: str
    title: str
    meta: Dict[str, Any]
    links: List[str]
    images: List[str]
    custom_data: Dict[str, Any]
    screenshot_url: Optional[str] = None
    error: Optional[str] = None
    scraped_at: datetime = None
    processing_time_ms: int = 0


class ScoupClient:
    """Client for interacting with Scoup web crawler microservice"""
    
    def __init__(self, config: ScoupConfig = None):
        self.config = config or ScoupConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = asyncio.Semaphore(self.config.rate_limit)
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if not self.session:
            headers = {}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def health_check(self) -> bool:
        """Check if Scoup service is healthy"""
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.config.base_url}/health") as response:
                return response.status == 200
        except Exception:
            return False
    
    async def scrape_url(self, request: ScrapeRequest) -> ScrapeResult:
        """Scrape a single URL"""
        async with self._rate_limiter:
            return await self._scrape_single(request)
    
    async def _scrape_single(self, request: ScrapeRequest) -> ScrapeResult:
        """Internal method to scrape a single URL"""
        await self._ensure_session()
        
        payload = {
            "url": request.url,
            "options": {
                "method": request.method,
                "headers": request.headers or {},
                "cookies": request.cookies or {},
                "proxy": request.proxy,
                "userAgent": request.user_agent,
                "waitFor": request.wait_for,
                "screenshot": request.screenshot,
                "extractLinks": request.extract_links,
                "extractImages": request.extract_images,
                "extractText": request.extract_text,
                "customSelectors": request.custom_selectors or {},
                "javascript": request.javascript,
                "mobile": request.mobile
            }
        }
        
        start_time = datetime.now()
        
        try:
            async with self.session.post(
                f"{self.config.base_url}/scrape",
                json=payload
            ) as response:
                
                processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                if response.status == 200:
                    data = await response.json()
                    return ScrapeResult(
                        url=request.url,
                        status_code=data.get('statusCode', 200),
                        success=True,
                        content=data.get('content', ''),
                        html=data.get('html', ''),
                        text=data.get('text', ''),
                        title=data.get('title', ''),
                        meta=data.get('meta', {}),
                        links=data.get('links', []),
                        images=data.get('images', []),
                        custom_data=data.get('customData', {}),
                        screenshot_url=data.get('screenshotUrl'),
                        scraped_at=datetime.now(),
                        processing_time_ms=processing_time
                    )
                else:
                    error_data = await response.text()
                    return ScrapeResult(
                        url=request.url,
                        status_code=response.status,
                        success=False,
                        content='',
                        html='',
                        text='',
                        title='',
                        meta={},
                        links=[],
                        images=[],
                        custom_data={},
                        error=f"HTTP {response.status}: {error_data}",
                        scraped_at=datetime.now(),
                        processing_time_ms=processing_time
                    )
        
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return ScrapeResult(
                url=request.url,
                status_code=0,
                success=False,
                content='',
                html='',
                text='',
                title='',
                meta={},
                links=[],
                images=[],
                custom_data={},
                error=str(e),
                scraped_at=datetime.now(),
                processing_time_ms=processing_time
            )
    
    async def scrape_multiple(self, requests: List[ScrapeRequest], concurrency: int = 5) -> List[ScrapeResult]:
        """Scrape multiple URLs with controlled concurrency"""
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_semaphore(request: ScrapeRequest) -> ScrapeResult:
            async with semaphore:
                return await self.scrape_url(request)
        
        tasks = [scrape_with_semaphore(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    async def scrape_sitemap(self, sitemap_url: str, filters: Optional[Dict[str, Any]] = None) -> List[ScrapeResult]:
        """Scrape URLs from a sitemap"""
        await self._ensure_session()
        
        payload = {
            "sitemapUrl": sitemap_url,
            "filters": filters or {}
        }
        
        try:
            async with self.session.post(
                f"{self.config.base_url}/scrape/sitemap",
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    urls = data.get('urls', [])
                    
                    # Create scrape requests for all URLs
                    requests = [ScrapeRequest(url=url) for url in urls]
                    return await self.scrape_multiple(requests)
                else:
                    raise Exception(f"Sitemap scraping failed: HTTP {response.status}")
        
        except Exception as e:
            raise Exception(f"Sitemap scraping error: {str(e)}")
    
    async def get_page_info(self, url: str) -> Dict[str, Any]:
        """Get basic page information without full scraping"""
        await self._ensure_session()
        
        payload = {"url": url, "infoOnly": True}
        
        try:
            async with self.session.post(
                f"{self.config.base_url}/info",
                json=payload
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Page info failed: HTTP {response.status}")
        
        except Exception as e:
            raise Exception(f"Page info error: {str(e)}")


class ScoupJobManager:
    """Manager for Scoup crawling jobs with database integration"""
    
    def __init__(self, client: ScoupClient = None):
        self.client = client or ScoupClient()
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'datalake', 'scraped_data')
        os.makedirs(self.data_dir, exist_ok=True)
    
    async def create_job(
        self,
        job_name: str,
        target_url: str,
        job_type: str = 'content_scraping',
        config: Optional[Dict[str, Any]] = None,
        schedule: Optional[str] = None
    ) -> int:
        """Create a new crawling job"""
        # This would integrate with the database
        # For now, return a mock job ID
        job_config = {
            'target_url': target_url,
            'job_type': job_type,
            'scrape_config': config or {},
            'schedule': schedule
        }
        
        print(f"Created job: {job_name}")
        print(f"Config: {json.dumps(job_config, indent=2)}")
        
        return 1  # Mock job ID
    
    async def run_job(self, job_id: int) -> Dict[str, Any]:
        """Execute a crawling job"""
        # Mock job execution
        job_name = f"job_{job_id}"
        target_url = "https://example.com"  # Would come from database
        
        print(f"Running job {job_id}: {job_name}")
        
        try:
            # Create scrape request
            request = ScrapeRequest(
                url=target_url,
                extract_links=True,
                extract_images=True,
                extract_text=True,
                javascript=True
            )
            
            # Execute scraping
            async with self.client:
                result = await self.client.scrape_url(request)
            
            if result.success:
                # Save results to data lake
                await self._save_result(job_id, result)
                
                return {
                    'job_id': job_id,
                    'status': 'completed',
                    'items_scraped': 1,
                    'success': True,
                    'message': 'Job completed successfully'
                }
            else:
                return {
                    'job_id': job_id,
                    'status': 'failed',
                    'success': False,
                    'error': result.error
                }
        
        except Exception as e:
            return {
                'job_id': job_id,
                'status': 'failed',
                'success': False,
                'error': str(e)
            }
    
    async def _save_result(self, job_id: int, result: ScrapeResult):
        """Save scraping result to data lake"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"job_{job_id}_{timestamp}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        data = {
            'job_id': job_id,
            'scraped_at': result.scraped_at.isoformat() if result.scraped_at else None,
            'url': result.url,
            'title': result.title,
            'text': result.text,
            'links': result.links,
            'images': result.images,
            'meta': result.meta,
            'custom_data': result.custom_data,
            'processing_time_ms': result.processing_time_ms,
            'success': result.success,
            'error': result.error
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved result to: {filepath}")
    
    async def get_job_results(self, job_id: int) -> List[Dict[str, Any]]:
        """Get results for a specific job"""
        results = []
        
        for filename in os.listdir(self.data_dir):
            if filename.startswith(f"job_{job_id}_") and filename.endswith('.json'):
                filepath = os.path.join(self.data_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(data)
        
        return sorted(results, key=lambda x: x.get('scraped_at', ''))


# =============================================================================
# PRESET CONFIGURATIONS FOR COMMON SCRAPING TASKS
# =============================================================================

class ScrapingPresets:
    """Predefined configurations for common scraping scenarios"""
    
    @staticmethod
    def ecommerce_product() -> ScrapeRequest:
        """Configuration for scraping e-commerce product pages"""
        return ScrapeRequest(
            url="",  # To be filled
            javascript=True,
            custom_selectors={
                'price': '.price, .cost, [data-price]',
                'title': 'h1, .product-title, .item-name',
                'description': '.description, .product-description',
                'rating': '.rating, .stars, .review-score',
                'availability': '.availability, .stock, .in-stock'
            },
            extract_images=True,
            wait_for='.price'
        )
    
    @staticmethod
    def blog_article() -> ScrapeRequest:
        """Configuration for scraping blog articles"""
        return ScrapeRequest(
            url="",  # To be filled
            custom_selectors={
                'title': 'h1, .entry-title, .post-title',
                'content': '.content, .entry-content, .post-content, article',
                'author': '.author, .byline, .post-author',
                'date': '.date, .published, .post-date',
                'tags': '.tags, .categories, .post-tags'
            },
            extract_links=True,
            extract_text=True
        )
    
    @staticmethod
    def competitor_analysis() -> ScrapeRequest:
        """Configuration for competitor website analysis"""
        return ScrapeRequest(
            url="",  # To be filled
            javascript=True,
            custom_selectors={
                'navigation': 'nav, .menu, .navigation',
                'features': '.features, .services, .offerings',
                'pricing': '.pricing, .plans, .cost',
                'contact': '.contact, .about, .company-info'
            },
            extract_links=True,
            extract_images=True,
            screenshot=True
        )
    
    @staticmethod
    def social_media() -> ScrapeRequest:
        """Configuration for social media content"""
        return ScrapeRequest(
            url="",  # To be filled
            javascript=True,
            mobile=True,
            custom_selectors={
                'posts': '.post, .tweet, .update',
                'engagement': '.likes, .shares, .comments',
                'hashtags': '.hashtag, .tag',
                'mentions': '.mention, .user-mention'
            },
            wait_for='.post'
        )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

async def example_usage():
    """Example of how to use the Scoup client"""
    
    # Initialize client
    config = ScoupConfig(
        base_url="http://localhost:3001",
        rate_limit=5
    )
    
    async with ScoupClient(config) as client:
        # Health check
        healthy = await client.health_check()
        print(f"Scoup service healthy: {healthy}")
        
        if not healthy:
            print("Scoup service not available, skipping examples")
            return
        
        # Single URL scraping
        request = ScrapeRequest(
            url="https://example.com",
            javascript=True,
            custom_selectors={
                'title': 'h1',
                'content': 'main, .content'
            }
        )
        
        result = await client.scrape_url(request)
        print(f"Scraped: {result.title}")
        print(f"Success: {result.success}")
        
        # Multiple URLs
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ]
        
        requests = [ScrapeRequest(url=url) for url in urls]
        results = await client.scrape_multiple(requests, concurrency=3)
        
        print(f"Scraped {len(results)} pages")
        for result in results:
            print(f"  {result.url}: {'✅' if result.success else '❌'}")


if __name__ == "__main__":
    asyncio.run(example_usage())