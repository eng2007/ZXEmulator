import os
from python_minifier import minify

# Создаем каталог 'minified', если он не существует
minified_dir = 'minified'
if not os.path.exists(minified_dir):
    os.makedirs(minified_dir)

# Перебираем все файлы в текущем каталоге
for filename in os.listdir('.'):
    # Проверяем, что файл имеет расширение .py
    if filename.endswith('.py'):
        try:
            # Читаем содержимое файла
            print(f'Processing {filename}')
            with open(filename, 'r', encoding='utf-8') as file:
                code = file.read()
            
            # Минимизируем содержимое
            minified_code = minify(code, rename_locals = False, rename_globals = False, hoist_literals=False, remove_literal_statements=True)
            
            # Путь для сохранения минимизированного файла
            minified_filename = os.path.join(minified_dir, filename)
            
            # Записываем минимизированный код в файл
            with open(minified_filename, 'w', encoding='utf-8') as minified_file:
                minified_file.write(minified_code)
        except:
            print('Error')

print("Минимизация завершена.")
