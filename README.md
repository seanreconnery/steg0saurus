# steg0saurus
Python webapp with Flask that provides a GUI interface for leveraging some steganography tools such as StegDetect, Stegano, JSteg, and OutGuess that are installed on the server.  A user can scan images with various steganography tools and receive results back, all through their web browser.  See it in action here:  https://lukeslytalker.pythonanywhere.com

This repo is NOT ready to use out of the box if you're cloning it.  You'll need to have all the necessary steganography tools installed in the specified areas:
 - OutGuess
 - JSteg
 - Stegano
 - StegDetect
 
FUTURE PLANS:
  - adding an "all in one" scan option that will run each tool on a single uploaded image (instead of going tool by tool)
  - increase embedding options --> allow for more filetypes to be embedded images
       * check difference between file sizes of: cover image and file to be embedded  (Cover image needs to be at least ~3-4x larger filesize than file to be embedded)
  - add more embedding options with OutGuess
       * OutGuess supports embedding 2 separate files into the same cover image
           ~ add 2nd option for file ( -D option )
           ~ add 2nd option for password ( -K option )
       * add audio file support for OutGuess
  - add support for ZSTEG (png scan)
  - add support for LSBSteg
  - add support to scan with StegExpose (scans png's for LSB steganography)
  - add support for OpenStego
