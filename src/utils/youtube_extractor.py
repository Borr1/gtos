"""YouTube transcript extraction with robust rate limiting.

Fixes the KAP pipeline failures by implementing the rate limiting rules
from PROPOSED_AGENT1_CHANGES.md. This utility can be used standalone
or integrated into the KAP agents.
"""

import time
import random
import json
import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Result of transcript extraction attempt."""
    success: bool
    url: str
    video_id: str
    word_count: int = 0
    error_message: str = None
    file_path: str = None


class YouTubeRateLimitedExtractor:
    """YouTube transcript extractor with built-in rate limiting."""
    
    def __init__(self, output_dir: str = "research/kap_outputs/transcripts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting state
        self._last_request_time = 0
        self._request_count = 0
        self._block_count = 0
        self._block_until = 0
        
        # Statistics
        self.succeeded = 0
        self.failed = 0
        self.blocked = 0
        
        # Initialize transcript API
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api.formatters import TextFormatter
            self.api = YouTubeTranscriptApi
            self.formatter = TextFormatter()
            logger.info("YouTube transcript API initialized")
        except ImportError:
            logger.error("youtube-transcript-api not installed")
            raise
    
    def extract_batch(self, urls: List[str], signal_file: Optional[str] = None) -> List[ExtractionResult]:
        """Extract transcripts from a batch of URLs with rate limiting."""
        results = []
        
        logger.info(f"Starting extraction of {len(urls)} videos")
        logger.info("Rate limiting: 10-12s between requests, 60s every 5 requests")
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing video {i}/{len(urls)}: {url}")
            
            # Apply rate limiting
            self._apply_rate_limit()
            
            # Check if we're blocked
            if self._is_blocked():
                logger.warning(f"Rate limited, waiting for block to clear...")
                self._wait_for_block()
            
            # Extract transcript
            result = self._extract_single(url, i)
            results.append(result)
            
            # Update statistics
            if result.success:
                self.succeeded += 1
                logger.info(f"  ✓ {result.word_count} words saved to {result.file_path}")
            else:
                self.failed += 1
                logger.error(f"  ✗ Failed: {result.error_message}")
            
            # Update signal file incrementally (for downstream agents)
            if signal_file:
                self._update_signal(signal_file, urls)
            
            # Log progress
            if i % 5 == 0 or i == len(urls):
                logger.info(f"Progress: {i}/{len(urls)} processed, {self.succeeded} succeeded, {self.failed} failed")
        
        logger.info(f"Batch complete: {self.succeeded}/{len(urls)} succeeded")
        return results
    
    def _apply_rate_limit(self):
        """Apply rate limiting before each request."""
        current_time = time.time()
        
        # Basic rate limiting: 10-12 seconds between requests
        time_since_last = current_time - self._last_request_time
        if time_since_last < 10:
            sleep_time = 10 + random.uniform(0, 2)  # 10-12 seconds
            logger.debug(f"Rate limit: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
        self._request_count += 1
        
        # Extra pause every 5 requests
        if self._request_count % 5 == 0:
            logger.info("Rate limit: 5-request pause (60s)")
            time.sleep(60)
    
    def _is_blocked(self) -> bool:
        """Check if we're currently in a block period."""
        return time.time() < self._block_until
    
    def _wait_for_block(self):
        """Wait for block period to end."""
        wait_time = self._block_until - time.time()
        if wait_time > 0:
            logger.warning(f"Waiting {wait_time:.1f}s for block to clear")
            time.sleep(wait_time)
    
    def _handle_429_error(self):
        """Handle 429 rate limit error with exponential backoff."""
        self._block_count += 1
        self.blocked += 1
        
        # Exponential backoff: 90s * block_count (max 10 minutes)
        backoff_seconds = min(90 * self._block_count, 600)
        self._block_until = time.time() + backoff_seconds
        
        logger.error(
            f"YouTube 429 error (block #{self._block_count}), "
            f"backing off for {backoff_seconds}s"
        )
    
    def _extract_single(self, url: str, video_num: int) -> ExtractionResult:
        """Extract transcript from a single video."""
        video_id = self._extract_video_id(url)
        if not video_id:
            return ExtractionResult(
                success=False,
                url=url,
                video_id="unknown",
                error_message="Could not extract video ID from URL"
            )
        
        try:
            # Try to get transcript
            transcript_list = self.api.get_transcript(video_id)
            
            # Format as text
            transcript_text = self.formatter.format_transcript(transcript_list)
            
            # Save to file
            filename = f"video_{video_num:02d}.md"
            file_path = self.output_dir / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# Video {video_num:02d}\n\n")
                f.write(f"**URL:** {url}\n")
                f.write(f"**Video ID:** {video_id}\n")
                f.write(f"**Extracted:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## Transcript\n\n")
                f.write(transcript_text)
            
            word_count = len(transcript_text.split())
            
            return ExtractionResult(
                success=True,
                url=url,
                video_id=video_id,
                word_count=word_count,
                file_path=str(file_path)
            )
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific YouTube errors
            if "429" in error_msg or "rate limit" in error_msg.lower():
                self._handle_429_error()
                error_msg = "Rate limited by YouTube"
            elif "not available" in error_msg.lower():
                error_msg = "Transcript not available"
            elif "disabled" in error_msg.lower():
                error_msg = "Transcripts disabled for this video"
            
            return ExtractionResult(
                success=False,
                url=url,
                video_id=video_id,
                error_message=error_msg
            )
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        # Handle various YouTube URL formats
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        elif "youtube.com/watch" in url:
            if "v=" in url:
                return url.split("v=")[1].split("&")[0]
        elif "youtube.com/embed/" in url:
            return url.split("/embed/")[1].split("?")[0]
        
        # Try to extract 11-character video ID pattern
        import re
        match = re.search(r'[a-zA-Z0-9_-]{11}', url)
        return match.group(0) if match else None
    
    def _update_signal(self, signal_file: str, total_urls: List[str]):
        """Update signal file for downstream agents."""
        try:
            with open(signal_file, 'w') as f:
                f.write(f'READY\n')
                f.write(f'Transcripts: {self.succeeded}\n')
                f.write(f'Failed: {self.failed}\n')
                f.write(f'Pending: {len(total_urls) - self.succeeded - self.failed}\n')
                f.write(f'Blocked: {self.blocked}\n')
        except Exception as e:
            logger.error(f"Failed to update signal file: {e}")


def extract_from_urls_file(urls_file: str, output_dir: str = None, signal_file: str = None) -> bool:
    """Extract transcripts from URLs listed in a file.
    
    This function implements the KAP Agent 1 workflow with proper rate limiting.
    """
    # Read URLs
    try:
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        logger.error(f"URLs file not found: {urls_file}")
        return False
    
    if not urls:
        logger.warning("No URLs found in file")
        return False
    
    logger.info(f"Found {len(urls)} URLs to process")
    
    # Initialize extractor
    if output_dir is None:
        output_dir = os.path.dirname(urls_file) + "/transcripts"
    
    extractor = YouTubeRateLimitedExtractor(output_dir)
    
    # Extract transcripts
    results = extractor.extract_batch(urls, signal_file)
    
    # Summary
    success_count = sum(1 for r in results if r.success)
    logger.info(f"Extraction complete: {success_count}/{len(urls)} succeeded")
    
    return success_count > 0


if __name__ == "__main__":
    import sys
    import argparse
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Extract YouTube transcripts with rate limiting')
    parser.add_argument('urls_file', help='File containing YouTube URLs (one per line)')
    parser.add_argument('--output-dir', help='Output directory for transcripts')
    parser.add_argument('--signal-file', help='Signal file to update for downstream agents')
    
    args = parser.parse_args()
    
    success = extract_from_urls_file(args.urls_file, args.output_dir, args.signal_file)
    sys.exit(0 if success else 1)
