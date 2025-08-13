#!/usr/bin/env python3
# 虚拟热敏打印机 - 完整的ESC/POS仿真器
# 支持中文、格式化输出、多任务队列

import socket
import datetime
import threading
import os
import time
import queue
from collections import OrderedDict

class ESCPOSParser:
    """ESC/POS命令解析器"""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """重置打印机状态"""
        self.bold = False
        self.underline = False
        self.font_size = 0  # 0=正常, 1=2倍高, 2=2倍宽, 3=2倍高宽
        self.align = 0  # 0=左, 1=中, 2=右
        
    def parse(self, data):
        """解析ESC/POS数据流"""
        commands = []
        i = 0
        
        while i < len(data):
            # ESC @ - 初始化打印机
            if i + 1 < len(data) and data[i:i+2] == b'\x1B\x40':
                commands.append(('INIT', None))
                self.reset()
                i += 2
                
            # GS V - 切纸
            elif i + 1 < len(data) and data[i:i+2] == b'\x1D\x56':
                commands.append(('CUT', None))
                i += 3 if i + 2 < len(data) else 2
                
            # ESC E - 粗体
            elif i + 2 < len(data) and data[i:i+2] == b'\x1B\x45':
                self.bold = bool(data[i+2])
                commands.append(('BOLD', self.bold))
                i += 3
                
            # ESC ! - 设置打印模式
            elif i + 2 < len(data) and data[i:i+2] == b'\x1B\x21':
                mode = data[i+2]
                commands.append(('PRINT_MODE', mode))
                i += 3
                
            # FS ! - 设置汉字打印模式
            elif i + 2 < len(data) and data[i:i+2] == b'\x1C\x21':
                mode = data[i+2]
                commands.append(('CJK_MODE', mode))
                i += 3
                
            # GS ! - 字体大小
            elif i + 2 < len(data) and data[i:i+2] == b'\x1D\x21':
                size = data[i+2]
                self.font_size = size
                commands.append(('SIZE', size))
                i += 3
                
            # ESC a - 对齐方式
            elif i + 2 < len(data) and data[i:i+2] == b'\x1B\x61':
                align = data[i+2]
                self.align = align
                commands.append(('ALIGN', align))
                i += 3
                
            # GS a - 自动状态返回
            elif i + 2 < len(data) and data[i:i+2] == b'\x1D\x61':
                commands.append(('AUTO_STATUS', data[i+2]))
                i += 3
                
            # GS B - 反白打印
            elif i + 2 < len(data) and data[i:i+2] == b'\x1D\x42':
                reverse = bool(data[i+2])
                commands.append(('REVERSE', reverse))
                i += 3
                
            # ESC J - 打印并进纸
            elif i + 2 < len(data) and data[i:i+2] == b'\x1B\x4A':
                feed = data[i+2]
                commands.append(('FEED', feed))
                i += 3
                
            # ESC d - 打印并进纸n行
            elif i + 2 < len(data) and data[i:i+2] == b'\x1B\x64':
                lines = data[i+2]
                commands.append(('FEED_LINES', lines))
                i += 3
                
            # ESC B - 设置垂直制表位
            elif i + 1 < len(data) and data[i:i+2] == b'\x1B\x42':
                i += 2
                vtab_positions = []
                # 读取参数直到遇到NUL或下一个ESC命令
                while i < len(data):
                    if data[i] == 0x00:  # NUL结束符
                        i += 1
                        break
                    elif data[i] == 0x1B or data[i] == 0x1D or data[i] == 0x10:  # 下一个命令开始
                        break
                    else:
                        vtab_positions.append(data[i])
                        i += 1
                commands.append(('VTAB', vtab_positions))
                
            # GS r - 传输状态
            elif i + 2 < len(data) and data[i:i+2] == b'\x1D\x72':
                status_type = data[i+2]
                commands.append(('TRANSMIT_STATUS', status_type))
                i += 3
                
            # DLE EOT - 状态查询
            elif i + 2 < len(data) and data[i:i+2] == b'\x10\x04':
                commands.append(('STATUS', data[i+2]))
                i += 3
                
            # GS v 0 - 光栅位图（图像）
            elif i + 3 < len(data) and data[i:i+3] == b'\x1D\x76\x30':
                # 跳过图像数据
                if i + 7 < len(data):
                    width_l = data[i+4]
                    width_h = data[i+5]
                    height_l = data[i+6]
                    height_h = data[i+7]
                    width = width_l + width_h * 256
                    height = height_l + height_h * 256
                    image_size = width * height
                    commands.append(('IMAGE', f'{width}x{height}'))
                    i += 8 + image_size
                else:
                    i += 3
                    
            # 换行符
            elif data[i] == 0x0A:
                commands.append(('LF', None))
                i += 1
                
            # 其他控制字符
            elif data[i] < 0x20:
                i += 1
                
            # 文本数据
            else:
                # 提取连续的文本（包括中文高位字节）
                text_start = i
                while i < len(data):
                    # 如果是控制字符（小于0x20），检查是否是命令开始
                    if data[i] < 0x20:
                        # 检查是否是已知的命令序列
                        if i + 1 < len(data):
                            if data[i:i+2] in [b'\x1B\x40', b'\x1D\x56', b'\x1B\x45', 
                                               b'\x1D\x21', b'\x1B\x61', b'\x10\x04',
                                               b'\x1D\x76', b'\x1D\x61', b'\x1D\x42',
                                               b'\x1C\x21', b'\x1B\x21', b'\x1B\x4A',
                                               b'\x1B\x64', b'\x1D\x48', b'\x1D\x6B',
                                               b'\x1B\x42', b'\x1D\x72']:  # 添加ESC B和GS r
                                break
                        # 单字节控制命令
                        if data[i] in [0x0A, 0x0D, 0x09]:  # LF, CR, TAB
                            break
                    i += 1
                
                if i > text_start:
                    text_data = data[text_start:i]
                    # 尝试解码中文
                    text = self.decode_text(text_data)
                    if text and text.strip():  # 只添加非空文本
                        commands.append(('TEXT', text))
                        
        return commands
    
    def decode_text(self, data):
        """解码文本，支持中文"""
        # 尝试不同的编码
        for encoding in ['gbk', 'gb2312', 'gb18030', 'utf-8']:
            try:
                text = data.decode(encoding)
                # 过滤掉不可见字符
                text = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
                return text
            except:
                continue
        # 如果都失败，返回ASCII
        return data.decode('ascii', errors='ignore')


class ReceiptRenderer:
    """收据渲染器"""
    
    def __init__(self, width=42):
        self.width = width
        self.reset()
        
    def reset(self):
        """重置渲染器状态"""
        self.lines = []
        self.current_line = ""
        self.bold = False
        self.size = 0
        self.align = 0
        self.reverse = False
        
    def render(self, commands):
        """渲染命令为可视化收据"""
        self.reset()
        
        for cmd, value in commands:
            if cmd == 'INIT':
                # 初始化时先输出当前内容
                if self.current_line:
                    self.new_line()
                
            elif cmd == 'TEXT':
                self.add_text(value)
                
            elif cmd == 'LF':
                self.new_line()
                
            elif cmd == 'BOLD':
                self.bold = value
                
            elif cmd == 'SIZE':
                self.size = value
                
            elif cmd == 'ALIGN':
                self.align = value
                
            elif cmd == 'REVERSE':
                self.reverse = value
                
            elif cmd == 'FEED_LINES':
                for _ in range(value):
                    self.new_line()
                    
            elif cmd == 'CUT':
                self.new_line()
                self.lines.append("✂" + "─" * (self.width - 1))
                
            elif cmd == 'IMAGE':
                self.new_line()
                self.lines.append(f"[图像 {value}]")
                
        # 完成最后一行
        if self.current_line:
            self.new_line()
            
        return self.format_receipt()
    
    def add_text(self, text):
        """添加文本到当前行"""
        self.current_line += text
        
    def new_line(self):
        """换行"""
        # 应用对齐
        line = self.current_line
        if self.align == 1:  # 居中
            line = line.center(self.width)
        elif self.align == 2:  # 右对齐
            line = line.rjust(self.width)
        else:  # 左对齐
            line = line.ljust(self.width)
            
        # 应用格式（只有有内容时才应用）
        if line.strip():
            if self.reverse:
                # 反白显示用█包围
                line = f"█{line.strip()}█"
                
            if self.bold:
                line = f"**{line.strip()}**"
                
            if self.size & 0x11:  # 双倍高宽
                line = f"[大] {line}"
            elif self.size & 0x01:  # 双倍宽
                line = f"[宽] {line}"
        
        self.lines.append(line)
        self.current_line = ""
    
    def format_receipt(self):
        """格式化收据输出"""
        output = []
        output.append("╔" + "═" * self.width + "╗")
        
        for line in self.lines:
            # 确保每行正确的宽度
            if len(line) > self.width:
                # 分割长行
                for i in range(0, len(line), self.width):
                    segment = line[i:i+self.width]
                    output.append("║" + segment.ljust(self.width) + "║")
            else:
                output.append("║" + line[:self.width].ljust(self.width) + "║")
                
        output.append("╚" + "═" * self.width + "╝")
        return '\n'.join(output)


class PlainTextRenderer:
    """纯文本渲染器 - 用于数据提取，去除所有格式标记"""
    
    def __init__(self, width=42):
        self.width = width
        self.reset()
        
    def reset(self):
        """重置渲染器状态"""
        self.lines = []
        self.current_line = ""
        self.align = 0  # 0=左, 1=中, 2=右
        
    def render(self, commands):
        """渲染命令为纯文本收据（无格式标记）"""
        self.reset()
        
        for cmd, value in commands:
            if cmd == 'INIT':
                # 初始化时先输出当前内容
                if self.current_line:
                    self.new_line()
                    
            elif cmd == 'TEXT':
                # 过滤掉纯分隔符文本
                if not (set(value) <= set('-=_')):
                    self.add_text(value)
                
            elif cmd == 'LF':
                self.new_line()
                
            elif cmd == 'ALIGN':
                self.align = value
                
            elif cmd == 'FEED_LINES':
                for _ in range(value):
                    self.new_line()
                    
            elif cmd == 'CUT':
                self.new_line()
                # 不添加分隔线，只添加空行
                self.lines.append("")
                
            # 忽略所有格式相关命令：SIZE, BOLD, REVERSE, IMAGE等
                
        # 完成最后一行
        if self.current_line:
            self.new_line()
            
        return self.format_receipt()
    
    def add_text(self, text):
        """添加文本到当前行"""
        self.current_line += text
        
    def new_line(self):
        """换行"""
        line = self.current_line
        
        # 应用对齐（使用空格）
        if self.align == 1:  # 居中
            padding = (self.width - len(line)) // 2
            line = ' ' * padding + line
        elif self.align == 2:  # 右对齐
            line = line.rjust(self.width)
        # 左对齐不需要处理
        
        self.lines.append(line)
        self.current_line = ""
    
    def format_receipt(self):
        """格式化纯文本收据输出"""
        if not self.lines:
            return ""
            
        output = []
        
        # 添加内容（不添加边框）
        for line in self.lines:
            # 跳过由分隔符生成的行
            if line.startswith('---') or line.startswith('==='):
                continue
                
            # 确保不超过宽度
            if len(line) > self.width:
                # 分割长行
                for i in range(0, len(line), self.width):
                    segment = line[i:i+self.width]
                    output.append(segment)
            else:
                output.append(line)
                
        return '\n'.join(output)


class VirtualPrinter:
    """虚拟打印机主类"""
    
    def __init__(self):
        self.parser = ESCPOSParser()
        self.renderer = ReceiptRenderer()
        self.plain_renderer = PlainTextRenderer()  # 添加纯文本渲染器
        self.print_queue = queue.Queue()
        self.connection_count = 0
        self.print_count = 0
        self.session_start = datetime.datetime.now()
        
    def start_server(self):
        """启动打印机服务器"""
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        host = '0.0.0.0'
        port = 9100
        server_sock.bind((host, port))
        server_sock.listen(5)
        
        print("="*60)
        print("🖨️  虚拟热敏打印机已启动")
        print("="*60)
        print(f"📍 监听地址: {host}:{port}")
        print(f"📁 输出目录: output/")
        print(f"⏰ 启动时间: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print("\n功能特性：")
        print("• 完整ESC/POS命令解析")
        print("• 中文支持 (GBK/GB2312)")
        print("• 格式化收据显示")
        print("• 多任务队列管理")
        print("• 自动保存到output文件夹")
        print("\n" + "="*60)
        print("⏰ 等待打印任务...\n")
        
        # 启动队列处理线程
        queue_thread = threading.Thread(target=self.process_queue)
        queue_thread.daemon = True
        queue_thread.start()
        
        try:
            while True:
                client_sock, client_addr = server_sock.accept()
                self.connection_count += 1
                
                # 创建线程处理连接
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_sock, client_addr, self.connection_count)
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\n" + "="*60)
            print("📊 会话统计：")
            print(f"• 总连接数: {self.connection_count}")
            print(f"• 打印任务: {self.print_count}")
            print(f"• 运行时长: {(datetime.datetime.now() - self.session_start).seconds}秒")
            print("="*60)
            print("正在关闭服务...")
        finally:
            server_sock.close()
            print("服务已关闭")
    
    def handle_client(self, client_sock, client_addr, conn_num):
        """处理客户端连接"""
        # 静默处理连接，不显示每个连接
        
        session_data = []
        last_data_time = time.time()
        idle_timeout = 30.0  # 增加到30秒，给POS机更多时间
        connection_closed_by_peer = False
        is_initialization = False
        
        try:
            client_sock.settimeout(1.0)  # 增加超时时间
            
            while True:
                try:
                    data = client_sock.recv(1024)
                    if not data:
                        # 检查是否真的断开
                        if time.time() - last_data_time > idle_timeout:
                            break
                        continue
                    
                    last_data_time = time.time()
                    session_data.append(data)
                    
                    # 检查是否是初始化序列
                    if b'\x1b\x21' in data or b'\x1c\x21' in data or b'\x1d\x21' in data:
                        is_initialization = True
                    
                    # 智能响应
                    response = self.get_response(data, is_initialization)
                    if response:
                        client_sock.send(response)
                        # 静默发送响应，不显示详细信息
                        
                except socket.timeout:
                    # 超时不立即断开，检查空闲时间
                    if time.time() - last_data_time > idle_timeout:
                        break
                    continue
                except ConnectionResetError:
                    # POS机主动断开连接（这是正常的）
                    connection_closed_by_peer = True
                    break
                    
        except ConnectionResetError:
            # POS机主动断开连接（这是正常的）
            connection_closed_by_peer = True
        except Exception as e:
            if "Connection reset by peer" not in str(e):
                print(f"❌ 错误: {e}")
        finally:
            client_sock.close()
            
            # 处理累积的数据
            if session_data:
                complete_data = b''.join(session_data)
                
                # 静默处理，不显示连接细节
                    
                # 检查是否包含实际打印内容
                has_text = False
                has_cut = b'\x1D\x56' in complete_data
                has_init = b'\x1B\x40' in complete_data
                
                # 如果有初始化或切纸命令，通常是真实打印
                if (len(complete_data) > 50) or has_cut or has_init:
                    has_text = True
                    
                if has_text:
                    # 静默加入队列，不显示中间状态
                    self.print_queue.put({
                        'data': complete_data,
                        'address': client_addr,
                        'time': datetime.datetime.now()
                    })
                # 静默处理状态查询，不输出任何信息
    
    def get_response(self, data, is_initialization=False):
        """生成响应"""
        # 分析收到的命令
        i = 0
        responses = []
        has_status_query = False
        
        while i < len(data):
            # DLE EOT状态查询
            if i + 2 < len(data) and data[i:i+2] == b'\x10\x04':
                cmd_type = data[i+2]
                has_status_query = True
                if cmd_type == 1:
                    responses.append(b'\x16')  # 打印机在线
                elif cmd_type == 2:
                    responses.append(b'\x12')  # 纸张状态正常
                elif cmd_type == 3:
                    responses.append(b'\x12')  # 无错误
                elif cmd_type == 4:
                    responses.append(b'\x12')  # 有纸
                else:
                    responses.append(b'\x16')
                i += 3
            else:
                # 静默处理其他命令，不输出日志
                i += 1
        
        # 只在第一次状态查询时显示简单日志
        if has_status_query and len(data) <= 20:
            # 这是纯状态查询，不显示详细信息
            pass
        
        # 如果有状态查询，返回响应
        if responses:
            return b''.join(responses)
        
        # 对于初始化命令，始终返回ACK
        if is_initialization:
            return b'\x06'  # ACK
            
        # 其他数据
        if len(data) > 0:
            return b'\x06'  # ACK
            
        return None
    
    def process_queue(self):
        """处理打印队列"""
        while True:
            try:
                job = self.print_queue.get(timeout=1)
                self.print_count += 1
                
                print(f"\n{'='*60}")
                print(f"📄 打印任务 #{self.print_count}")
                print(f"📱 来源: {job['address'][0]}")
                print(f"⏰ 时间: {job['time'].strftime('%H:%M:%S')}")
                print(f"📦 大小: {len(job['data'])} bytes")
                print("="*60)
                
                # 解析ESC/POS命令
                commands = self.parser.parse(job['data'])
                
                # 渲染收据（调试版，带格式标记）
                receipt_debug = self.renderer.render(commands)
                
                # 渲染纯文本版（用于数据提取）
                receipt_plain = self.plain_renderer.render(commands)
                
                # 只在控制台显示纯文本版
                print("\n📄 纯文本输出：")
                print("-" * 40)
                print(receipt_plain)
                print("-" * 40)
                
                # 保存到文件
                timestamp = job['time'].strftime("%Y%m%d_%H%M%S")
                
                # 保存调试版收据（带格式标记）
                debug_file = f"output/receipt_debug_{timestamp}_{self.print_count}.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(receipt_debug)
                    f.write(f"\n\n来源: {job['address'][0]}\n")
                    f.write(f"时间: {job['time']}\n")
                print(f"💾 调试版: {debug_file}")
                
                # 保存纯文本版（用于解析）
                plain_file = f"output/receipt_plain_{timestamp}_{self.print_count}.txt"
                with open(plain_file, 'w', encoding='utf-8') as f:
                    f.write(receipt_plain)
                    f.write(f"\n\n来源: {job['address'][0]}\n")
                    f.write(f"时间: {job['time']}\n")
                print(f"📄 纯文本: {plain_file}")
                
                # 保存原始数据（用于调试）
                raw_file = f"output/raw_{timestamp}_{self.print_count}.bin"
                with open(raw_file, 'wb') as f:
                    f.write(job['data'])
                
                print("="*60)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"处理打印任务时出错: {e}")


if __name__ == "__main__":
    print("🖨️ 虚拟热敏打印机 v2.0")
    print("-" * 40)
    
    # 确保output目录存在
    os.makedirs("output", exist_ok=True)
    
    printer = VirtualPrinter()
    printer.start_server()