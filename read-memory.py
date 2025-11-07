import ctypes
from ctypes import wintypes
import psutil
import struct
import time

class MemoryReader:
    def __init__(self):
        self.process_handle = None
        self.pid = None
        self.process_name = None
        
    def find_process_by_name(self, process_name):
        """Encontra processo pelo nome"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    self.pid = proc.info['pid']
                    self.process_name = process_name
                    print(f"✅ Processo encontrado: {process_name} (PID: {self.pid})")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print(f"❌ Processo '{process_name}' não encontrado!")
        return False
    
    def find_process_by_pid(self, pid):
        """Encontra processo pelo PID"""
        try:
            proc = psutil.Process(pid)
            self.pid = pid
            self.process_name = proc.name()
            print(f"✅ Processo encontrado: {self.process_name} (PID: {pid})")
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print(f"❌ Processo com PID {pid} não encontrado ou sem permissão!")
            return False
    
    def open_process(self):
        """Abre handle do processo para leitura"""
        if not self.pid:
            print("❌ Nenhum processo selecionado!")
            return False
            
        # Constantes do Windows
        PROCESS_VM_READ = 0x0010
        PROCESS_QUERY_INFORMATION = 0x0400
        
        self.process_handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
            False,
            self.pid
        )
        
        if not self.process_handle:
            error_code = ctypes.windll.kernel32.GetLastError()
            print(f"❌ Falha ao abrir processo! Código de erro: {error_code}")
            print("💡 Dica: Execute como administrador ou verifique se o processo existe")
            return False
            
        print(f"🔓 Handle do processo aberto com sucesso!")
        return True
    
    def read_memory(self, address, size):
        """Lê dados brutos da memória"""
        if not self.process_handle:
            print("❌ Processo não foi aberto!")
            return None
            
        buffer = (ctypes.c_byte * size)()
        bytes_read = ctypes.c_size_t()
        
        success = ctypes.windll.kernel32.ReadProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(bytes_read)
        )
        
        if success and bytes_read.value == size:
            return bytes(buffer)
        else:
            print(f"❌ Falha ao ler memória no endereço 0x{address:08X}")
            return None
    
    def read_int8(self, address):
        """Lê um byte (8 bits) com sinal"""
        data = self.read_memory(address, 1)
        if data:
            return struct.unpack('b', data)[0]
        return None
    
    def read_uint8(self, address):
        """Lê um byte (8 bits) sem sinal"""
        data = self.read_memory(address, 1)
        if data:
            return struct.unpack('B', data)[0]
        return None
    
    def read_int16(self, address):
        """Lê um inteiro de 16 bits com sinal"""
        data = self.read_memory(address, 2)
        if data:
            return struct.unpack('<h', data)[0]  # little-endian
        return None
    
    def read_uint16(self, address):
        """Lê um inteiro de 16 bits sem sinal"""
        data = self.read_memory(address, 2)
        if data:
            return struct.unpack('<H', data)[0]
        return None
    
    def read_int32(self, address):
        """Lê um inteiro de 32 bits com sinal"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('<i', data)[0]
        return None
    
    def read_uint32(self, address):
        """Lê um inteiro de 32 bits sem sinal"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('<I', data)[0]
        return None
    
    def read_int64(self, address):
        """Lê um inteiro de 64 bits com sinal"""
        data = self.read_memory(address, 8)
        if data:
            return struct.unpack('<q', data)[0]
        return None
    
    def read_uint64(self, address):
        """Lê um inteiro de 64 bits sem sinal"""
        data = self.read_memory(address, 8)
        if data:
            return struct.unpack('<Q', data)[0]
        return None
    
    def read_float(self, address):
        """Lê um float de 32 bits"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('<f', data)[0]
        return None
    
    def read_double(self, address):
        """Lê um double de 64 bits"""
        data = self.read_memory(address, 8)
        if data:
            return struct.unpack('<d', data)[0]
        return None
    
    def read_string(self, address, length, encoding='utf-8'):
        """Lê uma string de tamanho fixo"""
        data = self.read_memory(address, length)
        if data:
            try:
                # Remove null terminators
                string_data = data.split(b'\x00')[0]
                return string_data.decode(encoding, errors='ignore')
            except UnicodeDecodeError:
                return data.hex()  # Retorna em hex se não conseguir decodificar
        return None
    
    def read_pointer(self, address):
        """Lê um ponteiro (32 ou 64 bits dependendo da arquitetura)"""
        # Verificar se é processo 64-bit
        import platform
        if platform.machine().endswith('64'):
            return self.read_uint64(address)
        else:
            return self.read_uint32(address)
    
    def read_bytes_hex(self, address, size):
        """Lê dados e retorna em formato hexadecimal"""
        data = self.read_memory(address, size)
        if data:
            return ' '.join(f'{byte:02X}' for byte in data)
        return None
    
    def read_bytes(self, address, size):
        """Lê dados brutos como bytes"""
        return self.read_memory(address, size)
    
    def monitor_address(self, address, data_type='int32', interval=1.0):
        """Monitora um endereço continuamente"""
        print(f"🔍 Monitorando endereço 0x{address:08X} ({data_type})")
        print("Pressione Ctrl+C para parar...\n")
        
        read_functions = {
            'int8': self.read_int8,
            'uint8': self.read_uint8,
            'int16': self.read_int16,
            'uint16': self.read_uint16,
            'int32': self.read_int32,
            'uint32': self.read_uint32,
            'int64': self.read_int64,
            'uint64': self.read_uint64,
            'float': self.read_float,
            'double': self.read_double
        }
        
        read_func = read_functions.get(data_type, self.read_int32)
        last_value = None
        
        try:
            while True:
                current_value = read_func(address)
                
                if current_value is not None:
                    if current_value != last_value:
                        timestamp = time.strftime('%H:%M:%S')
                        if isinstance(current_value, float):
                            print(f"[{timestamp}] 0x{address:08X} = {current_value:.6f}")
                        else:
                            print(f"[{timestamp}] 0x{address:08X} = {current_value}")
                        last_value = current_value
                else:
                    print(f"❌ Falha na leitura do endereço 0x{address:08X}")
                    
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹️ Monitoramento interrompido pelo usuário")
    
    def list_processes(self):
        """Lista todos os processos em execução"""
        print("📋 Processos em execução:\n")
        print(f"{'PID':<8} {'Nome do Processo':<35} {'Memória (MB)':<12}")
        print("=" * 60)
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                memory = proc.info['memory_info'].rss / (1024 * 1024)  # Converter para MB
                processes.append((pid, name, memory))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Ordenar por PID
        processes.sort(key=lambda x: x[0])
        
        for pid, name, memory in processes:
            print(f"{pid:<8} {name:<35} {memory:<12.1f}")
            
        print(f"\n📊 Total de processos: {len(processes)}")
    
    def close(self):
        """Fecha o handle do processo"""
        if self.process_handle:
            ctypes.windll.kernel32.CloseHandle(self.process_handle)
            print("🔒 Handle do processo fechado")

def main():
    """Função principal - interface de linha de comando"""
    reader = MemoryReader()
    
    print("🎮 Leitor de Memória de Processo")
    print("=" * 40)
    
    while True:
        print("\n📋 Opções:")
        print("1. Listar todos os processos")
        print("2. Buscar processo por nome")
        print("3. Conectar por nome do processo")
        print("4. Conectar por PID")
        print("5. Ler endereço específico")
        print("6. Monitorar endereço")
        print("7. Sair")
        
        choice = input("\n👆 Escolha uma opção: ").strip()
        
        if choice == '1':
            reader.list_processes()
            
        elif choice == '2':
            search_name = input("🔍 Digite parte do nome do processo: ").strip().lower()
            if search_name:
                print(f"\n🔎 Processos contendo '{search_name}':\n")
                print(f"{'PID':<8} {'Nome do Processo':<35} {'Memória (MB)':<12}")
                print("=" * 60)
                
                found = False
                for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                    try:
                        pid = proc.info['pid']
                        name = proc.info['name']
                        memory = proc.info['memory_info'].rss / (1024 * 1024)
                        
                        if search_name in name.lower():
                            print(f"{pid:<8} {name:<35} {memory:<12.1f}")
                            found = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if not found:
                    print(f"❌ Nenhum processo encontrado com '{search_name}'")
            
        elif choice == '3':
            process_name = input("📝 Nome do processo (ex: notepad.exe): ").strip()
            if reader.find_process_by_name(process_name):
                reader.open_process()
                
        elif choice == '4':
            try:
                pid = int(input("🔢 PID do processo: ").strip())
                if reader.find_process_by_pid(pid):
                    reader.open_process()
            except ValueError:
                print("❌ PID inválido!")
                
        elif choice == '5':
            if not reader.process_handle:
                print("❌ Conecte-se a um processo primeiro!")
                continue
                
            try:
                address_str = input("📍 Endereço (hex, ex: 0x12345678): ").strip()
                address = int(address_str, 16) if address_str.startswith('0x') else int(address_str, 16)
                
                print("\n📊 Tipos de dados disponíveis:")
                print("1. int32 (padrão)   2. uint32   3. float    4. double")
                print("5. int16           6. uint16   7. int8     8. uint8")
                print("9. string          10. bytes")
                
                type_choice = input("👆 Tipo de dado (1-10): ").strip()
                
                if type_choice == '1' or not type_choice:
                    value = reader.read_int32(address)
                    print(f"🔍 Valor: {value}")
                elif type_choice == '2':
                    value = reader.read_uint32(address)
                    print(f"🔍 Valor: {value}")
                elif type_choice == '3':
                    value = reader.read_float(address)
                    print(f"🔍 Valor: {value}")
                elif type_choice == '4':
                    value = reader.read_double(address)
                    print(f"🔍 Valor: {value}")
                elif type_choice == '5':
                    value = reader.read_int16(address)
                    print(f"🔍 Valor: {value}")
                elif type_choice == '6':
                    value = reader.read_uint16(address)
                    print(f"🔍 Valor: {value}")
                elif type_choice == '7':
                    value = reader.read_int8(address)
                    print(f"🔍 Valor: {value}")
                elif type_choice == '8':
                    value = reader.read_uint8(address)
                    print(f"🔍 Valor: {value}")
                elif type_choice == '9':
                    length = int(input("📏 Comprimento da string: "))
                    value = reader.read_string(address, length)
                    print(f"🔍 Valor: '{value}'")
                elif type_choice == '10':
                    size = int(input("📏 Número de bytes: "))
                    value = reader.read_bytes_hex(address, size)
                    print(f"🔍 Bytes: {value}")
                    
            except ValueError:
                print("❌ Endereço inválido!")
                
        elif choice == '6':
            if not reader.process_handle:
                print("❌ Conecte-se a um processo primeiro!")
                continue
                
            try:
                address_str = input("📍 Endereço (hex): ").strip()
                address = int(address_str, 16) if address_str.startswith('0x') else int(address_str, 16)
                
                data_type = input("📊 Tipo (int32/float/uint32/etc): ").strip().lower()
                if not data_type:
                    data_type = 'int32'
                    
                interval = float(input("⏰ Intervalo em segundos (padrão 1.0): ") or "1.0")
                
                reader.monitor_address(address, data_type, interval)
                
            except ValueError as e:
                print(f"❌ Entrada inválida: {e}")
                
        elif choice == '7':
            reader.close()
            print("👋 Até mais!")
            break
            
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    main()
