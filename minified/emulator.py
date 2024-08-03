import logging,pygame
from memory import Memory
from new_cpu import Z80
from interrupt_controller import InterruptController
from io_controller import IOController
from graphics import ZX_Spectrum_Graphics
from keyboard import Keyboard
import os,const,zipfile,tempfile
def draw_text(surface,text,pos,font,color):rendered_text=font.render(text,True,color);surface.blit(rendered_text,pos)
def draw_rainbow_stripe(surface,height):
	colors=[(0,0,255),(0,255,255),(0,255,0),(255,255,0),(255,0,0),(255,0,255)];stripe_height=height//len(colors)
	for(i,color)in enumerate(colors):pygame.draw.rect(surface,color,(0,i*stripe_height,surface.get_width(),stripe_height))
def process_zip_file(zip_path):
	zip_files=[]
	with zipfile.ZipFile(zip_path,'r')as zip_ref:
		for file in zip_ref.namelist():
			if file.lower().endswith('.z80'):
				with tempfile.NamedTemporaryFile(delete=False,suffix='.z80')as temp_file:temp_file.write(zip_ref.read(file));zip_files.append((f"{os.path.basename(zip_path)}:{file}",temp_file.name))
	return zip_files
def get_rom_files(directory):
	rom_files=[]
	for(root,dirs,files)in os.walk(directory):
		for file in files:
			if file.lower().endswith(('.rom','.bin','.z80','.zip','.scr','.sna')):
				full_path=os.path.join(root,file)
				if file.lower().endswith('.zip'):rom_files.extend(process_zip_file(full_path))
				else:rom_files.append((file,full_path))
	return rom_files
def zx_spectrum_menu():
	pygame.init();screen=pygame.display.set_mode((640,480));pygame.display.set_caption('ZX Spectrum ROM Selector');BLACK=0,0,0;WHITE=255,255,255;CYAN=0,255,255;MAGENTA=255,0,255;font=pygame.font.Font(None,32);files=get_rom_files('.');rom48=next((i for(i,(file_name,file_path))in enumerate(files)if file_name=='48.rom'),None);rom128=next((i for(i,(file_name,file_path))in enumerate(files)if file_name=='128k.rom'),None);selected=0;scroll_offset=0;max_visible=11;rainbow_height=30;running=True
	while running:
		screen.fill(BLACK);draw_rainbow_stripe(screen,rainbow_height);draw_text(screen,'ZX Spectrum ROM Selector',(20,rainbow_height+10),font,CYAN);draw_text(screen,'Use UP/DOWN to select, ENTER to load',(20,rainbow_height+50),font,WHITE)
		for i in range(max_visible):
			index=scroll_offset+i
			if index<len(files):color=MAGENTA if index==selected else WHITE;draw_text(screen,files[index][0],(40,rainbow_height+90+i*30),font,color)
		pygame.display.flip()
		for event in pygame.event.get():
			if event.type==pygame.QUIT:return
			if event.type==pygame.KEYDOWN:
				if event.key==pygame.K_UP:
					selected=(selected-1)%len(files)
					if selected<scroll_offset:scroll_offset=selected
					elif selected>=scroll_offset+max_visible:scroll_offset=max(0,selected-max_visible+1)
				elif event.key==pygame.K_DOWN:
					selected=(selected+1)%len(files)
					if selected>=scroll_offset+max_visible:scroll_offset=selected-max_visible+1
					elif selected<scroll_offset:scroll_offset=selected
				elif event.key==pygame.K_RETURN:pygame.quit();return files[selected],files[rom48],files[rom128]
	pygame.quit()
class ZX_Spectrum_Emulator:
	def __init__(self):self.pixel_size=2;self.border_size=80;self.memory=Memory();self.io_controller=IOController(self);self.cpu=Z80(self.memory,self.io_controller,0);self.interrupt_controller=InterruptController(self.cpu);self.graphics=ZX_Spectrum_Graphics(self.memory,self.pixel_size);self.keyboard=Keyboard(self.io_controller);self.reset_requested=False
	def load_rom(self,file_path,addr=0):self.memory.load_rom(file_path,0)
	def load_rom128(self,file_path,addr=0):self.memory.load_rom128(file_path)
	def load_scr_file(self,file_path):self.graphics.load_scr_file(file_path)
	def set_border(self,color):0
	def reset(self):self.cpu.reset();self.memory.reset();self.reset_requested=False;print('CPU reset performed')
	def emulate_load_screen(self,file_path):
		pygame.init();main_screen=pygame.display.set_mode((self.graphics.screen_width*self.pixel_size+self.border_size*2,self.graphics.screen_height*self.pixel_size+self.border_size*2));pygame.display.set_caption('ZX Spectrum Emulator');screen=pygame.Surface((self.graphics.screen_width*self.pixel_size,self.graphics.screen_height*self.pixel_size));border=pygame.Surface((self.graphics.screen_width*self.pixel_size+self.border_size*2,self.graphics.screen_height*self.pixel_size+self.border_size*2));self.graphics.set_screen(screen);self.load_scr_file(file_path);clock=pygame.time.Clock();running=True
		while running:
			for event in pygame.event.get():
				if event.type==pygame.QUIT:running=False
			self.graphics.render_screen();pygame.draw.rect(border,self.graphics.colors[1],(0,0,border.get_width(),border.get_height()));main_screen.blit(border,(0,0));main_screen.blit(screen,(self.border_size,self.border_size));pygame.display.flip()
		pygame.quit()
	def emulate(self):
		pygame.init();left_panel_width=460;main_screen=pygame.display.set_mode((self.graphics.screen_width*self.pixel_size+left_panel_width+self.border_size*2,self.graphics.screen_height*self.pixel_size+self.border_size*2));pygame.display.set_caption('ZX Spectrum Emulator');screen=pygame.Surface((self.graphics.screen_width*self.pixel_size,self.graphics.screen_height*self.pixel_size));border=pygame.Surface((self.graphics.screen_width*self.pixel_size+self.border_size*2,self.graphics.screen_height*self.pixel_size+self.border_size*2));self.graphics.set_screen(screen);state_window=pygame.Surface((left_panel_width,self.graphics.screen_height*self.pixel_size+self.border_size*2));pygame.draw.rect(border,self.graphics.colors[self.io_controller.border_color],(0,0,border.get_width(),border.get_height()));main_screen.blit(border,(0,0));main_screen.blit(screen,(self.border_size,self.border_size));main_screen.blit(state_window,(self.graphics.screen_width*self.pixel_size+self.border_size*2,0));font=pygame.font.SysFont('Courier',18);clock=pygame.time.Clock();running=True;i=0
		while running:
			for event in pygame.event.get():
				if event.type==pygame.QUIT:running=False
				elif event.type==pygame.KEYDOWN:
					if event.key==pygame.K_F1:return'OPEN_MENU'
					elif event.key==pygame.K_F2:self.reset_requested=True
			if self.reset_requested:self.reset()
			self.keyboard.read_keyboard()
			if not self.cpu.halted:prev_pc=self.cpu.registers['PC'];self.cpu.execute_instruction()
			self.interrupt_controller.check_and_trigger_interrupt();i+=1
			if i>100000:i=0
			if i%10000==0:
				if i%10000==0:self.graphics.render_screen()
				state_window.fill((0,0,0));self.cpu.display_registers(state_window,font,0);self.keyboard.display_keyboard(state_window,font,200);self.memory.display_memory_dump(23718,32,state_window,font,400);pygame.draw.rect(border,self.graphics.colors[self.io_controller.border_color],(0,0,border.get_width(),border.get_height()));main_screen.blit(border,(0,0));main_screen.blit(screen,(self.border_size,self.border_size));main_screen.blit(state_window,(self.graphics.screen_width*self.pixel_size+self.border_size*2,0));pygame.display.flip()
		pygame.quit()
def main_loop():
	zx_emulator=ZX_Spectrum_Emulator()
	while True:
		selected_file,rom48,rom128=zx_spectrum_menu()
		if selected_file:
			zx_emulator.cpu.reset();zx_emulator.memory.reset();file_name,file_path=selected_file
			if file_name.lower().endswith('.zip'):file_name=os.path.basename(file_path);zx_emulator.memory.temp_files.append(('snapshot',file_path))
			if file_name.lower().endswith('z80'):
				if zx_emulator.memory.load_snapshot_z80_check48(file_path):file_name,file_path=rom48
				else:file_name,file_path=rom128
			if file_name.lower().endswith('sna'):file_name,file_path=rom48
			if file_name.lower().endswith('scr'):zx_emulator.emulate_load_screen(file_path);continue
			file_size=os.path.getsize(file_path);print(f"Loading file: {file_name}");print(f"File size: {file_size} bytes")
			if file_size>16*1024:print('Using load_rom128 method');zx_emulator.load_rom128(file_path)
			else:print('Using load_rom method');zx_emulator.load_rom(file_path)
			file_name,file_path=selected_file
			if file_name.lower().endswith('z80'):zx_emulator.memory.load_snapshot_z80(file_path,zx_emulator.cpu)
			if file_name.lower().endswith('sna'):zx_emulator.memory.load_snapshot_sna(file_path,zx_emulator.cpu)
			for(_,path)in zx_emulator.memory.temp_files:
				if os.path.exists(path):os.unlink(path)
			result=zx_emulator.emulate()
			if result!='OPEN_MENU':break
		else:print('No ROM file selected. Exiting.');break
if __name__=='__main__':main_loop()