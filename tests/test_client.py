#!/usr/bin/env python3
"""
SmartDoc Dolphin API 测试客户端
"""

import asyncio
import json
import time
from pathlib import Path

import httpx
from PIL import Image


class SmartDocClient:
    """SmartDoc Dolphin API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)  # 5分钟超时
    
    async def health_check(self):
        """健康检查"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def process_page(self, image_path: str, max_batch_size: int = 16):
        """页面级文档处理"""
        try:
            with open(image_path, "rb") as f:
                files = {"file": (Path(image_path).name, f, "image/png")}
                data = {"max_batch_size": max_batch_size}
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/process/page",
                    files=files,
                    data=data
                )
                
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def process_element(self, image_path: str, element_type: str = "text"):
        """元素级处理"""
        try:
            with open(image_path, "rb") as f:
                files = {"file": (Path(image_path).name, f, "image/png")}
                data = {"element_type": element_type}
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/process/element",
                    files=files,
                    data=data
                )
                
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_result(self, task_id: str):
        """获取处理结果"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/result/{task_id}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def main():
    """测试主函数"""
    client = SmartDocClient()
    
    print("🔍 Testing SmartDoc Dolphin API...")
    
    # 健康检查
    print("\n1. Health Check:")
    health = await client.health_check()
    print(json.dumps(health, indent=2))
    
    # 如果有测试图像，可以测试处理功能
    test_images = [
        "./demo/test.png",
        "./demo/test.jpg", 
        "./test.png",
        "./test.jpg"
    ]
    
    test_image = None
    for img_path in test_images:
        if Path(img_path).exists():
            test_image = img_path
            break
    
    if test_image:
        print(f"\n2. Testing page processing with: {test_image}")
        start_time = time.time()
        
        result = await client.process_page(test_image, max_batch_size=8)
        
        if "error" not in result:
            print(f"✅ Processing completed in {time.time() - start_time:.2f}s")
            print(f"📄 Elements found: {result['result']['total_elements']}")
            print(f"⏱️  Processing time: {result['result']['processing_time']:.2f}s")
            
            # 显示前几个元素
            elements = result['result']['elements'][:3]
            for i, element in enumerate(elements):
                print(f"\nElement {i+1}:")
                print(f"  Type: {element['type']}")
                print(f"  Text: {element['text'][:100]}...")
                print(f"  BBox: {element['bbox']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        print(f"\n3. Testing element processing with: {test_image}")
        element_result = await client.process_element(test_image, "text")
        
        if "error" not in element_result:
            print(f"✅ Element processing completed")
            print(f"📝 Text: {element_result['text'][:200]}...")
        else:
            print(f"❌ Error: {element_result['error']}")
            
    else:
        print("\n⚠️  No test images found. Please add a test image to:")
        print("   ./demo/test.png or ./test.png")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(main()) 