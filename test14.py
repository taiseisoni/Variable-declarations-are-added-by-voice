#カーソルがある関数の中身を見て、挿入する変数宣言の文章をInsertion.txtとして作る
#正常に動作する

import json
import os
import clang.cindex
import re

# Clangライブラリのパスを設定
clang.cindex.Config.set_library_path(r"C:\Program Files\LLVM\bin")

def normalize_type(type_spelling):
    """
    ポインタや配列修飾子を無視して基本型を抽出
    """
    return type_spelling.replace('*', '').replace('[', '').replace(']', '').strip()
    
#指定された行を取得し、宣言文の末尾に新しい変数を追加する。
def append_to_existing_declaration(file_path, target_line, declare_word):   
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 対象行のインデックスを計算
    line_index = target_line - 1
    original_line = lines[line_index].strip()

    # コメントを検出
    comment_match = re.search(r'(//.*|/\*.*?\*/)', original_line)

    if comment_match:
        # コメントを取り除いた部分を取得
        code_part = original_line[:comment_match.start()].rstrip()
        comment_part = original_line[comment_match.start():]

        if code_part.endswith(';'):
            # セミコロンの前に新しい変数を挿入
            code_part = code_part[:-1] + f", {declare_word};"
        else:
            # セミコロンがない場合、そのまま追加
            code_part += f", {declare_word};"

        # 修正後の行を構築
        modified_line = f"{code_part} {comment_part}"

    else:
    #コメントが無い場合、セミコロンの有無を確認。ない場合は追加
        if original_line.endswith(';'):
            modified_line = original_line[:-1]  # セミコロンを削除
        else:
            modified_line = original_line

        # 新しい変数を追加してセミコロンを再付与
        modified_line += f", {declare_word};\n"
    with open('insertion.txt', 'w', encoding='utf-8') as insertion_file:
        insertion_file.write(f"{target_line}\n\t{modified_line}\n")

def show_variable_types_in_function(file_path, line, column):
    index = clang.cindex.Index.create()
    translation_unit = index.parse(file_path)
    with open('variable-type.txt', 'r', encoding='utf-8') as f:
        target_variable_type = f.read().strip()
    with open('declare-word.txt', 'r', encoding='utf-8') as f:
        declare_word = f.read().strip()

    find_any_variables = False

    def is_within_range(cursor):
        # カーソルがソースファイル内にあるか確認
        if cursor.location.file is None or cursor.location.file.name != file_path:
            return False
        extent = cursor.extent
        start = extent.start
        end = extent.end
        return (
        start.line < line < end.line or
        (start.line == line and start.column <= column) or
        (end.line == line and column <= end.column)
    )

    def find_function_and_variables(cursor):
        #関数でカーソルの中か否かを判定する
        
        if cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL and cursor.location.file and cursor.location.file.name == file_path and is_within_range(cursor):
            print(f"Cursor is in function: {cursor.spelling}")
            variables = {} #辞書型を用意
            target_line = None
            match_variable_type = False

            for child in cursor.get_children():
                if child.kind == clang.cindex.CursorKind.COMPOUND_STMT:
                    for stmt in child.get_children():
                        if stmt.kind == clang.cindex.CursorKind.DECL_STMT:
                            find_any_variables = True
                            for var in stmt.get_children():
                                if var.kind == clang.cindex.CursorKind.VAR_DECL:
                                    # 変数の名前、型、位置を取得
                                    var_name = var.spelling
                                    var_type = var.type.spelling.strip()
                                    start_line = var.extent.start.line
                                    #挿入する変数の型と記述されている変数型が一致
                                    #print(f"target_variable_type:{target_variable_type} var_type:{var_type}")
                                    if normalize_type(var_type) == normalize_type(target_variable_type): #挿入する変数型が既に存在する
                                        match_variable_type = True
                                        if target_line is None: #挿入する行を記録
                                            target_line = start_line
                                            #print(f"Update targetline:{target_line},Start line:{start_line}")
                    if match_variable_type and target_line :
                        #print("Macth any variables.")
                        append_to_existing_declaration(file_path, target_line,declare_word)
                        variables[target_line] = []
                        variables[target_line].append(declare_word)
                        return variables
                    
            if not match_variable_type: #関数内だが同じ変数型が無い
                #ここの条件を満たしたらvariablesに挿入する式を追加したい。
                #print("No matching variable type found.")
                target_line = cursor.extent.start.line
                if target_line not in variables:
                    variables[target_line] =[]
                variables[target_line].append(declare_word)
                with open('insertion.txt', 'w', encoding='utf-8') as insertion_file:
                    insertion_file.write(f"{target_line}\n\n{target_variable_type} {declare_word};\n")
                return variables

            if target_line in variables:
                #print("Save as the same variable type.")
                with open('insertion.txt','w',encoding='utf-8')as insertion_file:
                    variables_to_write =", ".join(variables[target_line])
                    insertion_file.write(f"{target_line}\n\t{target_variable_type} {variables_to_write}, {declare_word};\n")
            return variables        
        for child in cursor.get_children():
            result = find_function_and_variables(child)
            if result:
                return result
        return None
    
    variables_by_line = find_function_and_variables(translation_unit.cursor)
    if variables_by_line:
        #print("Variables grouped by line:")
        for line, variable_names in variables_by_line.items():
            print(f"Line {line}: {', '.join(variable_names)}")
    else:   #関数外だった場合に実行される
        #print("Cursor is outside of any function.\n")
        with open('insertion.txt','w',encoding='utf-8')as insertion_file:
            # 新しい行（関数の末尾）に移動した際にファイルに保存
            insertion_file.write(f"{line}\n{target_variable_type} {declare_word};\n")



def process_cursor_position():
    cursor_file = './cursor_position.json'

    if not os.path.exists(cursor_file):
        print("Cursor information not found.")
        return

    with open(cursor_file, 'r', encoding='utf-8') as f:
        cursor_data = json.load(f)

    line = cursor_data.get('line')
    column = cursor_data.get('column')
    file_path = cursor_data.get('file')

    if not line or not column or not file_path:
        print("Cursor information is incomplete.")
        return

    #print(f"Cursor position: {file_path}, line: {line}, column: {column}")
    show_variable_types_in_function(file_path, line, column)

if __name__ == "__main__":
    process_cursor_position()
