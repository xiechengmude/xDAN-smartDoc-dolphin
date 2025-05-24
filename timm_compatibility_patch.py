"""
兼容性补丁：为 timm 1.0.15 添加 ImageNetInfo 支持
解决 "cannot import name 'ImageNetInfo' from 'timm.data'" 错误

使用方法：
在导入 transformers 之前先导入此补丁：
import timm_compatibility_patch
"""
import sys


# 创建虚拟的 ImageNetInfo 类
class ImageNetInfo:
    """兼容性类，用于替代已移除的 timm.data.ImageNetInfo"""
    
    def __init__(self, num_classes=1000):
        self.num_classes = num_classes
        self.label_names = [f"class_{i}" for i in range(num_classes)]
    
    @property
    def synsets(self):
        return self.label_names


def infer_imagenet_subset(*args, **kwargs):
    """兼容性函数，用于替代已移除的 infer_imagenet_subset"""
    return ImageNetInfo()


# 动态注入到 timm.data 模块
try:
    import timm.data as timm_data
    
    # 检查并添加缺失的属性
    if not hasattr(timm_data, 'ImageNetInfo'):
        timm_data.ImageNetInfo = ImageNetInfo
        print("✅ 已为 timm.data 添加 ImageNetInfo 兼容性支持")
    
    if not hasattr(timm_data, 'infer_imagenet_subset'):
        timm_data.infer_imagenet_subset = infer_imagenet_subset
        print("✅ 已为 timm.data 添加 infer_imagenet_subset 兼容性支持")
        
except ImportError as e:
    print(f"⚠️ timm 未安装或导入失败: {e}")
except Exception as e:
    print(f"⚠️ 补丁应用失败: {e}") 