#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG透明图像专用处理器
专门处理带有透明图层的PNG图像，确保透明度信息完整保留
同时移除元数据和潜在的追踪信息
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageFilter
from typing import Tuple, Optional
import struct
import zlib

class PNGTransparencyProcessor:
    """PNG透明图像专用处理器"""
    
    def __init__(self):
        self.supported_modes = ['RGBA', 'LA', 'P']
        self._palette_info = None
        
    def process_png_with_transparency(self, input_path: str, output_path: str = None, 
                                    preserve_quality: bool = True) -> bool:
        """
        处理带透明度的PNG图像
        
        Args:
            input_path: 输入图像路径
            output_path: 输出图像路径
            preserve_quality: 是否保持最高质量
            
        Returns:
            处理是否成功
        """
        try:
            if output_path is None:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_cleaned{ext}"
                
            # 加载图像
            original_image = Image.open(input_path)
            
            # 检查是否为PNG格式
            if original_image.format != 'PNG':
                print(f"警告: {input_path} 不是PNG格式")
                return False
                
            # 深度清理PNG图像
            cleaned_image = self._deep_clean_png(original_image, preserve_quality)
            
            # 保存清理后的图像
            self._save_png_with_transparency(cleaned_image, output_path, preserve_quality)
            
            print(f"PNG透明图像处理完成: {output_path}")
            return True
            
        except Exception as e:
            print(f"PNG透明图像处理失败: {str(e)}")
            return False
            
    def _deep_clean_png(self, image: Image.Image, preserve_quality: bool) -> Image.Image:
        """
        深度清理PNG图像，保持透明度完整性
        
        Args:
            image: 原始PIL图像
            preserve_quality: 是否保持质量
            
        Returns:
            清理后的PIL图像
        """
        # 保存原始信息
        original_mode = image.mode
        original_size = image.size
        
        # 提取透明度信息
        alpha_data = self._extract_alpha_channel(image)
        
        # 清理元数据
        clean_image = self._strip_all_metadata(image)
        
        # 处理图像内容，移除潜在追踪信息
        if preserve_quality:
            processed_image = self._gentle_content_cleaning(clean_image, alpha_data)
        else:
            processed_image = self._aggressive_content_cleaning(clean_image, alpha_data)
            
        # 恢复透明度
        final_image = self._restore_alpha_channel(processed_image, alpha_data, original_mode)
        
        return final_image
        
    def _extract_alpha_channel(self, image: Image.Image) -> Optional[np.ndarray]:
        """
        提取透明度通道数据
        
        Args:
            image: PIL图像
            
        Returns:
            透明度数据数组
        """
        try:
            if image.mode == 'RGBA':
                return np.array(image)[:, :, 3]
            elif image.mode == 'LA':
                return np.array(image)[:, :, 1]
            elif image.mode == 'P' and 'transparency' in image.info:
                # 处理调色板模式的透明度
                # 保存原始调色板信息
                original_palette = image.getpalette()
                transparency_index = image.info['transparency']
                
                # 转换为RGBA以提取透明度
                rgba_image = image.convert('RGBA')
                alpha_data = np.array(rgba_image)[:, :, 3]
                
                # 同时保存调色板相关信息
                self._palette_info = {
                    'palette': original_palette,
                    'transparency_index': transparency_index
                }
                
                return alpha_data
            else:
                return None
        except Exception as e:
            print(f"提取透明度通道失败: {str(e)}")
            return None
            
    def _strip_all_metadata(self, image: Image.Image) -> Image.Image:
        """
        彻底清理所有元数据
        
        Args:
            image: 原始图像
            
        Returns:
            清理元数据后的图像
        """
        # 转换为numpy数组
        img_array = np.array(image)
        
        # 创建新的干净图像，不保留任何元数据
        clean_image = Image.fromarray(img_array, mode=image.mode)
        
        # 对于P模式，需要保留调色板和透明度信息
        if image.mode == 'P':
            # 保留调色板
            if hasattr(image, 'palette') and image.palette:
                clean_image.putpalette(image.palette.getdata()[1])
            
            # 保留透明度信息
            if 'transparency' in image.info:
                clean_image.info['transparency'] = image.info['transparency']
        else:
            # 确保没有任何附加信息
            clean_image.info = {}
        
        return clean_image
        
    def _gentle_content_cleaning(self, image: Image.Image, alpha_data: Optional[np.ndarray]) -> Image.Image:
        """
        温和的内容清理，保持图像质量
        
        Args:
            image: 输入图像
            alpha_data: 透明度数据
            
        Returns:
            清理后的图像
        """
        # 对P模式进行特殊处理，尽量保持调色板
        if image.mode == 'P':
            # 对于P模式，只进行最小化的元数据清理
            return self._strip_all_metadata(image)
        
        # 转换为RGB进行处理（保留透明度信息）
        if image.mode in ['RGBA', 'LA']:
            rgb_image = image.convert('RGB')
        else:
            rgb_image = image
            
        # 轻微的噪声清理
        img_array = np.array(rgb_image)
        
        # 确保是3维数组
        if len(img_array.shape) == 2:
            # 如果是灰度图，转换为3通道
            img_array = np.stack([img_array] * 3, axis=-1)
        elif len(img_array.shape) == 3 and img_array.shape[2] == 1:
            # 如果是单通道但3维，扩展为3通道
            img_array = np.repeat(img_array, 3, axis=2)
        
        # 使用更温和的处理方式
        # 1. 轻微的高斯模糊去除噪声
        cleaned_array = cv2.GaussianBlur(img_array, (3, 3), 0.3)
        
        # 2. 非常轻微的色彩调整，只移除最低位信息
        cleaned_array = self._minimal_color_adjustment(cleaned_array)
        
        return Image.fromarray(cleaned_array, 'RGB')
        
    def _aggressive_content_cleaning(self, image: Image.Image, alpha_data: Optional[np.ndarray]) -> Image.Image:
        """
        激进的内容清理，彻底移除追踪信息
        
        Args:
            image: 输入图像
            alpha_data: 透明度数据
            
        Returns:
            清理后的图像
        """
        # 对P模式进行特殊处理，尽量保持调色板
        if image.mode == 'P':
            # 对于P模式，只进行元数据清理和轻微的调色板优化
            cleaned_image = self._strip_all_metadata(image)
            # 可以考虑轻微的调色板优化，但要保持透明度
            return cleaned_image
        
        # 转换为RGB进行处理
        if image.mode in ['RGBA', 'LA']:
            rgb_image = image.convert('RGB')
        else:
            rgb_image = image
            
        img_array = np.array(rgb_image)
        
        # 确保是3维数组
        if len(img_array.shape) == 2:
            # 如果是灰度图，转换为3通道
            img_array = np.stack([img_array] * 3, axis=-1)
        elif len(img_array.shape) == 3 and img_array.shape[2] == 1:
            # 如果是单通道但3维，扩展为3通道
            img_array = np.repeat(img_array, 3, axis=2)
        
        # 多层清理
        # 1. 高斯模糊去除细微追踪点
        blurred = cv2.GaussianBlur(img_array, (3, 3), 0.5)
        
        # 2. 中值滤波去除孤立像素
        median_filtered = cv2.medianBlur(blurred, 3)
        
        # 3. 色彩量化，移除微小色差
        quantized = self._color_quantization(median_filtered)
        
        # 4. 边缘保护的降噪
        final_cleaned = cv2.fastNlMeansDenoisingColored(quantized, None, 10, 10, 7, 21)
        
        return Image.fromarray(final_cleaned, 'RGB')
        
    def _minimal_color_adjustment(self, img_array: np.ndarray) -> np.ndarray:
        """
        最小化的色彩调整，仅移除最低位信息
        
        Args:
            img_array: 图像数组
            
        Returns:
            调整后的图像数组
        """
        # 非常轻微的色彩量化，只移除最低1位
        adjusted = img_array.copy()
        
        # 对每个颜色通道进行最小量化
        for i in range(3):
            # 只移除最低1位，保持图像质量
            adjusted[:, :, i] = (adjusted[:, :, i] // 2) * 2
            
        return adjusted
        
    def _subtle_color_adjustment(self, img_array: np.ndarray) -> np.ndarray:
        """
        微妙的色彩调整，移除隐藏信息
        
        Args:
            img_array: 图像数组
            
        Returns:
            调整后的图像数组
        """
        # 轻微的色彩量化，移除最低位的潜在信息
        adjusted = img_array.copy()
        
        # 对每个颜色通道进行轻微量化
        for i in range(3):
            # 移除最低2位，减少隐写信息的可能性
            adjusted[:, :, i] = (adjusted[:, :, i] // 4) * 4
            
        return adjusted
        
    def _color_quantization(self, img_array: np.ndarray, levels: int = 32) -> np.ndarray:
        """
        色彩量化，减少色彩层次
        
        Args:
            img_array: 图像数组
            levels: 量化级别
            
        Returns:
            量化后的图像数组
        """
        # 计算量化步长
        step = 256 // levels
        
        # 量化每个颜色通道
        quantized = (img_array // step) * step
        
        return quantized.astype(np.uint8)
        
    def _restore_alpha_channel(self, rgb_image: Image.Image, alpha_data: Optional[np.ndarray], 
                             original_mode: str) -> Image.Image:
        """
        恢复透明度通道
        
        Args:
            rgb_image: RGB图像
            alpha_data: 透明度数据
            original_mode: 原始图像模式
            
        Returns:
            恢复透明度的图像
        """
        if alpha_data is None:
            return rgb_image
            
        try:
            rgb_array = np.array(rgb_image)
            
            if original_mode == 'RGBA':
                # 合并RGB和Alpha通道
                rgba_array = np.dstack((rgb_array, alpha_data))
                return Image.fromarray(rgba_array, 'RGBA')
            elif original_mode == 'LA':
                # 转换为灰度并添加Alpha通道
                gray_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)
                la_array = np.dstack((gray_array, alpha_data))
                return Image.fromarray(la_array, 'LA')
            elif original_mode == 'P':
                # 对于调色板模式，尝试保持原始调色板
                rgba_array = np.dstack((rgb_array, alpha_data))
                rgba_image = Image.fromarray(rgba_array, 'RGBA')
                
                # 如果有保存的调色板信息，尝试恢复
                if hasattr(self, '_palette_info') and self._palette_info:
                    try:
                        # 转换为P模式并恢复调色板
                        p_image = rgba_image.convert('P', palette=Image.ADAPTIVE)
                        if self._palette_info['palette']:
                            p_image.putpalette(self._palette_info['palette'])
                        if 'transparency_index' in self._palette_info:
                            p_image.info['transparency'] = self._palette_info['transparency_index']
                        return p_image
                    except Exception as e:
                        print(f"恢复调色板失败，使用RGBA模式: {str(e)}")
                        return rgba_image
                else:
                    # 如果没有调色板信息，返回RGBA模式
                    return rgba_image
            else:
                return rgb_image
                
        except Exception as e:
            print(f"恢复透明度通道失败: {str(e)}")
            return rgb_image
            
    def _save_png_with_transparency(self, image: Image.Image, output_path: str, 
                                  preserve_quality: bool = True):
        """
        保存PNG图像，保持透明度
        
        Args:
            image: 要保存的图像
            output_path: 输出路径
            preserve_quality: 是否保持质量
        """
        save_kwargs = {
            'format': 'PNG',
            'optimize': not preserve_quality,  # 高质量模式不优化
        }
        
        # 如果是高质量模式，使用无损压缩
        if preserve_quality:
            save_kwargs['compress_level'] = 1  # 最快压缩，保持质量
        else:
            save_kwargs['compress_level'] = 9  # 最高压缩
            
        image.save(output_path, **save_kwargs)
        
    def get_transparency_info(self, image_path: str) -> dict:
        """
        获取PNG图像的透明度信息
        
        Args:
            image_path: 图像路径
            
        Returns:
            透明度信息字典
        """
        try:
            image = Image.open(image_path)
            
            info = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'has_transparency': False,
                'transparency_type': None,
                'alpha_channel_stats': None
            }
            
            # 检查透明度
            if image.mode == 'RGBA':
                alpha_channel = np.array(image)[:, :, 3]
                info['has_transparency'] = True
                info['transparency_type'] = 'RGBA'
                info['alpha_channel_stats'] = {
                    'min': int(alpha_channel.min()),
                    'max': int(alpha_channel.max()),
                    'mean': float(alpha_channel.mean()),
                    'unique_values': len(np.unique(alpha_channel))
                }
            elif image.mode == 'LA':
                alpha_channel = np.array(image)[:, :, 1]
                info['has_transparency'] = True
                info['transparency_type'] = 'LA'
                info['alpha_channel_stats'] = {
                    'min': int(alpha_channel.min()),
                    'max': int(alpha_channel.max()),
                    'mean': float(alpha_channel.mean()),
                    'unique_values': len(np.unique(alpha_channel))
                }
            elif image.mode == 'P' and 'transparency' in image.info:
                info['has_transparency'] = True
                info['transparency_type'] = 'Palette'
                info['transparency_index'] = image.info['transparency']
                
            return info
            
        except Exception as e:
            return {'error': str(e)}