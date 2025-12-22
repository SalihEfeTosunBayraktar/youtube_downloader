from gui.app import App

if __name__ == "__main__":
    while True:
        app = App()
        app.mainloop()
        if not app.reload_requested:
            break
