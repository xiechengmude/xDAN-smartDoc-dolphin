#!/usr/bin/env python3
"""
xDAN-Vision-SmartDoc API 调用示例
演示不同场景下的API使用方法
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any

import httpx
import requests


class SimpleAPIExample:
    """简单的API调用示例"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def test_health(self):
        """测试服务健康状态"""
        print("🔍 检查服务健康状态...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ 服务正常运行")
                print(f"   版本: {health_data.get('version')}")
                print(f"   设备: {health_data.get('components', {}).get('compute_device', 'unknown')}")
                return True
            else:
                print(f"❌ 服务异常，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def simple_document_process(self, image_path: str):
        """最简单的文档处理"""
        print(f"\n📄 处理文档: {image_path}")
        
        if not Path(image_path).exists():
            print(f"❌ 文件不存在: {image_path}")
            return None
        
        try:
            with open(image_path, "rb") as f:
                files = {"file": (Path(image_path).name, f, "image/png")}
                data = {"output_format": "json"}
                
                response = requests.post(
                    f"{self.base_url}/api/process/document",
                    files=files,
                    data=data,
                    timeout=300
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 处理成功")
                print(f"   任务ID: {result['task_id']}")
                print(f"   识别元素: {result['total_elements']}")
                print(f"   处理时间: {result['processing_time']:.2f}s")
                return result
            else:
                print(f"❌ 处理失败，状态码: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 处理异常: {e}")
            return None
    
    def markdown_output_example(self, image_path: str):
        """Markdown格式输出示例"""
        print(f"\n📝 生成Markdown格式输出: {image_path}")
        
        try:
            with open(image_path, "rb") as f:
                files = {"file": (Path(image_path).name, f, "image/png")}
                data = {
                    "output_format": "markdown",
                    "max_batch_size": 16,
                    "include_confidence": True,
                    "merge_text_blocks": True
                }
                
                response = requests.post(
                    f"{self.base_url}/api/process/document",
                    files=files,
                    data=data,
                    timeout=300
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Markdown生成成功")
                
                # 保存Markdown文件
                if result.get('markdown_content'):
                    output_file = f"result_{int(time.time())}.md"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result['markdown_content'])
                    print(f"   Markdown已保存到: {output_file}")
                
                return result
            else:
                print(f"❌ Markdown生成失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Markdown生成异常: {e}")
            return None
    
    def high_precision_example(self, image_path: str):
        """高精度处理示例"""
        print(f"\n🎯 高精度处理: {image_path}")
        
        try:
            with open(image_path, "rb") as f:
                files = {"file": (Path(image_path).name, f, "image/png")}
                data = {
                    "output_format": "structured",  # 结构化输出
                    "max_batch_size": 4,           # 小批次提高精度
                    "include_confidence": True,     # 包含置信度
                    "include_coordinates": True,    # 包含坐标
                    "include_images": False,        # 不包含图像数据
                    "merge_text_blocks": False      # 不合并文本块
                }
                
                response = requests.post(
                    f"{self.base_url}/api/process/document",
                    files=files,
                    data=data,
                    timeout=300
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 高精度处理完成")
                
                # 分析置信度
                elements = result.get('elements', [])
                if elements:
                    confidences = [elem.get('confidence', 0) for elem in elements if elem.get('confidence')]
                    if confidences:
                        avg_confidence = sum(confidences) / len(confidences)
                        print(f"   平均置信度: {avg_confidence:.3f}")
                        high_conf = len([c for c in confidences if c >= 0.8])
                        print(f"   高置信度元素: {high_conf}/{len(confidences)}")
                
                return result
            else:
                print(f"❌ 高精度处理失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 高精度处理异常: {e}")
            return None


class AsyncAPIExample:
    """异步API调用示例"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def batch_process_example(self, image_paths: list):
        """批量处理示例"""
        print(f"\n📦 批量处理 {len(image_paths)} 个文档...")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # 并发处理多个文档
            tasks = []
            for image_path in image_paths:
                if Path(image_path).exists():
                    task = self.process_single_async(client, image_path)
                    tasks.append(task)
                else:
                    print(f"⚠️ 跳过不存在的文件: {image_path}")
            
            if not tasks:
                print("❌ 没有有效的文件可处理")
                return []
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            success_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"❌ {image_paths[i]} 处理失败: {result}")
                elif result:
                    success_count += 1
                    print(f"✅ {image_paths[i]} 处理成功")
            
            print(f"\n📊 批量处理完成: 成功 {success_count}/{len(tasks)}")
            return results
    
    async def process_single_async(self, client: httpx.AsyncClient, image_path: str):
        """异步处理单个文档"""
        try:
            with open(image_path, "rb") as f:
                files = {"file": (Path(image_path).name, f, "image/png")}
                data = {
                    "output_format": "json",
                    "max_batch_size": 16
                }
                
                response = await client.post(
                    f"{self.base_url}/api/process/document",
                    files=files,
                    data=data
                )
                
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ {image_path} 处理失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ {image_path} 处理异常: {e}")
            return None


def demo_curl_commands():
    """演示cURL命令"""
    print("\n💻 cURL 命令示例:")
    print("=" * 60)
    
    print("\n1. 健康检查:")
    print('curl -X GET "http://localhost:8000/health"')
    
    print("\n2. 基础文档处理:")
    print('curl -X POST "http://localhost:8000/api/process/document" \\')
    print('  -H "Content-Type: multipart/form-data" \\')
    print('  -F "file=@document.png" \\')
    print('  -F "output_format=json"')
    
    print("\n3. Markdown格式输出:")
    print('curl -X POST "http://localhost:8000/api/process/document" \\')
    print('  -H "Content-Type: multipart/form-data" \\')
    print('  -F "file=@document.png" \\')
    print('  -F "output_format=markdown" \\')
    print('  -F "max_batch_size=16"')
    
    print("\n4. 高精度处理:")
    print('curl -X POST "http://localhost:8000/api/process/document" \\')
    print('  -H "Content-Type: multipart/form-data" \\')
    print('  -F "file=@document.png" \\')
    print('  -F "output_format=structured" \\')
    print('  -F "max_batch_size=4" \\')
    print('  -F "include_confidence=true" \\')
    print('  -F "include_coordinates=true"')
    
    print("\n5. 获取性能指标:")
    print('curl -X GET "http://localhost:8000/api/metrics"')
    
    print("\n6. 获取支持的格式:")
    print('curl -X GET "http://localhost:8000/api/formats"')


async def main():
    """主函数 - 演示各种API调用"""
    print("🚀 xDAN-Vision-SmartDoc API 调用示例")
    print("=" * 60)
    
    # 初始化示例类
    simple_api = SimpleAPIExample()
    async_api = AsyncAPIExample()
    
    # 1. 健康检查
    if not simple_api.test_health():
        print("❌ 服务未启动，请先启动API服务器")
        print("   启动命令: python start_xdan_vision_server.py")
        return
    
    # 查找测试图像
    test_images = [
        "./demo/test.png",
        "./demo/test.jpg", 
        "./test.png",
        "./sample.png",
        "./document.png"
    ]
    
    available_images = [img for img in test_images if Path(img).exists()]
    
    if not available_images:
        print("\n⚠️ 未找到测试图像文件")
        print("请在以下位置放置测试图像:")
        for img in test_images:
            print(f"   {img}")
        print("\n💻 您仍然可以查看cURL命令示例:")
        demo_curl_commands()
        return
    
    test_image = available_images[0]
    print(f"\n📸 使用测试图像: {test_image}")
    
    try:
        # 2. 简单文档处理
        simple_result = simple_api.simple_document_process(test_image)
        
        # 3. Markdown输出示例
        if simple_result:
            markdown_result = simple_api.markdown_output_example(test_image)
        
        # 4. 高精度处理示例
        precision_result = simple_api.high_precision_example(test_image)
        
        # 5. 批量处理示例 (如果有多个图像)
        if len(available_images) > 1:
            batch_images = available_images[:3]  # 最多处理3个
            await async_api.batch_process_example(batch_images)
        
        # 6. 显示结果分析
        if precision_result:
            print("\n📊 结果分析:")
            elements = precision_result.get('elements', [])
            if elements:
                element_types = {}
                for elem in elements:
                    elem_type = elem.get('type', 'unknown')
                    element_types[elem_type] = element_types.get(elem_type, 0) + 1
                
                print(f"   元素类型统计:")
                for elem_type, count in element_types.items():
                    print(f"     - {elem_type}: {count}")
                
                # 显示前几个元素的文本
                print(f"\n   识别内容预览:")
                for i, elem in enumerate(elements[:3]):
                    text = elem.get('text', '').strip()
                    if text:
                        preview = text[:50] + "..." if len(text) > 50 else text
                        print(f"     {i+1}. [{elem.get('type', 'unknown')}] {preview}")
        
    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
    
    # 7. 显示cURL命令示例
    demo_curl_commands()
    
    print("\n" + "=" * 60)
    print("🎉 API调用示例演示完成!")
    print("📚 更多详情请查看: API_USAGE_GUIDE.md")
    print("🌐 API文档: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(main()) 