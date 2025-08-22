#!/usr/bin/env python3
"""
Script to test the Vehicle Damage Detection API endpoints.
This script starts the API server and tests various endpoints with the car videos.
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional


class APITester:
    """Class to test the Vehicle Damage Detection API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def wait_for_server(self, timeout: int = 30) -> bool:
        """Wait for the API server to be ready."""
        print(f"Waiting for server at {self.base_url} to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with self.session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        print("✓ Server is ready!")
                        return True
            except Exception:
                pass
            
            await asyncio.sleep(1)
        
        print("✗ Server failed to start within timeout")
        return False
    
    async def test_health_endpoints(self) -> Dict[str, Any]:
        """Test health check endpoints."""
        print("\n" + "=" * 40)
        print("Testing Health Endpoints")
        print("=" * 40)
        
        results = {}
        
        # Test basic health check
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                data = await response.json()
                results["basic_health"] = {
                    "status": response.status,
                    "data": data
                }
                print(f"✓ Basic health check: {response.status}")
        except Exception as e:
            results["basic_health"] = {"error": str(e)}
            print(f"✗ Basic health check failed: {e}")
        
        # Test detailed health check
        try:
            async with self.session.get(f"{self.api_base}/health/detailed") as response:
                data = await response.json()
                results["detailed_health"] = {
                    "status": response.status,
                    "data": data
                }
                print(f"✓ Detailed health check: {response.status}")
                
                if response.status == 200 and data.get("success"):
                    health_data = data.get("data", {})
                    print(f"  Dependencies: {health_data.get('dependencies', {})}")
                    print(f"  System: {health_data.get('system', {})}")
        except Exception as e:
            results["detailed_health"] = {"error": str(e)}
            print(f"✗ Detailed health check failed: {e}")
        
        # Test model info
        try:
            async with self.session.get(f"{self.api_base}/health/model-info") as response:
                data = await response.json()
                results["model_info"] = {
                    "status": response.status,
                    "data": data
                }
                print(f"✓ Model info: {response.status}")
        except Exception as e:
            results["model_info"] = {"error": str(e)}
            print(f"✗ Model info failed: {e}")
        
        return results
    
    async def test_file_endpoints(self) -> Dict[str, Any]:
        """Test file management endpoints."""
        print("\n" + "=" * 40)
        print("Testing File Endpoints")
        print("=" * 40)
        
        results = {}
        
        # Test file validation
        video_files = ["videos/car1.mp4", "videos/car2.mp4"]
        
        for video_file in video_files:
            file_path = str(Path(video_file).resolve())
            
            try:
                payload = {
                    "file_path": file_path,
                    "check_format": True,
                    "check_size": True,
                    "check_corruption": False
                }
                
                async with self.session.post(
                    f"{self.api_base}/files/validate",
                    json=payload
                ) as response:
                    data = await response.json()
                    results[f"validate_{Path(video_file).name}"] = {
                        "status": response.status,
                        "data": data
                    }
                    
                    if response.status == 200:
                        is_valid = data.get("data", {}).get("is_valid", False)
                        print(f"✓ {video_file} validation: {'Valid' if is_valid else 'Invalid'}")
                    else:
                        print(f"✗ {video_file} validation failed: {response.status}")
                        
            except Exception as e:
                results[f"validate_{Path(video_file).name}"] = {"error": str(e)}
                print(f"✗ {video_file} validation error: {e}")
        
        # Test disk usage
        try:
            async with self.session.get(f"{self.api_base}/files/disk-usage") as response:
                data = await response.json()
                results["disk_usage"] = {
                    "status": response.status,
                    "data": data
                }
                print(f"✓ Disk usage: {response.status}")
        except Exception as e:
            results["disk_usage"] = {"error": str(e)}
            print(f"✗ Disk usage failed: {e}")
        
        return results
    
    async def test_video_processing(self) -> Dict[str, Any]:
        """Test video processing endpoints."""
        print("\n" + "=" * 40)
        print("Testing Video Processing")
        print("=" * 40)
        
        results = {}
        video_ids = []
        
        # Process individual videos
        video_files = ["videos/car1.mp4", "videos/car2.mp4"]
        
        for video_file in video_files:
            file_path = str(Path(video_file).resolve())
            
            try:
                payload = {
                    "video_path": file_path,
                    "confidence_threshold": 0.5,
                    "save_annotated": True,
                    "create_thumbnail": True
                }
                
                print(f"Processing {video_file}...")
                async with self.session.post(
                    f"{self.api_base}/videos/process",
                    json=payload
                ) as response:
                    data = await response.json()
                    results[f"process_{Path(video_file).name}"] = {
                        "status": response.status,
                        "data": data
                    }
                    
                    if response.status == 200:
                        video_id = data.get("data", {}).get("video_id")
                        detections = data.get("data", {}).get("detections", [])
                        print(f"✓ {video_file} processed successfully")
                        print(f"  Video ID: {video_id}")
                        print(f"  Detections: {len(detections)}")
                        
                        if video_id:
                            video_ids.append(video_id)
                    else:
                        print(f"✗ {video_file} processing failed: {response.status}")
                        print(f"  Error: {data.get('detail', 'Unknown error')}")
                        
            except Exception as e:
                results[f"process_{Path(video_file).name}"] = {"error": str(e)}
                print(f"✗ {video_file} processing error: {e}")
        
        # Test multiple video processing
        try:
            video_paths = [str(Path(vf).resolve()) for vf in video_files]
            payload = {
                "video_paths": video_paths,
                "confidence_threshold": 0.5,
                "save_annotated": True,
                "create_thumbnail": True,
                "max_concurrent": 2
            }
            
            print("Processing multiple videos...")
            async with self.session.post(
                f"{self.api_base}/videos/process-multiple",
                json=payload
            ) as response:
                data = await response.json()
                results["process_multiple"] = {
                    "status": response.status,
                    "data": data
                }
                
                if response.status == 200:
                    processed_videos = data.get("data", {}).get("results", [])
                    print(f"✓ Multiple videos processed: {len(processed_videos)}")
                else:
                    print(f"✗ Multiple video processing failed: {response.status}")
                    
        except Exception as e:
            results["process_multiple"] = {"error": str(e)}
            print(f"✗ Multiple video processing error: {e}")
        
        # List processed videos
        try:
            async with self.session.get(f"{self.api_base}/videos") as response:
                data = await response.json()
                results["list_videos"] = {
                    "status": response.status,
                    "data": data
                }
                
                if response.status == 200:
                    videos = data.get("data", {}).get("videos", [])
                    print(f"✓ Listed videos: {len(videos)}")
                else:
                    print(f"✗ List videos failed: {response.status}")
                    
        except Exception as e:
            results["list_videos"] = {"error": str(e)}
            print(f"✗ List videos error: {e}")
        
        return results, video_ids
    
    async def test_detection_endpoints(self, video_ids: list) -> Dict[str, Any]:
        """Test detection result endpoints."""
        print("\n" + "=" * 40)
        print("Testing Detection Endpoints")
        print("=" * 40)
        
        results = {}
        
        # Get all detections
        try:
            async with self.session.get(f"{self.api_base}/detections") as response:
                data = await response.json()
                results["list_detections"] = {
                    "status": response.status,
                    "data": data
                }
                
                if response.status == 200:
                    detections = data.get("data", {}).get("results", [])
                    print(f"✓ Listed detections: {len(detections)}")
                else:
                    print(f"✗ List detections failed: {response.status}")
                    
        except Exception as e:
            results["list_detections"] = {"error": str(e)}
            print(f"✗ List detections error: {e}")
        
        # Get detection statistics
        try:
            async with self.session.get(f"{self.api_base}/detections/statistics") as response:
                data = await response.json()
                results["detection_stats"] = {
                    "status": response.status,
                    "data": data
                }
                
                if response.status == 200:
                    stats = data.get("data", {})
                    print(f"✓ Detection statistics retrieved")
                    print(f"  Total detections: {stats.get('total_detections', 0)}")
                    print(f"  Total videos: {stats.get('total_videos', 0)}")
                else:
                    print(f"✗ Detection statistics failed: {response.status}")
                    
        except Exception as e:
            results["detection_stats"] = {"error": str(e)}
            print(f"✗ Detection statistics error: {e}")
        
        # Get detections for specific videos
        for video_id in video_ids[:2]:  # Test first 2 video IDs
            try:
                async with self.session.get(
                    f"{self.api_base}/detections/video/{video_id}"
                ) as response:
                    data = await response.json()
                    results[f"detections_video_{video_id}"] = {
                        "status": response.status,
                        "data": data
                    }
                    
                    if response.status == 200:
                        detections = data.get("data", {}).get("results", [])
                        print(f"✓ Detections for video {video_id}: {len(detections)}")
                    else:
                        print(f"✗ Detections for video {video_id} failed: {response.status}")
                        
            except Exception as e:
                results[f"detections_video_{video_id}"] = {"error": str(e)}
                print(f"✗ Detections for video {video_id} error: {e}")
        
        return results
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run all API tests."""
        print("=" * 60)
        print("Vehicle Damage Detection API Tests")
        print("=" * 60)
        
        all_results = {}
        
        # Wait for server to be ready
        if not await self.wait_for_server():
            return {"error": "Server not ready"}
        
        # Test health endpoints
        health_results = await self.test_health_endpoints()
        all_results["health"] = health_results
        
        # Test file endpoints
        file_results = await self.test_file_endpoints()
        all_results["files"] = file_results
        
        # Test video processing
        video_results, video_ids = await self.test_video_processing()
        all_results["videos"] = video_results
        
        # Test detection endpoints
        if video_ids:
            detection_results = await self.test_detection_endpoints(video_ids)
            all_results["detections"] = detection_results
        
        # Test summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in all_results.items():
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    total_tests += 1
                    if isinstance(result, dict) and result.get("status") == 200:
                        passed_tests += 1
        
        print(f"Total tests: {total_tests}")
        print(f"Passed tests: {passed_tests}")
        print(f"Failed tests: {total_tests - passed_tests}")
        print(f"Success rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        
        return all_results


async def main():
    """Main function to run API tests."""
    async with APITester() as tester:
        results = await tester.run_tests()
        
        # Save results to file
        output_file = Path("api_test_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\nTest results saved to: {output_file}")
        
        # Check if tests were successful
        if "error" in results:
            print("\n❌ API tests failed to run.")
            return 1
        
        print("\n🎉 API tests completed!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)