# Display

## About

Library to show graphics on the SSD1309

(First library for the Novodo Glass system!)

## Usage

### System commands

| Command                   | Params                                         | Description                                              |
|---------------------------|------------------------------------------------|----------------------------------------------------------|
| \_\_init\_\_              | spi_bus, spi_device, dc_pin, reset_pin, cs_pin | Setup GPIO and SPI.                                      |
| reset                     | None                                           | Resets display.                                          |
| init_display              | None                                           | Initialises display.                                     |
| send_command              | cmd                                            | Send a command to the display.                           |
| send_data                 | data                                           | Send data to the display.                                |
| _transfer_image_to_buffer | img                                            | Transfer an image to the buffer (used for text drawing). |

### App commands

| Command        | Params                                                        | Description                                                                                                                      |
|----------------|---------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| update_display | None                                                          | Refresh the display to apply changes.                                                                                            |
| clear          | None                                                          | Clear the display.                                                                                                               |
| set_pixel      | x, y, color                                                   | Set a pixel to either True of False for on and off correspondingly.                                                              |
| draw_box       | x1, y1, x2, y2, color                                         | Draw a box with a fill of either True of False for on and off correspondingly.                                                   |
| draw_line      | x1, y1, x2, y2, color, thickness                              | Draw a box with a color of either True of False for on and off correspondingly with a thickness option.                          |
| draw_cirlce    | x, y, diameter, color                                         | Draw a circle with a certain diameter and a fill of either True of False for on and off correspondingly.                         |
| draw_image     | image_path, x_offset, y_offset, fac                           | Draw an image (from a path) at a certain size (fac).                                                                             |
| draw_text      | text, x, y, font_path, font_size, duration, width, get_height | Draw text on the screen with a custom font, width (for text wrap). If get_height is True, it will return the height of the text. |

### Note

The draw_text - font_size and duration are currently not working