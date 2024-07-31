import os
from python_minifier import minify
minified_dir='minified'
if not os.path.exists(minified_dir):os.makedirs(minified_dir)
for filename in os.listdir('.'):
	if filename.endswith('.py'):
		try:
			print(f"Processing {filename}")
			with open(filename,'r',encoding='utf-8')as file:code=file.read()
			minified_code=minify(code,rename_locals=False,rename_globals=False,hoist_literals=False,remove_literal_statements=True);minified_filename=os.path.join(minified_dir,filename)
			with open(minified_filename,'w',encoding='utf-8')as minified_file:minified_file.write(minified_code)
		except:print('Error')
print('Минимизация завершена.')