#!/usr/bin/env python3
"""
Script to process test videos (car1.mp4 and car2.mp4) using the Vehicle Damage Detection API.
This script demonstrates the complete workflow of video processing and damage detection.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.infrastructure.config.settings import Settings
from src.infrastructure.config.dependencies import DependencyContainer
from src.infrastructure.config.logging_config import setup_logging, get_logger

# Initialize settings and logging
settings = Settings()
setup_logging()
logger = get_logger(__name__)


class VideoProcessingDemo:
    """Demo class for processing test videos."""
    
    def __init__(self):
        self.settings = Settings()
        self.container = DependencyContainer()
        self.video_files = [
            "videos/car1.mp4",
            "videos/car2.mp4"
        ]
        
    async def setup(self):
        """Setup directories and dependencies."""
        logger.info("Setting up video processing demo")
        
        # Directories are automatically set up in Settings.__init__
        
        # Check dependency health
        health_status = await self.container.health_check()
        if not all(health_status.values()):
            logger.warning(f"Some dependencies failed health check: {health_status}")
            return False
        
        logger.info("Setup completed successfully")
        return True
    
    async def validate_video_files(self) -> Dict[str, bool]:
        """Validate that test video files exist and are processable."""
        logger.info("Validating test video files")
        
        video_service = self.container.get_video_processing_service()
        validation_results = {}
        
        for video_file in self.video_files:
            file_path = Path(video_file).resolve()
            
            if not file_path.exists():
                logger.error(f"Video file not found: {file_path}")
                validation_results[video_file] = False
                continue
            
            try:
                # Validate video file
                result = await video_service.validate_video(file_path)
                
                validation_results[video_file] = result
                
                if result:
                    logger.info(f"✓ {video_file}: Valid")
                else:
                    logger.warning(f"✗ {video_file}: Invalid")
                            
            except Exception as e:
                logger.error(f"Failed to validate {video_file}: {e}")
                validation_results[video_file] = False
        
        return validation_results
    
    async def process_single_video(self, video_file: str) -> Dict[str, Any]:
        """Process a single video file."""
        logger.info(f"Processing video: {video_file}")
        
        video_use_case = self.container.get_process_video_use_case()
        
        try:
            # Process video
            result = await video_use_case.execute(
                video_path=video_file,
                confidence_threshold=0.5
            )
            
            logger.info(f"✓ Processing completed for {video_file}")
            logger.info(f"  Video ID: {result.video_id}")
            logger.info(f"  Damages detected: {len(result.damages)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process {video_file}: {e}")
            return {"error": str(e), "video_file": video_file}
    
    async def process_multiple_videos(self) -> List[Dict[str, Any]]:
        """Process multiple videos concurrently."""
        logger.info("Processing multiple videos concurrently")
        
        video_use_case = self.container.get_process_video_use_case()
        
        try:
            # Get absolute paths
            video_paths = [str(Path(video_file).resolve()) for video_file in self.video_files]
            
            # Process videos concurrently
            tasks = [
                video_use_case.execute(
                    video_path=video_file,
                    confidence_threshold=0.5
                )
                for video_file in self.video_files
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"✓ Successfully processed {len(results)} videos")
            
            # Log summary
            total_detections = 0
            for result in results:
                if 'detections' in result:
                    total_detections += len(result['detections'])
            
            logger.info(f"Total detections across all videos: {total_detections}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to process multiple videos: {e}")
            return [{"error": str(e)}]
    
    async def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics and results summary."""
        logger.info("Retrieving processing statistics")
        
        detection_use_case = self.container.get_detection_results_use_case()
        
        try:
            # Get all detection results to calculate statistics
            results = await detection_use_case.execute()
            
            # Calculate basic statistics
            total_detections = len(results)
            damage_types = {}
            for result in results:
                for damage in result.damages:
                    damage_type = damage.damage_type.value
                    damage_types[damage_type] = damage_types.get(damage_type, 0) + 1
            
            stats = {
                'total_detections': total_detections,
                'damage_types': damage_types,
                'videos_processed': len(set(result.video_id for result in results))
            }
            
            logger.info("Processing Statistics:")
            logger.info(f"  Total videos processed: {stats['videos_processed']}")
            logger.info(f"  Total detections: {stats['total_detections']}")
            
            if stats['damage_types']:
                logger.info("  Damage type distribution:")
                for damage_type, count in stats['damage_types'].items():
                    logger.info(f"    {damage_type}: {count}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}
    
    async def export_results(self) -> Dict[str, Any]:
        """Export processing results."""
        logger.info("Exporting processing results")
        
        try:
            # For now, just log that export would happen here
            logger.info("✓ Export functionality would be implemented here")
            
            return {
                'status': 'Export feature not yet implemented'
            }
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return {"error": str(e)}
    
    async def run_demo(self):
        """Run the complete video processing demo."""
        logger.info("=" * 60)
        logger.info("Starting Vehicle Damage Detection Demo")
        logger.info("=" * 60)
        
        try:
            # Setup
            if not await self.setup():
                logger.error("Setup failed, aborting demo")
                return False
            
            # Validate video files
            logger.info("\n" + "=" * 40)
            logger.info("Step 1: Validating Video Files")
            logger.info("=" * 40)
            
            validation_results = await self.validate_video_files()
            valid_videos = [video for video, is_valid in validation_results.items() if is_valid]
            
            if not valid_videos:
                logger.error("No valid video files found, aborting demo")
                return False
            
            # Process videos individually
            logger.info("\n" + "=" * 40)
            logger.info("Step 2: Processing Videos Individually")
            logger.info("=" * 40)
            
            individual_results = []
            for video_file in valid_videos:
                result = await self.process_single_video(video_file)
                individual_results.append(result)
                await asyncio.sleep(1)  # Small delay between processing
            
            # Process videos concurrently
            logger.info("\n" + "=" * 40)
            logger.info("Step 3: Processing Videos Concurrently")
            logger.info("=" * 40)
            
            concurrent_results = await self.process_multiple_videos()
            
            # Get statistics
            logger.info("\n" + "=" * 40)
            logger.info("Step 4: Processing Statistics")
            logger.info("=" * 40)
            
            stats = await self.get_processing_statistics()
            
            # Export results
            logger.info("\n" + "=" * 40)
            logger.info("Step 5: Exporting Results")
            logger.info("=" * 40)
            
            export_result = await self.export_results()
            
            # Demo summary
            logger.info("\n" + "=" * 60)
            logger.info("Demo Completed Successfully!")
            logger.info("=" * 60)
            
            logger.info(f"Videos processed: {len(valid_videos)}")
            logger.info(f"Individual processing results: {len(individual_results)}")
            logger.info(f"Concurrent processing results: {len(concurrent_results)}")
            
            if 'export_file' in export_result:
                logger.info(f"Results exported to: {export_result['export_file']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Demo failed with error: {e}")
            return False


async def main():
    """Main function to run the video processing demo."""
    demo = VideoProcessingDemo()
    success = await demo.run_demo()
    
    if success:
        print("\n🎉 Video processing demo completed successfully!")
        print("Check the logs and output directory for detailed results.")
        return 0
    else:
        print("\n❌ Video processing demo failed.")
        print("Check the logs for error details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)