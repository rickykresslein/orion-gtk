import os
from pathlib import Path

from gi.repository import Adw, Gio, Gtk, WebKit

@Gtk.Template(resource_path='/io/unobserved/Kagi/window.ui')
#@Gtk.Template(filename='/home/ricky/Projects/kagi/src/window.ui')
class KagiWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'KagiWindow'

    file_list_box = Gtk.Template.Child()
    web_scrolled = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #self.file_watcher = FileWatcher(self._refresh_file_list)

        open_dir_action = Gio.SimpleAction(name="open")
        open_dir_action.connect("activate", self._open_dir_picker)
        self.add_action(open_dir_action)

        self.file_list_box.connect('row-selected', self._on_file_selected)

        self.monitor = None

        # Web view
        self.web_view = WebKit.WebView()
        self.web_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.web_scrolled.set_child(self.web_view)
        self.web_scrolled.set_vexpand(True)

    def _open_dir_picker(self, action, _):
        """Open a directory"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Choose Directory")

        def on_response(dialog, result):
            try:
                folder = dialog.select_folder_finish(result)
                if folder:
                    self.current_directory = folder.get_path()
                    self._refresh_file_list()
                    #self.file_watcher.watch_directory(self.current_directory)
                    self.watch_directory(self.current_directory)
            except Exception as e:
                print(f"Directory selection canceled or failed: {e}")

        dialog.select_folder(parent=self, callback=on_response)

    def _refresh_file_list(self):
        """Refresh the file list from the current directory"""
        print("Refreshing...")
        # Clear existing items
        while True:
            row = self.file_list_box.get_first_child()
            if row is None:
                break
            self.file_list_box.remove(row)

        if not self.current_directory or not os.path.exists(self.current_directory):
            return

        try:
            # Get directory contents
            entries = []
            for item in os.listdir(self.current_directory):
                full_path = os.path.join(self.current_directory, item)
                if os.path.isfile(full_path):
                    entries.append((item, full_path))

            # Sort entries
            entries.sort(key=lambda x: x[0].lower())

            # Add to list box
            for filename, full_path in entries:
                row = self._create_file_row(filename, full_path)
                self.file_list_box.append(row)

        except PermissionError:
            print(f"Permission denied accessing {self.current_directory}")
        except Exception as e:
            print(f"Error reading directory: {e}")

        return False  # Don't repeat timeout

    def _create_file_row(self, filename, full_path):
        """Create a list box row for a file"""
        row = Adw.ActionRow()
        row.set_title(filename)

        # Store full path as data
        row.full_path = full_path

        # Add icon based on file type
        if filename.lower().endswith(('.html', '.htm')):
            icon = Gtk.Image.new_from_icon_name("text-html-symbolic")
            row.set_subtitle("HTML file")
        else:
            icon = Gtk.Image.new_from_icon_name("text-x-generic-symbolic")
            row.set_subtitle("File")

        row.add_prefix(icon)

        return row

    def _on_file_selected(self, list_box, row):
        if row is None:
            return

        filename = row.get_title()
        full_path = row.full_path

        # Check if it's an HTML file
        if filename.lower().endswith(('.html', '.htm')):
            self._load_html_file(full_path)
        else:
            # Show message for non-HTML files
            self.web_view.load_html("""
                <html>
                <head>
                    <style>
                        body {
                            font-family: system-ui;
                            text-align: center;
                            padding: 2rem;
                            color: #666;
                        }
                    </style>
                </head>
                <body>
                    <h3>Not an HTML file</h3>
                    <p>Select an HTML file to view its contents.</p>
                </body>
                </html>
            """)

    def _load_html_file(self, file_path):
        """Load HTML file in web view"""
        try:
            if os.path.exists(file_path):
                file_uri = Path(file_path).as_uri()
                self.web_view.load_uri(file_uri)
            else:
                self.web_view.load_html("""
                    <html>
                    <head>
                        <style>
                            body {
                                font-family: system-ui;
                                text-align: center;
                                padding: 2rem;
                                color: #666;
                            }
                        </style>
                    </head>
                    <body>
                        <h3>File not found</h3>
                        <p>The selected file could not be loaded.</p>
                    </body>
                    </html>
                """)
        except Exception as e:
            error_html = f"""
                <html>
                <head>
                    <style>
                        body {{
                            font-family: system-ui;
                            text-align: center;
                            padding: 2rem;
                            color: #666;
                        }}
                    </style>
                </head>
                <body>
                    <h3>Error loading file</h3>
                    <p>{str(e)}</p>
                </body>
                </html>
            """
            self.web_view.load_html(error_html)

    def watch_directory(self, path):
        if self.monitor:
            self.monitor.cancel()

        if not path or not os.path.exists(path):
            return

        directory = Gio.File.new_for_path(path)
        self.monitor = directory.monitor_directory(Gio.FileMonitorFlags.NONE, None)
        self.monitor.connect('changed', self.directory_changed)

    def directory_changed(self, monitor, file, other_file, event_type):
        self._refresh_file_list
