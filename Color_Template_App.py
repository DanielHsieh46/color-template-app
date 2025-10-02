#!/usr/bin/env python
# coding: utf-8

# In[3]:


import sys, os, json
from PyQt6 import QtWidgets, QtGui, QtCore

# === File storage ===
PALETTE_FILE = "palettes.json"

def load_palettes():
    if os.path.exists(PALETTE_FILE):
        with open(PALETTE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_palettes(palettes):
    with open(PALETTE_FILE, "w", encoding="utf-8") as f:
        json.dump(palettes, f, indent=4)

# === Helpers ===
def clamp(v, lo, hi): return max(lo, min(hi, v))
def round_to_step(v, step=8): return int((v + step / 2) // step * step)
def compute_gutter(width): return round_to_step(clamp(int(width * 0.15), 40, 260), step=8)

def hex_to_rgb(hex_color: str):
    hex_color = hex_color.strip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def is_light(hex_color: str) -> bool:
    r, g, b = hex_to_rgb(hex_color)
    lum = 0.2126 * (r/255) + 0.7152 * (g/255) + 0.0722 * (b/255)
    return lum > 0.65

def text_color_for(bg_hex: str) -> str:
    return "#000000" if is_light(bg_hex) else "#FFFFFF"


# === Add Palette Dialog ===
class AddPaletteDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Palette")

        layout = QtWidgets.QVBoxLayout(self)
        
        self.resize(400, 120)   

        self.name_input = QtWidgets.QLineEdit(self)
        self.name_input.setPlaceholderText("Palette name")
        layout.addWidget(self.name_input)

        self.colors_input = QtWidgets.QLineEdit(self)
        self.colors_input.setPlaceholderText("Colors (comma separated, e.g. #FF0000,#00FF00)")
        layout.addWidget(self.colors_input)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        name = self.name_input.text().strip()
        colors = [c.strip() for c in self.colors_input.text().split(",") if c.strip()]
        return name, colors

# === Custom Dropdown (QMenu-based, non-blocking) ===
class CustomDropdown(QtWidgets.QPushButton):
    valueChanged = QtCore.pyqtSignal(str)

    def __init__(self, values, parent=None):
        super().__init__(values[0] if values else "", parent)
        self.values = values
        self.actions = []
        self.menu = QtWidgets.QMenu(self)
        self.set_menu_style()
        self.rebuild_menu(values)

        self.setFixedHeight(40)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                border-radius: 6px;
                border: 1px solid #3a3a3a;
                text-align: left;
                padding-left: 12px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)

    def set_menu_style(self):
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 4px 0;
            }
            QMenu::item {
                padding: 6px 12px;
                background: transparent;
            }
            QMenu::item:selected {
                background: #3d3d3d;
                color: white;
            }
        """)

    def rebuild_menu(self, values):
        self.menu.clear()
        self.actions.clear()
        for v in values:
            act = self.menu.addAction(v)
            act.triggered.connect(lambda _, val=v: self._select_value(val))
            self.actions.append(act)
        if values:
            self.setText(values[0])

    def _select_value(self, value: str):
        self.setText(value)
        self.valueChanged.emit(value)

    def mousePressEvent(self, event):
        pos = self.mapToGlobal(self.rect().bottomLeft())
        self.menu.setMinimumWidth(self.width())
        self.menu.popup(pos)

# === Main Window ===
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Color Template")
        self.setMinimumSize(400, 300)
        self.resize(800, 600)  # Default size

        # Load palettes
        self.palettes = load_palettes()
        if not self.palettes:  # seed defaults
            self.palettes = {
                "Pastel": ["#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF"],
                "Dark Mode": ["#121212", "#1E1E1E", "#3A3A3A", "#BB86FC", "#03DAC6"],
                "Brand Colors": ["#0070F3", "#FF4081", "#FFC107", "#4CAF50"],
            }
            save_palettes(self.palettes)

        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        self.outer_layout = QtWidgets.QVBoxLayout(central)
        self.outer_layout.setContentsMargins(40, 0, 40, 0)
        self.outer_layout.setSpacing(0)
        self.outer_layout.addStretch(1)

        self.content = QtWidgets.QFrame(central)
        self.outer_layout.addWidget(self.content, 0)
        self.outer_layout.addStretch(1)
        self.content_layout = QtWidgets.QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 40, 0, 20)
        self.content_layout.setSpacing(16)

        # === Custom Title (West Coast font) ===
        font_id = QtGui.QFontDatabase.addApplicationFont("Pacifico-Regular.ttf")
        if font_id != -1:
            font_family = QtGui.QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            font_family = "Arial"  

        self.title_label = QtWidgets.QLabel("Color Template")
        title_font = QtGui.QFont(font_family, 32)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #FFFFFF;")  
        self.content_layout.addWidget(self.title_label)
        self.content_layout.addSpacing(10)

        # Dropdown
        self.dropdown = CustomDropdown(list(self.palettes.keys()), self.content)
        self.dropdown.valueChanged.connect(self.show_palette)
        self.content_layout.addWidget(self.dropdown)

        # Add/Remove Palette buttons
        # Add/Remove Palette + Color buttons
        btns_row = QtWidgets.QHBoxLayout()
        
        # Add Palette
        self.add_btn = QtWidgets.QPushButton("+ Add Palette")
        self.add_btn.setFixedHeight(40)
        self.add_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.add_btn.clicked.connect(self.add_palette)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                border-radius: 6px;
                border: 1px solid #3a3a3a;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        btns_row.addWidget(self.add_btn)
        
        # ± Color (menu button)
        self.color_btn = QtWidgets.QPushButton(" Add/Remove Color")
        self.color_btn.setFixedHeight(40)
        self.color_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.color_btn.setMenu(self._build_color_menu())
        self.color_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                border-radius: 6px;
                border: 1px solid #3a3a3a;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton::menu-indicator {
                image: none;
                width: 0px;
                height: 0px;
            }

        """)
        btns_row.addWidget(self.color_btn)
        
        # Remove Palette
        self.remove_btn = QtWidgets.QPushButton("– Remove Palette")
        self.remove_btn.setFixedHeight(40)
        self.remove_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.remove_btn.clicked.connect(self.remove_palette)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                border-radius: 6px;
                border: 1px solid #3a3a3a;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        btns_row.addWidget(self.remove_btn)
        
        self.content_layout.addLayout(btns_row)


        # Scroll area for color buttons
        self.scroll_area = QtWidgets.QScrollArea(self.content)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.buttons_container = QtWidgets.QWidget()
        self.buttons_layout = QtWidgets.QVBoxLayout(self.buttons_container)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(8)

        self.scroll_area.setWidget(self.buttons_container)
        self.content_layout.addWidget(self.scroll_area)

        # Status label
        self.status_label = QtWidgets.QLabel("", self.content)
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        font = self.status_label.font()
        font.setPointSize(12)
        self.status_label.setFont(font)
        self.content_layout.addWidget(self.status_label)

        self._buttons = []
        self.show_palette(self.dropdown.text())

        # Responsive padding
        self._resize_timer = QtCore.QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self.apply_responsive_padding)
        self._last_gutter = 40
        QtCore.QTimer.singleShot(0, self.apply_responsive_padding)

    def copy_color(self, hex_color: str):
        QtGui.QGuiApplication.clipboard().setText(hex_color)
        self.status_label.setText(f"{hex_color} copied!")
        self.status_label.setStyleSheet(f"color: {hex_color};")
    
        # Cancel previous timer if still running
        if hasattr(self, "_clear_timer") and self._clear_timer.isActive():
            self._clear_timer.stop()
    
        # Start a new timer
        self._clear_timer = QtCore.QTimer(self)
        self._clear_timer.setSingleShot(True)
        self._clear_timer.timeout.connect(self._clear_status)
        self._clear_timer.start(1500)


    def _clear_status(self):
        self.status_label.setText("")
        self.status_label.setStyleSheet("")

    def show_palette(self, name: str):
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._buttons.clear()

        colors = self.palettes.get(name, [])
        for color in colors:
            btn = QtWidgets.QPushButton(color, self.buttons_container)
            btn.setFixedHeight(40)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            fg = text_color_for(color)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: {fg};
                    border-radius: 8px;
                    text-align: center;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    border: 2px solid #FFFFFF;
                }}
            """)
            btn.clicked.connect(lambda _, c=color: self.copy_color(c))
            self.buttons_layout.addWidget(btn)
            self._buttons.append(btn)

        self.buttons_layout.addStretch(1)

    def add_palette(self):
        dialog = AddPaletteDialog(self)
        if dialog.exec():
            name, colors = dialog.get_data()
            if name and colors:
                self.palettes[name] = colors
                save_palettes(self.palettes)
                self.dropdown.rebuild_menu(list(self.palettes.keys()))

    def remove_palette(self):
        current = self.dropdown.text()
        if current and current in self.palettes:
            reply = QtWidgets.QMessageBox.warning(
                self,
                "Remove Palette",
                f"Are you sure you want to remove the palette '{current}'?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                del self.palettes[current]
                save_palettes(self.palettes)
                self.dropdown.rebuild_menu(list(self.palettes.keys()))
                if self.palettes:
                    self.show_palette(next(iter(self.palettes)))
                else:
                    self.show_palette("")


    def apply_responsive_padding(self):
        w = max(1, self.width())
        gutter = compute_gutter(w)
        if gutter != self._last_gutter:
            self.outer_layout.setContentsMargins(gutter, 0, gutter, 0)
            self._last_gutter = gutter
    def resizeEvent(self, event):
        super().resizeEvent(event)
    
        base_size = 32
        width = self.width()
    
        scale = width / 800   
        new_size = max(20, int(base_size * scale))  
    
        font = self.title_label.font()
        font.setPointSize(new_size)
        self.title_label.setFont(font)

    def add_color_to_palette(self):
        current = self.dropdown.text()
        if not current or current not in self.palettes:
            QtWidgets.QMessageBox.warning(self, "No Palette Selected", "Please select a palette first.")
            return

        color, ok = QtWidgets.QInputDialog.getText(
            self,
            "Add Color",
            "Enter a hex color (e.g. #FF0000):"
        )
        if ok and color:
            color = color.strip()
            if not (color.startswith("#") and len(color) == 7):
                QtWidgets.QMessageBox.warning(self, "Invalid Color", "Please enter a valid hex color like #RRGGBB.")
                return
            self.palettes[current].append(color)
            save_palettes(self.palettes)
            self.show_palette(current)

    def remove_color_from_palette(self):
        current = self.dropdown.text()
        if not current or current not in self.palettes or not self.palettes[current]:
            QtWidgets.QMessageBox.warning(self, "No Colors", "No colors available to remove.")
            return

        color, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Remove Color",
            "Select a color to remove:",
            self.palettes[current],
            0,
            False
        )
        if ok and color:
            self.palettes[current].remove(color)
            save_palettes(self.palettes)
            self.show_palette(current)

    def _build_color_menu(self):
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 4px 0;
            }
            QMenu::item {
                padding: 6px 16px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)
    
        add_action = menu.addAction("+ Add Color")
        add_action.triggered.connect(self.add_color_to_palette)
    
        remove_action = menu.addAction("– Remove Color")
        remove_action.triggered.connect(self.remove_color_from_palette)
    
        # 👇 Force menu width to match button
        menu.aboutToShow.connect(lambda: menu.setFixedWidth(self.color_btn.width()))
    
        return menu





def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark Fusion Palette
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#0f0f10"))
    palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#1e1e1e"))
    palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#2b2b2b"))
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#EDEDED"))
    palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#EDEDED"))
    palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#2b2b2b"))
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#EDEDED"))
    palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#3d3d3d"))
    palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#FFFFFF"))
    app.setPalette(palette)

    # Global QLineEdit style
    app.setStyleSheet("""
        QLineEdit {
            color: white;
            background-color: #2b2b2b;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
        }
        QLineEdit::placeholder {
            color: #AAAAAA;
        }
    """)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


# In[ ]:




