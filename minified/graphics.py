import numpy as np,pygame,sys
class ZX_Spectrum_Graphics:
	def __init__(self,memory,pixel_size):self.screen_width=256;self.screen_height=192;self.pixel_size=pixel_size;self.memory_size=6912;self.memory=memory;self.scr_base_address=16384;self.scr_addr=np.zeros((self.screen_width,self.screen_height,3),dtype=np.uint16);self.buffer=np.zeros((self.screen_width,self.screen_height,3),dtype=np.uint8);self.colors=[(0,0,0),(0,0,200),(200,0,0),(200,0,200),(0,200,0),(0,200,200),(200,200,0),(200,200,200)];self.bright_colors=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)];self.fill_scr_addr();pygame.display.set_caption('ZX Spectrum Emulator')
	def set_screen(self,screen):self.screen=screen
	def fill_scr_addr(self):
		for y in range(self.screen_height):
			for x in range(self.screen_width):byte_index=x//8;address=self.scr_base_address+((y&192)<<5)|(y&56)<<2|((y&7)<<8)+byte_index;attribute_address=self.scr_base_address+6144+y//8*32+byte_index;self.scr_addr[(x,y)][0]=address;self.scr_addr[(x,y)][1]=attribute_address
	def set_pixel(self,x,y,color_index):
		assert 0<=x<self.screen_width,'x coordinate out of bounds';assert 0<=y<self.screen_height,'y coordinate out of bounds';assert 0<=color_index<8,'Invalid color index';byte_index,bit=divmod(x,8);line_offset=y&192|(y&56)>>3|(y&7)<<3;address=self.scr_base_address+line_offset*32+byte_index
		if color_index:self.memory[address]|=1<<7-bit
		else:self.memory[address]&=~(1<<7-bit)
	def set_attribute(self,x,y,ink,paper,bright=False):assert 0<=x<self.screen_width,'x coordinate out of bounds';assert 0<=y<self.screen_height,'y coordinate out of bounds';assert 0<=ink<8,'Invalid ink color index';assert 0<=paper<8,'Invalid paper color index';attribute_address=self.scr_base_address+6144+y//8*32+x//8;attribute=bright<<6|paper<<3|ink;self.memory[attribute_address]=attribute
	def reset_screen(self,ink,paper,bright=False):
		assert 0<=ink<8,'Invalid ink color index';assert 0<=paper<8,'Invalid paper color index';attribute=bright<<6|paper<<3|ink
		for addr in range(768):attribute_address=self.scr_base_address+6144+addr;self.memory.write(attribute_address,attribute)
	def get_pixel_color(self,x,y):
		byte_index,bit=divmod(x,8);address=self.scr_base_address+((y&192)<<5)|(y&56)<<2|((y&7)<<8)+byte_index;pixel_value=self.memory[address]>>7-bit&1;attribute_address=self.scr_base_address+6144+y//8*32+x//8;attribute=self.memory[attribute_address];bright=(attribute&64)>>6;ink=attribute&7;paper=(attribute&56)>>3
		if pixel_value:return self.bright_colors[ink]if bright else self.colors[ink]
		else:return self.bright_colors[paper]if bright else self.colors[paper]
	def get_pixel_color(self,x,y):
		byte_index,bit=divmod(x,8);address=self.scr_base_address+((y&192)<<5)|(y&56)<<2|((y&7)<<8)+byte_index;pixel_value=self.memory.read(address)>>7-bit&1;attribute_address=self.scr_base_address+6144+y//8*32+x//8;attribute=self.memory.read(attribute_address);bright=(attribute&64)>>6;ink=attribute&7;paper=(attribute&56)>>3
		if pixel_value:return self.bright_colors[ink]if bright else self.colors[ink]
		else:return self.bright_colors[paper]if bright else self.colors[paper]
	def generate_new_screen(self):import random;return[[random.choice((0,1))for _ in range(self.screen_width)]for _ in range(self.screen_height)]
	def render_screen_fast2(self):
		buffer=np.zeros((self.screen_width,self.screen_height,3),dtype=np.uint8)
		for y in range(self.screen_height):
			address_y=self.scr_base_address+((y&192)<<5)|(y&56)<<2|(y&7)<<8;attr_address_y=self.scr_base_address+6144+y//8*32
			for x in range(0,self.screen_width,8):
				byte_index=x//8;address=address_y+byte_index;attribute_address=attr_address_y+byte_index;attribute=self.memory[attribute_address];bright=(attribute&64)>>6;ink=attribute&7;paper=(attribute&56)>>3
				for x_offs in range(8):
					xs=x+x_offs;pixel_value=self.memory[address]>>7-x_offs&1
					if pixel_value:buffer[(xs,y)]=self.bright_colors[ink]if bright else self.colors[ink]
					else:buffer[(xs,y)]=self.bright_colors[paper]if bright else self.colors[paper]
		pygame.surfarray.blit_array(self.screen,np.kron(buffer,np.ones((self.pixel_size,self.pixel_size,1),dtype=np.uint8)))
	def render_screen_fast4(self):
		for y in range(0,self.screen_height,8):
			for x in range(0,self.screen_width,8):
				attribute_address=self.scr_addr[(x,y)][1];attribute=self.memory.read(attribute_address);bright=(attribute&64)>>6;ink=attribute&7;paper=(attribute&56)>>3;color_ink=self.bright_colors[ink]if bright else self.colors[ink];color_paper=self.bright_colors[paper]if bright else self.colors[paper]
				for y_offs in range(8):ys=y+y_offs;address=self.scr_addr[(x,ys)][0];value=self.memory.read(address);bits=np.unpackbits(np.array([value],dtype=np.uint8))[:8];pixel_colors=np.array([color_ink if bit else color_paper for bit in bits]);self.buffer[x:x+8,ys]=pixel_colors
		pygame.surfarray.blit_array(self.screen,np.kron(self.buffer,np.ones((self.pixel_size,self.pixel_size,1),dtype=np.uint8)))
	def render_screen_fast(self):
		buffer=np.zeros((self.screen_width,self.screen_height,3),dtype=np.uint8)
		for y in range(self.screen_height):
			for x in range(0,self.screen_width,8):
				attribute_address=self.scr_addr[(x,y)][1];attribute=self.memory.read(attribute_address);bright=(attribute&64)>>6;ink=attribute&7;paper=(attribute&56)>>3;address=self.scr_addr[(x,y)][0]
				for bit in range(8):
					xs=x+bit;pixel_value=self.memory.read(address)>>7-bit&1
					if pixel_value:color=self.bright_colors[ink]if bright else self.colors[ink]
					else:color=self.bright_colors[paper]if bright else self.colors[paper]
					buffer[(xs,y)]=color
		pygame.surfarray.blit_array(self.screen,np.kron(buffer,np.ones((self.pixel_size,self.pixel_size,1),dtype=np.uint8)))
	def render_screen_fast3(self):
		buffer=np.zeros((self.screen_height,self.screen_width,3),dtype=np.uint8);attr_addresses=self.scr_addr[:,:,1].reshape(-1);pixel_addresses=self.scr_addr[:,:,0].reshape(-1);attributes=np.array([self.memory.read(addr)for addr in attr_addresses]);pixels=np.array([self.memory.read(addr)for addr in pixel_addresses]);bright=(attributes&64)>>6;ink=attributes&7;paper=(attributes&56)>>3;ink_colors=np.where(bright[:,np.newaxis],self.bright_colors[ink],self.colors[ink]);paper_colors=np.where(bright[:,np.newaxis],self.bright_colors[paper],self.colors[paper])
		for i in range(8):mask=pixels>>7-i&1;buffer[:,i::8]=np.where(mask[:,np.newaxis],ink_colors,paper_colors).reshape(self.screen_height,-1,3)
		scaled_buffer=np.kron(buffer,np.ones((self.pixel_size,self.pixel_size,1),dtype=np.uint8));pygame.surfarray.blit_array(self.screen,scaled_buffer)
	def render_screen_slow(self):
		buffer=np.zeros((self.screen_width,self.screen_height,3),dtype=np.uint8)
		for y in range(self.screen_height):
			for x in range(self.screen_width):buffer[(x,y)]=self.get_pixel_color(x,y)
	def render_screen(self):self.render_screen_fast4()
	def load_screen(self,pixel_data,attribute_data):assert len(pixel_data)==6144,'Invalid pixel data size';assert len(attribute_data)==768,'Invalid attribute data size';self.memory[self.scr_base_address:self.scr_base_address+6144]=pixel_data;self.memory[self.scr_base_address+6144:]=attribute_data
	def load_scr_file(self,file_path):
		with open(file_path,'rb')as f:
			scr_data=f.read();assert len(scr_data)==6912,'Invalid .scr file size'
			for(i,_)in enumerate(scr_data):
				self.memory[self.scr_base_address+i]=scr_data[i]
				if i%512!=0 and i<6144:continue
				if i%32!=0:continue