import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.gui import MainWindow


def main():
    # Retina / HiDPI auf macOS
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Downloader")
    app.setOrganizationName("Personal")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
