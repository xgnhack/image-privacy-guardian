#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
估算JPEG图像的质量参数
"""

import os
from PIL import Image
import numpy as np

def estimate_jpeg_quality(image_path):
    """
    根据量化表估算JPEG质量
    """
    try:
        with Image.open(image_path) as img:
            if not hasattr(img, 'quantization') or not img.quantization:
                return 85  # 默认质量
                
            # 获取亮度量化表
            luma_qtable = img.quantization.get(0, [])
            if not luma_qtable:
                return 85
                
            # 计算量化表的平均值
            avg_q = np.mean(luma_qtable)
            
            # 根据量化表平均值估算质量
            # 这是一个经验公式
            if avg_q <= 1.5:
                quality = 98
            elif avg_q <= 2.0:
                quality = 95
            elif avg_q <= 3.0:
                quality = 90
            elif avg_q <= 5.0:
                quality = 85
            elif avg_q <= 8.0:
                quality = 80
            elif avg_q <= 12.0:
                quality = 75
            else:
                quality = 70
                
            print(f"文件: {os.path.basename(image_path)}")
            print(f"量化表平均值: {avg_q:.2f}")
            print(f"估算质量: {quality}")
            print("-" * 30)
            
            return quality
            
    except Exception as e:
        print(f"估算质量失败: {e}")
        return 85

def main():
    jpg_dir = "jpg"
    
    if not os.path.exists(jpg_dir):
        print(f"目录不存在: {jpg_dir}")
        return
        
    jpg_files = [f for f in os.listdir(jpg_dir) if f.lower().endswith(('.jpg', '.jpeg'))]
    
    qualities = []
    for jpg_file in jpg_files[:5]:  # 分析前5个文件
        jpg_path = os.path.join(jpg_dir, jpg_file)
        quality = estimate_jpeg_quality(jpg_path)
        qualities.append(quality)
    
    if qualities:
        avg_quality = np.mean(qualities)
        print(f"平均估算质量: {avg_quality:.1f}")
        print(f"建议使用质量: {int(avg_quality)}")

if __name__ == "__main__":
    main()