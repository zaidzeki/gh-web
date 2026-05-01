import os
from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from .auth import routes as auth_routes
    from .repos import routes as repos_routes
    from .prs import routes as prs_routes
    from .issues import routes as issues_routes
    from .workspace import routes as workspace_routes
    from .tasks import routes as tasks_routes
    from .releases import routes as releases_routes

    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(repos_routes.bp)
    app.register_blueprint(prs_routes.bp)
    app.register_blueprint(issues_routes.bp)
    app.register_blueprint(workspace_routes.bp)
    app.register_blueprint(tasks_routes.bp)
    app.register_blueprint(releases_routes.bp)

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://avatars.githubusercontent.com;"
        return response

    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    return app
