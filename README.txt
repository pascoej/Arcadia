This project is a server - client model for a MOBA game. 

To start, run python3 server.py inside termproject folder, install any libraries mentioned in errors. I think (tornado,timeout-decorator,pypng)

pip3 install timeout-decorator pypng tornado

should do it

Server testing done on OSX / Linux. Unkown if there are any quirks on 
windows based machines. You will want to edit the server list at the top of 
the client main.js file if you want to point to your own server that's not
localhost.

The server also shuts down when a game ends, so you have to restart it when this happens,
I prefer using the bash script to auto restart. \

The client files must be hosted somewhere (localhost python -m SimpleHTTPServer
 or http-server package with nodejs work great for this)
 It also should be hosted at http://www.contrib.andrew.cmu.edu/~jpascoe/web/ later


The server is not designed to be run on a laptop with chrome running at the 
same time, low performance may occur in this situation. I prefer a dedicated
server like the one that I have in the defaults in the client. CMU / AWS.

Unsupported on non chrome platforms


To dev client, open web-new folder in term, type npm install and npm stat. 
Builds go in the build folder.