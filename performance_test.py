#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本 - Aegis Folder Watch
用于验证资源优化效果和性能表现
"""

import os
import sys
import time
import json
import shutil
import psutil
import threading
from datetime import datetime
from pathlib import Path
from PIL import Image
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitoring_manager import MonitoringManager, MemoryMonitor
from sanitizer_engine import ImageSanitizer


class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self):
        self.test_dir = "performance_test_data"
        self.backup_dir = "performance_test_backup"
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def setup_test_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        
        # 清理旧的测试数据
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)
            
        # 创建测试目录
        os.makedirs(self.test_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        print(f"✅ 测试环境已设置: {self.test_dir}")
    
    def generate_test_images(self, count=50, sizes=[(800, 600), (1920, 1080), (3840, 2160)]):
        """生成测试图像"""
        print(f"🖼️ 生成 {count} 个测试图像...")
        
        generated_files = []
        
        for i in range(count):
            # 随机选择尺寸
            size = sizes[i % len(sizes)]
            
            # 创建随机图像
            image_array = np.random.randint(0, 256, (size[1], size[0], 3), dtype=np.uint8)
            image = Image.fromarray(image_array)
            
            # 添加一些元数据
            from PIL.ExifTags import TAGS
            exif_dict = {
                "0th": {
                    256: size[0],  # ImageWidth
                    257: size[1],  # ImageLength
                    272: f"TestCamera_{i}",  # Make
                    306: datetime.now().strftime("%Y:%m:%d %H:%M:%S"),  # DateTime
                },
                "Exif": {
                    36867: datetime.now().strftime("%Y:%m:%d %H:%M:%S"),  # DateTimeOriginal
                    37521: f"Test image {i}",  # SubsecTime
                }
            }
            
            # 保存图像
            filename = f"test_image_{i:03d}_{size[0]}x{size[1]}.jpg"
            filepath = os.path.join(self.test_dir, filename)
            
            try:
                image.save(filepath, "JPEG", quality=85)
                generated_files.append(filepath)
            except Exception as e:
                print(f"⚠️ 生成图像失败 {filename}: {e}")
                
        print(f"✅ 成功生成 {len(generated_files)} 个测试图像")
        return generated_files
    
    def monitor_system_resources(self, duration=60, interval=1):
        """监控系统资源使用情况"""
        print(f"📊 开始监控系统资源 ({duration}秒)...")
        
        resource_data = {
            'timestamps': [],
            'cpu_percent': [],
            'memory_percent': [],
            'memory_mb': [],
            'disk_io_read': [],
            'disk_io_write': []
        }
        
        start_time = time.time()
        last_disk_io = psutil.disk_io_counters()
        
        while time.time() - start_time < duration:
            timestamp = time.time() - start_time
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 磁盘IO
            current_disk_io = psutil.disk_io_counters()
            disk_read = current_disk_io.read_bytes - last_disk_io.read_bytes
            disk_write = current_disk_io.write_bytes - last_disk_io.write_bytes
            last_disk_io = current_disk_io
            
            # 记录数据
            resource_data['timestamps'].append(timestamp)
            resource_data['cpu_percent'].append(cpu_percent)
            resource_data['memory_percent'].append(memory.percent)
            resource_data['memory_mb'].append(process_memory)
            resource_data['disk_io_read'].append(disk_read)
            resource_data['disk_io_write'].append(disk_write)
            
            time.sleep(interval)
            
        return resource_data
    
    def test_monitoring_performance(self, test_files):
        """测试监控性能"""
        print("🚀 开始监控性能测试...")
        
        # 创建监控管理器
        manager = MonitoringManager(backup_folder=self.backup_dir)
        
        # 配置监控
        config = {
            'enabled': True,
            'remove_metadata': True,
            'advanced_cleaning': True
        }
        
        # 记录开始时间和资源
        start_time = time.time()
        start_memory = psutil.virtual_memory().percent
        start_cpu = psutil.cpu_percent()
        
        # 启动资源监控线程
        resource_monitor_active = True
        resource_data = []
        
        def monitor_resources():
            while resource_monitor_active:
                resource_data.append({
                    'timestamp': time.time() - start_time,
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                    'active_threads': len([t for t in manager.processing_threads if t.is_alive()])
                })
                time.sleep(0.5)
        
        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.start()
        
        try:
            # 启动监控
            manager.start_monitoring([self.test_dir], config)
            
            # 等待处理完成
            processed_count = 0
            max_wait_time = 300  # 最多等待5分钟
            wait_start = time.time()
            
            while processed_count < len(test_files) and (time.time() - wait_start) < max_wait_time:
                time.sleep(1)
                with manager.stats_lock:
                    processed_count = manager.stats['processed']
                    
                print(f"\r📈 处理进度: {processed_count}/{len(test_files)} ({processed_count/len(test_files)*100:.1f}%)", end="")
            
            print()  # 换行
            
            # 停止监控
            manager.stop_monitoring()
            
        finally:
            resource_monitor_active = False
            monitor_thread.join()
        
        # 记录结束时间和资源
        end_time = time.time()
        end_memory = psutil.virtual_memory().percent
        end_cpu = psutil.cpu_percent()
        
        # 计算性能指标
        total_time = end_time - start_time
        processing_speed = len(test_files) / total_time if total_time > 0 else 0
        
        with manager.stats_lock:
            final_stats = manager.stats.copy()
        
        # 计算资源使用统计
        if resource_data:
            avg_cpu = sum(r['cpu_percent'] for r in resource_data) / len(resource_data)
            max_cpu = max(r['cpu_percent'] for r in resource_data)
            avg_memory = sum(r['memory_mb'] for r in resource_data) / len(resource_data)
            max_memory = max(r['memory_mb'] for r in resource_data)
            max_threads = max(r['active_threads'] for r in resource_data)
        else:
            avg_cpu = max_cpu = avg_memory = max_memory = max_threads = 0
        
        test_result = {
            'test_name': 'monitoring_performance',
            'file_count': len(test_files),
            'total_time_seconds': round(total_time, 2),
            'processing_speed_files_per_second': round(processing_speed, 2),
            'final_stats': final_stats,
            'resource_usage': {
                'avg_cpu_percent': round(avg_cpu, 2),
                'max_cpu_percent': round(max_cpu, 2),
                'avg_memory_mb': round(avg_memory, 2),
                'max_memory_mb': round(max_memory, 2),
                'max_active_threads': max_threads,
                'memory_change_percent': round(end_memory - start_memory, 2)
            },
            'thread_pool_performance': {
                'min_threads': manager.min_threads,
                'max_threads': manager.max_threads,
                'final_concurrent_threads': manager.max_concurrent_threads,
                'cpu_threshold_increase': manager.cpu_threshold_increase,
                'cpu_threshold_decrease': manager.cpu_threshold_decrease
            }
        }
        
        return test_result
    
    def test_memory_monitor(self):
        """测试内存监控器"""
        print("🧠 测试内存监控器...")
        
        # 创建内存监控器
        config = {
            'max_memory_usage_mb': 1024,
            'cleanup_threshold_mb': 512,
            'gc_interval_seconds': 5
        }
        
        memory_monitor = MemoryMonitor(config)
        
        # 记录初始内存
        initial_memory = memory_monitor.get_memory_usage_mb()
        
        # 模拟内存使用
        large_data = []
        for i in range(100):
            # 创建一些大对象
            data = np.random.rand(1000, 1000)  # 约8MB
            large_data.append(data)
            
            current_memory = memory_monitor.get_memory_usage_mb()
            
            if memory_monitor.should_cleanup():
                print(f"🧹 内存清理触发，当前内存: {current_memory:.1f}MB")
                memory_monitor.force_garbage_collection()
                break
        
        # 清理数据
        del large_data
        memory_monitor.force_garbage_collection()
        
        final_memory = memory_monitor.get_memory_usage_mb()
        
        test_result = {
            'test_name': 'memory_monitor',
            'initial_memory_mb': round(initial_memory, 2),
            'final_memory_mb': round(final_memory, 2),
            'memory_stats': memory_monitor.get_memory_stats(),
            'cleanup_triggered': final_memory < initial_memory + 100  # 允许100MB误差
        }
        
        return test_result
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🎯 开始性能测试套件...")
        self.start_time = datetime.now()
        
        try:
            # 设置测试环境
            self.setup_test_environment()
            
            # 生成测试图像
            test_files = self.generate_test_images(count=30)
            
            # 测试监控性能
            monitoring_result = self.test_monitoring_performance(test_files)
            self.results.append(monitoring_result)
            
            # 测试内存监控器
            memory_result = self.test_memory_monitor()
            self.results.append(memory_result)
            
            self.end_time = datetime.now()
            
            # 生成测试报告
            self.generate_report()
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 清理测试数据
            self.cleanup_test_environment()
    
    def generate_report(self):
        """生成测试报告"""
        print("📋 生成测试报告...")
        
        report = {
            'test_suite': 'Aegis Folder Watch Performance Test',
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_duration': str(self.end_time - self.start_time),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
                'python_version': sys.version,
                'platform': sys.platform
            },
            'test_results': self.results
        }
        
        # 保存报告到文件
        report_filename = f"performance_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        print("\n" + "="*60)
        print("📊 性能测试报告摘要")
        print("="*60)
        
        for result in self.results:
            print(f"\n🔍 测试: {result['test_name']}")
            
            if result['test_name'] == 'monitoring_performance':
                print(f"  📁 处理文件数: {result['file_count']}")
                print(f"  ⏱️ 总耗时: {result['total_time_seconds']}秒")
                print(f"  🚀 处理速度: {result['processing_speed_files_per_second']} 文件/秒")
                print(f"  ✅ 成功处理: {result['final_stats']['success']}")
                print(f"  ❌ 处理失败: {result['final_stats']['failed']}")
                print(f"  🧠 平均内存使用: {result['resource_usage']['avg_memory_mb']}MB")
                print(f"  💻 平均CPU使用: {result['resource_usage']['avg_cpu_percent']}%")
                print(f"  🔧 最大活跃线程: {result['resource_usage']['max_active_threads']}")
                
            elif result['test_name'] == 'memory_monitor':
                print(f"  🧠 初始内存: {result['initial_memory_mb']}MB")
                print(f"  🧠 最终内存: {result['final_memory_mb']}MB")
                print(f"  🧹 清理触发: {'是' if result['cleanup_triggered'] else '否'}")
        
        print(f"\n📄 详细报告已保存到: {report_filename}")
        print("="*60)
    
    def cleanup_test_environment(self):
        """清理测试环境"""
        print("🧹 清理测试环境...")
        
        try:
            if os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir)
            if os.path.exists(self.backup_dir):
                shutil.rmtree(self.backup_dir)
            print("✅ 测试环境清理完成")
        except Exception as e:
            print(f"⚠️ 清理测试环境时出错: {e}")


def main():
    """主函数"""
    print("🎯 Aegis Folder Watch 性能测试")
    print("="*50)
    
    # 检查依赖
    try:
        import psutil
        import numpy as np
        from PIL import Image
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("请安装: pip install psutil numpy pillow")
        return
    
    # 运行测试套件
    test_suite = PerformanceTestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()