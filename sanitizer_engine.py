"""
图像清理引擎 - Image Privacy Guardian
负责执行图像的元数据清理和高级OpenCV清理
支持 JPEG/JPG、PNG、BMP、TIFF/TIF、WebP、HEIF/HEIC 格式
"""

import os
import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS

# 导入HEIF支持
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False


class ImageSanitizer:
    """图像清理器 - 执行元数据清理和高级清理"""
    
    def __init__(self):
        # 基础支持的格式
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
        
        # 如果HEIF库可用，添加HEIF/HEIC支持
        if HEIF_AVAILABLE:
            self.supported_formats.update({'.heif', '.heic'})
        
    def clean_image(self, input_path: str, output_path: str = None, advanced_config: dict = None) -> bool:
        """
        清理图像文件
        
        Args:
            input_path: 输入图像路径
            output_path: 输出图像路径（如果为None，则直接替换原文件）
            advanced_config: 高级配置参数
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 验证输入文件
            if not os.path.exists(input_path):
                print(f"错误：输入文件不存在 - {input_path}")
                return False
            
            # 检查文件格式
            if not self._is_supported_format(input_path):
                print(f"错误：不支持的文件格式 - {input_path}")
                return False
            
            # 如果没有指定输出路径，直接替换原文件
            if output_path is None:
                output_path = input_path
            
            # 创建输出目录
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 创建临时文件路径
            temp_path = input_path + ".aegis_temp"
            
            # 第一步：使用Pillow进行元数据清理
            cleaned_image = self._strip_metadata_with_pillow(input_path)
            
            # 第二步：检查是否启用高级清理
            if advanced_config and advanced_config.get('enabled', False):
                cleaned_image = self._remove_tracking_dots(cleaned_image, advanced_config)
            
            # 保存到临时文件
            self._save_cleaned_image(cleaned_image, temp_path)
            
            # 替换原文件
            if temp_path != output_path:
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(temp_path, output_path)
            
            print(f"✅ 图像清理完成: {os.path.basename(output_path)}")
            return True
            
        except Exception as e:
            print(f"❌ 图像清理失败: {str(e)}")
            # 清理临时文件
            temp_file = input_path + ".aegis_temp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False
            
    def _is_supported_format(self, file_path: str) -> bool:
        """检查是否为支持的图像格式"""
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.supported_formats
        
    def _strip_metadata_with_pillow(self, input_path: str) -> Image.Image:
        """
        使用Pillow清理图像元数据
        
        Args:
            input_path: 输入图像路径
            
        Returns:
            清理后的PIL图像对象
        """
        try:
            # 打开图像
            with Image.open(input_path) as img:
                # 获取原始图像数据（不包含EXIF等元数据）
                data = list(img.getdata())
                
                # 创建新的图像对象（不包含元数据）
                clean_img = Image.new(img.mode, img.size)
                clean_img.putdata(data)
                
                # 如果原图有透明度，保持透明度
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    clean_img = clean_img.convert('RGBA')
                else:
                    clean_img = clean_img.convert('RGB')
                    
                return clean_img
                
        except Exception as e:
            raise Exception(f"Pillow元数据清理失败: {str(e)}")
            
    def _remove_tracking_dots(self, pil_image: Image.Image, advanced_config: dict) -> Image.Image:
        """
        使用OpenCV移除跟踪点
        
        Args:
            pil_image: PIL图像对象
            advanced_config: 高级清理配置
            
        Returns:
            清理后的PIL图像对象
        """
        try:
            # 转换PIL图像为OpenCV格式
            if pil_image.mode == 'RGBA':
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGR)
            else:
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                
            # 应用OpenCV清理算法
            cleaned_cv = self._apply_opencv_cleaning(cv_image, advanced_config)
            
            # 转换回PIL格式
            if pil_image.mode == 'RGBA':
                # 保持透明度通道
                cleaned_rgb = cv2.cvtColor(cleaned_cv, cv2.COLOR_BGR2RGB)
                alpha_channel = np.array(pil_image)[:, :, 3]
                cleaned_rgba = np.dstack((cleaned_rgb, alpha_channel))
                return Image.fromarray(cleaned_rgba, 'RGBA')
            else:
                cleaned_rgb = cv2.cvtColor(cleaned_cv, cv2.COLOR_BGR2RGB)
                return Image.fromarray(cleaned_rgb, 'RGB')
                
        except Exception as e:
            print(f"OpenCV清理警告: {str(e)}")
            # 如果OpenCV清理失败，返回原图像
            return pil_image
            
    def _apply_opencv_cleaning(self, cv_image: np.ndarray, config: dict) -> np.ndarray:
        """
        应用OpenCV清理算法
        
        Args:
            cv_image: OpenCV图像数组
            config: 配置参数
            
        Returns:
            清理后的OpenCV图像数组
        """
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        
        # 获取配置参数
        hue_center = config.get('hue_center', 120)
        hue_tolerance = config.get('hue_tolerance', 10)
        min_saturation = config.get('min_saturation', 50)
        min_value = config.get('min_value', 50)
        median_blur_kernel = config.get('median_blur_kernel', 5)
        morphology_iterations = config.get('morphology_iterations', 2)
        
        # 创建HSV颜色范围
        lower_hsv = np.array([
            max(0, hue_center - hue_tolerance),
            min_saturation,
            min_value
        ])
        upper_hsv = np.array([
            min(179, hue_center + hue_tolerance),
            255,
            255
        ])
        
        # 创建颜色掩码
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        
        # 应用中值滤波去噪
        if median_blur_kernel > 1:
            # 确保核大小为奇数
            if median_blur_kernel % 2 == 0:
                median_blur_kernel += 1
            mask = cv2.medianBlur(mask, median_blur_kernel)
            
        # 形态学操作清理掩码
        if morphology_iterations > 0:
            kernel = np.ones((3, 3), np.uint8)
            # 闭运算：填充小洞
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=morphology_iterations)
            # 开运算：移除小噪点
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=morphology_iterations)
            
        # 修复检测到的区域
        result = self._inpaint_detected_regions(cv_image, mask)
        
        return result
        
    def _inpaint_detected_regions(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        修复检测到的区域
        
        Args:
            image: 原始图像
            mask: 检测掩码
            
        Returns:
            修复后的图像
        """
        try:
            # 尝试使用OpenCV的inpainting功能
            if hasattr(cv2, 'INPAINT_TELEA'):
                return cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)
            else:
                # 如果没有inpaint功能，使用高斯模糊替代
                return self._gaussian_blur_replacement(image, mask)
                
        except Exception:
            # 备用方案：高斯模糊
            return self._gaussian_blur_replacement(image, mask)
            
    def _gaussian_blur_replacement(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        使用高斯模糊作为inpainting的替代方案
        
        Args:
            image: 原始图像
            mask: 检测掩码
            
        Returns:
            处理后的图像
        """
        result = image.copy()
        
        # 创建模糊版本
        blurred = cv2.GaussianBlur(image, (15, 15), 0)
        
        # 在掩码区域应用模糊
        result[mask > 0] = blurred[mask > 0]
        
        return result
        
    def _save_cleaned_image(self, pil_image: Image.Image, output_path: str):
        """
        保存清理后的图像
        
        Args:
            pil_image: 清理后的PIL图像
            output_path: 输出路径
        """
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            # 根据文件扩展名确定保存格式
            _, ext = os.path.splitext(output_path.lower())
            
            if ext in ['.jpg', '.jpeg']:
                # JPEG不支持透明度，转换为RGB
                if pil_image.mode in ('RGBA', 'LA'):
                    # 创建白色背景
                    background = Image.new('RGB', pil_image.size, (255, 255, 255))
                    if pil_image.mode == 'RGBA':
                        background.paste(pil_image, mask=pil_image.split()[-1])
                    else:
                        background.paste(pil_image)
                    pil_image = background
                pil_image.save(output_path, 'JPEG', quality=95, optimize=True)
                
            elif ext == '.png':
                pil_image.save(output_path, 'PNG', optimize=True)
                
            elif ext in ['.bmp']:
                if pil_image.mode in ('RGBA', 'LA'):
                    pil_image = pil_image.convert('RGB')
                pil_image.save(output_path, 'BMP')
                
            elif ext in ['.tiff', '.tif']:
                pil_image.save(output_path, 'TIFF')
                
            elif ext == '.webp':
                # WebP支持透明度和高质量压缩
                pil_image.save(output_path, 'WEBP', quality=95, method=6)
                
            elif ext in ['.heif', '.heic']:
                # HEIF/HEIC格式支持（需要pillow-heif）
                if HEIF_AVAILABLE:
                    # HEIF不支持透明度，转换为RGB
                    if pil_image.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', pil_image.size, (255, 255, 255))
                        if pil_image.mode == 'RGBA':
                            background.paste(pil_image, mask=pil_image.split()[-1])
                        else:
                            background.paste(pil_image)
                        pil_image = background
                    pil_image.save(output_path, 'HEIF', quality=95)
                else:
                    # 如果HEIF不可用，保存为JPEG
                    if pil_image.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', pil_image.size, (255, 255, 255))
                        if pil_image.mode == 'RGBA':
                            background.paste(pil_image, mask=pil_image.split()[-1])
                        else:
                            background.paste(pil_image)
                        pil_image = background
                    jpeg_path = output_path.rsplit('.', 1)[0] + '.jpg'
                    pil_image.save(jpeg_path, 'JPEG', quality=95, optimize=True)
                    
            else:
                # 默认保存为PNG
                pil_image.save(output_path, 'PNG')
                
        except Exception as e:
            raise Exception(f"保存图像失败: {str(e)}")
            
    def get_image_info(self, image_path: str) -> dict:
        """
        获取图像信息（用于调试）
        
        Args:
            image_path: 图像路径
            
        Returns:
            图像信息字典
        """
        try:
            with Image.open(image_path) as img:
                info = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'has_exif': bool(img.getexif()),
                    'has_transparency': 'transparency' in img.info
                }
                
                # 获取EXIF信息
                exif_data = img.getexif()
                if exif_data:
                    info['exif_tags'] = []
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        info['exif_tags'].append(f"{tag}: {value}")
                        
                return info
                
        except Exception as e:
            return {'error': str(e)}