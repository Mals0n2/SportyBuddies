"""
The flask application package.
"""

from flask import Flask
from flask_mail import Mail
app = Flask(__name__)

import SportyBuddies.views
