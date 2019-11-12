import server

app = server.create_app().app

if __name__ == "__main__":
    app.run()
