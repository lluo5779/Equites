import server.config_old as config
from server.common.database import User

@config.login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




