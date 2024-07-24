import tkinter as tk
from tkinter import messagebox
import mysql.connector
import cv2
import numpy as np
from collections import Counter
import pickle
import time

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Form Data Nasabah")
        window_width = 1200
        window_height = 800
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        self.current_frame = None
        self.first_page_data = {}
        self.nik = tk.StringVar()
        self.show_frame(StartPage)

    def show_frame(self, frame_class, *args):
        new_frame = frame_class(self, *args)
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = new_frame
        self.current_frame.pack(fill="both", expand=True)

class StartPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        labels = ["NIK", "Nama", "Tempat Lahir", "Tanggal Lahir (YYYY-MM-DD)", "Alamat", "Kelurahan", "Kecamatan", "Kabupaten", "Provinsi", "Agama"]
        self.entries = {}

        for i, label_text in enumerate(labels):
            tk.Label(self, text=label_text, font=("Arial", 24)).grid(row=i, column=0, padx=10, pady=5, sticky='w')
            entry = tk.Entry(self, width=50, font=("Arial", 24))
            entry.grid(row=i, column=1, padx=10, pady=3, sticky='w')
            self.entries[label_text.lower()] = entry

        tk.Label(self, text="Jenis Kelamin", font=("Arial", 24)).grid(row=len(labels), column=0, padx=10, pady=5, sticky='w')
        self.selected_gender = tk.StringVar(self)
        self.selected_gender.set("Laki-laki")
        gender_menu = tk.OptionMenu(self, self.selected_gender, "Laki-laki", "Perempuan")
        gender_menu.config(font=("Arial", 24), width=15)
        gender_menu.grid(row=len(labels), column=1, padx=10, pady=3, sticky='w')

        next_button = tk.Button(self, text="Next", font=("Arial", 24), command=self.submit_first_page)
        next_button.grid(row=len(labels) + 1, columnspan=2, pady=10)

    def submit_first_page(self):
        self.master.first_page_data = {
            "nik": self.entries["nik"].get(),
            "nama": self.entries["nama"].get(),
            "tempat_lahir": self.entries["tempat lahir"].get(),
            "tanggal_lahir": self.entries["tanggal lahir (yyyy-mm-dd)"].get(),
            "alamat": self.entries["alamat"].get(),
            "kelurahan": self.entries["kelurahan"].get(),
            "kecamatan": self.entries["kecamatan"].get(),
            "kabupaten": self.entries["kabupaten"].get(),
            "provinsi": self.entries["provinsi"].get(),
            "agama": self.entries["agama"].get(),
            "jenis_kelamin": self.selected_gender.get()
        }

        for key, value in self.master.first_page_data.items():
            if not value:
                messagebox.showwarning("Input Error", "Semua field harus diisi!")
                return

        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                database="ta",
                password="1234"
            )
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT * FROM penduduk 
            WHERE nik = %s AND nama = %s AND tempat_lahir = %s AND tanggal_lahir = %s
            AND alamat = %s AND kelurahan = %s AND kecamatan = %s AND kabupaten = %s
            AND provinsi = %s AND agama = %s AND jenis_kelamin = %s
            """
            cursor.execute(query, (
                self.master.first_page_data['nik'], self.master.first_page_data['nama'], self.master.first_page_data['tempat_lahir'], 
                self.master.first_page_data['tanggal_lahir'], self.master.first_page_data['alamat'], self.master.first_page_data['kelurahan'], 
                self.master.first_page_data['kecamatan'], self.master.first_page_data['kabupaten'], self.master.first_page_data['provinsi'], 
                self.master.first_page_data['agama'], self.master.first_page_data['jenis_kelamin']
            ))
            result = cursor.fetchone()

            if result:
                messagebox.showinfo("Info", "Data SESUAI dengan data kependudukan.")
                self.save_to_new_table(conn, self.master.first_page_data)
                self.clear_fields()
                self.master.show_frame(FaceRecognitionPage, self.master.first_page_data['nik'])
            else:
                messagebox.showinfo("WARNING", "Data BERBEDA dengan data kependudukan.\n Segera laporkan ke Dinas DUKCAPIL!")

            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def clear_fields(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.selected_gender.set("Laki-laki")

    def save_to_new_table(self, conn, user_data):
        cursor = conn.cursor()
        query = """
        INSERT INTO nasabah (NIK, Nama, Tempat_Lahir, Tanggal_Lahir, Alamat, Kelurahan, Kecamatan, Kabupaten, Provinsi, Agama, Jenis_Kelamin)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (
                user_data['nik'], user_data['nama'], user_data['tempat_lahir'], 
                user_data['tanggal_lahir'], user_data['alamat'], user_data['kelurahan'], 
                user_data['kecamatan'], user_data['kabupaten'], user_data['provinsi'], 
                user_data['agama'], user_data['jenis_kelamin']
            ))
            conn.commit()
        except mysql.connector.Error as err:
            if err.errno == 1062:
                messagebox.showwarning("Duplicate Entry", "Data dengan NIK tersebut sudah ada di tabel nasabah.")
            else:
                messagebox.showerror("Database Error", f"Error: {err}")

class FaceRecognitionPage(tk.Frame):
    def __init__(self, master, nik):
        super().__init__(master)
        self.master = master
        self.nik = nik

        tk.Label(self, text="Mulai Pengenalan Wajah", font=("Arial", 24)).pack(pady=20)
        tk.Button(self, text="Mulai", font=("Arial", 24), command=self.recognize_face).pack(pady=20)
        tk.Button(self, text="Back", font=("Arial", 24), command=self.go_back).pack(pady=10)

    def go_back(self):
        self.master.show_frame(StartPage)

    def recognize_face(self):
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read('trainer/trainer.yml')

        with open('trainer/nik_to_int.pkl', 'rb') as f:
            nik_to_int = pickle.load(f)
        with open('trainer/int_to_nik.pkl', 'rb') as f:
            int_to_nik = pickle.load(f)

        face_cascade = cv2.CascadeClassifier('/home/pi/LBPH/haarcascade_frontalface_default.xml')
        cam = cv2.VideoCapture(0)
        detected_niks = []
        DETECTION_LIMIT = 10

        for _ in range(DETECTION_LIMIT):
            ret, frame = cam.read()
            if not ret:
                print("[ERROR] Failed to capture image")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            for (x, y, w, h) in faces:
                face = gray[y:y+h, x:x+w]
                id_, conf = recognizer.predict(face)
                if conf < 70:
                    detected_niks.append(int_to_nik[id_])

            cv2.imshow('Face Recognition', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()

        if detected_niks:
            most_common_nik, count = Counter(detected_niks).most_common(1)[0]
            if count >= DETECTION_LIMIT // 2:
                messagebox.showinfo("Success", f"Wajah dikenali sebagai: {most_common_nik}")
                self.master.show_frame(InputPage, self.nik)
            else:
                messagebox.showwarning("Error", "Wajah tidak dikenali.")
        else:
            messagebox.showwarning("Error", "Tidak ada wajah yang dikenali.")

class InputPage(tk.Frame):
    def __init__(self, master, nik):
        super().__init__(master)
        self.master = master
        self.nik = nik

        labels = ["Email", "Nama Gadis Ibu Kandung", "Pekerjaan"]
        self.entries = {}

        for i, label_text in enumerate(labels):
            tk.Label(self, text=label_text, font=("Arial", 24)).grid(row=i, column=0, padx=10, pady=5, sticky='w')
            entry = tk.Entry(self, width=50, font=("Arial", 24))
            entry.grid(row=i, column=1, padx=10, pady=3, sticky='w')
            self.entries[label_text.lower()] = entry

        tk.Button(self, text="Submit", font=("Arial", 24), command=self.submit_second_page).grid(row=len(labels), columnspan=2, pady=10)
        tk.Button(self, text="Back", font=("Arial", 24), command=self.go_back).grid(row=len(labels) + 1, columnspan=2, pady=10)

    def go_back(self):
        self.master.show_frame(FaceRecognitionPage, self.nik)

    def submit_second_page(self):
        additional_data = {
            "email": self.entries["email"].get(),
            "nama_gadis_ibu_kandung": self.entries["nama gadis ibu kandung"].get(),
            "pekerjaan": self.entries["pekerjaan"].get()
        }

        for key, value in additional_data.items():
            if not value:
                messagebox.showwarning("Input Error", "Semua field harus diisi!")
                return

        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                database="tugas",
                password="1234"
            )
            cursor = conn.cursor()
            query = """
            UPDATE nasabah 
            SET Email = %s, Nama_Gadis_Ibu_Kandung = %s, Pekerjaan = %s 
            WHERE NIK = %s
            """
            cursor.execute(query, (additional_data['email'], additional_data['nama_gadis_ibu_kandung'], additional_data['pekerjaan'], self.nik))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Data tambahan berhasil disimpan.")
            self.clear_fields()
            self.master.show_frame(DatasetCapturePage, self.nik)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def clear_fields(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)

class DatasetCapturePage(tk.Frame):
    def __init__(self, master, nik):
        super().__init__(master)
        self.master = master
        self.nik = nik

        tk.Label(self, text="Ambil Gambar Wajah", font=("Arial", 24)).pack(pady=20)
        tk.Button(self, text="Mulai", font=("Arial", 24), command=self.capture_faces).pack(pady=20)
        tk.Button(self, text="Back", font=("Arial", 24), command=self.go_back).pack(pady=10)

        # Load encoders
        with open('trainer/nik_to_int.pkl', 'rb') as f:
            self.nik_to_int = pickle.load(f)
        with open('trainer/int_to_nik.pkl', 'rb') as f:
            self.int_to_nik = pickle.load(f)

    def go_back(self):
        self.master.show_frame(InputPage, self.nik)

    def capture_faces(self):
        face_cascade = cv2.CascadeClassifier('/home/pi/LBPH/haarcascade_frontalface_default.xml')
        cam = cv2.VideoCapture(0)
        sampleNum = 0
        dataset_limit = 20

        while True:
            ret, img = cam.read()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                sampleNum += 1
                face = cv2.resize(gray[y:y + h, x:x + w], (200, 200))
                face = np.expand_dims(face, axis=-1)
                face = np.expand_dims(face, axis=0)

                try:
                    conn = mysql.connector.connect(
                        host="localhost",
                        user="root",
                        database="tugas",
                        password="1234"
                    )
                    cursor = conn.cursor()
                    query = "INSERT INTO face_images (nik, image) VALUES (%s, %s)"
                    cursor.execute(query, (self.nik, face.tobytes()))
                    conn.commit()
                    cursor.close()
                    conn.close()
                except mysql.connector.Error as err:
                    messagebox.showerror("Database Error", f"Error: {err}")
                    cam.release()
                    cv2.destroyAllWindows()
                    return

                cv2.putText(img, f"Face: {sampleNum}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

            cv2.imshow('Dataset Capture', img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if sampleNum >= dataset_limit:
                break

        cam.release()
        cv2.destroyAllWindows()
        messagebox.showinfo("Info", "Pengambilan dataset wajah selesai.")
        self.master.show_frame(StartPage)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
