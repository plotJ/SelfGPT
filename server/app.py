from flask import Flask
from server.backend import Backend_Api
from server.website import Website
from server.config import Config

app = Flask(__name__, template_folder='../client/html')
config = Config()

backend_api = Backend_Api(app, config)
website = Website(app)

# Register routes
for route, info in backend_api.routes.items():
    app.add_url_rule(route, view_func=info['function'], methods=info['methods'])

for route, info in website.routes.items():
    app.add_url_rule(route, view_func=info['function'], methods=info['methods'])

@app.route('/')
def home():
    return "Hello from Vercel!"

if __name__ == '__main__':
    app.run(host=config.host, port=config.port, debug=config.debug)