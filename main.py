"""OvozYoz ishga tushirish nuqtasi."""
import ctypes
from ovozyoz import APP
from ovozyoz.winapi import single_instance


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    if not single_instance(APP):
        return  # allaqachon ishlayapti
    from ovozyoz.app import App
    App().run()


if __name__ == "__main__":
    main()
