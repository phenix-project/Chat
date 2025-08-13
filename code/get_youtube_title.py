
import yt_dlp
# NOTE: install with command like:  pip install yt_dlp

def run(fn):
  ydl_opts = {}
  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info_dict = ydl.extract_info(fn, download=False)
    display_id = info_dict['display_id']
    video_title = info_dict['title']
    short_title = video_title.replace(" ","")
    f = open('%s.txt' %(short_title),'w')
    print(video_title, file =f)
    #text = open('old/video_%s.txt' %(display_id)).read()
    #print("\n%s" %(text), file =f)
    f.close()
    print("Wrote title and text to %s" %('%s.txt' %(short_title)))

if __name__ == "__main__":
   import sys
   fn = sys.argv[1]
   run(fn)
