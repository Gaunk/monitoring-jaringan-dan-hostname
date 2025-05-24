import socket
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from urllib.parse import urlparse
from datetime import datetime
from PIL import Image, ImageTk
import sys
import os

# ------------------ HELPER -------------------

def resource_path(relative_path):
    try:
        return os.path.join(sys._MEIPASS, relative_path)
    except Exception:
        return os.path.join(os.path.abspath("."), relative_path)

def parse_stratum_url(url):
    if not url.startswith("stratum+tcp://"):
        return None, None
    try:
        parsed = urlparse(url)
        return parsed.hostname, parsed.port
    except Exception:
        return None, None

def check_tcp_connection(host, port, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

# ------------------ MONITORING -------------------

def update_status():
    if not monitoring_active:
        return
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for url in stratum_urls:
        host, port = parse_stratum_url(url)
        if host and port:
            is_up = check_tcp_connection(host, port)
            status = "✅ UP" if is_up else "❌ DOWN"
        else:
            host, port, status = url, "", "INVALID"
        stratum_table.insert("", "end", values=(current_time, host, port, status))
        stratum_table.see(stratum_table.get_children()[-1])

    for host in monitored_hosts:
        try:
            hostname, port = host.split(":")
            port = int(port)
            is_up = check_tcp_connection(hostname, port)
            status = "✅ UP" if is_up else "❌ DOWN"
        except:
            hostname, port, status = host, "", "❌ DOWN"
        host_table.insert("", "end", values=(current_time, hostname, port, status))
        host_table.see(host_table.get_children()[-1])

    window.after(1000, update_status)

def start_monitoring():
    global monitoring_active
    monitoring_active = True
    start_button.config(state="disabled")
    stop_button.config(state="normal")
    update_status()

def stop_monitoring():
    global monitoring_active
    monitoring_active = False
    start_button.config(state="normal")
    stop_button.config(state="disabled")

# ------------------ ACTIONS -------------------

def add_stratum_url():
    url = stratum_entry.get().strip()
    if url and url.startswith("stratum+tcp://"):
        if url not in stratum_urls:
            stratum_urls.append(url)
            input_stratum_table.insert("", "end", values=(url,))
            messagebox.showinfo("Stratum Ditambahkan", f"Stratum '{url}' berhasil ditambahkan.")
            stratum_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Duplikat", "Stratum sudah ada.")
    else:
        messagebox.showerror("Format Salah", "Gunakan format: stratum+tcp://host:port")

def edit_stratum():
    selected = input_stratum_table.selection()
    if not selected:
        messagebox.showwarning("Pilih item", "Pilih entri yang ingin diedit.")
        return
    item = input_stratum_table.item(selected)
    old_value = item["values"][0]
    new_value = simpledialog.askstring("Edit Stratum", "Masukkan URL stratum baru:", initialvalue=old_value)

    if new_value and new_value.startswith("stratum+tcp://"):
        index = stratum_urls.index(old_value)
        stratum_urls[index] = new_value
        input_stratum_table.item(selected, values=(new_value,))
    else:
        messagebox.showerror("Format Salah", "Gunakan format: stratum+tcp://host:port")

def delete_stratum():
    selected = input_stratum_table.selection()
    if not selected:
        messagebox.showwarning("Pilih item", "Pilih entri yang ingin dihapus.")
        return
    item = input_stratum_table.item(selected)
    value = item["values"][0]
    if value in stratum_urls:
        stratum_urls.remove(value)
    input_stratum_table.delete(selected)

# edit_host
def edit_host():
    selected = input_host_table.selection()
    if not selected:
        messagebox.showwarning("Pilih item", "Pilih host yang ingin diedit.")
        return

    item = input_host_table.item(selected)
    original_host_port = item["values"][0]  # Domain/IP as input
    old_ip_port = item["values"][1]         # Resolved IP

    new_value = simpledialog.askstring("Edit Host", "Masukkan IP/domain baru (opsional :port):", initialvalue=original_host_port)
    if not new_value:
        return

    default_port = 80
    if ":" in new_value:
        host_part, port_part = new_value.split(":")
        try:
            port = int(port_part)
        except:
            messagebox.showerror("Format Salah", "Port harus berupa angka.")
            return
    else:
        host_part = new_value
        port = default_port

    try:
        new_ip = socket.gethostbyname(host_part)
        new_ip_port = f"{new_ip}:{port}"
        new_input_value = f"{host_part}:{port}"

        if new_ip_port in monitored_hosts and new_ip_port != old_ip_port:
            messagebox.showwarning("Duplikat", "Host/IP sudah ada.")
            return

        # Update monitored_hosts list
        if old_ip_port in monitored_hosts:
            monitored_hosts.remove(old_ip_port)
        monitored_hosts.append(new_ip_port)

        # Update table
        input_host_table.item(selected, values=(new_input_value, new_ip_port))
        messagebox.showinfo("Host Diperbarui", f"Host berhasil diperbarui ke:\n{new_input_value}\nResolved IP: {new_ip_port}")
    except Exception as e:
        messagebox.showerror("Gagal Resolve", f"Terjadi kesalahan saat resolve: {e}")

# delete_host
def delete_host():
    selected = input_host_table.selection()
    if not selected:
        messagebox.showwarning("Pilih item", "Pilih host yang ingin dihapus.")
        return
    item = input_host_table.item(selected)
    ip_port = item["values"][1]  # IP:Port disimpan di kolom kedua

    if ip_port in monitored_hosts:
        monitored_hosts.remove(ip_port)
    input_host_table.delete(selected)
    messagebox.showinfo("Host Dihapus", f"Host '{ip_port}' berhasil dihapus.")

def add_host():
    entry = host_entry.get().strip()
    default_port = 80  # Anda bisa ubah ke 53, 443, atau port default lain

    if entry:
        if ":" in entry:
            host_part, port_part = entry.split(":")
            try:
                port = int(port_part)
            except ValueError:
                messagebox.showerror("Format Salah", "Port harus berupa angka.")
                return
        else:
            host_part = entry
            port = default_port

        try:
            ip = socket.gethostbyname(host_part)
            ip_entry = f"{ip}:{port}"
            original_entry = f"{host_part}:{port}"

            if ip_entry not in monitored_hosts:
                monitored_hosts.append(ip_entry)
                input_host_table.insert("", "end", values=(original_entry, ip_entry))
                messagebox.showinfo("Host Ditambahkan", f"'{original_entry}' berhasil ditambahkan.\nResolved ke IP: {ip_entry}")
                host_entry.delete(0, tk.END)
            else:
                messagebox.showwarning("Duplikat", "Host sudah ada.")
        except Exception as e:
            messagebox.showerror("Kesalahan", f"Gagal resolve host: {e}")
    else:
        messagebox.showerror("Input Kosong", "Masukkan IP atau domain (opsional: tambahkan port).")


def save_logs_to_csv():
    folder = filedialog.askdirectory(title="Pilih folder untuk menyimpan log")
    if not folder:
        return

    with open(f"{folder}/stratum_log.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Host", "Port", "Status"])
        for row in stratum_table.get_children():
            writer.writerow(stratum_table.item(row)["values"])

    with open(f"{folder}/host_log.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Host", "Port", "Status"])
        for row in host_table.get_children():
            writer.writerow(host_table.item(row)["values"])

    messagebox.showinfo("Sukses", "Log berhasil disimpan.")

def exit_app():
    if messagebox.askokcancel("Keluar", "Yakin ingin keluar dari aplikasi?"):
        window.destroy()

# ------------------ DATA -------------------

stratum_urls = [
    "stratum+tcp://10.0.0.211:5051",
    "stratum+tcp://ss.id.antpool.com:3333"
]

monitored_hosts = [
    "8.8.8.8:53",
    "1.1.1.1:53"
]

monitoring_active = False

# ------------------ GUI -------------------

window = tk.Tk()
window.title("🔍 Network & Stratum Monitoring By Cibinong Cyber")
window.state('zoomed')
window.configure(bg="#f0f0f0")

# Icon
try:
    logo_img = Image.open(resource_path("assets/logo.ico"))
    logo_photo = ImageTk.PhotoImage(logo_img)
    window.tk.call('wm', 'iconphoto', window._w, logo_photo)
except:
    pass

# Header Logo
try:
    logo_img = Image.open(resource_path("assets/logo.png"))
    logo_photo = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(window, image=logo_photo, bg="#f0f0f0")
except:
    logo_label = tk.Label(window, text="Cibinong Cyber Monitoring", font=("Arial", 14, "bold"), bg="#f0f0f0")
logo_label.pack(pady=10)

# Control Frame
control_frame = tk.Frame(window, bg="#f0f0f0")
control_frame.pack(pady=10)

# Icons
edit_img = ImageTk.PhotoImage(Image.open(resource_path("assets/edit.png")).resize((16, 16)))
delete_img = ImageTk.PhotoImage(Image.open(resource_path("assets/delete.png")).resize((16, 16)))
start_img = ImageTk.PhotoImage(Image.open(resource_path("assets/play.png")).resize((20, 20)))
stop_img = ImageTk.PhotoImage(Image.open(resource_path("assets/stop.png")).resize((20, 20)))
add_img = ImageTk.PhotoImage(Image.open(resource_path("assets/add.png")).resize((16, 16)))
exit_img = ImageTk.PhotoImage(Image.open(resource_path("assets/exit.png")).resize((20, 20)))
save_img = ImageTk.PhotoImage(Image.open(resource_path("assets/save.png")).resize((20, 20)))

# Control Buttons
start_button = tk.Button(control_frame, text=" Mulai Monitoring", image=start_img, compound="left", command=start_monitoring, font=("Arial", 11))
stop_button = tk.Button(control_frame, text=" Stop Monitoring", image=stop_img, compound="left", command=stop_monitoring, font=("Arial", 11), state="disabled")
exit_button = tk.Button(control_frame, text=" Keluar", image=exit_img, compound="left", command=exit_app, font=("Arial", 11), fg="red")
save_button = tk.Button(control_frame, text=" Simpan Log", image=save_img, compound="left", command=save_logs_to_csv, font=("Arial", 11))

start_button.grid(row=0, column=0, padx=5)
stop_button.grid(row=0, column=1, padx=5)
exit_button.grid(row=0, column=2, padx=5)
save_button.grid(row=0, column=3, padx=5)

# Host Entry
# Host Entry Row (Row 1)
host_entry = tk.Entry(control_frame, width=30)
host_entry.insert(0, "")
host_entry.grid(row=1, column=0, pady=5)
tk.Button(control_frame, text=" Tambah Host", image=add_img, compound="left", command=add_host).grid(row=1, column=1, padx=5)
tk.Button(control_frame, text=" Edit Host", image=edit_img, compound="left", command=edit_host).grid(row=1, column=2, padx=5)
tk.Button(control_frame, text=" Hapus Host", image=delete_img, compound="left", command=delete_host).grid(row=1, column=3, padx=5)



# Stratum Entry
stratum_entry = tk.Entry(control_frame, width=30)
stratum_entry.grid(row=2, column=0, pady=5)
tk.Button(control_frame, text=" Tambah Stratum", image=add_img, compound="left", command=add_stratum_url).grid(row=2, column=1)
tk.Button(control_frame, text=" Edit Stratum", image=edit_img, compound="left", command=edit_stratum).grid(row=2, column=2, padx=5)
tk.Button(control_frame, text=" Hapus Stratum", image=delete_img, compound="left", command=delete_stratum).grid(row=2, column=3, padx=5)


# ------------------ TABLES -------------------

# Input Stratum Table
tk.Label(window, text="📋 Daftar Stratum yang Diinput", font=("Arial", 12, "bold"), bg="#f0f0f0").pack()
input_stratum_frame = tk.Frame(window)
input_stratum_frame.pack()
input_stratum_table = ttk.Treeview(input_stratum_frame, columns=("Stratum URL",), show="headings", height=4)
input_stratum_table.heading("Stratum URL", text="Stratum URL")
input_stratum_table.pack(side="left")
scroll_stratum_input = tk.Scrollbar(input_stratum_frame, orient="vertical", command=input_stratum_table.yview)
scroll_stratum_input.pack(side="right", fill="y")
input_stratum_table.configure(yscrollcommand=scroll_stratum_input.set)

# Input Host Table
tk.Label(window, text="📋 Daftar Host yang Diinput", font=("Arial", 12, "bold"), bg="#f0f0f0").pack()
input_host_frame = tk.Frame(window)
input_host_frame.pack()
input_host_table = ttk.Treeview(input_host_frame, columns=("Host:Port",), show="headings", height=4)
input_host_table.heading("Host:Port", text="Host:Port")
input_host_table.pack(side="left")
scroll_host_input = tk.Scrollbar(input_host_frame, orient="vertical", command=input_host_table.yview)
scroll_host_input.pack(side="right", fill="y")
input_host_table.configure(yscrollcommand=scroll_host_input.set)

# Stratum Monitoring Table
tk.Label(window, text="📡 Stratum Status", font=("Arial", 14, "bold"), bg="#f0f0f0").pack()
stratum_frame = tk.Frame(window)
stratum_frame.pack()
stratum_table = ttk.Treeview(stratum_frame, columns=("Time", "Host", "Port", "Status"), show="headings", height=8)
for col in ("Time", "Host", "Port", "Status"):
    stratum_table.heading(col, text=col)
stratum_table.pack(side="left")
scroll1 = tk.Scrollbar(stratum_frame, orient="vertical", command=stratum_table.yview)
scroll1.pack(side="right", fill="y")
stratum_table.configure(yscrollcommand=scroll1.set)

# Host Monitoring Table
tk.Label(window, text="🖥️ Host Status", font=("Arial", 14, "bold"), bg="#f0f0f0").pack()
host_frame = tk.Frame(window)
host_frame.pack()
host_table = ttk.Treeview(host_frame, columns=("Time", "Host", "Port", "Status"), show="headings", height=8)
for col in ("Time", "Host", "Port", "Status"):
    host_table.heading(col, text=col)
host_table.pack(side="left")
scroll2 = tk.Scrollbar(host_frame, orient="vertical", command=host_table.yview)
scroll2.pack(side="right", fill="y")
host_table.configure(yscrollcommand=scroll2.set)

# Footer
description = tk.Label(window, text="Aplikasi untuk memantau konektivitas stratum dan host secara real-time - Team Cibinong Cyber Security", font=("Arial", 10), bg="#f0f0f0")
description.pack(pady=(0, 10))
footer = tk.Label(window, text="CRDM - DAM © 2023 Cibinong Cyber | Versi 1.0.0", font=("Arial", 9), bg="#f0f0f0", fg="gray")
footer.pack(side="bottom", pady=10)

# ------------------ MAINLOOP -------------------

window.mainloop()
