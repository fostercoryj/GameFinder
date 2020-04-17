from flask import Flask, render_template, request, redirect, flash, session
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
import re
configfiletest = '*******GONNA BE HARD TO MISS THIS*******'