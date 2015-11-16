#!/usr/bin/python

import vte,gtk,re,time
from thread import start_new_thread
from collections import deque
import threading
import yaml
from string import Template
import os

#queue = deque([["proxychains4 ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no hutama@papi1",False],
#			["sudo rpm -qa | grep linux",True],
#			["sudo netstat -tulpn",True]
#			])

class TerminalScrap(threading.Thread):
	cont = False
	filename = "out.png"
	
	def append_queue(self,item):
		self.queue.append(item)
		print "insert", item
	
	def text_changed(self,term):
		self.cont = True
		print "text changed"

	def get_screenshot(self):
		print "thread 'screenshot' started"
		while (not self.cont):
			time.sleep(1)
			continue
		self.cont = False
		while True:
			while len(self.queue) == 0:
				time.sleep(1)
				continue
			self.reset()
			time.sleep(1)
			command = self.queue.popleft()
			print "command = ",command
			if command[1]:
				self.run_command_and_snapshot(command[0])
			else:
				self.run_command_and_wait(command[0])

	def reset(self):
		print "run reset"
		gtk.threads_enter()
		self.term.feed_child("reset\n")
		gtk.threads_leave()
		time.sleep(2)
		self.cont = False

	def run_command_and_wait(self,command):
		self.cont = False
		print "run command and wait ",command
		print "cont = ",self.cont
		gtk.threads_enter()
		self.term.feed_child(command+"\n")
		gtk.threads_leave()
		while (not self.cont):
			time.sleep(5)
			continue
		self.cont = False
		print "leave run_command_and_wait"

	def run_command_and_snapshot(self,command):
		self.cont = False
		print "run command and snap ",command
		print "cont = ",self.cont
		gtk.threads_enter()
		self.term.feed_child(command+"\n")
		gtk.threads_leave()
		while (not self.cont):
			time.sleep(1)
			continue
		self.cont = False
		gtk.threads_enter()
		text = self.term.get_text()
		print repr(text)
		words = re.findall(r'(?<=\n)(\n)(?=\n)', text)
		print "words",words
		print "words len = ",len(words)
		height = (300 - len(words))*15
		print "height",height
		pixbuf = self.owindow.get_pixbuf()
		cropped_pixbuf = pixbuf.subpixbuf(0,0,1282,height)
		path = 	self.host
		try: 
			os.makedirs(path)
		except OSError:
			if not os.path.isdir(path):
				raise
		cropped_pixbuf.save(path+"/"+self.filename,'png')
		#pixbuf.save('out2.png','png')
		gtk.threads_leave()
		print "screenshot captured"
	
	def __init__(self, filename,host):
		threading.Thread.__init__(self)
		self.queue = deque()
		self.filename = filename
		self.host = host
		
	def run(self):
		self.term = vte.Terminal()
		self.term.fork_command()
		palette = [gtk.gdk.color_parse('red')] * 16
		self.term.set_colors(gtk.gdk.color_parse('black'), gtk.gdk.color_parse('white'), palette)
		self.cont = False
		print "forked"
		self.term.set_size(160,300)
		self.owindow = gtk.OffscreenWindow()
		self.owindow.add(self.term)
		self.owindow.show_all()
		self.handler_id = self.term.connect('contents-changed', self.text_changed)
		start_new_thread(self.get_screenshot,())
		#gtk.gdk.threads_init()
		#gtk.threads_enter()
		#print "entering main loop"
		#gtk.main()
		#gtk.threads_leave()
		print "executed"

if __name__ == "__main__":
	user = ""
	threads = []
	f = file('data.yml','r')
	document = f.read()
	f.close()
	data = yaml.load(document)
	print data
	gtk.gdk.threads_init()
	pre_command = data[0]['pre-command']
	user = data[1]['user']
	
	for i in data:
		if 'host' not in i:
			continue
		for host in i['host']:
			d = dict(host=host,user=user,name=i['name'])
			filename = Template("$name-$host.png").safe_substitute(d)
			snap_thread = TerminalScrap(filename,host)
			precommand = Template(pre_command).safe_substitute(d)
			snap_thread.append_queue([precommand,False])
			if type(i['command']) == str:
				command = Template(i['command']).safe_substitute(d)
			snap_thread.append_queue([command,True])
			threads += [snap_thread]
	for thread in threads:
		thread.run()
	gtk.threads_enter()
	print "entering main loop"
	gtk.main()
	gtk.threads_leave()
