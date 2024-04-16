
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from functools import wraps

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.secret_key = 'abcdefg'


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "ef2729"
DATABASE_PASSWRD = "ef2729"
DATABASE_HOST = "34.148.107.47" # change to 34.28.53.86 if you used database 2 for part 2
DATABASEURI = "postgresql://ef2729:ef2729@35.212.75.104/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
with engine.connect() as conn:
	create_table_command = """
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	"""
	res = conn.execute(text(create_table_command))
	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	conn.commit()


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
	"""
	request is a special object that Flask provides to access web request information:

	request.method:   "GET" or "POST"
	request.form:     if the browser submitted a form, this contains the data in the form
	request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

	See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
	"""

	# DEBUG: this is debugging code to see what request looks like
	print(request.args)


	#
	# example of a database query
	#
	select_query = "SELECT * from recipe"
	cursor = g.conn.execute(text(select_query))
	names = []
	for result in cursor:
		names.append(result)

	popular_query = "SELECT recipe_id FROM popular_recipe"
	popular_recipe_ids = {row[0] for row in g.conn.execute(text(popular_query)).fetchall()}
	cursor.close()

	
	#
	# Flask uses Jinja templates, which is an extension to HTML where you can
	# pass data to a template and dynamically generate HTML based on the data
	# (you can think of it as simple PHP)
	# documentation: https://realpython.com/primer-on-jinja-templating/
	#
	# You can see an example template in templates/index.html
	#
	# context are the variables that are passed to the template.
	# for example, "data" key in the context variable defined below will be 
	# accessible as a variable in index.html:
	#
	#     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
	#     <div>{{data}}</div>
	#     
	#     # creates a <div> tag for each element in data
	#     # will print: 
	#     #
	#     #   <div>grace hopper</div>
	#     #   <div>alan turing</div>
	#     #   <div>ada lovelace</div>
	#     #
	#     {% for n in data %}
	#     <div>{{n}}</div>
	#     {% endfor %}
	#
	context = dict(data = names)


	#
	# render_template looks in the templates/ folder for files.
	# for example, the below file reads template/index.html
	#
	return render_template("index.html", **context, popular_recipe_ids=popular_recipe_ids)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to access this page')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
@login_required
def another():
	return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
	# accessing form inputs from user
	name = request.form['name']
	
	# passing params in for each variable into query
	params = {}
	params["new_name"] = name
	g.conn.execute(text('INSERT INTO recipe(name) VALUES (:new_name)'), params)
	g.conn.commit()
	return redirect('/')

@app.route('/search', methods=['POST'])
def search():
    search_name = request.form['search_name']
    search_query = "SELECT recipe_id, name, description FROM recipe WHERE name ILIKE :search_name"
    cursor = g.conn.execute(text(search_query), {"search_name": f'%{search_name}%'})
    recipes = [{"recipe_id": result[0], "name": result[1], "description": result[2]} for result in cursor]
    cursor.close()

    return render_template("index.html", data=recipes)

def user_has_liked_recipe(user_id, recipe_id):
	query = """
    SELECT EXISTS (
        SELECT 1
        FROM recipe_likes
        WHERE user_id = :user_id AND recipe_id = :recipe_id
    )
    """
	params = {"user_id": user_id, "recipe_id": recipe_id}
	result = g.conn.execute(text(query), params).scalar()
	return result

@app.route('/recipes/<recipe_id>')
def recipe_detail(recipe_id):
	user_id = session.get('user_id')
	user_liked = False
	if user_id:
		user_liked = user_has_liked_recipe(user_id, recipe_id)


	# Fetch the recipe from the database using its ID
	query = "SELECT * FROM recipe WHERE recipe_id = :recipe_id"
	recipe = g.conn.execute(text(query), {"recipe_id": recipe_id}).fetchone()
	
	# Check if the recipe was found
	if recipe is None:
		return "Recipe not found", 404
	

	ingredients_query = """
	SELECT ingredients.name, recipe_ingredients.quantity
	FROM recipe_ingredients
	JOIN ingredients ON recipe_ingredients.ingredient_id = ingredients.ingredient_id
	WHERE recipe_ingredients.recipe_id = :recipe_id
	"""

	ingredients = g.conn.execute(text(ingredients_query), {"recipe_id": recipe_id}).fetchall()

	# Fetch the instructions for the recipe 
	instructionsQuery = "SELECT * FROM instructions WHERE recipe_id  = :recipe_id"
	instructions = g.conn.execute(text(instructionsQuery), {"recipe_id": recipe_id}).fetchall()

	# Render a template to display the recipe's details
	return render_template("recipe_detail.html", recipe=recipe, ingredients=ingredients, user_liked=user_liked, instructions=instructions)

@app.route('/like_recipe/<recipe_id>', methods=['POST'])
@login_required
def like_recipe(recipe_id):
	user_id = session['user_id']
	insert_query = """
	INSERT INTO recipe_likes (user_id, recipe_id) VALUES (:user_id, :recipe_id)
	"""
	print("user_id", user_id)
	print("recipe_id", recipe_id)
	prms = {"user_id": user_id, "recipe_id": recipe_id}
	g.conn.execute(text(insert_query), prms)

	update_like_count_query = """
	UPDATE recipe SET like_count = like_count + 1 WHERE recipe_id = :recipe_id
	"""
	g.conn.execute(text(update_like_count_query), {"recipe_id": recipe_id})

	g.conn.commit()

	return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/user/<user_id>')
@login_required
def user_liked_recipes(user_id):
	# Query the database for liked recipes
	query = """
	SELECT recipe.*
	FROM recipe
	JOIN recipe_likes ON recipe.recipe_id = recipe_likes.recipe_id
	WHERE recipe_likes.user_id = :user_id
	"""
	liked_recipes = g.conn.execute(text(query), {"user_id": user_id}).fetchall()
	
	profile_query = """
	SELECT profile_information FROM users WHERE user_id = :user_id
	"""
	profile_result = g.conn.execute(text(profile_query), {"user_id": user_id}).fetchone()
	
	followers_query = """
	SELECT users.user_id, users.username FROM users
	JOIN user_followers ON users.user_id = user_followers.follower_id
	WHERE user_followers.followee_id = :user_id
    """
	followers = g.conn.execute(text(followers_query), {"user_id": user_id}).fetchall()

	favorite_dishes_query = """
    SELECT favorite_dishes FROM users WHERE user_id = :user_id
    """
	favorite_dishes_result = g.conn.execute(text(favorite_dishes_query), {"user_id": user_id}).fetchone()
	favorite_dishes = favorite_dishes_result[0] if favorite_dishes_result else []
	
	return render_template('profile.html', recipes=liked_recipes, profile_result=profile_result, followers=followers, favorite_dishes=favorite_dishes)

@app.route('/login', methods=['POST'])
def login():
	username = request.form['username']
	password = request.form['password']

	# Query the database for the user
	query = "SELECT user_id, password FROM users WHERE username = :username"
	user = g.conn.execute(text(query), {"username": username}).fetchone()
	if user and user.password == password:
		# If the user exists and password is correct, log them in
		print("success")
		session['user_id'] = user.user_id  # Start a session
		return redirect(url_for('index'))
	else:
		flash('Invalid username or password')
		return redirect(url_for('index'))
	
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
