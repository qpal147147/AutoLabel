from typing import Dict
from pathlib import Path

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox

class CategoryDialog(QDialog):
    classes = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Classes")
        
        layout = QVBoxLayout()
        self.listWidget = QListWidget()
        self.listWidget.addItems(CategoryDialog.classes)
        self.listWidget.itemDoubleClicked.connect(lambda: self.accept())
        layout.addWidget(self.listWidget)
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

def load_classes_from_file(file_path: Path) -> None:
    file_name = file_path.name

    if not file_path.exists():
        with open(file_name, "w") as f:
            f.writelines(["dog\n", "person\n", "cat\n", "tv\n", "car"])
            
    with open(file_name, "r")  as f:
        lines = f.readlines()
        for line in lines:
            c = line.strip()
            CategoryDialog.classes.append(c)

def create_class_index_dictionary() -> Dict[str, int]:
    class_index_dict = {classes: index for index, classes in enumerate(CategoryDialog.classes)}
    return class_index_dict 