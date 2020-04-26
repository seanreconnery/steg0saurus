import os
from flask import Flask, flash, request, redirect, url_for, render_template, Markup
from werkzeug.utils import secure_filename
from stegano import lsb, tools

# define the default folder paths for uploading files + where the example images are stored
UPLOAD_FOLDER = os.path.abspath(os.path.dirname(__file__)) + "/uploads"
EXAMPLES_FOLDER = os.path.abspath(os.path.dirname(__file__)) + "/examples"
OUTGUESS_FOLDER = os.path.abspath(os.path.dirname(__file__)) + "/outguess"
CICADA_FOLDER = os.path.abspath(os.path.dirname(__file__)) + "/cicada3301"

# specify the filetypes that are allowed
ALLOWED_OG_IMGS = set(['jpg', 'jpeg'])
ALLOWED_STEGANO = set(['png', 'bmp'])
ALLOWED_EXTENSIONS = set(['png', 'bmp', 'jpg', 'txt'])

app = Flask(__name__)

# limit the upload size to a 5mb file
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024

# set the folders as defined above
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EXAMPLES_FOLDER'] = EXAMPLES_FOLDER
app.config['OUTGUESS_FOLDER'] = OUTGUESS_FOLDER
app.config['CICADA_FOLDER'] = CICADA_FOLDER

app.secret_key = "YOUR.SECRET.API.KEY.HERE"

# function to check if the filetype is allowed to be uploaded as set above
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# define OutGuess 
def allowed_file_OG(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_OG_IMGS
# define Stegano
def allowed_file_STEGANO(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_STEGANO
# define DeepScan
def allowed_file_JPG(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_OG_IMGS


####### INDEX PAGE
@app.route('/', methods=['GET', 'POST'])
def index_file():
    return render_template('layouts/index.html')


####### DEEP SCAN #######
@app.route('/deepscan', methods=['GET', 'POST'])
def deepscan():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'deepscan' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['deepscan']

        # if user does not select file or the browser
        # sent an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file_JPG(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            thisimg = url_for('uploaded_file', filename=filename)
            imgfile = "/home/lukeslytalker/deploy/uploads/" + filename

            with open(imgfile, 'rb') as f:
                # read in file
                s = f.read()

            pkscan = ""
            # find(byte-string, start, end)
            found = s.find(b'\xFF\xC0\x00\x11\x08')  # PIXEL KNOT string
            if found == -1:
                # didn't find PK string
                pkscan = "<p><b>Found <span style='color: #f01723'><u>NO</u></span> indication of <span style='color: #f01723'>PIXEL KNOT</span></b><br>"
            else:
                # found PK string
                pkscan = "<p><b><span style='color: #f01723'><u>FOUND</u></span> indications of <span style='color: #f01723'>PIXEL KNOT</span></b><br>"


            stegd = '/home/lukeslytalker/deploy/./steg-check.sh /home/lukeslytalker/deploy/uploads/' + filename
            stream = os.popen(stegd)
            output = stream.readlines()
            results = ""
            for x in output:
                results = results + x

            sdheader = "<br>Image Scanned:  <br><img src='" + thisimg + "' class='img-fluid' border='0' width='23%'>"

            sdata = sdheader + "<br><span style='font-size: 23px;'>" + pkscan + results + "</span>"

            return render_template('out.html', message=Markup("<span class='text-dark text-center'><h1><u>Analysis Results</u>:  </h1></span><span class='text-dark text-left'>" + sdata + "</span>"))

    return render_template('out.html')


####### STEGANO / EMBED #######
@app.route('/stegano/hide', methods=['GET', 'POST'])
def stegano_hide():
    if request.method == 'POST':
        # check if the POST request contains a file
        if 'file' not in request.files:
            flash('No cover image')
            return redirect(request.url)
        file = request.files['file']
        secretmsg = request.form['txtmsg']

        # if user does not select a valid file (or if the browser somehow doesn't have it)
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # everything's cool--there's a file & its extentions are allowed
        if file and allowed_file_STEGANO(file.filename):
            # create a variable that holds the filename & saves it to the "uploads" folder
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # use Stegano's tools to open the image for analysis
            theimg = tools.open_image(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # use Stegano [LSB method] to hide data (txtmsg, passed from FORM) in an image (theimg)
            secret = lsb.hide(theimg, secretmsg)
            # save the stego'ed image as a new file with the prefix "steg-"
            secret.save("/home/lukeslytalker/deploy/uploads/steg-" + filename)

            # get the URL for the steg'ed image so we can display it for the
            # user to Right Click on and download.
            thisimg = url_for('uploaded_file', filename="steg-" + filename)

            # create the HTML to display the newly generated image
            # and confirm that the data did indeed embed by displaying it
            # using LSB.REVEAL
            themsg = '<h2><span class="text-dark"><em>Your Stegoed image:</em></span></h2>'
            themsg = themsg + '<img class="img-fluid" src="' + thisimg + '" border="0" height="17%"><br><br>'
            themsg = themsg + '<h4 class="text-dark">Right Click -- Save Image As</h4>'
            themsg = themsg + '<p class="text-dark"><b>Embedded Message:</b>  ' + str(lsb.reveal("deploy/uploads/steg-" + filename))
            # render the template and inject the generated HTML in thru the message variable
            return render_template('out.html', message=Markup(themsg))

    return render_template('out.html')

####### STEGANO {scan} #######
@app.route('/stegano/scan', methods=['GET', 'POST'])
def stegano_scan():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'digfile' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['digfile']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file_STEGANO(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #return redirect(url_for('uploaded_file', filename=filename))
            theimg = tools.open_image(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            ## use Stegano [LSB method] to hide data (txtmsg, passed from FORM) in an image (theimg)
            themsg = str(lsb.reveal(theimg))


            thisimg = url_for('uploaded_file', filename=filename)
            sdheader = "<br>Image Scanned:  <br><img src='" + thisimg + "' class='img-fluid' border='0' width='23%'>"
            stegf = "Data Found:  "

            if themsg == '' or themsg == 'None':
                # no result
                result = sdheader + "<br><span>No data found</span>"
            else:
                # found something
                result = sdheader + "<br><span>" + stegf + themsg + "</span>"

            return render_template('out.html', message=Markup("<span class='text-dark text-center'><h1>Stegano:</h1>" + result + "</span>"))



            return render_template('out.html', message=Markup("<span class='text-dark'><h1>Stegano:  </h1>" + themsg + "</span>"))

    return render_template('out.html')


####### OUTGUESS {embed} #######
@app.route('/outguess/hide', methods=['GET', 'POST'])
def outguess_hide():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'ofile' not in request.files:
            flash('No cover image')
            return redirect(request.url)
        file = request.files['ofile']

        if 'hidefile' not in request.files:
            flash('No file to hide')
            return redirect(request.url)
        hidefile = request.files['hidefile']
        passw = request.form['passw']

        # if user does not select a file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No cover image selected')
            return redirect(request.url)
        if file and allowed_file_OG(file.filename) and hidefile:
            # cover image:
            filename = secure_filename(file.filename)
            # file to hide:
            hideout = secure_filename(hidefile.filename)
            # save the file:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            hidefile.save("/home/lukeslytalker/deploy/outguess/" + hideout)
            hfilepath = "/home/lukeslytalker/deploy/outguess/" + hideout
            cfilepath = "/home/lukeslytalker/deploy/uploads/" + filename
            stegpath = "/home/lukeslytalker/deploy/outguess/outguess-"
            outgcom = '/home/lukeslytalker/outguess/./outguess -k "' + passw + '" -d ' + hfilepath + ' -F- ' + cfilepath + ' ' + stegpath + filename
            stream = os.popen(outgcom)
            output = stream.readlines()
            results = ""
            for x in output:
                results = results + x + "<br>"

            outgimg = url_for('outguess_file', filename=("outguess-" + filename))

            themsg = '<h2><span class="text-dark"><em>Your Stegoed image:</em></span></h2>'
            themsg = themsg + '<img class="img-fluid" src="' + outgimg + '" border="0" width="23%"><br><br>'
            themsg = themsg + '<h4 class="text-dark">Right Click -- Save Image As</h4>'
            themsg = themsg + '<br><hr>OutGuess Embedding Output<br>' + results

            return render_template('out.html', message=Markup("<span class='text-dark'>" + themsg + "</span>"))

    return render_template('out.html')



####### OUTGUESS / SCAN #######
@app.route('/outguess/scan', methods=['GET', 'POST'])
def outguess_scan():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'outgfile' not in request.files:
            flash('No image selected')
            return redirect(request.url)
        file = request.files['outgfile']
        passwd = request.form['passwd']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file_OG(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if passwd == "":
                # no password supplied, run OutGuess without -k
                outgcom = '/home/lukeslytalker/deploy/./scan_outguess_nopw.sh /home/lukeslytalker/deploy/uploads/' + filename
            else:
                outgcom = '/home/lukeslytalker/deploy/./scan_outguess.sh /home/lukeslytalker/deploy/uploads/' + filename + ' ' + passwd
            stream = os.popen(outgcom)
            thisimg = url_for('uploaded_file', filename=filename)
            output = stream.readlines()
            results = "Image Scanned:  <img src='" + thisimg + "' class='img-fluid' border='0' width='23%'>"
            for x in output:
                results = results + "<br>" + x

            return render_template('out.html', message=Markup("<span class='text-dark'>" + results + "</span>"))

    return render_template('out.html')

####### STEGDETECT / SCAN #######
@app.route('/stegdetect', methods=['GET', 'POST'])
def stegdetect():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'stegdet' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['stegdet']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file_JPG(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Get sensitivity level
            sens = request.form['sens']

            stegd = '/home/lukeslytalker/stegdetect/./stegdetect -s ' + sens + ' /home/lukeslytalker/deploy/uploads/' + filename
            stream = os.popen(stegd)
            output = stream.read()

            thisimg = url_for('uploaded_file', filename=filename)
            sdheader = "<br>Image Scanned @ Sensitivity [" + sens + "]:  <br><img src='" + thisimg + "' class='img-fluid' border='0' width='23%'>"
            stegdetected = ''

            data = output.split(": ", 1)
            for x in data:
                stegdetected = x

            stegd = sdheader + "<br><span class='text-red'>" + stegdetected + "</span>"
            if stegdetected == "negative":
                return render_template('out.html', message=Markup("<span class='text-dark text-center'><b>StegDetect</b></em> didn't seem to find anything...<br>Consider trying a program-specific scan as <b>StegDetect</b> is prone to <b><em>false negatives</em> sometimes</b>"))
            else:
                return render_template('out.html', message=Markup("<span class='text-dark text-center'><h1><u>StegDetect</u>:  " + stegd + "</h1></span>"))

    return render_template('out.html')


##### JSTEG / SCAN #######
@app.route('/jsteg/scan', methods=['GET', 'POST'])
def jsteg_scan():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'jsteg' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['jsteg']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No image selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            jstegd = '/home/lukeslytalker/./jsteg reveal /home/lukeslytalker/deploy/uploads/' + filename
            stream = os.popen(jstegd)
            data = stream.readlines()

            thisimg = url_for('uploaded_file', filename=filename)
            sdheader = "<br>Image Scanned:  <br><img src='" + thisimg + "' class='img-fluid' border='0' width='23%'>"
            jstegf = "Data Found:  <span class='text-red'>"

            jstegout = ''
            for x in data:
                jstegout = jstegout + x

            if jstegout == '':
                # no result
                result = sdheader + "<br><span class='text-red'>No data found"
            else:
                # found something
                result = sdheader + "<br><span class='text-red'>" + jstegout + "</span>"

            return render_template('out.html', message=Markup("<span class='text-dark text-center'><h1>JSteg:</h1>" + result + "</span></span>"))

    return render_template('out.html')


####### JSTEG / EMBED #######
@app.route('/jsteg/hide', methods=['GET', 'POST'])
def jsteg_hide():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No cover image')
            return redirect(request.url)
        file = request.files['file']
        secret = request.files['jshide']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '' or secret.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            hidefile = secure_filename(secret.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            secret.save(os.path.join(app.config['UPLOAD_FOLDER'], hidefile))
            cover = '/home/lukeslytalker/deploy/uploads/' + filename
            hide = '/home/lukeslytalker/deploy/uploads/' + hidefile
            steg = '/home/lukeslytalker/deploy/uploads/jsteg-' + filename
            jscom = '/home/lukeslytalker/./jsteg hide ' + cover + ' ' + hide + ' ' + steg
            stream = os.popen(jscom)
            jstegout = ''
            jstegout = stream.read()
            if jstegout == '':
                # success
                thisimg = url_for('uploaded_file', filename="jsteg-" + filename)
                themsg = '<h2><span class="text-light"><em>Your Stegoed image:</em></span></h2>'
                themsg = themsg + '<img class="img-fluid" src="' + thisimg + '" border="0" height="17%"><br><br>'
                themsg = themsg + '<h4 class="text-light">Right Click -- Save Image As</h4>'
            else:
                themsg = "JSteg Error:  " + jstegout
            return render_template('out.html', message=Markup("<span class='text-dark text-center'><h1>JSteg:</h1>" + themsg + "</span>"))

    return render_template('out.html')




from flask import send_from_directory

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

from werkzeug.middleware.shared_data import SharedDataMiddleware
app.add_url_rule('/uploads/<filename>', 'uploaded_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/uploads':  app.config['UPLOAD_FOLDER']
})


@app.route('/examples/<filename>')
def example_file(filename):
    return send_from_directory(app.config['EXAMPLES_FOLDER'],
                               filename)
from werkzeug.middleware.shared_data import SharedDataMiddleware

app.add_url_rule('/examples/<filename>', 'example_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/examples':  app.config['EXAMPLES_FOLDER']
})


@app.route('/outguess/<filename>')
def outguess_file(filename):
    return send_from_directory(app.config['OUTGUESS_FOLDER'], filename)

from werkzeug.middleware.shared_data import SharedDataMiddleware

app.add_url_rule('/outguess/<filename>', 'outguess_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/outguess':  app.config['OUTGUESS_FOLDER']
})


@app.route('/cicada3301/<filename>')
def cicada_file(filename):
    return send_from_directory(app.config['CICADA_FOLDER'], filename)

from werkzeug.middleware.shared_data import SharedDataMiddleware

app.add_url_rule('/cicada3301/<filename>', 'cicada_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/cicada3301':  app.config['CICADA_FOLDER']
})

####### STEGANO / EMBED #######
@app.route('/stegano/hide', methods=['GET', 'POST'])
def stegano_hide():
    if request.method == 'POST':
        # check if the POST request contains a file
        if 'file' not in request.files:
            flash('No cover image')
            return redirect(request.url)
        file = request.files['file']
        secretmsg = request.form['txtmsg']

        # if user does not select a valid file (or if the browser somehow doesn't have it)
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # everything's cool--there's a file & its extentions are allowed
        if file and allowed_file(file.filename):
            # create a variable that holds the filename & saves it to the "uploads" folder
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # use Stegano's tools to open the image for analysis
            theimg = tools.open_image(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # use Stegano [LSB method] to hide data (txtmsg, passed from FORM) in an image (theimg)
            secret = lsb.hide(theimg, secretmsg)
            # save the stego'ed image as a new file with the prefix "steg-"
            secret.save("/home/lukeslytalker/deploy/uploads/steg-" + filename)

            # get the URL for the steg'ed image so we can display it for the
            # user to Right Click on and download.
            thisimg = url_for('uploaded_file', filename="steg-" + filename)

            # create the HTML to display the newly generated image
            # and confirm that the data did indeed embed by displaying it
            # using LSB.REVEAL
            themsg = '<h2><span class="text-dark"><em>Your Stegoed image:</em></span></h2>'
            themsg = themsg + '<img class="img-fluid" src="' + thisimg + '" border="0" height="17%"><br><br>'
            themsg = themsg + '<h4 class="text-dark">Right Click -- Save Image As</h4>'
            themsg = themsg + '<p class="text-dark"><b>Embedded Message:</b>  ' + str(lsb.reveal("deploy/uploads/steg-" + filename))
            # render the template and inject the generated HTML in thru the message variable
            return render_template('out.html', message=Markup(themsg))

    return render_template('out.html')

####### STEGANO {scan} #######
@app.route('/stegano/scan', methods=['GET', 'POST'])
def stegano_scan():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'digfile' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['digfile']

        # if user does not select file...
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            theimg = tools.open_image(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # use Stegano [LSB method] to hide data (txtmsg, passed from FORM) in an image (theimg)
            # store the resulting data into the variable 'themsg'
            themsg = str(lsb.reveal(theimg))

            # grab the URL for the uploaded image so we can display it for the user with the results
            thisimg = url_for('uploaded_file', filename=filename)
            sdheader = "<br>Image Scanned:  <br><img src='" + thisimg + "' class='img-fluid' border='0' width='23%'>"
            stegf = "Data Found:  <span class='text-red'>"

            # check for a result
            if themsg == '' or themsg == 'None':
                # no result
                result = sdheader + "<br><span class='text-red'>No data found"
            else:
                # found something
                result = sdheader + "<br><span class='text-red'>" + stegf + themsg + "</span>"
            # render the template and inject the generated result + HTML
            return render_template('out.html', message=Markup("<span class='text-dark text-center'><h1>Stegano:</h1>" + result + "</span></span>"))

    return render_template('out.html')


####### OUTGUESS {embed} #######
@app.route('/outguess/hide', methods=['GET', 'POST'])
def outguess_hide():
    if request.method == 'POST':
        # check if the post request has a cover image..
        if 'ofile' not in request.files:
            flash('No cover image')
            return redirect(request.url)
        # set the variable for the COVER IMAGE
        file = request.files['ofile']
        # check if there's data to actually embed
        if 'hidefile' not in request.files:
            flash('No file to hide')
            return redirect(request.url)
        # set the variables for the HIDDEN DATA and the KEY/PASSWORD (if there is one)
        hidefile = request.files['hidefile']
        passw = request.form['passw']

        # make sure the user has supplied the necessary files
        if file.filename == '':
            flash('No cover image selected')
            return redirect(request.url)
        if file and allowed_file(file.filename) and hidefile:
            # cover image:
            filename = secure_filename(file.filename)
            # file to hide:
            hideout = secure_filename(hidefile.filename)
            # save the file:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            hidefile.save("/home/lukeslytalker/deploy/outguess/" + hideout)
            # set the paths for the cover image, hide file, output path, and the command string to pass to the console
            hfilepath = "/home/lukeslytalker/deploy/outguess/" + hideout
            cfilepath = "/home/lukeslytalker/deploy/uploads/" + filename
            stegpath = "/home/lukeslytalker/deploy/outguess/outguess-"
            outgcom = '/home/lukeslytalker/outguess/./outguess -k "' + passw + '" -d ' + hfilepath + ' -F- ' + cfilepath + ' ' + stegpath + filename
            # pass the OutGuess command to the terminal
            stream = os.popen(outgcom)
            output = stream.readlines()
            # grab the output from OutGuess, line by line, and store into the variable "results"
            results = ""
            for x in output:
                results = results + x + "<br>"

            # get the URL for the newly generated STEGO image so we can display it for the user to download
            outgimg = url_for('outguess_file', filename=("outguess-" + filename))
            # build the HTML response
            themsg = '<h2><span class="text-dark"><em>Your Stegoed image:</em></span></h2>'
            themsg = themsg + '<img class="img-fluid" src="' + outgimg + '" border="0" width="23%"><br><br>'
            themsg = themsg + '<h4 class="text-dark">Right Click -- Save Image As</h4>'
            themsg = themsg + '<br><hr>OutGuess Embedding Output<br>' + results
            # render the template and injec the generated HTML results
            return render_template('out.html', message=Markup("<span class='text-dark'>" + themsg + "</span>"))

    return render_template('out.html')

####### OUTGUESS / SCAN #######
@app.route('/outguess/scan', methods=['GET', 'POST'])
def outguess_scan():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'outgfile' not in request.files:
            flash('No image selected')
            return redirect(request.url)
        file = request.files['outgfile']
        passwd = request.form['passwd']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if passwd == "":
                # no password supplied, run OutGuess without -k
                outgcom = '/home/lukeslytalker/deploy/./scan_outguess_nopw.sh /home/lukeslytalker/deploy/uploads/' + filename
            else:
                outgcom = '/home/lukeslytalker/deploy/./scan_outguess.sh /home/lukeslytalker/deploy/uploads/' + filename + ' ' + passwd
            stream = os.popen(outgcom)
            output = stream.readlines()
            thisimg = url_for('uploaded_file', filename=filename)
            results = "Image Scanned:  <img src='" + thisimg + "' class='img-fluid' border='0' width='23%'>"
            for x in output:
                results = results + "<br>" + x

            return render_template('out.html', message=Markup("<span class='text-dark'>" + results + "</span>"))

    return render_template('out.html')

####### STEGDETECT / SCAN #######
@app.route('/stegdetect', methods=['GET', 'POST'])
def stegdetect():
    if request.method == 'POST':
        # check if the post request has the file
        if 'stegdet' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['stegdet']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            stegd = '/home/lukeslytalker/stegdetect/./stegdetect -t jopifa /home/lukeslytalker/deploy/uploads/' + filename
            stream = os.popen(stegd)
            output = stream.read()

            thisimg = url_for('uploaded_file', filename=filename)
            sdheader = "<br>Image Scanned:  <br><img src='" + thisimg + "' class='img-fluid' border='0' width='23%'>"

            data = output.split(": ", 1)
            for x in data:
                stegdetected = x

            stegd = sdheader + "<br><span class='text-red'>" + stegdetected + "</span>"
            if stegdetected == "negative":
                return render_template('out.html', message=Markup("<span class='text-dark text-center'><b>StegDetect</b></em> didn't seem to find anything...<br>Consider trying a program-specific scan as <b>StegDetect</b> is prone to <b><em>false negatives</em></b>"))
            else:
                return render_template('out.html', message=Markup("<span class='text-dark text-center'><h1><u>StegDetect</u>:  " + stegd + "</h1></span>"))

    return render_template('out.html')


##### JSTEG / SCAN #######
@app.route('/jsteg/scan', methods=['GET', 'POST'])
def jsteg_scan():
    if request.method == 'POST':

        if 'jsteg' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['jsteg']

        if file.filename == '':
            flash('No image selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            jstegd = '/home/lukeslytalker/./jsteg reveal /home/lukeslytalker/deploy/uploads/' + filename
            stream = os.popen(jstegd)
            data = stream.readlines()

            thisimg = url_for('uploaded_file', filename=filename)
            sdheader = "<br>Image Scanned:  <br><img src='" + thisimg + "' class='img-fluid' border='0' width='23%'>"
            jstegf = "Data Found:  <span class='text-red'>"

            jstegout = ''
            for x in data:
                jstegout = jstegout + x

            if jstegout == '':
                # no result
                result = sdheader + "<br><span class='text-red'>No data found"
            else:
                # found something
                result = sdheader + "<br><span class='text-red'>" + jstegout + "</span>"

            return render_template('out.html', message=Markup("<span class='text-dark text-center'><h1>JSteg:</h1>" + result + "</span></span>"))

    return render_template('out.html')


####### JSTEG / EMBED #######
@app.route('/jsteg/hide', methods=['GET', 'POST'])
def jsteg_hide():
    if request.method == 'POST':

        if 'file' not in request.files:
            flash('No cover image')
            return redirect(request.url)
        file = request.files['file']
        secret = request.files['jshide']

        if file.filename == '' or secret.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            hidefile = secure_filename(secret.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            secret.save(os.path.join(app.config['UPLOAD_FOLDER'], hidefile))
            cover = '/home/lukeslytalker/deploy/uploads/' + filename
            hide = '/home/lukeslytalker/deploy/uploads/' + hidefile
            steg = '/home/lukeslytalker/deploy/uploads/jsteg-' + filename
            jscom = '/home/lukeslytalker/./jsteg hide ' + cover + ' ' + hide + ' ' + steg
            stream = os.popen(jscom)
            jstegout = ''
            jstegout = stream.read()
            if jstegout == '':
                # success
                thisimg = url_for('uploaded_file', filename="jsteg-" + filename)
                themsg = '<h2><span class="text-light"><em>Your Stegoed image:</em></span></h2>'
                themsg = themsg + '<img class="img-fluid" src="' + thisimg + '" border="0" height="17%"><br><br>'
                themsg = themsg + '<h4 class="text-light">Right Click -- Save Image As</h4>'
            else:
                themsg = "JSteg Error:  " + jstegout
            return render_template('out.html', message=Markup("<span class='text-dark text-center'><h1>JSteg:</h1>" + themsg + "</span>"))

    return render_template('out.html')


from flask import send_from_directory

# view a file stored in the UPLOADS folder (by filename)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


app.add_url_rule('/uploads/<filename>', 'uploaded_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/uploads':  app.config['UPLOAD_FOLDER']
})


# view a file stored in the EXAMPLES folder (by filename)
@app.route('/examples/<filename>')
def example_file(filename):
    return send_from_directory(app.config['EXAMPLES_FOLDER'],
                               filename)

app.add_url_rule('/examples/<filename>', 'example_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/examples':  app.config['EXAMPLES_FOLDER']
})


# view a file stored in the OUTGUESS folder (by filename)
@app.route('/outguess/<filename>')
def outguess_file(filename):
    return send_from_directory(app.config['OUTGUESS_FOLDER'], filename)

app.add_url_rule('/outguess/<filename>', 'outguess_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/outguess':  app.config['OUTGUESS_FOLDER']
})


# view a file stored in the CICADA3301 EXAMPLES folder (by filename)
@app.route('/cicada3301/<filename>')
def cicada_file(filename):
    return send_from_directory(app.config['CICADA_FOLDER'], filename)

app.add_url_rule('/cicada3301/<filename>', 'cicada_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/cicada3301':  app.config['CICADA_FOLDER']
})
