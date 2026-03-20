from app import create_app

app = create_app()

if __name__ == "__main__":
    # use_reloader=False prevents Flask watchdog from restarting when
    # torch/transformers write cache files during model loading
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
