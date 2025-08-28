"""
高级设置对话框 - Aegis Folder Watch
这是一个交互式工具，用于配置和调试OpenCV清理算法
"""

import sys
import json
import cv2
import numpy as np
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QSlider, QSpinBox, QPushButton, QFileDialog,
                             QGroupBox, QMessageBox, QApplication, QSplitter,
                             QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QCursor
from PIL import Image


class ClickableLabel(QLabel):
    """可点击的图像标签，用于颜色选择"""
    clicked = pyqtSignal(int, int)
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(200, 150)
        self.setStyleSheet("border: 1px solid #dee2e6;")
        self.setAlignment(Qt.AlignCenter)
        self.setText("点击加载图像...")
        self.color_picking_mode = False
        
    def mousePressEvent(self, event):
        if self.color_picking_mode and event.button() == Qt.LeftButton:
            self.clicked.emit(event.x(), event.y())
        super().mousePressEvent(event)
        
    def set_color_picking_mode(self, enabled):
        self.color_picking_mode = enabled
        if enabled:
            self.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))


class AdvancedSettingsDialog(QDialog):
    """高级设置对话框 - 用于配置OpenCV清理算法"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔬 高级清理设置")
        self.setModal(True)
        self.resize(1300, 800)  # 减少高度
        self.setMinimumSize(1100, 650)  # 减少最小尺寸
        
        # 当前加载的图像
        self.current_image = None
        self.current_image_cv = None
        
        # 设置存储
        self.settings = QSettings("AegisFolderWatch", "AdvancedSettings")
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # 右侧图像预览面板
        preview_panel = self.create_preview_panel()
        splitter.addWidget(preview_panel)
        
        # 设置分割器比例
        splitter.setSizes([450, 750])
        
        # 底部按钮面板 - 紧凑布局
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.StyledPanel)
        button_frame.setMaximumHeight(50)  # 限制高度
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(8, 5, 8, 5)  # 减少边距
        button_layout.setSpacing(8)  # 适中间距
        
        self.load_image_btn = QPushButton("📂 加载图像")
        self.load_image_btn.clicked.connect(self.load_sample_image)
        self.load_image_btn.setMinimumHeight(32)
        self.load_image_btn.setMaximumHeight(32)
        
        self.apply_preview_btn = QPushButton("🔄 预览")
        self.apply_preview_btn.clicked.connect(self.apply_and_preview)
        self.apply_preview_btn.setEnabled(False)
        self.apply_preview_btn.setMinimumHeight(32)
        self.apply_preview_btn.setMaximumHeight(32)
        
        self.save_btn = QPushButton("💾 保存")
        self.save_btn.clicked.connect(self.save_settings_and_close)
        self.save_btn.setMinimumHeight(32)
        self.save_btn.setMaximumHeight(32)
        
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setMinimumHeight(32)
        self.cancel_btn.setMaximumHeight(32)
        
        self.reset_btn = QPushButton("↩️ 重置")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        self.reset_btn.setMinimumHeight(32)
        self.reset_btn.setMaximumHeight(32)
        
        button_layout.addWidget(self.load_image_btn)
        button_layout.addWidget(self.apply_preview_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addWidget(button_frame)
        
    def create_control_panel(self):
        """创建左侧控制面板"""
        scroll_area = QScrollArea()
        scroll_widget = QFrame()
        layout = QVBoxLayout(scroll_widget)
        
        # 启用/禁用高级清理
        enable_group = QGroupBox("高级清理设置")
        enable_layout = QVBoxLayout(enable_group)
        
        self.enable_advanced = QPushButton("✅ 启用高级清理")
        self.enable_advanced.setCheckable(True)
        self.enable_advanced.setChecked(True)
        self.enable_advanced.toggled.connect(self.on_enable_toggled)
        enable_layout.addWidget(self.enable_advanced)
        
        layout.addWidget(enable_group)
        
        # 目标颜色选择
        color_group = QGroupBox("目标颜色选择")
        color_layout = QVBoxLayout(color_group)
        
        self.pick_color_btn = QPushButton("💧 从图像中选择颜色")
        self.pick_color_btn.clicked.connect(self.start_color_picking)
        self.pick_color_btn.setEnabled(False)
        color_layout.addWidget(self.pick_color_btn)
        
        layout.addWidget(color_group)
        
        # HSV阈值设置
        hsv_group = QGroupBox("HSV颜色阈值")
        hsv_layout = QGridLayout(hsv_group)
        
        # 色调范围
        hsv_layout.addWidget(QLabel("色调中心 (0-179):"), 0, 0)
        self.hue_center_slider = QSlider(Qt.Horizontal)
        self.hue_center_slider.setRange(0, 179)
        self.hue_center_slider.setValue(120)
        self.hue_center_slider.valueChanged.connect(self.on_settings_changed)
        self.hue_center_value = QLabel("120")
        hsv_layout.addWidget(self.hue_center_slider, 0, 1)
        hsv_layout.addWidget(self.hue_center_value, 0, 2)
        
        hsv_layout.addWidget(QLabel("色调容差 (0-20):"), 1, 0)
        self.hue_tolerance_slider = QSlider(Qt.Horizontal)
        self.hue_tolerance_slider.setRange(0, 20)
        self.hue_tolerance_slider.setValue(10)
        self.hue_tolerance_slider.valueChanged.connect(self.on_settings_changed)
        self.hue_tolerance_value = QLabel("10")
        hsv_layout.addWidget(self.hue_tolerance_slider, 1, 1)
        hsv_layout.addWidget(self.hue_tolerance_value, 1, 2)
        
        # 饱和度范围
        hsv_layout.addWidget(QLabel("最小饱和度 (0-255):"), 2, 0)
        self.min_saturation_slider = QSlider(Qt.Horizontal)
        self.min_saturation_slider.setRange(0, 255)
        self.min_saturation_slider.setValue(50)
        self.min_saturation_slider.valueChanged.connect(self.on_settings_changed)
        self.min_saturation_value = QLabel("50")
        hsv_layout.addWidget(self.min_saturation_slider, 2, 1)
        hsv_layout.addWidget(self.min_saturation_value, 2, 2)
        
        # 明度范围
        hsv_layout.addWidget(QLabel("最小明度 (0-255):"), 3, 0)
        self.min_value_slider = QSlider(Qt.Horizontal)
        self.min_value_slider.setRange(0, 255)
        self.min_value_slider.setValue(50)
        self.min_value_slider.valueChanged.connect(self.on_settings_changed)
        self.min_value_value = QLabel("50")
        hsv_layout.addWidget(self.min_value_slider, 3, 1)
        hsv_layout.addWidget(self.min_value_value, 3, 2)
        
        # 连接滑块值变化
        self.hue_center_slider.valueChanged.connect(lambda v: self.hue_center_value.setText(str(v)))
        self.hue_tolerance_slider.valueChanged.connect(lambda v: self.hue_tolerance_value.setText(str(v)))
        self.min_saturation_slider.valueChanged.connect(lambda v: self.min_saturation_value.setText(str(v)))
        self.min_value_slider.valueChanged.connect(lambda v: self.min_value_value.setText(str(v)))
        
        layout.addWidget(hsv_group)
        
        # 滤波参数
        filter_group = QGroupBox("滤波参数")
        filter_layout = QGridLayout(filter_group)
        
        filter_layout.addWidget(QLabel("中值滤波核大小:"), 0, 0)
        self.median_blur_spin = QSpinBox()
        self.median_blur_spin.setRange(3, 15)
        self.median_blur_spin.setSingleStep(2)
        self.median_blur_spin.setValue(5)
        self.median_blur_spin.valueChanged.connect(self.on_settings_changed)
        filter_layout.addWidget(self.median_blur_spin, 0, 1)
        
        filter_layout.addWidget(QLabel("形态学操作迭代次数:"), 1, 0)
        self.morphology_iterations_spin = QSpinBox()
        self.morphology_iterations_spin.setRange(1, 5)
        self.morphology_iterations_spin.setValue(2)
        self.morphology_iterations_spin.valueChanged.connect(self.on_settings_changed)
        filter_layout.addWidget(self.morphology_iterations_spin, 1, 1)
        
        layout.addWidget(filter_group)
        
        layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(350)
        scroll_area.setMaximumWidth(500)
        
        return scroll_area
        
    def create_preview_panel(self):
        """创建右侧图像预览面板"""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        
        # 图像预览区域
        preview_layout = QHBoxLayout()
        
        # 原始图像
        original_group = QGroupBox("原始图像")
        original_layout = QVBoxLayout(original_group)
        self.original_label = ClickableLabel()
        self.original_label.clicked.connect(self.on_image_clicked)
        original_layout.addWidget(self.original_label)
        preview_layout.addWidget(original_group)
        
        # 检测掩码
        mask_group = QGroupBox("检测掩码")
        mask_layout = QVBoxLayout(mask_group)
        self.mask_label = QLabel()
        self.mask_label.setMinimumSize(200, 150)
        self.mask_label.setStyleSheet("border: 1px solid gray;")
        self.mask_label.setAlignment(Qt.AlignCenter)
        self.mask_label.setText("等待处理...")
        mask_layout.addWidget(self.mask_label)
        preview_layout.addWidget(mask_group)
        
        # 清理结果
        result_group = QGroupBox("清理结果")
        result_layout = QVBoxLayout(result_group)
        self.result_label = QLabel()
        self.result_label.setMinimumSize(200, 150)
        self.result_label.setStyleSheet("border: 1px solid gray;")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setText("等待处理...")
        result_layout.addWidget(self.result_label)
        preview_layout.addWidget(result_group)
        
        layout.addLayout(preview_layout)
        
        return panel
        
    def on_enable_toggled(self, checked):
        """启用/禁用切换"""
        if checked:
            self.enable_advanced.setText("✅ 启用高级清理")
        else:
            self.enable_advanced.setText("❌ 禁用高级清理")
            
    def on_settings_changed(self):
        """设置变化时的处理"""
        if self.current_image is not None:
            # 自动预览（可选）
            pass
            
    def load_sample_image(self):
        """加载测试图像"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择测试图像", "", 
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.webp *.heif *.heic)"
        )
        
        if file_path:
            try:
                # 使用PIL加载图像
                pil_image = Image.open(file_path)
                self.current_image = pil_image.copy()
                
                # 转换为OpenCV格式
                self.current_image_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                
                # 显示原始图像
                self.display_image(self.original_label, pil_image)
                
                # 启用相关按钮
                self.apply_preview_btn.setEnabled(True)
                self.pick_color_btn.setEnabled(True)
                
                # 清空其他预览
                self.mask_label.clear()
                self.mask_label.setText("点击'应用并预览'")
                self.result_label.clear()
                self.result_label.setText("点击'应用并预览'")
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法加载图像: {str(e)}")
                
    def display_image(self, label, pil_image, max_size=(300, 200)):
        """在标签中显示PIL图像"""
        # 转换为QPixmap
        if pil_image.mode == 'RGBA':
            pil_image = pil_image.convert('RGB')
            
        # 调整大小保持比例
        pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 转换为QImage
        w, h = pil_image.size
        qimage = QImage(pil_image.tobytes(), w, h, QImage.Format_RGB888)
        
        # 设置到标签
        pixmap = QPixmap.fromImage(qimage)
        label.setPixmap(pixmap)
        
    def start_color_picking(self):
        """开始颜色选择模式"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先加载测试图像")
            return
            
        self.original_label.set_color_picking_mode(True)
        self.pick_color_btn.setText("点击图像中的目标颜色...")
        
    def on_image_clicked(self, x, y):
        """处理图像点击事件"""
        if self.current_image_cv is None:
            return
            
        # 获取点击位置的颜色
        try:
            # 计算实际图像坐标
            pixmap = self.original_label.pixmap()
            if pixmap is None:
                return
                
            # 计算缩放比例
            label_size = self.original_label.size()
            pixmap_size = pixmap.size()
            
            scale_x = self.current_image_cv.shape[1] / pixmap_size.width()
            scale_y = self.current_image_cv.shape[0] / pixmap_size.height()
            
            # 计算偏移（居中显示）
            offset_x = (label_size.width() - pixmap_size.width()) // 2
            offset_y = (label_size.height() - pixmap_size.height()) // 2
            
            # 调整点击坐标
            img_x = int((x - offset_x) * scale_x)
            img_y = int((y - offset_y) * scale_y)
            
            # 确保坐标在图像范围内
            img_x = max(0, min(img_x, self.current_image_cv.shape[1] - 1))
            img_y = max(0, min(img_y, self.current_image_cv.shape[0] - 1))
            
            # 获取BGR颜色
            bgr_color = self.current_image_cv[img_y, img_x]
            
            # 转换为HSV
            hsv_color = cv2.cvtColor(np.uint8([[bgr_color]]), cv2.COLOR_BGR2HSV)[0][0]
            
            # 更新滑块值
            self.hue_center_slider.setValue(int(hsv_color[0]))
            self.min_saturation_slider.setValue(max(50, int(hsv_color[1]) - 30))
            self.min_value_slider.setValue(max(50, int(hsv_color[2]) - 30))
            
            # 退出颜色选择模式
            self.original_label.set_color_picking_mode(False)
            self.pick_color_btn.setText("💧 从图像中选择颜色")
            
            # 自动应用预览
            self.apply_and_preview()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"颜色选择失败: {str(e)}")
            
    def apply_and_preview(self):
        """应用设置并预览结果"""
        if self.current_image_cv is None:
            QMessageBox.warning(self, "警告", "请先加载测试图像")
            return
            
        try:
            # 获取当前设置
            config = self.get_current_config()
            
            # 应用OpenCV算法
            mask, result = self.apply_opencv_algorithm(self.current_image_cv, config)
            
            # 显示掩码
            mask_pil = Image.fromarray(mask)
            self.display_image(self.mask_label, mask_pil)
            
            # 显示结果
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            result_pil = Image.fromarray(result_rgb)
            self.display_image(self.result_label, result_pil)
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"预览失败: {str(e)}")
            
    def apply_opencv_algorithm(self, image, config):
        """应用OpenCV清理算法"""
        # 转换为HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 创建颜色掩码
        hue_center = config['hue_center']
        hue_tolerance = config['hue_tolerance']
        min_saturation = config['min_saturation']
        min_value = config['min_value']
        
        # HSV范围
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
        
        # 创建掩码
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        
        # 中值滤波
        kernel_size = config['median_blur_kernel']
        if kernel_size > 1:
            mask = cv2.medianBlur(mask, kernel_size)
            
        # 形态学操作
        iterations = config['morphology_iterations']
        if iterations > 0:
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=iterations)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=iterations)
            
        # 修复图像（简单的高斯模糊替代inpainting）
        result = image.copy()
        blurred = cv2.GaussianBlur(image, (15, 15), 0)
        result[mask > 0] = blurred[mask > 0]
        
        return mask, result
        
    def get_current_config(self):
        """获取当前配置"""
        return {
            'enabled': self.enable_advanced.isChecked(),
            'hue_center': self.hue_center_slider.value(),
            'hue_tolerance': self.hue_tolerance_slider.value(),
            'min_saturation': self.min_saturation_slider.value(),
            'min_value': self.min_value_slider.value(),
            'median_blur_kernel': self.median_blur_spin.value(),
            'morphology_iterations': self.morphology_iterations_spin.value()
        }
        
    def load_settings(self, config=None):
        """加载设置"""
        # 默认值
        defaults = {
            'enabled': True,
            'hue_center': 120,
            'hue_tolerance': 10,
            'min_saturation': 50,
            'min_value': 50,
            'median_blur_kernel': 5,
            'morphology_iterations': 2
        }
        
        # 使用传入的配置或默认值
        settings = config if config else defaults
        
        # 应用设置到UI
        self.enable_advanced.setChecked(bool(settings.get('enabled', defaults['enabled'])))
        self.hue_center_slider.setValue(int(settings.get('hue_center', defaults['hue_center'])))
        self.hue_tolerance_slider.setValue(int(settings.get('hue_tolerance', defaults['hue_tolerance'])))
        self.min_saturation_slider.setValue(int(settings.get('min_saturation', defaults['min_saturation'])))
        self.min_value_slider.setValue(int(settings.get('min_value', defaults['min_value'])))
        self.median_blur_spin.setValue(int(settings.get('median_blur_kernel', defaults['median_blur_kernel'])))
        self.morphology_iterations_spin.setValue(int(settings.get('morphology_iterations', defaults['morphology_iterations'])))
                
    def reset_to_defaults(self):
        """重置为默认值"""
        self.enable_advanced.setChecked(True)
        self.hue_center_slider.setValue(120)
        self.hue_tolerance_slider.setValue(10)
        self.min_saturation_slider.setValue(50)
        self.min_value_slider.setValue(50)
        self.median_blur_spin.setValue(5)
        self.morphology_iterations_spin.setValue(2)
        
    def save_settings_and_close(self):
        """保存设置并关闭"""
        # 不再在这里保存，由主窗口统一管理
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = AdvancedSettingsDialog()
    dialog.show()
    sys.exit(app.exec_())