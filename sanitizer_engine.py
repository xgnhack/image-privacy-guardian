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
from png_transparency_processor import PNGTransparencyProcessor

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
        
        # 初始化PNG透明度处理器
        self.png_processor = PNGTransparencyProcessor()
        
    def clean_image(self, input_path: str, output_path: str = None, 
                   remove_metadata: bool = True, 
                   advanced_cleaning: bool = False,
                   advanced_config: dict = None) -> bool:
        """
        清理图像文件
        
        Args:
            input_path: 输入图像路径
            output_path: 输出图像路径（如果为None，则直接替换原文件）
            remove_metadata: 是否移除元数据
            advanced_cleaning: 是否进行高级清理（移除跟踪点等）
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
            
            # 打开图像
            with Image.open(input_path) as img:
                # 获取原始格式信息
                original_format = img.format
                file_ext = os.path.splitext(output_path)[1].lower()
                
                # 根据文件类型选择处理流程
                if file_ext == '.png' and img.mode in ('RGBA', 'LA', 'P'):
                     # PNG透明图像使用专门的处理器
                     print("🔍 检测到PNG透明图像，使用专门的透明度保护处理...")
                     # PNG处理器需要文件路径，不是PIL图像对象
                     temp_path = input_path  # 使用输入路径
                     success = self.png_processor.process_png_with_transparency(
                         temp_path, 
                         output_path,
                         preserve_quality=not advanced_cleaning
                     )
                     if success:
                         # PNG处理器已经保存了文件，直接返回
                         print(f"✅ 图像清理完成: {os.path.basename(output_path)}")
                         return True
                     else:
                         # 如果PNG处理器失败，使用标准流程
                         cleaned_img = img
                elif file_ext in ['.jpg', '.jpeg']:
                    # JPG图像使用最保守的处理策略，只清理元数据，不进行像素处理
                    print("📸 处理JPG图像，使用质量保护策略...")
                    if remove_metadata:
                        cleaned_img = self._remove_metadata_only(img)
                    else:
                        cleaned_img = img
                    # 对于JPG，完全跳过高级清理以避免质量损失
                else:
                    # 其他格式使用标准流程
                    cleaned_img = img
                    
                    # 移除元数据
                    if remove_metadata:
                        cleaned_img = self._remove_metadata(cleaned_img)
                    
                    # 高级清理（移除跟踪点等）
                    if advanced_cleaning:
                        cleaned_img = self._remove_tracking_dots(cleaned_img, advanced_config or {})
                
                # 保存清理后的图像
                self._save_cleaned_image(cleaned_img, output_path, original_format)
            
            print(f"✅ 图像清理完成: {os.path.basename(output_path)}")
            return True
            
        except Exception as e:
            print(f"❌ 图像清理失败: {str(e)}")
            return False
            
    def _is_supported_format(self, file_path: str) -> bool:
        """检查是否为支持的图像格式"""
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.supported_formats
        
    def _is_png_with_transparency(self, file_path: str) -> bool:
        """
        检查是否为带透明度的PNG图像
        
        Args:
            file_path: 图像文件路径
            
        Returns:
            bool: 是否为带透明度的PNG图像
        """
        try:
            # 首先检查是否为PNG文件
            if not file_path.lower().endswith('.png'):
                return False
                
            # 打开图像检查透明度
            with Image.open(file_path) as img:
                # 检查图像模式
                if img.mode in ['RGBA', 'LA']:
                    return True
                elif img.mode == 'P' and 'transparency' in img.info:
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"检查PNG透明度时出错: {str(e)}")
            return False
        
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
                # 保存原始模式和调色板信息
                original_mode = img.mode
                original_palette = None
                transparency_info = None
                
                # 保存调色板信息（对于P模式图像）
                if img.mode == 'P':
                    original_palette = img.getpalette()
                    if 'transparency' in img.info:
                        transparency_info = img.info['transparency']
                
                # 获取原始图像数据（不包含EXIF等元数据）
                data = list(img.getdata())
                
                # 创建新的图像对象（不包含元数据，但保持原始模式）
                clean_img = Image.new(original_mode, img.size)
                clean_img.putdata(data)
                
                # 恢复调色板信息（对于P模式图像）
                if original_mode == 'P' and original_palette:
                    clean_img.putpalette(original_palette)
                    if transparency_info is not None:
                        clean_img.info['transparency'] = transparency_info
                
                # 只有在必要时才进行模式转换（主要是为了后续OpenCV处理）
                # 对于PNG等支持多种模式的格式，尽量保持原始模式
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
            # 保存原始模式和相关信息
            original_mode = pil_image.mode
            original_palette = None
            transparency_info = None
            
            # 保存调色板信息（对于P模式图像）
            if original_mode == 'P':
                original_palette = pil_image.getpalette()
                if 'transparency' in pil_image.info:
                    transparency_info = pil_image.info['transparency']
            
            # 为OpenCV处理准备图像
            working_image = pil_image
            
            # 将特殊模式转换为OpenCV可处理的格式
            if original_mode == 'L':  # 灰度图
                working_image = pil_image.convert('RGB')
            elif original_mode == 'P':  # 调色板模式
                if 'transparency' in pil_image.info:
                    working_image = pil_image.convert('RGBA')
                else:
                    working_image = pil_image.convert('RGB')
            elif original_mode == 'LA':  # 灰度+透明度
                working_image = pil_image.convert('RGBA')
            
            # 转换PIL图像为OpenCV格式
            if working_image.mode == 'RGBA':
                cv_image = cv2.cvtColor(np.array(working_image), cv2.COLOR_RGBA2BGR)
                has_alpha = True
            else:
                cv_image = cv2.cvtColor(np.array(working_image), cv2.COLOR_RGB2BGR)
                has_alpha = False
                
            # 应用OpenCV清理算法
            cleaned_cv = self._apply_opencv_cleaning(cv_image, advanced_config)
            
            # 转换回PIL格式
            if has_alpha:
                # 保持透明度通道
                cleaned_rgb = cv2.cvtColor(cleaned_cv, cv2.COLOR_BGR2RGB)
                alpha_channel = np.array(working_image)[:, :, 3]
                cleaned_rgba = np.dstack((cleaned_rgb, alpha_channel))
                result_image = Image.fromarray(cleaned_rgba, 'RGBA')
            else:
                cleaned_rgb = cv2.cvtColor(cleaned_cv, cv2.COLOR_BGR2RGB)
                result_image = Image.fromarray(cleaned_rgb, 'RGB')
            
            # 恢复原始模式
            if original_mode == 'L':  # 转换回灰度
                result_image = result_image.convert('L')
            elif original_mode == 'P':  # 转换回调色板模式
                if original_palette:
                    result_image = result_image.convert('P', palette=Image.ADAPTIVE)
                    result_image.putpalette(original_palette)
                    if transparency_info is not None:
                        result_image.info['transparency'] = transparency_info
                else:
                    result_image = result_image.convert('P')
            elif original_mode == 'LA':  # 转换回灰度+透明度
                result_image = result_image.convert('LA')
            
            return result_image
                
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
        
    def _clean_jpg_image(self, pil_image: Image.Image, remove_metadata: bool = True, advanced_cleaning: bool = False) -> Image.Image:
        """
        专门用于JPG图像的轻量级清理策略
        
        Args:
            pil_image: PIL图像对象
            remove_metadata: 是否移除元数据
            advanced_cleaning: 是否进行高级清理（对JPG采用保守策略）
            
        Returns:
            清理后的PIL图像对象
        """
        try:
            # 对于JPG，采用最保守的策略，直接返回原图
            # 元数据清理将在保存时通过不传递info参数来实现
            return pil_image
                
        except Exception as e:
            print(f"JPG清理警告: {str(e)}")
            return pil_image
            
    def _remove_metadata_only(self, pil_image: Image.Image) -> Image.Image:
        """
        仅移除元数据，保持像素数据完全不变
        
        Args:
            pil_image: PIL图像对象
            
        Returns:
            移除元数据后的图像
        """
        try:
            # 获取像素数据
            data = list(pil_image.getdata())
            
            # 创建新的图像对象（不包含元数据）
            clean_img = Image.new(pil_image.mode, pil_image.size)
            clean_img.putdata(data)
            
            return clean_img
            
        except Exception as e:
            raise Exception(f"元数据清理失败: {str(e)}")
    
    def _remove_metadata(self, image: Image.Image) -> Image.Image:
        """
        移除图像元数据
        """
        return self._remove_metadata_only(image)
            
    def _light_jpg_cleaning(self, pil_image: Image.Image) -> Image.Image:
        """
        对JPG图像进行轻量级清理，最小化质量损失
        
        Args:
            pil_image: PIL图像对象
            
        Returns:
            轻微清理后的图像
        """
        try:
            # 转换为numpy数组进行轻微处理
            img_array = np.array(pil_image)
            
            # 只进行非常轻微的中值滤波（去除单像素噪点）
            from scipy import ndimage
            if len(img_array.shape) == 3:  # 彩色图像
                for i in range(img_array.shape[2]):
                    img_array[:, :, i] = ndimage.median_filter(img_array[:, :, i], size=3)
            else:  # 灰度图像
                img_array = ndimage.median_filter(img_array, size=3)
            
            # 转换回PIL图像
            return Image.fromarray(img_array)
            
        except Exception as e:
            print(f"轻量级清理失败，返回原图像: {str(e)}")
            return pil_image
        
    def _save_cleaned_image(self, pil_image: Image.Image, output_path: str, original_format: str = None):
        """
        保存清理后的图像
        
        Args:
            pil_image: 清理后的PIL图像
            output_path: 输出路径
            original_format: 原始图像格式
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
                
                # 对于JPG，使用最高质量保存以避免重压缩损失
                if original_format == 'JPEG':
                    # 原始就是JPEG，使用最高质量保存以最小化重压缩损失
                    quality = 98  # 使用接近无损的质量
                    optimize = False  # 不进行优化以保持原始特性
                    progressive = False
                    
                    save_kwargs = {
                        'quality': quality,
                        'optimize': optimize,
                        'progressive': progressive,
                        'subsampling': 0  # 禁用色度子采样以保持最高质量
                    }
                        
                else:
                    # 从其他格式转换为JPEG
                    quality = 95
                    save_kwargs = {
                        'quality': quality,
                        'optimize': False,  # 改为False以保持质量
                        'progressive': False,
                        'subsampling': 0  # 禁用色度子采样
                    }
                    
                pil_image.save(output_path, 'JPEG', **save_kwargs)
                
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