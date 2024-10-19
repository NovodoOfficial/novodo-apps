import os
import sys
from PIL import Image, ImageDraw, ImageFont
import spidev
import RPi.GPIO as GPIO
import time
import json
import tempfile

args = sys.argv[1:]

def respond(response):
    temp_dir = tempfile.gettempdir()
    response_path = os.path.join(temp_dir, 'response.json')
    
    with open(response_path, 'w') as f:
        json.dump(response, f)

    sys.exit(0)

# Constants for the SSD1309 display
SSD1309_WIDTH = 128
SSD1309_HEIGHT = 64
SSD1309_NUM_PAGES = SSD1309_HEIGHT // 8

# Command definitions
SSD1309_COMMAND = 0x00
SSD1309_DATA = 0x01

class SSD1309:
    def __init__(self, spi_bus=0, spi_device=0, dc_pin=25, reset_pin=27, cs_pin=8):
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = 8000000  # 8 MHz
        self.spi.mode = 0  # SPI mode 0

        self.dc_pin = dc_pin
        self.reset_pin = reset_pin
        self.cs_pin = cs_pin

        # Set up GPIO
        GPIO.setwarnings(False)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.dc_pin, GPIO.OUT)
        GPIO.setup(self.reset_pin, GPIO.OUT)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.output(self.cs_pin, GPIO.HIGH)  # Start with CS high

        # Initialize the display
        self.reset()
        self.init_display()

        # Initialize the display buffer
        self.buffer = [0] * (SSD1309_WIDTH * SSD1309_NUM_PAGES)

    def reset(self):
        GPIO.output(self.reset_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.reset_pin, GPIO.HIGH)
        time.sleep(0.1)

    def init_display(self):
        commands = [
            0xAE,  # Display OFF
            0xD5, 0x80,  # Set Display Clock Divide Ratio/Oscillator Frequency
            0xA8, 0x3F,  # Set Multiplex Ratio
            0xD3, 0x00,  # Set Display Offset
            0x40,  # Set Display Start Line
            0x8D, 0x14,  # Charge Pump Setting
            0x20, 0x00,  # Set Memory Addressing Mode
            0xA1,  # Set Segment Re-Map
            0xC8,  # Set COM Output Scan Direction
            0xDA, 0x12,  # Set COM Pins Hardware Configuration
            0x81, 0x7F,  # Set Contrast Control
            0xD9, 0x22,  # Set Pre-Charge Period
            0xDB, 0x20,  # Set VCOMH Deselect Level
            0xA4,  # Entire Display ON
            0xA6,  # Set Normal Display
            0xAF   # Display ON
        ]
        for cmd in commands:
            self.send_command(cmd)

    def send_command(self, cmd):
        GPIO.output(self.dc_pin, GPIO.LOW)
        GPIO.output(self.cs_pin, GPIO.LOW)
        self.spi.xfer2([cmd])
        GPIO.output(self.cs_pin, GPIO.HIGH)

    def send_data(self, data):
        GPIO.output(self.dc_pin, GPIO.HIGH)
        GPIO.output(self.cs_pin, GPIO.LOW)
        self.spi.xfer2([data])
        GPIO.output(self.cs_pin, GPIO.HIGH)

    def update_display(self):
        for page in range(SSD1309_NUM_PAGES):
            self.send_command(0xB0 + page)  # Set page address
            self.send_command(0x00)        # Set column address lower nibble to 0
            self.send_command(0x10)        # Set column address higher nibble to 0
            for x in range(SSD1309_WIDTH):
                self.send_data(self.buffer[x + page * SSD1309_WIDTH])

    def clear(self):
        self.buffer = [0] * (SSD1309_WIDTH * SSD1309_NUM_PAGES)
        self.update_display()

    def set_pixel(self, x, y, color):
        if x < 0 or x >= SSD1309_WIDTH or y < 0 or y >= SSD1309_HEIGHT:
            return

        page = y // 8
        bit = 1 << (y % 8)

        index = x + page * SSD1309_WIDTH

        if color:
            self.buffer[index] |= bit
        else:
            self.buffer[index] &= ~bit

    def draw_box(self, x1, y1, x2, y2, color=True):
        """Draws a filled rectangular box defined by the top-left (x1, y1) and bottom-right (x2, y2) corners."""
        # Loop through each pixel within the defined rectangle
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.set_pixel(x, y, color)
        
    def draw_line(self, x1, y1, x2, y2, color=True, thickness=1):
        """Draw a line from (x1, y1) to (x2, y2) with a specified thickness."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        # Draw circles along the line to create a thicker line effect
        while True:
            # Draw a circle at the current point with the specified thickness
            self.draw_circle(x1, y1, thickness, color=color)

            if x1 == x2 and y1 == y2:
                break
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def draw_circle(self, x, y, diameter, color=True):
        """Draw a filled circle at (x, y) with the specified diameter."""
        radius = diameter // 2
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    self.set_pixel(x + dx, y + dy, color)

    def draw_image(self, image_path, x_offset=0, y_offset=0, fac=1):
        with Image.open(image_path) as img:
            img = img.convert("RGBA")  # Convert to RGBA if not already

            # Resize the image by the factor 'fac'
            img_width, img_height = img.size
            new_width = int(img_width * fac)
            new_height = int(img_height * fac)  # Fixing the typo here

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            for y in range(new_height):
                for x in range(new_width):
                    display_x = x + x_offset
                    display_y = y + y_offset

                    if display_x < 0 or display_x >= SSD1309_WIDTH or display_y < 0 or display_y >= SSD1309_HEIGHT:
                        continue

                    r, g, b, a = img.getpixel((x, y))
                    if a > 127:  # Check if the alpha (opacity) is greater than 50%
                        self.set_pixel(display_x, display_y, color=True)
    
    def draw_text(self, text, x, y, font_path=os.path.abspath("Arial.ttf"), font_size=12, duration=0, width=0, get_height=False):
        if not text.strip():
            return 0  # Return 0 if the text is empty

        # Create an image to draw on
        img = Image.new("1", (SSD1309_WIDTH, SSD1309_HEIGHT), 0)  # Monochrome 1-bit image
        draw = ImageDraw.Draw(img)

        # Load a font
        font = ImageFont.truetype(font_path, font_size)

        current_x = x
        current_y = y
        words = text.split(' ')  # Split the text into words for wrapping
        max_height = 0  # Variable to track the maximum height of the drawn text

        for word in words:
            while word:  # Process the word in case it needs to be split
                # Get the bounding box for the word to calculate its width
                bbox = draw.textbbox((current_x, current_y), word, font=font)
                word_width = bbox[2] - bbox[0]  # Width is bbox[2] - bbox[0]

                if current_x + word_width > width and width > 0:
                    # If the word is too wide, start shrinking it character by character
                    temp_word = word
                    while current_x + word_width > width and len(temp_word) > 1:
                        temp_word = temp_word[:-1]  # Remove one character at a time
                        bbox = draw.textbbox((current_x, current_y), temp_word + "-", font=font)
                        word_width = bbox[2] - bbox[0]  # Recalculate word width for shortened word

                    # Draw the shortened word with a hyphen
                    draw.text((current_x, current_y), temp_word + "-", font=font, fill=255)
                    current_x = x
                    current_y += font_size  # Move to the next line
                    max_height = max(max_height, bbox[3] - bbox[1])  # Update max height

                    word = word[len(temp_word):]  # Update word to the remaining part
                else:
                    # Draw the word if it fits
                    draw.text((current_x, current_y), word, font=font, fill=255)
                    current_x += word_width + draw.textbbox((0, 0), " ", font=font)[2]  # Space between words
                    word = ""  # Word has been fully drawn, exit the loop

        # Final transfer of the image to the buffer after drawing all text
        if get_height != True:
            self._transfer_image_to_buffer(img)

        # Return the total height of the drawn text
        return current_y - y + max_height  # Total height from starting y to the final y position plus the height of the last line

    def _transfer_image_to_buffer(self, img):
        if not img:
            return

        # Ensure the buffer has the correct size
        if len(self.buffer) != SSD1309_NUM_PAGES * SSD1309_WIDTH:
            self.buffer = [0] * (SSD1309_NUM_PAGES * SSD1309_WIDTH)  # Initialize the buffer if not done

        for page in range(SSD1309_NUM_PAGES):
            for x in range(SSD1309_WIDTH):
                byte_value = 0
                for bit in range(8):
                    pixel_y = page * 8 + bit
                    if pixel_y < SSD1309_HEIGHT:  # Ensure we don't go out of bounds
                        pixel = img.getpixel((x, pixel_y))
                        if pixel:  # Only set buffer pixel if image pixel is non-zero
                            byte_value |= (1 << bit)
                self.buffer[page * SSD1309_WIDTH + x] |= byte_value  # Retain current buffer values

Display = SSD1309()
