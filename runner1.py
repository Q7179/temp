#!/usr/bin/env python3
import subprocess
import time

IP_FILE = "dana_na_443_ip.txt"
LOG_OK = "log.txt"
LOG_ERR = "log_erro.txt"
CMD_TIMEOUT = 60          # giây
MAX_LOG_LEN = 1000        # ký tự

def read_ip_list(path):
    ips = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            ip = line.strip()
            if not ip:
                continue
            # nếu muốn bỏ qua comment thì mở uncomment dòng dưới
            # if ip.startswith("#"):
            #     continue
            ips.append(ip)
    return ips

def run_for_ip(idx, ip):
    print(f"[{idx}] Đang xử lý IP: {ip}")

    # chạy: python3 p1.py ip p2.php
    proc = subprocess.Popen(
        ["python3", "p1.py", ip, "p2.php"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    start_time = time.time()
    output = ""
    wrote_error_log = False

    try:
        while True:
            # nếu process đã kết thúc
            if proc.poll() is not None:
                # đọc nốt phần còn lại (nếu có)
                rest = proc.stdout.read()
                if rest:
                    output += rest
                break

            # đọc từng dòng (non-blocking tương đối)
            line = proc.stdout.readline()
            if line:
                output += line

                # nếu log vượt quá 1000 ký tự
                if len(output) > MAX_LOG_LEN:
                    print(f"    [!] Log IP {ip} > {MAX_LOG_LEN} ký tự, kill p1.py và ghi vào {LOG_ERR}")
                    proc.kill()
                    proc.wait()
                    with open(LOG_ERR, "a", encoding="utf-8") as f:
                        f.write(f"===== IP {ip} (OUTPUT TOO LONG) =====\n")
                        f.write(output)
                        f.write("\n\n")
                    wrote_error_log = True
                    break

            # check timeout 60 giây
            if time.time() - start_time > CMD_TIMEOUT:
                print(f"    [!] IP {ip} chạy quá {CMD_TIMEOUT}s, kill p1.py và bỏ qua")
                proc.kill()
                proc.wait()
                return  # bỏ qua IP này, không log gì thêm

        # nếu không bị quá 1000 ký tự và không timeout
        if not wrote_error_log:
            if "is accessible" in output:
                print(f"    [+] Tìm thấy 'is accessible' với IP {ip}, ghi vào {LOG_OK}")
                with open(LOG_OK, "a", encoding="utf-8") as f:
                    f.write(f"===== IP {ip} =====\n")
                    f.write(output)
                    f.write("\n\n")
            else:
                print(f"    [-] IP {ip}: không có chuỗi 'is accessible', không ghi log")

    except Exception as e:
        print(f"    [!] Lỗi khi xử lý IP {ip}: {e}")
        try:
            proc.kill()
            proc.wait()
        except Exception:
            pass

def main():
    ips = read_ip_list(IP_FILE)
    if not ips:
        print(f"Không có IP nào trong file {IP_FILE}")
        return

    print(f"Tổng số IP: {len(ips)}")
    for idx, ip in enumerate(ips, start=1):
        run_for_ip(idx, ip)

if __name__ == "__main__":
    main()
