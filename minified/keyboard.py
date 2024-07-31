import pygame,numpy as np
class Keyboard:
	def __init__(self,io_controller):self.io_controller=io_controller;self.keyboard_matrix=np.zeros((8,8),dtype=bool);self.keymap={pygame.K_1:(0,0),pygame.K_2:(0,1),pygame.K_3:(0,2),pygame.K_4:(0,3),pygame.K_5:(0,4),pygame.K_0:(1,0),pygame.K_9:(1,1),pygame.K_8:(1,2),pygame.K_7:(1,3),pygame.K_6:(1,4),pygame.K_q:(2,0),pygame.K_w:(2,1),pygame.K_e:(2,2),pygame.K_r:(2,3),pygame.K_t:(2,4),pygame.K_p:(3,0),pygame.K_o:(3,1),pygame.K_i:(3,2),pygame.K_u:(3,3),pygame.K_y:(3,4),pygame.K_a:(4,0),pygame.K_s:(4,1),pygame.K_d:(4,2),pygame.K_f:(4,3),pygame.K_g:(4,4),pygame.K_RETURN:(5,0),pygame.K_l:(5,1),pygame.K_k:(5,2),pygame.K_j:(5,3),pygame.K_h:(5,4),pygame.K_LSHIFT:(6,0),pygame.K_z:(6,1),pygame.K_x:(6,2),pygame.K_c:(6,3),pygame.K_v:(6,4),pygame.K_SPACE:(7,0),pygame.K_RSHIFT:(7,1),pygame.K_m:(7,2),pygame.K_n:(7,3),pygame.K_b:(7,4),pygame.K_BACKSPACE:(0,5),pygame.K_LEFT:(0,6),pygame.K_DOWN:(0,7),pygame.K_UP:(1,5),pygame.K_RIGHT:(1,6),pygame.K_F3:(1,7),pygame.K_F4:(2,5),pygame.K_F1:(2,6),pygame.K_F2:(2,7),pygame.K_F5:(3,5),pygame.K_ESCAPE:(3,6),pygame.K_TAB:(3,7),pygame.K_CAPSLOCK:(4,5),pygame.K_LCTRL:(4,6),pygame.K_LALT:(4,7),pygame.K_F6:(5,5),pygame.K_F7:(5,6),pygame.K_F8:(5,7),pygame.K_F9:(6,5),pygame.K_F10:(6,6),pygame.K_F11:(6,7),pygame.K_F12:(7,5),pygame.K_RCTRL:(7,6),pygame.K_RALT:(7,7)};self.port=[63486,61438,64510,57342,65022,49150,65278,32766]
	def read_keyboard(self):
		pressed_keys=pygame.key.get_pressed()
		for(key,(row,col))in self.keymap.items():self.keyboard_matrix[(row,col)]=pressed_keys[key]
	def read_port_fe(self,port):
		keyboard_line=~port&65280;result=255
		for row in range(8):
			cur_line=~self.port[row]&65280
			if keyboard_line&cur_line!=0:
				row_value=0
				for col in range(8):
					if self.keyboard_matrix[(row,col)]:row_value|=1<<col
				result&=~row_value&255
		return result
	def get_matrix(self):return self.keyboard_matrix
	def display_keyboard(self,screen,font,offset):
		x,y=10,10+offset;row_text='KEYBOARD (ZX Spectrum 128)';text=font.render(row_text,True,(255,255,255));screen.blit(text,(x,y));y+=20
		for(row_index,row)in enumerate(self.keyboard_matrix):row_text=f"Row {row_index}: "+' '.join('P'if pressed else'.'for pressed in row);row_text+=f" {self.port[row_index]:04X} {self.read_port_fe(self.port[row_index]):08b}";text=font.render(row_text,True,(255,255,255));screen.blit(text,(x,y));y+=20