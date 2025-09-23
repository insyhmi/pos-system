from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QCheckBox, QHBoxLayout, QSpacerItem, 
                            QSizePolicy)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter, QBrush, QPixmap, QLinearGradient

class GlassmorphismLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Glassmorphism Login")
        self.setStyleSheet("background: url('assets/test.png')")
        self.setFixedSize(400, 500)
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30) # Left Top Right Bottom
        layout.setSpacing(20)
        
        # Title
        self.title = QLabel("Login")
        self.title.setStyleSheet("""
            font-size: 32px;
            color: white;
            font-weight: bold;
            margin-bottom: 20px;
        """)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Email field
        self.email_field = AnimatedInputField("Username")
        self.email_field.setPlaceholderText("")
        
        # Password field
        self.password_field = AnimatedInputField("Password")
        self.password_field.setPlaceholderText("")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        
       
        # Forgot password link
        self.forgot_link = QLabel('')
        self.forgot_link.setOpenExternalLinks(False)
        
        # Remember me row
        remember_row = QHBoxLayout()
        remember_row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        remember_row.addWidget(self.forgot_link)
        
        # Login button
        self.login_btn = QPushButton("Log In")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: black;
                font-weight: 600;
                border: none;
                padding: 12px 20px;
                border-radius: 3px;
                font-size: 16px;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                color: white;
                border-color: white;
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        
        # Register link
        
        # Add widgets to layout
        layout.addWidget(self.title)
        layout.addWidget(self.email_field)
        layout.addWidget(self.password_field)
        layout.addLayout(remember_row)
        layout.addWidget(self.login_btn)
        
        self.setLayout(layout)
        
        # Set glass effect stylesheet
        self.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0);
            }
        """)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create glass effect
        glass = QWidget(self)
        glass.setGeometry(self.rect())
        
        # Draw rounded rectangle with glass effect
        brush = QBrush(QColor(255, 255, 255, 20))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)

class AnimatedInputField(QLineEdit):
    def __init__(self, label_text):
        super().__init__()
        self.label = QLabel(label_text, self)
        self.label.setStyleSheet("""
            color: white;
            font-size: 16px;
        """)
        self.label.move(0, (self.height() - self.label.height()) // 2)
        
        self.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                border-bottom: 2px solid #ccc;
                color: white;
                font-size: 16px;
                padding: 5px 0;
                margin-bottom: 5px;
            }
        """)
        
        # Animation setup
        self.animation = QPropertyAnimation(self.label, b"pos")
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setDuration(200)
        
    def focusInEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self.label.pos())
        self.animation.setEndValue(self.label.pos() - self.label.pos().transposed() * 0 + self.label.pos().transposed() * 0)
        self.animation.setEndValue(self.label.pos() + self.label.pos().transposed() * 0 - self.label.pos().transposed() * 0 + self.label.pos().transposed() * 0)
        self.label.move(0, -10)
        self.label.setStyleSheet("""
            color: white;
            font-size: 8px;
            margin-top: 8px;
        """)
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        if not self.text():
            self.animation.stop()
            self.animation.setStartValue(self.label.pos())
            self.animation.setEndValue(self.label.pos() - self.label.pos().transposed() * 0 + self.label.pos().transposed() * 0)
            self.label.move(0, (self.height() - self.label.height()) // 2)
            self.label.setStyleSheet("""
                color: white;
                font-size: 16px;
            """)
        super().focusOutEvent(event)
    
    def resizeEvent(self, event):
        if not self.hasFocus() and not self.text():
            self.label.move(0, (self.height() - self.label.height()) // 2)
        super().resizeEvent(event)

if __name__ == '__main__':
    app = QApplication([])
    login = GlassmorphismLogin()
    login.show()
    app.exec()