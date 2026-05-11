import customtkinter as ctk
from PIL import Image
import os
import logging

# Configure logging for style.py
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

current_dir = os.path.dirname(os.path.abspath(__file__))
license = [
    'MlBBQ1gtMXZSV0NSYzFsLW5L',
    'MHI1NWx5dzg4Vk16b0JW',
    'XzU3dmtjZ2d4YXp1Zko4SmY1N',
    '2w2RnRKcHQ1R0dpM0YyQ1',
    'pLZV93bVk1YnRJaXJkbkthbjk='
]

class Config:
    def __init__(self):
        logging.info("Initializing Config class")
    
    class Colors:
        transparent = "transparent"
        # background
        ofFrame1 = "#a7a29e"
        ofFrame2 = "#dad5cf"
        ofFrame3 = "#001500"
        ofScrew = "#6b6765"
        ofFrameBorder = "#2f2e2c"
        # button
        ofButton = "#f0e9e2"
        ofHoverButton = "#a7a29e"
        ofHideMK = "#54703c"
        ofPressLoop = "#6b6765"
        ofPressHideMK = "#6b6765"
        # entry
        ofMSV = "#54703c"
        ofMK = "#54703c"
        ofMLHP = "transparent"
        ofBorderMSV = "#2f2e2c"
        ofBorderMK = "#2f2e2c"
        ofBorderMLHP = "#03B500"
        # text
        ofTextMSVMK = "#ffffff"
        ofTextMLHP = "#03B500"
        ofTextStatus = "#03B500"

    class Icons:
        @staticmethod
        def load_icon(name, size=(20, 20)):
            path = os.path.join(current_dir, "assets", f"{name}.png")
            logging.info(f"Loading assets: {path}")
            if not os.path.exists(path):
                logging.error(f"Icon file {path} not found")
                raise FileNotFoundError(f"Icon file {path} not found")
            return ctk.CTkImage(Image.open(path), size=size)

        on = load_icon("on")
        stop = load_icon("stop")
        start = load_icon("start")
        loop = load_icon("loop")