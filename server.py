from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
from MolDisplay import Molecule
import molecule
import io
import urllib;  # code to parse for data
import json


public_files = [ '/index.html', '/script.js'];



class Server(BaseHTTPRequestHandler): 
    def do_GET(self): 
        if self.path in public_files:   # make sure it's a valid file
            self.send_response( 200 );  # OK
            self.send_header( "Content-type", "text/html" );

            fp = open( self.path[1:] ); 
            # [1:] to remove leading / so that file is found in current dir

            # load the specified file
            page = fp.read();
            fp.close();

            # create and send headers
            self.send_header( "Content-length", len(page) );
            self.end_headers();

            # send the contents
            self.wfile.write( bytes( page, "utf-8" ) );
        
        # if self.path == "/":
        #     self.send_response(200);
        #     self.send_header('Content-type', 'text/html'); 
        #     self.send_header("Content-length", len(html)); 
        #     self.end_headers();
        #     self.wfile.write(bytes(html, "utf-8"));

        else:
            #Return 404 error
            self.send_response( 404 );
            self.end_headers();
            self.wfile.write(bytes( "404: not found", "utf-8"));

    def do_POST(self):

        if self.path == "/add":
            # this is specific to 'multipart/form-data' encoding used by POST
            content_length = int(self.headers['Content-Length']);
            body = self.rfile.read(content_length);


            print( repr( body.decode('utf-8') ) );

            # convert POST content into a dictionary
            postvars = urllib.parse.parse_qs( body.decode( 'utf-8' ) );
            

            elementname = postvars['elementnumber']
            elementcode = postvars['elementcode']
            color1 = postvars['color1']
            color2 = postvars['color2']
            color3 = postvars['color3']
            elementradius = postvars['elementradius']
            elementnumber = postvars['elementnumber']

            print(elementname, elementcode, elementnumber, color1, color2, color3, elementradius)

            message = "data received";

            self.send_response( 200 ); # OK
            self.send_header( "Content-type", "application/json" );
            self.end_headers();
            self.wfile.write(json.dumps(response).encode('utf-8'))

            #self.wfile.write( bytes( message, "utf-8" ) );
      # Checks for correct path
        if self.path == "/molecule":
          content_length = int(self.headers["Content-Length"])
          # Read the post data and create a file object
          post_data = self.rfile.read(content_length)
          file_obj = io.StringIO(post_data.decode('utf-8'))
          # Skips 4 lines
          for i in range(4):
            next(file_obj)
        
        
          # Make a molecule object
          mol = Molecule()
          # Parse
          mol.parse(file_obj)
          # SVG data generated
          svg_data = mol.svg()
          self.send_response(200)
          self.send_header("Content-type", "image/svg+xml")
          self.end_headers()
          self.wfile.write(bytes(svg_data, "utf-8"))
        # Otherwise, send a 404 error.
        else: 
            self.send_response(404)




# html = """
# <html>
#     <head>
#         <title> File Upload </title>
#     </head>
#     <body>
#         <h1> File Upload </h1>
#         <form action="molecule" enctype="multipart/form-data" method="post">
#             <p>
#                 <input type="file" id="sdf_file" name="filename"/>
#             </p>
#             <p>
#                 <input type="submit" value="Upload"/>
#             </p>
#         </form>
#     </body>
# </html>
# """;

httpd = HTTPServer( ( 'localhost', int(sys.argv[1]) ), Server );
httpd.serve_forever();
    

