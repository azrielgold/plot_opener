import os
import sys
import time
import pickle
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QVBoxLayout, QWidget, QAction, QFileDialog, QCheckBox, QLineEdit, QPushButton
from PyQt5 import QtCore
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')

FILE_READ_ATTEMPTS = 2


def get_files_in_dir(cur_dir):
    return set(filter(lambda filename: os.path.isfile(os.path.join(cur_dir, filename)), os.listdir(cur_dir)))


def open_plots(file_paths):

    def load_plot(f_path):
        with open(f_path, 'rb') as pickle_file:
            fig = pickle.load(pickle_file)
            plt.gcf().canvas.manager.set_window_title(file_path[file_path.rfind("/") + 1:])

    plot_count = 0
    for file_path in file_paths:
        attempt_counter = 0
        attempt_additional_load = True
        while attempt_additional_load:
            try:
                load_plot(file_path)
                attempt_additional_load = False
                plot_count += 1
            except pickle.UnpicklingError:
                print(f'Plot not found in: {file_path}.', file=sys.stderr)
                attempt_additional_load = False
            except PermissionError:
                attempt_counter += 1
                if attempt_counter < FILE_READ_ATTEMPTS:
                    time.sleep(1)
                else:
                    print(f'File at following path could not be loaded: {file_path}.', file=sys.stderr)
                    attempt_additional_load = False
    if plot_count > 0:
        plt.show(block=False)


class BackgroundLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setText('Drag & drop one or more\npython plot files here.\n\nYou can also drop a folder to watch.')
        self.setFont(QFont('Arial', 20))
        self.setStyleSheet('color: gray; font-weight:bold; border: 4px dashed gray')

    def setPixmap(self, image):
        super().setPixmap(image)


class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        # toolbar
        self.toolbar = self.addToolBar('Controls')
        self.create_toolbar()

        # window background
        layout = QVBoxLayout()
        background_graphic = BackgroundLabel()
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        layout.addWidget(background_graphic)

        # general window layout options
        self.setWindowTitle("Plot opener")
        self.resize(720, 480)
        self.setAcceptDrops(True)

        # folder watching variables
        self.currently_watched_dir = None
        self.files_in_watched_folder = None
        self.file_watcher = QtCore.QFileSystemWatcher()
        self.file_watcher.directoryChanged.connect(self.watch_dir_changed)

    def create_toolbar(self):
        open_btn = QAction('&Open plot files…', self, shortcut='Ctrl+O', triggered=self.open_dialog)
        self.toolbar.addAction(open_btn)

        self.toolbar.addSeparator()

        self.watch_checkbox = QCheckBox('Enable folder watch:', self.toolbar)
        self.watch_checkbox.stateChanged.connect(self.watch_checkbox_changed)
        self.toolbar.addWidget(self.watch_checkbox)

        self.watch_path_textbox = QLineEdit(self.toolbar)
        self.watch_path_textbox.setEnabled(False)
        self.toolbar.addWidget(self.watch_path_textbox)
        self.watch_path_textbox.textChanged.connect(self.watch_textbox_changed)

        self.watch_browse_btn = QPushButton('Browse...', self.toolbar)
        self.watch_browse_btn.clicked.connect(self.browse_watch_dir)
        self.watch_browse_btn.setEnabled(False)
        self.toolbar.addWidget(self.watch_browse_btn)

        self.toolbar.setMovable(False)

    def watch_textbox_changed(self):
        if self.watch_checkbox.isChecked():
            self.init_new_watch()

    def browse_watch_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Select folder to watch')
        if dir_path != '':
            self.watch_path_textbox.setText(dir_path)

    def init_new_watch(self):
        new_dir = self.watch_path_textbox.text()
        if not os.path.isdir(new_dir):
            return

        if self.currently_watched_dir is not None:
            self.file_watcher.removePath(self.currently_watched_dir)
        self.file_watcher.addPath(new_dir)
        self.files_in_watched_folder = get_files_in_dir(new_dir)
        self.currently_watched_dir = new_dir

    def watch_dir_changed(self, dir_path):
        new_file_set = get_files_in_dir(dir_path)
        old_file_set = self.files_in_watched_folder

        new_files = new_file_set.difference(old_file_set)
        self.files_in_watched_folder = new_file_set
        if len(new_files) > 0:
            open_plots([os.path.join(dir_path, new_file_path) for new_file_path in new_files])

    def watch_checkbox_changed(self, a):
        is_checkbox_checked = self.watch_checkbox.isChecked()

        self.watch_path_textbox.setEnabled(is_checkbox_checked)
        self.watch_browse_btn.setEnabled(is_checkbox_checked)

        if is_checkbox_checked:
            self.init_new_watch()
        else:
            self.file_watcher.removePath(self.currently_watched_dir)
            self.currently_watched_dir = None

    def open_dialog(self):
        file_path, _ = QFileDialog.getOpenFileNames(self, 'Select plot files to open', '', 'All files (*.*)')
        open_plots(file_path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = [u.toLocalFile() for u in event.mimeData().urls()]
        files = []
        folders = []
        for url in urls:
            if os.path.isfile(url):
                files.append(url)
            else:
                folders.append(url)
        open_plots(files)
        if len(folders) == 1:
            self.watch_path_textbox.setText(folders[0])
            self.watch_checkbox.setChecked(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MainWidget()
    ui.show()
    sys.exit(app.exec())
