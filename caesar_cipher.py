import multiprocessing
import os
import psutil
from typing import List, Tuple
import time
import argparse
from logger import Logger

def process_chunk_wrapper(args: Tuple[str, int, bool, str]) -> Tuple[str, str]:
    chunk, shift, encrypt, temp_dir = args
    try:
        processed = caesar_cipher(chunk, shift, encrypt)
        temp_file = os.path.join(temp_dir, f"temp_{multiprocessing.current_process().pid}.tmp")
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(processed)
        return (chunk, temp_file)
    except Exception as e:
        print(f"Ошибка в process_chunk: {e}")
        raise

def caesar_cipher(text: str, shift: int, encrypt: bool = True) -> str:
    result = []
    for char in text:
        if char.isalpha():
            shift_amount = shift if encrypt else -shift
            if char.isupper():
                new_char = chr((ord(char) - ord('A') + shift_amount) % 26 + ord('A'))
            else:
                new_char = chr((ord(char) - ord('a') + shift_amount) % 26 + ord('a'))
            result.append(new_char)
        else:
            result.append(char)
    return ''.join(result)

class CaesarCipher:
    def __init__(self):
        self.logger = Logger(username="CAESAR_CIPHER")

    def split_text(self, text: str, n_chunks: int) -> List[str]:
        chunk_size = (len(text) + n_chunks - 1) // n_chunks
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def get_available_processes(self):
        try:
            cpu_count = os.cpu_count() or 4
            cpu_percent = psutil.cpu_percent(interval=1)
            available_percent = (100 - cpu_percent) / 100
            available_processes = max(1, int(cpu_count * available_percent))
            self.logger.log_info(f"Доступно ядер: {cpu_count}, загрузка CPU: {cpu_percent}%, доступно процессов: {available_processes}")
            return available_processes
        except Exception as e:
            self.logger.log_error("get_available_processes", str(e))
            return os.cpu_count() or 4

    def process_file(self, input_path: str, output_path: str, shift: int, encrypt: bool = True, n_processes: int = None):
        try:
            self.logger.log_info(f"Начало обработки файла: {input_path}")
            start_time = time.time()
            
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            max_processes = self.get_available_processes()
            n_processes = min(n_processes, max_processes) if n_processes else max_processes
            
            self.logger.log_info(f"Используется процессов: {n_processes}")
            
            temp_dir = os.path.join(os.path.dirname(output_path), "temp_caesar")
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                chunks = self.split_text(text, n_processes)
                
                with multiprocessing.Pool(processes=n_processes) as pool:
                    args = [(chunk, shift, encrypt, temp_dir) for chunk in chunks]
                    results = pool.map(process_chunk_wrapper, args)
                
                results.sort(key=lambda x: text.find(x[0]))
                
                with open(output_path, 'w', encoding='utf-8') as out_file:
                    for _, temp_file in results:
                        with open(temp_file, 'r', encoding='utf-8') as tmp:
                            out_file.write(tmp.read())
                
                elapsed = time.time() - start_time
                self.logger.log_info(f"Файл успешно обработан: {output_path}. Затраченное время: {elapsed:.2f} сек")
            finally:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        os.remove(os.path.join(root, file))
                os.rmdir(temp_dir)
        except Exception as e:
            self.logger.log_error("process_file", str(e))
            raise

def main():
    parser = argparse.ArgumentParser(description="Шифратор/дешифратор файлов")
    parser.add_argument('mode', choices=['encrypt', 'decrypt'])
    parser.add_argument('input_file')
    parser.add_argument('output_file')
    parser.add_argument('--shift', type=int, default=3)
    parser.add_argument('--processes', type=int, default=None)
    
    args = parser.parse_args()
    
    cipher = CaesarCipher()
    
    try:
        if args.mode == 'encrypt':
            cipher.logger.log_info(f"Запуск шифрования: {args.input_file} -> {args.output_file}")
            cipher.process_file(args.input_file, args.output_file, args.shift, encrypt=True, n_processes=args.processes)
        else:
            cipher.logger.log_info(f"Запуск дешифрования: {args.input_file} -> {args.output_file}")
            cipher.process_file(args.input_file, args.output_file, args.shift, encrypt=False, n_processes=args.processes)
    except Exception as e:
        cipher.logger.log_error("main", str(e))
        print(f"Ошибка: {e}")
    finally:
        cipher.logger.stop()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()