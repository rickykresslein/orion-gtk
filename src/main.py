import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Gio, Adw, WebKit
from .window import KagiWindow

class KagiApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.unobserved.Kagi',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
                         resource_base_path='/io/unobserved/Kagi')
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.current_directory = None

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = KagiWindow(application=self)
        win.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = KagiApplication()
    return app.run(sys.argv)
