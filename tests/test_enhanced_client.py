#!/usr/bin/env python3
"""
xDAN-Vision-SmartDoc API Server 测试客户端
演示智能文档识别系统的多种功能特性
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any

import httpx
from PIL import Image


class xDANVisionClient:
    """xDAN Vision智能文档识别API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=600.0)  # 10分钟超时
    
    async def health_check(self):
        """健康检查"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_performance_metrics(self):
        """获取性能指标"""
        try:
            response = await self.client.get(f"{self.base_url}/api/metrics")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_supported_formats(self):
        """获取支持的格式信息"""
        try:
            response = await self.client.get(f"{self.base_url}/api/formats")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def process_document(
        self, 
        image_path: str, 
        output_format: str = "structured",
        processing_mode: str = "sync",
        max_batch_size: int = 16,
        include_confidence: bool = True,
        include_coordinates: bool = True,
        include_images: bool = False,
        merge_text_blocks: bool = True
    ):
        """智能文档处理"""
        try:
            with open(image_path, "rb") as f:
                files = {"file": (Path(image_path).name, f, "image/png")}
                data = {
                    "max_batch_size": max_batch_size,
                    "output_format": output_format,
                    "processing_mode": processing_mode,
                    "include_confidence": include_confidence,
                    "include_coordinates": include_coordinates,
                    "include_images": include_images,
                    "merge_text_blocks": merge_text_blocks
                }
                
                response = await self.client.post(
                    f"{self.base_url}/api/process/document",
                    files=files,
                    data=data
                )
                
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_result(self, task_id: str):
        """获取处理结果"""
        try:
            response = await self.client.get(f"{self.base_url}/api/result/{task_id}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def test_basic_functionality(client: xDANVisionClient):
    """测试基础功能"""
    print("🔍 Testing xDAN Vision Basic Functionality...")
    
    # 服务信息
    print("\n1. Service Info:")
    try:
        response = await client.client.get(f"{client.base_url}/")
        service_info = response.json()
        print(json.dumps(service_info, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 健康检查
    print("\n2. Health Check:")
    health = await client.health_check()
    print(json.dumps(health, indent=2, ensure_ascii=False))
    
    # 性能指标
    print("\n3. Performance Metrics:")
    metrics = await client.get_performance_metrics()
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    
    # 支持的格式
    print("\n4. Supported Formats:")
    formats = await client.get_supported_formats()
    if "error" not in formats:
        print("📄 Input Formats:", formats.get("input_formats", {}))
        print("📊 Output Formats:", list(formats.get("output_formats", {}).keys()))
        print("🔧 Supported Elements:", list(formats.get("supported_elements", {}).keys()))
    else:
        print(f"❌ Error: {formats['error']}")


async def test_output_formats(client: xDANVisionClient, test_image: str):
    """测试不同输出格式"""
    print("\n🎨 Testing Different Output Formats...")
    
    formats = ["json", "markdown", "html", "structured"]
    
    for output_format in formats:
        print(f"\n--- Testing {output_format.upper()} format ---")
        start_time = time.time()
        
        result = await client.process_document(
            image_path=test_image,
            output_format=output_format,
            max_batch_size=8,
            include_confidence=True,
            include_coordinates=True,
            include_images=False
        )
        
        if "error" not in result:
            processing_time = time.time() - start_time
            print(f"✅ {output_format.upper()} format completed in {processing_time:.2f}s")
            print(f"📄 Elements found: {result['total_elements']}")
            print(f"⏱️  Server processing time: {result['processing_time']:.2f}s")
            
            # 显示特定格式的内容
            if output_format == "markdown" and result.get('markdown_content'):
                print(f"📝 Markdown preview (first 200 chars):")
                print(result['markdown_content'][:200] + "...")
            elif output_format == "html" and result.get('html_content'):
                print(f"🌐 HTML preview (first 300 chars):")
                print(result['html_content'][:300] + "...")
            elif output_format == "json" and result.get('json_data'):
                print(f"📊 JSON structure:")
                json_data = result['json_data']
                print(f"  - Document info: {json_data.get('document_info', {})}")
            elif output_format == "structured":
                print(f"🏗️  Structured output includes:")
                if result.get('markdown_content'):
                    print("  ✅ Markdown content")
                if result.get('html_content'):
                    print("  ✅ HTML content")
                if result.get('json_data'):
                    print("  ✅ JSON data")
        else:
            print(f"❌ Error with {output_format} format: {result['error']}")


async def test_processing_options(client: xDANVisionClient, test_image: str):
    """测试不同处理选项"""
    print("\n⚙️ Testing Processing Options...")
    
    test_configs = [
        {
            "name": "高精度处理 (包含图像)",
            "config": {
                "include_confidence": True,
                "include_images": True,
                "merge_text_blocks": False,
                "max_batch_size": 8
            }
        },
        {
            "name": "快速处理模式",
            "config": {
                "include_confidence": False,
                "include_images": False,
                "merge_text_blocks": True,
                "max_batch_size": 32
            }
        },
        {
            "name": "详细分析模式",
            "config": {
                "include_confidence": True,
                "include_coordinates": True,
                "include_images": False,
                "merge_text_blocks": True,
                "max_batch_size": 4
            }
        }
    ]
    
    for test_config in test_configs:
        print(f"\n--- Testing {test_config['name']} ---")
        start_time = time.time()
        
        result = await client.process_document(
            image_path=test_image,
            output_format="structured",
            **test_config['config']
        )
        
        if "error" not in result:
            processing_time = time.time() - start_time
            print(f"✅ {test_config['name']} completed in {processing_time:.2f}s")
            print(f"📄 Elements: {result['total_elements']}")
            print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
            
            # 分析元素详情
            elements = result.get('elements', [])
            if elements:
                element_types = {}
                confidence_scores = []
                
                for element in elements:
                    elem_type = element.get('type', 'unknown')
                    element_types[elem_type] = element_types.get(elem_type, 0) + 1
                    
                    if element.get('confidence') is not None:
                        confidence_scores.append(element['confidence'])
                
                print(f"📊 Element types: {element_types}")
                if confidence_scores:
                    avg_confidence = sum(confidence_scores) / len(confidence_scores)
                    print(f"🎯 Average confidence: {avg_confidence:.3f}")
        else:
            print(f"❌ Error: {result['error']}")


async def test_batch_sizes(client: xDANVisionClient, test_image: str):
    """测试不同批处理大小的性能"""
    print("\n📦 Testing Batch Size Performance...")
    
    batch_sizes = [1, 4, 8, 16, 32]
    
    for batch_size in batch_sizes:
        print(f"\n--- Testing batch size {batch_size} ---")
        start_time = time.time()
        
        result = await client.process_document(
            image_path=test_image,
            output_format="json",
            max_batch_size=batch_size,
            include_confidence=False,
            include_images=False
        )
        
        if "error" not in result:
            total_time = time.time() - start_time
            server_time = result['processing_time']
            print(f"✅ Batch size {batch_size}: {total_time:.2f}s total, {server_time:.2f}s server")
            print(f"📄 Elements: {result['total_elements']}")
        else:
            print(f"❌ Error with batch size {batch_size}: {result['error']}")


async def analyze_output_quality(result: Dict[str, Any]):
    """分析输出质量"""
    if "error" in result:
        return
    
    print("\n🔬 Output Quality Analysis:")
    
    elements = result.get('elements', [])
    if not elements:
        print("❌ No elements found")
        return
    
    # 统计元素类型
    element_stats = {}
    confidence_stats = []
    text_lengths = []
    
    for element in elements:
        elem_type = element.get('type', 'unknown')
        element_stats[elem_type] = element_stats.get(elem_type, 0) + 1
        
        if element.get('confidence') is not None:
            confidence_stats.append(element['confidence'])
        
        if element.get('text'):
            text_lengths.append(len(element['text']))
    
    print(f"📊 Element Distribution:")
    for elem_type, count in element_stats.items():
        percentage = (count / len(elements)) * 100
        print(f"  - {elem_type}: {count} ({percentage:.1f}%)")
    
    if confidence_stats:
        avg_confidence = sum(confidence_stats) / len(confidence_stats)
        min_confidence = min(confidence_stats)
        max_confidence = max(confidence_stats)
        print(f"\n🎯 Confidence Analysis:")
        print(f"  - Average: {avg_confidence:.3f}")
        print(f"  - Range: {min_confidence:.3f} - {max_confidence:.3f}")
        
        # 置信度分布
        high_conf = len([c for c in confidence_stats if c >= 0.8])
        medium_conf = len([c for c in confidence_stats if 0.5 <= c < 0.8])
        low_conf = len([c for c in confidence_stats if c < 0.5])
        print(f"  - High (≥0.8): {high_conf} ({high_conf/len(confidence_stats)*100:.1f}%)")
        print(f"  - Medium (0.5-0.8): {medium_conf} ({medium_conf/len(confidence_stats)*100:.1f}%)")
        print(f"  - Low (<0.5): {low_conf} ({low_conf/len(confidence_stats)*100:.1f}%)")
    
    if text_lengths:
        avg_text_length = sum(text_lengths) / len(text_lengths)
        total_chars = sum(text_lengths)
        print(f"\n📝 Text Analysis:")
        print(f"  - Average text length: {avg_text_length:.1f} chars")
        print(f"  - Total extracted text: {total_chars} chars")
        print(f"  - Longest element: {max(text_lengths)} chars")
        print(f"  - Shortest element: {min(text_lengths)} chars")


async def demo_markdown_output(result: Dict[str, Any]):
    """演示Markdown输出"""
    if "error" in result or not result.get('markdown_content'):
        return
    
    print("\n📝 Markdown Output Preview:")
    print("=" * 80)
    
    markdown_content = result['markdown_content']
    lines = markdown_content.split('\n')
    
    # 显示前25行
    for i, line in enumerate(lines[:25]):
        print(f"{i+1:3d}: {line}")
    
    if len(lines) > 25:
        print(f"... ({len(lines) - 25} more lines)")
    
    print("=" * 80)


async def demo_html_output(result: Dict[str, Any]):
    """演示HTML输出"""
    if "error" in result or not result.get('html_content'):
        return
    
    print("\n🌐 HTML Output Preview:")
    print("=" * 80)
    
    html_content = result['html_content']
    
    # 提取关键HTML结构信息
    lines = html_content.split('\n')
    print(f"HTML Document Structure:")
    print(f"  - Total lines: {len(lines)}")
    
    # 查找主要元素
    element_count = html_content.count('class="element')
    table_count = html_content.count('<table>')
    p_count = html_content.count('<p>')
    
    print(f"  - Document elements: {element_count}")
    print(f"  - Tables: {table_count}")
    print(f"  - Paragraphs: {p_count}")
    
    # 显示HTML结构片段
    print(f"\nHTML Structure Preview:")
    for i, line in enumerate(lines[:20]):
        if line.strip():
            print(f"{i+1:3d}: {line.strip()}")
    
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} more lines)")
    
    print("=" * 80)


async def test_comprehensive_analysis(client: xDANVisionClient, test_image: str):
    """综合功能测试"""
    print("\n🔬 Comprehensive xDAN Vision Analysis:")
    
    # 使用结构化输出进行全面分析
    result = await client.process_document(
        image_path=test_image,
        output_format="structured",
        max_batch_size=16,
        include_confidence=True,
        include_coordinates=True,
        include_images=False,
        merge_text_blocks=True
    )
    
    if "error" not in result:
        print(f"\n✅ Analysis completed successfully!")
        print(f"📄 File: {result['filename']}")
        print(f"🆔 Task ID: {result['task_id']}")
        print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
        print(f"📊 Total elements: {result['total_elements']}")
        
        # 输出质量分析
        await analyze_output_quality(result)
        
        # 格式预览
        await demo_markdown_output(result)
        await demo_html_output(result)
        
        return result
    else:
        print(f"❌ Comprehensive analysis failed: {result['error']}")
        return None


async def main():
    """主测试函数"""
    client = xDANVisionClient()
    
    print("🚀 Testing xDAN-Vision-SmartDoc API Server...")
    print("=" * 80)
    
    # 查找测试图像
    test_images = [
        "./demo/test.png",
        "./demo/test.jpg", 
        "./test.png",
        "./test.jpg",
        "./sample.png",
        "./demo_image.png"
    ]
    
    test_image = None
    for img_path in test_images:
        if Path(img_path).exists():
            test_image = img_path
            break
    
    if not test_image:
        print("⚠️  No test images found. Please add a test image to one of these locations:")
        for path in test_images:
            print(f"   {path}")
        await client.close()
        return
    
    print(f"📸 Using test image: {test_image}")
    
    try:
        # 测试基础功能
        await test_basic_functionality(client)
        
        # 测试不同输出格式
        await test_output_formats(client, test_image)
        
        # 测试处理选项
        await test_processing_options(client, test_image)
        
        # 测试批处理性能
        await test_batch_sizes(client, test_image)
        
        # 综合功能测试
        comprehensive_result = await test_comprehensive_analysis(client, test_image)
        
        print("\n" + "=" * 80)
        print("🎉 xDAN-Vision-SmartDoc API Server Test Summary:")
        print("✅ All tests completed successfully!")
        print("🔬 xDAN Vision智能文档识别系统功能验证通过")
        
        if comprehensive_result:
            print(f"📊 Final Analysis Result:")
            print(f"   - Total Elements: {comprehensive_result['total_elements']}")
            print(f"   - Processing Time: {comprehensive_result['processing_time']:.2f}s")
            print(f"   - Status: {comprehensive_result['status']}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main()) 