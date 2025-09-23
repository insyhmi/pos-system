import hashlib
import mysql.connector
import sys
import os
import json
from datetime import datetime, date
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QMessageBox, QSpacerItem, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView 
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal, QDateTime, QDate, QTime
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont, QPixmap, QShortcut, QKeySequence
from conn import *

APP_PATH = os.path.dirname(__file__)
ASSET_FOLDER = os.path.join(APP_PATH, 'assets')

# DATABASE CONNECTION 

try:
    db = mysql.connector.connect(
        host=r_host,
        user=r_username,
        password=r_password,
        database=r_database
    )
    cursor = db.cursor()
except mysql.connector.errors.DatabaseError: 
    print(f"Unable to connect to database '{r_database}' on host '{r_host}'")
    sys.exit(0)

def hash_password(pword):
    hash_object = hashlib.sha256(pword.encode('utf-8'))
    return hash_object.hexdigest()

#CONFIG FILE 

try:
    with open('config.json', 'r') as config_file:
        CONFIG = json.load(config_file)
except:
    print(f"Unable to parse configuration file 'config.json'")
    sys.exit(0)

# FRONTEND
# 
class CashierMainApp(QMainWindow):
    def __init__(self, username, full_name):
        super().__init__()
        # Initialize global variables
        self.CART = dict()
        self.TOTAL = 0.0
        self.PAID = 0.0
        self.TOGGLE_REMOVE_ITEM = False
        self.FULL_NAME = full_name
        self.USERNAME = username
        self.QDATETIME = QDateTime(QDate(1970, 1, 1), QTime(0,0,1))
        self.TRANSACTION_NO = 0

        # Cart dictionary format -> {item : metadata -> list()}; metadata = [quantity -> int, price_per_unit -> float, ean13 -> string]
        self.setWindowTitle(CONFIG['app_title'])
        # Main wrapper widget
        wrapper = QWidget()
        self.setCentralWidget(wrapper)
        # Layouts
        main_layout = QHBoxLayout()
        self.column1_layout = QVBoxLayout()
        column2_cashier_layout = QVBoxLayout()
        column2_paymentoption_layout = QVBoxLayout()
        column2_payment_layout = QVBoxLayout()
        column2_complete_layout = QVBoxLayout()
        self.column2_cashier_widget = QWidget()
        self.column2_paymentoption_widget = QWidget()
        self.column2_payment_widget = QWidget()
        self.column2_complete_widget = QWidget()

        # Column 1 Cart Table 
        self.cart_label = QLabel("Cart:")
        self.cart_label.setFont(QFont("Segoe UI", 20))
        self.column1_layout.addWidget(self.cart_label)
        self.table = QTableWidget(0,3)
        self.table.setHorizontalHeaderLabels(["Product Name", "Quantity", "Price (RM)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Disable user editing of the table directly

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setFont(QFont("Segoe UI", 12))
        header = self.table.horizontalHeader()
        header.setStyleSheet("""background-color: rgb(31, 224, 99); font-size: 15px; text-align: left; color: black;""")

        # Cell padding-like effect via setting column width and font size idk
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setFont(QFont("Segoe UI", 12))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.column1_layout.addWidget(self.table)

        # Column 2 transaction information
        self.column2_cashier_widget.setStyleSheet("""
            QLineEdit, QTextEdit{
                font-size: 13px;  
                border: none;
                border-bottom: 2px solid rgb(31, 224, 99);
                border-radius: 5px;
                padding: 2px 5px;
                margin: 10px 0px 15px;                          
            }
            QLineEdit{
            font-size: 18px;
            }
            QPushButton {
                padding: 5px 0px;
                border: 1px solid rgb(31, 224, 99);
                font-size: 14px;
            }
            QPushButton:hover{
                color: white;
                background: rgb(24, 180, 79);
            }
        """)
        self.label_cashier = QLabel("Cashier:")
        self.label_cashier.setFont(QFont("Segoe UI", 13))
        self.cashier_name = QLineEdit(f"Mr. {self.FULL_NAME}")
        self.cashier_name.setReadOnly(True)
        self.label_last_scan = QLabel("Last Scan:")
        self.label_last_scan.setFont(QFont("Segoe UI", 13))
        self.last_scan = QTextEdit()
        self.last_scan.setReadOnly(True)
        self.label_item_price = QLabel("Item Price: RM")
        self.label_item_price.setFont(QFont("Segoe UI", 13))
        self.item_price = QLineEdit("0.00")
        self.item_price.setReadOnly(True)
        self.label_total = QLabel("Total: RM")
        self.label_total.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.total_input = QLineEdit("0.00")
        self.total_input.setReadOnly(True)
        self.button_row = QHBoxLayout()
        self.remove_button = QPushButton("Remove item")
        self.remove_button.clicked.connect(self.toggle_remove_item)
        self.clear_button = QPushButton("Clear cart")
        self.clear_button.clicked.connect(self.clear_cart)
        self.logout_button = QPushButton("Log out")
        self.logout_button.clicked.connect(self.logout)
        self.button_row.addWidget(self.remove_button)
        self.button_row.addWidget(self.clear_button)
        self.button_row.addWidget(self.logout_button)

        # Payment shortcut - Ctrl + P
        
        self.label_barcode = QLabel("Scan item to add:")
        self.label_barcode.setFont(QFont("Segoe UI", 13))
        self.ean13_input = EAN13Input(self)
        self.total_input.setStyleSheet("font-size: 25px;")
        self.ean13_input.setStyleSheet("border: 2px solid rgb(47, 237, 171); padding: 7px 5px; margin-bottom: 5px;")
        self.payment_button = QPushButton("Pay")
        self.payment_button.clicked.connect(self.payment_widget)
        self.payment_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.payment_shortcut.activated.connect(self.payment_widget)
        column2_cashier_layout.addWidget(self.label_cashier)
        column2_cashier_layout.addWidget(self.cashier_name)
        column2_cashier_layout.addWidget(self.label_last_scan)
        column2_cashier_layout.addWidget(self.last_scan)
        column2_cashier_layout.addWidget(self.label_item_price)
        column2_cashier_layout.addWidget(self.item_price)
        column2_cashier_layout.addWidget(self.label_total)
        column2_cashier_layout.addWidget(self.total_input)
        column2_cashier_layout.addLayout(self.button_row)
        column2_cashier_layout.addWidget(self.label_barcode)
        column2_cashier_layout.addWidget(self.ean13_input)
        column2_cashier_layout.addWidget(self.payment_button)

        self.column2_cashier_widget.setLayout(column2_cashier_layout)
        self.column2_payment_widget.setStyleSheet("""
            QPushButton{
                border: 1px solid rgb(31, 224, 99);
                font-size: 25px;
            }
            QPushButton:hover {
                color: white;
                background: rgb(24, 180, 79);
            }
""")
        amount_widget = QWidget()
        amount_layout = QVBoxLayout(amount_widget)
        amount_layout.setContentsMargins(0, 0, 0, 0)
        amount_layout.setSpacing(0)
        self.amount_label = QLabel("Total: ")
        self.amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.amount_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        amount_layout.addWidget(self.amount_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        functional_button = QHBoxLayout()
        functional_button.setContentsMargins(0, 0, 0, 0)
        functional_button.setSpacing(5)
        self.back = QPushButton("Back")
        self.back.setStyleSheet("font-size: 15px; padding: 5px 0px")
        self.back.clicked.connect(self.close_payment_widget)
        self.exact = QPushButton("Exact Amount")
        self.exact.clicked.connect(self.exact_amout_payment)
        self.exact.setStyleSheet("font-size: 15px; padding: 5px 0px")
        functional_button.addWidget(self.back)
        functional_button.addWidget(self.exact)
        amount_layout.addLayout(functional_button)

        payment_input_label = QLabel("Amount paid: RM")
        payment_input_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        payment_input_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        payment_input_label.setStyleSheet("font-size: 15px; margin-top: 15px;padding: 0px;border: none;")
        amount_layout.addWidget(payment_input_label)

        self.payment_input = QLineEdit()
        self.payment_input.setStyleSheet("""
            font-size: 25px;
            padding: 10px;
            margin-top: 10px;
        """)
        self.payment_input.setText("0.00")
        self.payment_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        amount_layout.addWidget(self.payment_input)

        options_widget = QWidget()
        options_layout = QHBoxLayout(options_widget)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(0)

        bottom_widget = QWidget()
        grid_layout = QGridLayout(bottom_widget)
        grid_layout.setContentsMargins(2,2,2,2)
        grid_layout.setSpacing(0)
        
        # Create number buttons 0-9
        self.num_buttons = []
        for i in range(1, 10):  # Buttons 1-9
            btn = QPushButton(str(i))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda checked, num=i: self.enter_num(num))
            grid_layout.addWidget(btn, (i-1)//3, (i-1)%3)
            self.num_buttons.append(btn)
        
        btn0 = QPushButton("0") # Button 0
        btn0.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn0.clicked.connect(lambda: self.enter_num(0))
        grid_layout.addWidget(btn0, 3, 1)
        btn_ok = QPushButton("OK")
        btn_ok.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn_ok.clicked.connect(self.process_payment)
        grid_layout.addWidget(btn_ok, 3, 2)
        btn_backspace = QPushButton("<")
        btn_backspace.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn_backspace.clicked.connect(lambda: self.erase_num())
        grid_layout.addWidget(btn_backspace, 3, 0)

        column2_payment_layout.addWidget(amount_widget, 1)
        column2_payment_layout.addWidget(bottom_widget, 1)
        self.column2_payment_widget.setLayout(column2_payment_layout)
        
        # Configure grid rows/columns to expand
        for row in range(4):
            grid_layout.setRowStretch(row, 1)
        for col in range(3):
            grid_layout.setColumnStretch(col, 1)     

        self.column2_complete_widget.setStyleSheet("""
            QPushButton{
                border: 1px solid rgb(31, 224, 99);
                font-size: 25px;
            }
            QPushButton:hover {
                color: white;
                background: rgb(24, 180, 79);
            }""")
        payment_complete_header = QLabel("Payment Complete")
        payment_complete_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        payment_complete_header.setFont(QFont("Segoe UI", 19, QFont.Weight.Bold))
        payment_complete_header.setStyleSheet("margin-top: 50px; margin-bottom: 50px;")
        payment_details = QWidget()
        payment_details_layout = QGridLayout(payment_details)
        payment_details_layout.setContentsMargins(10,0,0,10)

        date_label = QLabel("Date: ")
        date_label.setFont(QFont("Segoe UI", 13))
        time_label = QLabel("Time: ")
        time_label.setFont(QFont("Segoe UI", 13))
        receipt_no_label = QLabel("Receipt # : ")
        receipt_no_label.setFont(QFont("Segoe UI", 13))
        total_label = QLabel("Total : ")
        total_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        amount_paid_label = QLabel("Amount paid : ")
        amount_paid_label.setFont(QFont("Segoe UI", 13))
        balance_label = QLabel("Balance : ")
        balance_label.setFont(QFont("Segoe UI", 15))
        self.date_value = QLabel()
        self.date_value.setFont(QFont("Segoe UI", 13))
        self.date_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.time_value = QLabel()
        self.time_value.setFont(QFont("Segoe UI", 13))
        self.time_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.receipt_no_value = QLabel()
        self.receipt_no_value.setFont(QFont("Segoe UI", 13))
        self.receipt_no_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_label_value = QLabel("self.total_label_value")
        self.total_label_value.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.total_label_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.amount_paid_value = QLabel("self.amount_paid_value")
        self.amount_paid_value.setFont(QFont("Segoe UI", 13))
        self.amount_paid_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.balance_value = QLabel("self.balance_value")
        self.balance_value.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.balance_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        payment_details_layout.setColumnStretch(0, 1)
        payment_details_layout.setColumnStretch(1, 1)
        payment_details_layout.addWidget(date_label, 0, 0)
        payment_details_layout.addWidget(time_label, 1, 0)
        payment_details_layout.addWidget(receipt_no_label, 2, 0)
        payment_details_layout.addWidget(total_label, 3, 0)
        payment_details_layout.addWidget(amount_paid_label, 4, 0)
        payment_details_layout.addWidget(balance_label, 5, 0)
        payment_details_layout.addWidget(self.date_value, 0, 1)
        payment_details_layout.addWidget(self.time_value, 1, 1)
        payment_details_layout.addWidget(self.receipt_no_value, 2, 1)
        payment_details_layout.addWidget(self.total_label_value, 3, 1)
        payment_details_layout.addWidget(self.amount_paid_value, 4, 1)
        payment_details_layout.addWidget(self.balance_value, 5, 1)
        payment_details_layout.setAlignment(Qt.AlignmentFlag.AlignTop| Qt.AlignmentFlag.AlignHCenter)
        payment_details.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        payment_complete_button = QHBoxLayout()
        payment_complete_button.setContentsMargins(0, 0, 0, 0)
        payment_complete_button.setSpacing(5)
        self.new = QPushButton("New Transaction")
        self.new.setStyleSheet("font-size: 15px; margin: 0px;")
        self.new.clicked.connect(self.new_transaction)
        self.reprint = QPushButton("Reprint Receipt")
        self.reprint.clicked.connect(self.print_receipt)
        self.reprint.setStyleSheet("font-size: 15px;  margin: 0px;")
        payment_complete_button.addWidget(self.reprint)
        payment_complete_button.addWidget(self.new)

        column2_complete_layout.addWidget(payment_complete_header, 0, Qt.AlignmentFlag.AlignCenter)
        column2_complete_layout.addWidget(payment_details)
        column2_complete_layout.addLayout(payment_complete_button)

        self.column2_complete_widget.setLayout(column2_complete_layout)

        main_layout.addLayout(self.column1_layout, stretch=70)
        main_layout.addWidget(self.column2_cashier_widget, stretch=30)
        main_layout.addWidget(self.column2_paymentoption_widget, stretch=30)
        main_layout.addWidget(self.column2_payment_widget, stretch=30)
        main_layout.addWidget(self.column2_complete_widget, stretch=30)
        # Layouts to be hidden on launch 
        self.column2_paymentoption_widget.hide()
        self.column2_payment_widget.hide()
        self.column2_complete_widget.hide()

        wrapper.setLayout(main_layout)
        self.ean13_input.setFocus() # SetFocus called after object creation
        self.showMaximized()

    def get_product_information(self, ean13):
        cursor.execute("SELECT product_name, ean13, price FROM products WHERE ean13 = %s", (ean13,))
        item = cursor.fetchone() # Format: tuple() (product_name, ean13, price)
        if not item:
            return False
        return item

    def update_cart(self):
        ean13 = self.ean13_input.text()
        self.ean13_input.setText("")
        rows = self.table.rowCount()
        if not self.TOGGLE_REMOVE_ITEM:
            item_information = self.get_product_information(ean13)
            if not item_information:
                self.last_scan.setText("ERROR: Product not found")
                return
            if item_information[0] not in self.CART.keys():
                self.CART[item_information[0]] = [0, item_information[2], ean13]
            self.CART[item_information[0]][0] += 1
            current_total = round(float(self.total_input.text()), 2)
            current_total += item_information[2]
            self.TOTAL += item_information[2]
            self.total_input.setText(f"{current_total:.2f}")
            self.last_scan.setText(item_information[0])
            self.item_price.setText(f"{item_information[2]:.2f}")
            for row in range(rows):
                if self.table.item(row, 0).text() == item_information[0]:
                    current_quantity = int(self.table.item(row, 1).text())
                    current_price = round(float(self.table.item(row, 2).text()), 2)
                    current_quantity += 1
                    current_price += item_information[2]
                    self.table.setItem(row, 1, QTableWidgetItem(str(current_quantity)))
                    self.table.setItem(row, 2, QTableWidgetItem(f"{current_price:.2f}"))
                    break
            else:
                self.table.insertRow(rows)
                self.table.setItem(rows, 0, QTableWidgetItem(item_information[0]))
                self.table.setItem(rows, 1, QTableWidgetItem("1"))
                self.table.setItem(rows, 2, QTableWidgetItem(f"{item_information[2]:.2f}"))
        else:
            for item_name, item_info in self.CART.items():
                if ean13 == item_info[2]:
                    item_info[0] -= 1
                    self.TOTAL -= item_info[1]
                    for row in range(self.table.rowCount()):
                        if self.table.item(row, 0).text() == item_name:
                            current_quantity = int(self.table.item(row, 1).text())
                            current_price = float(self.table.item(row, 2).text())
                            current_quantity -= 1
                            self.total_input.setText(f"{self.TOTAL:.2f}")
                            if current_quantity == 0:
                                self.table.removeRow(row)
                            else:
                                current_price -= item_info[1]
                                self.table.setItem(row, 1, QTableWidgetItem(f"{current_quantity}"))
                                self.table.setItem(row, 2, QTableWidgetItem(f"{current_price:.2f}"))
                            break
                    if item_info[0] == 0:
                        del self.CART[item_name]
                    break
            else:
                self.last_scan.setText("Item not in cart")

    def toggle_remove_item(self):
        if not self.TOGGLE_REMOVE_ITEM:
            self.TOGGLE_REMOVE_ITEM = True
            self.ean13_input.setStyleSheet("border: 2px solid rgb(255, 26, 26); padding: 7px 5px; margin-bottom: 20px;")
            self.last_scan.setStyleSheet("border: 2px solid rgb(255, 26, 26);")
            self.label_barcode.setText("Scan item to remove:")
        else:
            self.TOGGLE_REMOVE_ITEM = False
            self.ean13_input.setStyleSheet("border: 2px solid rgb(47, 237, 171); padding: 7px 5px; margin-bottom: 20px;")
            self.last_scan.setStyleSheet("border: 2px solid rgb(31, 224, 99);")
            self.label_barcode.setText("Scan item to add:")
        self.ean13_input.setFocus()

    def clear_cart(self, force=False):
        if not force:
            dlg_clear_cart = QMessageBox.warning(self, "Warning", "Are you sure you want to clear the cart?", buttons=QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if dlg_clear_cart == QMessageBox.StandardButton.No:
                return
        self.table.setRowCount(0)
        self.CART.clear()
        self.TOTAL = 0.0
        self.PAID = 0.0
        self.TRANSACTION_NO = 0
        self.last_scan.setText("")
        self.item_price.setText("0.00")
        self.total_input.setText("0.00")

    def new_transaction(self):
        self.column2_complete_widget.hide()
        self.clear_cart(force=True)
        self.payment_input.setText("0.00")
        self.column2_cashier_widget.show()
        self.ean13_input.setFocus()
    
    def process_payment(self):
        self.PAID = float(self.payment_input.text())
        if self.PAID < self.TOTAL:
            dlg_insufficient_amount = QMessageBox.warning(self, "Warning", "Payment insufficient")
            return
        self.TRANSACTION_NO = int(datetime.now().timestamp())
        self.column2_payment_widget.hide()
        self.column2_complete_widget.show()
        self.QDATETIME = QDateTime.currentDateTime()
        self.date_value.setText(f"{self.QDATETIME.date().day()}-{self.QDATETIME.date().month()}-{self.QDATETIME.date().year()}")
        self.time_value.setText(f"{self.QDATETIME.time().hour()}:{self.QDATETIME.time().minute()}:{self.QDATETIME.time().second()}")
        self.receipt_no_value.setText(f"{self.TRANSACTION_NO}")
        self.total_label_value.setText(f"RM {self.TOTAL:.2f}")
        self.amount_paid_value.setText(f"RM {self.PAID:.2f}")
        self.balance_value.setText(f"RM {(self.PAID - self.TOTAL):.2f}")        
        try:
            sql_date = date.today().strftime("%Y-%m-%d")
            item_array = [(item_name,  data[0], data[1], data[2], self.TRANSACTION_NO) for item_name, data in self.CART.items()]
            cursor.execute("INSERT INTO transactions (transaction_id, transaction_date, total_amount, cashier_username) VALUES (%s, %s, %s, %s)", (str(self.TRANSACTION_NO), sql_date, self.TOTAL, self.USERNAME))
            cursor.executemany("INSERT INTO transaction_items (item_name, quantity, price_per_unit, ean13, transaction_id) VALUES (%s, %s, %s, %s, %s)", item_array)
            db.commit()
        except Exception as e:
            print(f"An error occured while accessing database '{r_database}'")
            print(e)
        self.print_receipt()
        self.new.setFocus()
    
    def print_receipt(self):
        self.receipt = ReceiptWidget(self.CART, self.TOTAL, self.PAID, self.FULL_NAME, self.QDATETIME, self.TRANSACTION_NO)
        self.receipt.show()

    def exact_amout_payment(self):
        self.payment_input.setText(f"{self.TOTAL}")
        self.process_payment()

    def clear_payment_widget(self):
        self.payment_input.setText("0.00")

    def payment_widget(self):
        if self.TOTAL == 0.0:
            return
        self.amount_label.setText(f"Total: RM {self.TOTAL:.2f}")
        self.column2_cashier_widget.hide()
        self.column2_payment_widget.show()
        self.column2_payment_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.column2_payment_widget.setFocus()
    
    def close_payment_widget(self):
        self.clear_payment_widget()
        self.column2_cashier_widget.show()
        self.column2_payment_widget.hide()
        self.ean13_input.setFocus()

    def enter_num(self, num):
        c = float(self.payment_input.text())
        c *= 10
        c += (num * 0.01)
        self.payment_input.setText(f"{c:.2f}")
    
    def erase_num(self):
        current_text = self.payment_input.text().replace('.', '')
        if len(current_text) > 1:  # Ensure we don't erase below 0.00
            new_value = int(current_text[:-1]) 
            formatted = f"{new_value/100:.2f}" 
            self.payment_input.setText(formatted)
        else:
            self.payment_input.setText("0.00")

    def keyPressEvent(self, event):
        # Map number keys to numpad buttons
        key_mapping = {
            Qt.Key.Key_0: 0,
            Qt.Key.Key_1: 1,
            Qt.Key.Key_2: 2,
            Qt.Key.Key_3: 3,
            Qt.Key.Key_4: 4,
            Qt.Key.Key_5: 5,
            Qt.Key.Key_6: 6,
            Qt.Key.Key_7: 7,
            Qt.Key.Key_8: 8,
            Qt.Key.Key_9: 9,
            Qt.Key.Key_Backspace: -1,  # For backspace
            Qt.Key.Key_Enter: -2,      # For enter/return
            Qt.Key.Key_Return: -2      # Numpad enter key
        }
        if event.key() in key_mapping:
            num = key_mapping[event.key()]
            if num >= 0:
                self.enter_num(num)
            elif num == -1:
                self.erase_num()
            elif num == -2:
                if self.column2_payment_widget.isVisible():
                    self.process_payment()
                elif self.column2_complete_widget.isVisible():
                    self.new_transaction()
        else:
            super().keyPressEvent(event)
    
    def logout(self):
        logout_msg = QMessageBox.warning(self, "warning", "Are you sure you want to log out?", buttons=QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if logout_msg == QMessageBox.StandardButton.Yes:
            self.close()

class LoginContainer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(CONFIG['login_instance_title'])
        self.resize(800, 700)
        self.login = LoginPage()
        self.login.login_success.connect(self.login_auth)        
        layout = QVBoxLayout(self)
        layout.addWidget(self.login, 0, Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet("LoginContainer{background-image: url('assets/BACKGROUNDLINK');background-position: center;}")
    def login_auth(self, username, full_name):
        self.main_app = CashierMainApp(username, full_name)
        self.main_app.show()
        self.close()

class LoginPage(QWidget):
    login_success = pyqtSignal(str, str) # Receives username, full_name
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 600)
        self.setup_ui()
        self.username = ''
        self.full_name = ''
        
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30) # Left Top Right Bottom
        layout.setSpacing(20)

        # Title
        self.title = QLabel(CONFIG['login_instance_title'])
        self.title.setStyleSheet("""
            font-size: 32px;
            color: white;
            font-weight: bold;
        """)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_holder = QLabel()
        self.logo_holder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = QPixmap(os.path.join(ASSET_FOLDER, CONFIG['login_instance_icon']))
        self.logo = logo.scaled(128,128)
        self.logo_holder.setPixmap(self.logo)
        self.username_field = AnimatedInputField("Username")
        self.username_field.setPlaceholderText("")
        self.password_field = AnimatedInputField("Password")
        self.password_field.setPlaceholderText("")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Field layout
        fields = QVBoxLayout()
        fields.addWidget(self.username_field)
        fields.addWidget(self.password_field)

        self.login_result = QLabel('')
        self.login_result.setOpenExternalLinks(False)
        self.login_result.setStyleSheet("""
            QLabel{
                color: red;
                font-size: 15px;                            
            }                            
""")
        # Spacers
        spacer = QHBoxLayout()
        spacer.addWidget(self.login_result)
        spacer.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
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
            QPushButton:hover,  QPushButton:focus{
                color: white;
                border-color: white;
                background: rgba(31, 224, 99);
            }
        """)
        self.login_btn.clicked.connect(self.login)
        layout.addWidget(self.title)
        layout.addWidget(self.logo_holder)
        layout.addLayout(fields)
        layout.addLayout(spacer)
        layout.addWidget(self.login_btn)
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0);
            }
        """)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        glass = QWidget(self)
        glass.setGeometry(self.rect())    
        brush = QBrush(QColor(255, 255, 255, 20))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)

    # Backend processing
    def login(self):
        username = self.username_field.text()
        password = self.password_field.text()
        if len(username) == 0 or len(password) == 0:
            self.login_result.setText("Fields cannot be empty")
            return
        cursor.execute("SELECT * FROM users WHERE username = %s", (username, ))
        result = cursor.fetchone()
        if not result:
            self.login_result.setText("No username found!")
        elif result[2] != hash_password(password):
            self.login_result.setText("Password is incorrect")
        else:
            self.login_result.setText("Login successful")
            self.username = result[1]
            self.full_name = result[4]
            self.login_result.setStyleSheet("QLabel{ color : white; font-size: 15px; }")
            self.login_success.emit(self.username, self.full_name)

class AnimatedInputField(QLineEdit):
    def __init__(self, label_text):
        super().__init__()
        self.label = QLabel(label_text, self)
        self.setContentsMargins(0, 15, 0, 0)
        self.label.setStyleSheet("""
            color: white;
            font-size: 16px;
            padding-top: 10px;
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
        # Movement animation setup
        self.animation = QPropertyAnimation(self.label, b"pos")
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setDuration(200)
        # Font animation setup
        self.font_animation = QPropertyAnimation(self.label, b"font")
        self.animation.setDuration(200)

    def focusInEvent(self, event):
        self.animation.stop()
        self.font_animation.stop()
        self.animation.setStartValue(self.label.pos())
        self.animation.setEndValue(QPoint(0, -15))
        self.font_animation.setStartValue("16px")
        self.font_animation.setEndValue("8px")
        self.animation.start()
        self.font_animation.start()
        self.label.setStyleSheet("""
            color: rgb(31, 224, 99);
            margin-top: 8px;
        """)
        self.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                border-bottom: 2px solid rgb(31, 224, 99);
                color: white;
                font-size: 16px;
                padding: 5px 0;
                margin-bottom: 5px;
            }         
        """)
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        if not self.text():
            self.animation.stop()
            self.animation.setStartValue(self.label.pos())
            self.animation.setEndValue(QPoint(0, (self.height() - self.label.height()) // 2))
            self.animation.start()
            self.label.setStyleSheet("""
                color: white;
                font-size: 16px;
                padding-top: 10px;
            """)
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
        else:
            self.label.setStyleSheet("color: white; padding-top: 10px;")
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.parent().login()
        else:
            super().keyPressEvent(event)
    
    def resizeEvent(self, event):
        if not self.hasFocus() and not self.text():
            self.label.move(0, (self.height() - self.label.height()) // 2)
        super().resizeEvent(event)

class EAN13Input(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.parent().parent().parent().update_cart()
        else:
            super().keyPressEvent(event)

class ReceiptWidget(QWidget):
    def __init__(self, cart, total, amount_paid, cashier, qdatetime, receipt_no):
        super().__init__()
        self.setWindowTitle(f"Receipt #{receipt_no}. Press Enter to close")
        self.setFixedSize(500, 700)
        self.cart = cart
        self.total = total
        self.amount_paid = amount_paid
        self.cashier = cashier
        self.qdatetime = qdatetime
        self.receipt_no = receipt_no
        self.setup_ui()       

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Receipt container
        receipt_container = QWidget()
        receipt_container.setStyleSheet("""
            border-radius: 5px;
        """)
        receipt_layout = QVBoxLayout(receipt_container)
        receipt_layout.setContentsMargins(20, 20, 20, 20)
        receipt_layout.setSpacing(15)
        
        # Store name
        store_label = QLabel("Store Name")
        store_label.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        store_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        receipt_layout.addWidget(store_label)

        address_label = QLabel("Store Address Sample Text")
        address_label.setFont(QFont("Arial", 11))
        address_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        address_label.setStyleSheet("margin-bottom: 10px;")
        receipt_layout.addWidget(address_label)
        
        # Receipt info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        
        info_date = f"Date: {self.qdatetime.date().day()}-{self.qdatetime.date().month()}-{self.qdatetime.date().year()}" 
        info_receipt_number = f"Receipt #: {self.receipt_no}"
        info_cashier = f"Cashier: {self.cashier}"
        info_labels = [
            QLabel(info_date),
            QLabel(info_receipt_number),
            QLabel(info_cashier)
        ]
        
        for label in info_labels:
            label.setStyleSheet("font-size: 14px;")
            info_layout.addWidget(label)
        
        receipt_layout.addWidget(info_widget)
        
        # Items table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Item", "Qty", "Price (RM)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)

        # Enable text wrapping
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.TextElideMode.ElideNone)  # Show full text, no ellipsis
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # Style the table with wrapping support
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: transparent;
                border: none;
                padding-bottom: 8px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #eee;
                padding: 8px 0;
            }
        """)

        item_row = len(self.cart)
        self.table.setRowCount(item_row)
        row = 0
        for name, (qty, price_per_unit, ean13) in self.cart.items():
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsAutoTristate)
            
            qty_item = QTableWidgetItem(str(qty))
            qty_item.setFlags(qty_item.flags() | Qt.ItemFlag.ItemIsAutoTristate)
            
            price_item = QTableWidgetItem(f"{(price_per_unit * qty):.2f}")
            price_item.setFlags(price_item.flags() | Qt.ItemFlag.ItemIsAutoTristate)
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, qty_item)
            self.table.setItem(row, 2, price_item)
            
            # Center quantity column
            self.table.item(row, 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Right align price column
            self.table.item(row, 2).setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row += 1

        # Configure row height resizing
        self.table.verticalHeader().setDefaultSectionSize(24) 
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Empty row for spacing 
        self.table.insertRow(item_row)

        # Total row
        self.table.insertRow(item_row+1)
        total_item = QTableWidgetItem("Total")
        total_item.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.table.setItem(item_row+1, 0, total_item)        
        self.table.setSpan(item_row+1, 0, 1, 2)

        total_price = QTableWidgetItem(f"RM{self.total:.2f}")
        total_price.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        total_price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(item_row+1, 2, total_price)

        # Amount Paid row
        self.table.insertRow(item_row+2)
        amount_paid_label = QTableWidgetItem("Amount Paid")
        amount_paid_label.setFont(QFont("Arial"))
        self.table.setItem(item_row+2, 0, amount_paid_label)
        self.table.setSpan(item_row+2, 0, 1, 2)

        amount_paid = QTableWidgetItem(f"RM{self.amount_paid:.2f}")
        amount_paid.setFont(QFont("Arial"))
        amount_paid.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(item_row+2, 2, amount_paid)

        self.table.insertRow(item_row+3)
        change_label = QTableWidgetItem("Balance")
        change_label.setFont(QFont("Arial"))
        self.table.setItem(item_row+3, 0, change_label)
        self.table.setSpan(item_row+3, 0, 1, 2)

        change = QTableWidgetItem(f"RM{(self.amount_paid - self.total):.2f}")
        change.setFont(QFont("Arial"))
        change.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(item_row+3, 2, change)

        receipt_layout.addWidget(self.table)
        
        footer_label = QLabel("All prices are inclusive to 6% service tax\nThank you for your purchase!")
        footer_label.setStyleSheet("""
            font-size: 14px;
            color: #888;
        """)
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        receipt_layout.addWidget(footer_label)
        
        layout.addWidget(receipt_container)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.close()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    login_window = LoginContainer()
    login_window.show()
    app.exec()