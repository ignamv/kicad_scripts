import site

# Add the site-packages of the chosen virtualenv to work with
site.addsitedir('/var/www/spiral/lib/python3.4/site-packages')
 
activate_this = "/var/www/spiral/bin/activate_this.py"
with open(activate_this) as f:
    code = compile(f.read(), activate_this, 'exec')
    exec(code)
import sys
sys.path.insert(0, '/var/www/spiral')
from calculate import application
application.debug = True
