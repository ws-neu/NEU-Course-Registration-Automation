import customtkinter as ctk
import time, sys, re
import threading
import logging
from functions import create_driver, login, execute, checkMSV
from styles import Config
import tkinter.messagebox as messagebox

# Configure logging with file and console output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Set appearance and encoding
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Đăng ký tín chỉ NEU")
        self.root.geometry("800x400")
        self.root.configure(fg_color="#6b6765")
        self.stop_event = threading.Event()
        self.currentMLHP = 1
        self.MAX_MLHP = 8
        self.hideMK = True
        self.isON = False
        self.isLoop = False
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # Main frames
        self.frame1 = ctk.CTkFrame(
            master=self.root, 
            width=780, 
            height=380, 
            fg_color=Config.Colors.ofFrame1, 
            corner_radius=15
        )
        self.frame2 = ctk.CTkFrame(
            master=self.frame1, 
            width=740, 
            height=340, 
            fg_color=Config.Colors.ofFrame2, 
            corner_radius=15
        )
        self.frame3 = ctk.CTkFrame(
            master=self.frame2, 
            width=580, 
            height=240, 
            corner_radius=10,
            fg_color=Config.Colors.ofFrame3, 
            border_width=4, 
            border_color=Config.Colors.ofFrameBorder
        )
        self.frame4 = ctk.CTkFrame(
            master=self.frame2, 
            width=580, 
            height=240, 
            corner_radius=10,
            fg_color=Config.Colors.ofFrame3, 
            border_width=4, 
            border_color=Config.Colors.ofFrameBorder
        )

        # Decorative screws
        self.screws = []
        for i in range(6):
            screw = ctk.CTkFrame(
                master=self.frame1, width=10, height=10, fg_color=Config.Colors.ofScrew, corner_radius=15
            )
            self.screws.append(screw)

        # MSV and password input fields
        self.buttonOn = ctk.CTkButton(
            master=self.frame2, 
            width=40, 
            height=40, 
            text="", 
            command=self.onMachine,
            fg_color=Config.Colors.transparent, 
            border_width=4, 
            border_color="#6b6765",
            corner_radius=100, 
            image=Config.Icons.on, 
            hover_color=Config.Colors.ofHoverButton
        )
        self.entryMSV = ctk.CTkEntry(
            master=self.frame2, 
            width=100, 
            height=40, 
            corner_radius=10, 
            fg_color="#54703c",
            border_width=4, 
            border_color=Config.Colors.ofFrameBorder, 
            text_color=Config.Colors.ofTextMSVMK,
            font=("Arial", 14)
        )
        self.entryMK = ctk.CTkEntry(
            master=self.frame2, 
            width=160, 
            height=40, 
            corner_radius=10, 
            fg_color="#54703c",
            border_width=4, 
            border_color=Config.Colors.ofFrameBorder, 
            text_color=Config.Colors.ofTextMSVMK,
            font=("Arial", 14), 
            show="*"
        )
        self.buttonToggleMK = ctk.CTkButton(
            master=self.frame2, 
            width=30, 
            height=30, 
            text="", 
            command=self.toggleMK,
            fg_color=Config.Colors.transparent, 
            border_width=4, 
            border_color="#6b6765",
            corner_radius=100, 
            hover_color=Config.Colors.ofHoverButton
        )

        # MLHP input fields
        self.inputMLHPs = []
        self.positions = [
            (20 + i * 140, 60) if i < (self.MAX_MLHP // 2)
            else (20 + (i - (self.MAX_MLHP // 2)) * 140, 120)
            for i in range(self.MAX_MLHP)
        ]
        for i in range(self.MAX_MLHP):
            inputMLHP = ctk.CTkEntry(
                master=self.frame3, 
                width=120, 
                height=40, 
                corner_radius=10,
                fg_color=Config.Colors.transparent, 
                border_width=2, 
                border_color=Config.Colors.ofBorderMLHP,
                text_color=Config.Colors.ofTextMLHP, 
                font=("Arial", 10)
            )
            if i == 0:
                inputMLHP.place(x=self.positions[i][0], y=self.positions[i][1])
            self.inputMLHPs.append(inputMLHP)

        # Control buttons
        self.buttonAddMLHP = ctk.CTkButton(
            master=self.frame2, width=40, height=40, text="+", command=self.addMLHP,
            fg_color=Config.Colors.ofButton, border_width=4, border_color="#6b6765",
            text_color="#6b6765", font=("Arial", 14, "bold"), hover_color=Config.Colors.ofHoverButton
        )
        self.buttonDelMLHP = ctk.CTkButton(
            master=self.frame2, width=40, height=40, text="-", command=self.deleteMLHP,
            fg_color=Config.Colors.ofButton, border_width=4, border_color="#6b6765",
            text_color="#6b6765", font=("Arial", 14, "bold"), hover_color=Config.Colors.ofHoverButton
        )
        self.buttonStart = ctk.CTkButton(
            master=self.frame2, width=100, height=40, text="", command=self.run_script,
            fg_color=Config.Colors.ofButton, border_width=4, border_color="#6b6765",
            corner_radius=100, image=Config.Icons.start, hover_color=Config.Colors.ofHoverButton
        )
        self.buttonStop = ctk.CTkButton(
            master=self.frame2, width=100, height=40, text="", command=self.shutdown,
            fg_color=Config.Colors.ofButton, border_width=4, border_color="#6b6765",
            corner_radius=100, image=Config.Icons.stop, hover_color=Config.Colors.ofHoverButton
        )
        self.buttonLoop = ctk.CTkButton(
            master=self.frame2, width=100, height=40, text="", command=self.toggleLoop,
            fg_color=Config.Colors.ofButton, border_width=4, border_color="#6b6765",
            corner_radius=100, image=Config.Icons.loop, hover_color=Config.Colors.ofHoverButton
        )

        # Status labels
        self.pre_status = ctk.CTkLabel(
            master=self.frame4, text="", font=("Arial", 14), text_color=Config.Colors.ofTextStatus
        )
        self.status = ctk.CTkLabel(
            master=self.frame3,
            text="MSV hợp lệ. Điền MK ở ô cạnh MSV và MLHP ở các ô dưới đây.",
            font=("Arial", 14), text_color=Config.Colors.ofTextStatus
        )

        # Position elements
        self.frame1.place(x=10, y=10)
        self.frame2.place(x=20, y=20)
        self.frame3.place(x=20, y=80)
        self.frame4.place(x=20, y=80)
        self.screws[0].place(x=6, y=6)
        self.screws[1].place(x=6, y=364)
        self.screws[2].place(x=390, y=6)
        self.screws[3].place(x=390, y=364)
        self.screws[4].place(x=764, y=6)
        self.screws[5].place(x=764, y=364)
        self.entryMSV.place(x=20, y=20)
        self.entryMK.place(x=140, y=20)
        self.buttonOn.place(x=400, y=20)
        self.buttonToggleMK.place(x=310, y=25)
        rigX, rigY = 620, 90
        self.buttonLoop.place(x=rigX, y=rigY)
        self.buttonDelMLHP.place(x=rigX, y=rigY + 60)
        self.buttonAddMLHP.place(x=rigX + 60, y=rigY + 60)
        self.buttonStop.place(x=rigX, y=rigY + 120)
        self.buttonStart.place(x=rigX, y=rigY + 180)
        self.pre_status.place(x=20, y=20)
        self.status.place(x=20, y=20)
        
        self.update_button_states()

    def update_button_states(self):
        # Update button states based on program state.
        self.buttonStart.configure(state="normal" if self.isON else "disabled")
        self.buttonStop.configure(state="normal" if self.isON else "disabled")

    def toStatus(self, message):
        # Update status message and log it.
        self.status.configure(text=message)

    def validate_msv(self, msv):
        # Validate MSV format: 8 digits.
        is_valid = bool(re.match(r"^\d{8}$", msv))
        logging.info(f"Validating MSV: {msv}, Result: {is_valid}")
        return is_valid

    def onMachine(self):
        # Activate/deactivate processing mode.
        MSV = self.entryMSV.get().strip()
        logging.info(f"onMachine triggered with MSV: {MSV}")
        if not self.validate_msv(MSV):
            logging.warning(f"Invalid MSV format: {MSV}")
            return
        self.entryMSV.configure(state="disabled")
        def script_thread():
            logging.info("Checking MSV")
            self.pre_status.configure(text="Đang kiểm tra MSV...")
            if self.isON:
                logging.info("Deactivating processing mode")
                self.entryMSV.configure(state="normal")
                self.frame4.place(x=20, y=80)
                self.pre_status.place(x=20, y=20)
                self.pre_status.configure(text="")
                self.isON = False
            elif checkMSV(MSV):
                logging.info("MSV is valid")
                self.buttonStop.configure(state="normal")
                self.buttonStart.configure(state="normal")
                self.frame4.place_forget()
                self.pre_status.place_forget()
                self.toStatus("MSV hợp lệ. Nhập MK và MLHP.")
                self.isON = True
            else:
                logging.warning("MSV is invalid")
                self.pre_status.configure(text="MSV không hợp lệ. Vui lòng đăng ký.")
                self.entryMSV.configure(state="normal")
            self.update_button_states()
        thread = threading.Thread(target=script_thread, daemon=True)
        thread.start()

    def toggleLoop(self):
        # Toggle loop mode (only when 1 MLHP).
        if self.currentMLHP != 1:
            logging.warning("Toggle loop mode failed: more than 1 MLHP")
            self.toStatus("Chế độ lặp chỉ dùng khi có 1 MLHP.")
            return

        self.isLoop = not self.isLoop
        logging.info(f"Toggle loop mode: isLoop={self.isLoop}")
        self.buttonLoop.configure(fg_color=Config.Colors.ofPressLoop if self.isLoop else Config.Colors.ofButton)
        self.toStatus("Chế độ lặp đã được kích hoạt." if self.isLoop else "Chế độ lặp đã được tắt.")
        self.buttonAddMLHP.configure(state="normal" if not self.isLoop else "disabled")
        self.buttonDelMLHP.configure(state="normal" if not self.isLoop else "disabled")

    def toggleMK(self):
        # Show/hide password.
        self.hideMK = not self.hideMK
        logging.info(f"Toggle password visibility: hideMK={self.hideMK}")
        self.entryMK.configure(show="" if not self.hideMK else "*")
        self.buttonToggleMK.configure(fg_color=Config.Colors.ofHideMK if not self.hideMK else Config.Colors.ofPressHideMK)

    def addMLHP(self):
        # Add MLHP input field.
        logging.info(f"Add MLHP field, current: {self.currentMLHP+1}")
        if self.currentMLHP < self.MAX_MLHP:
            x, y = self.positions[self.currentMLHP]
            self.inputMLHPs[self.currentMLHP].place(x=x, y=y)
            self.currentMLHP += 1
            self.toStatus("Đã thêm 1 MLHP.")
        else:
            self.toStatus("Giới hạn số MLHP là 8. Không thể thêm nữa.")

    def deleteMLHP(self):
        # Remove MLHP input field.
        logging.info(f"Del MLHP field, current: {self.currentMLHP-1}")
        if self.currentMLHP > 1:
            self.currentMLHP -= 1
            self.inputMLHPs[self.currentMLHP].place_forget()
            self.toStatus("Đã xóa 1 MLHP.")
        else:
            self.toStatus("Không thể xóa thêm nữa. Phải có ít nhất 1 MLHP.")

    def shutdown(self): 
        # Stop the process.
        logging.info("Shutting down process")
        self.stop_event.set()
        self.toStatus("Đang dừng quy trình...")
        self.root.after(1000, lambda: self.toStatus("Đã dừng quy trình."))
        self.update_button_states()

    def split_mlhp(self, MLHP):
        # Split MLHP into MHP and LHP.
        pattern = r"^([A-Z0-9]+)\(\d+\)_(\d+)$"
        match = re.match(pattern, MLHP)
        if match:
            MHP, LHP = match.group(1), match.group(2)
            logging.info(f"Input: MLHP= {MLHP}, MHP={MHP}, LHP={LHP}")
            return MHP, LHP
        logging.error(f"Invalid MLHP format: {MLHP}")
        self.toStatus("Định dạng MLHP không hợp lệ. Vui lòng nhập theo dạng: TOKT1001(324)_01")
        raise ValueError("Invalid MLHP format")

    def run_script(self):
        # Run the course registration process.
        MSV = self.entryMSV.get().strip()
        MK = self.entryMK.get().strip()
        MLHP_values = [entry.get().strip() for entry in self.inputMLHPs if entry.get().strip()]
        logging.info(f"Running script: MSV={MSV}, MLHPs={MLHP_values}")

        if not MSV or not MK:
            logging.warning("MSV or MK is empty")
            self.toStatus("Vui lòng nhập MSV và mật khẩu.")
            return
        if not MLHP_values:
            logging.warning("No MLHP values provided")
            self.toStatus("Vui lòng thêm ít nhất 1 MLHP.")
            return
        for hp in MLHP_values:
            if not re.match(r"^[A-Z0-9]+\(\d+\)_(\d+)$", hp.strip()):
                logging.error(f"Invalid MLHP format: {hp}")
                self.toStatus(f"Định dạng MLHP {hp} không hợp lệ. Vui lòng kiểm tra lại.")
                return

        self.stop_event.clear()
        self.buttonStart.configure(state="disabled")
        self.toStatus("Đang xử lý...")
        logging.info("Starting registration process")

        def script_thread():
            driver = None
            try:
                driver = create_driver()
                success, driver = login(driver, MSV, MK)
                if success:
                    for hp in MLHP_values:
                        if self.stop_event.is_set():
                            logging.info("Process stopped by user")
                            self.root.after(0, lambda: self.toStatus("Quy trình đã bị dừng."))
                            return
                        MLHP = hp.strip()
                        if not MLHP:
                            logging.warning("Empty MLHP detected, skipping")
                            self.root.after(0, lambda: self.toStatus("Cảnh báo: Có MLHP trống, sẽ bỏ qua."))
                            continue
                        MHP, LHP = self.split_mlhp(MLHP)
                        if self.isLoop:
                            execute(driver, MHP, MLHP, 100000, self.stop_event)
                        else: 
                            execute(driver, MHP, MLHP, stop_event=self.stop_event)
                    if not self.stop_event.is_set():
                        logging.info("Registration process completed")
                        self.root.after(0, lambda: self.toStatus("Hoàn tất quy trình, vui lòng kiểm tra lại!"))
                else:
                    logging.error("Login failed")
                    self.root.after(0, lambda: self.toStatus("Đăng nhập không thành công. Vui lòng kiểm tra lại MSV và MK."))
            except Exception as e:
                if not self.stop_event.is_set():
                    error_message = str(e)
                    logging.error(f"Script error: {error_message}")
                    self.root.after(0, lambda msg=error_message: self.toStatus(f"Lỗi: {msg}"))
                    if self.isLoop:
                        logging.info("Retrying after error in loop mode")
                        time.sleep(5)
                        self.root.after(0, lambda: self.toStatus("Tiến hành thử lại."))
                        if driver:
                            try:
                                driver.quit()
                            except:
                                pass
                        script_thread()  # Retry the entire process
            finally:
                if driver:
                    try:
                        logging.info("Closing WebDriver")
                        driver.quit()
                    except Exception as e:
                        logging.error(f"Error closing WebDriver: {str(e)}")
                if not self.stop_event.is_set():
                    logging.info("Enabling Start button")
                    self.root.after(0, lambda: self.buttonStart.configure(state="normal"))
            logging.info("Closing thread")

        thread = threading.Thread(target=script_thread, daemon=True)
        thread.start()

    def on_closing(self):
        # Handle window close event.
        logging.info("Window close event triggered")
        if messagebox.askokcancel("Thoát", "Bạn có chắc muốn thoát?"):
            logging.info("User confirmed exit")
            self.shutdown()
            self.root.destroy()
        else:
            logging.info("User cancelled exit")

    def run(self):
        # Run the application.
        logging.info("###Program started###")
        self.root.mainloop()
        logging.info("###Program ended###")

if __name__ == "__main__":
    logging.info("Loading functions")
    root = ctk.CTk()
    app = App(root)
    app.run()