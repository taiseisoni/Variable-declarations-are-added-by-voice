#マイク入力をするプログラム
#入力された音声データを[output.wav]として保存

import openai
import time
from io import BytesIO
import numpy as np
import soundfile as sf
import speech_recognition as sr
import time
from word2number import w2n

# APIキーをセット
openai.api_key = "自分のAPIキーを使用"

def main():
    recognizer = sr.Recognizer()
    
    # 「マイクから音声を取得」参照
    # 「マイクから音声を取得」参照
    with sr.Microphone(sample_rate=16_000) as source:
        #何か発声したら処理が行われる
        record_S = time.time() #record_S,Eで発声時間を計測
        #recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.pause_threshold = 0.9  # 無音を許容する秒数
        audio = recognizer.listen(source)
        record_E = time.time()
    #print("音声処理中 ...")
    # 音声データをWAV形式のバイト列として取得。
    wav_audio = audio.get_wav_data()
    #print("音声処理完了。")

    other_record_S = time.time()
    with open("output.wav", "wb") as f:
        f.write(wav_audio)
    #print("音声をoutput.wavに保存しました")

    open_audio= open("output.wav", "rb")
    #print("WhisperAPIで音声認識を行います...")
    recognision_S = time.time() #recognision_S,Eで音声認識の時間を計測

    #？wavファイルを作りながらapenai.Audio.transcribeをする方法を作るのもいいかも　パイプ
    #openai.Audio.translate()はdict型
    #result = openai.Audio.translate("whisper-1", open_audio, language = 'en')
    result = openai.Audio.transcribe("whisper-1", open_audio, language = "en")

    #結果をstr型でr_textに代入
    r_text = result["text"]

    #発声内容を書き込む
    with open("test06-output.txt", "w",encoding='utf8') as file:
        file.write(r_text.strip().replace(".", "").lower())

    r_text = r_text.replace("-"," ").replace(", ",",").replace(","," ")

    if r_text.strip().replace(".", "").lower() == "cancel" :
        #print("Cancel Voice input")
        return  # プログラム終了

    recognision_E = time.time()
    #print("発声内容：",r_text,"\n発声時間：",record_E-record_S,"\n音声認識時間：",recognision_E-recognision_S,"\n発声以外",recognision_E-other_record_S)

    #-------------------------------#
    ####ここから変数名を取得していく####
    #-------------------------------#
    match_pointer = False
    match_array = False

    declare_index = r_text.find(" pointer variable ")
    declare_target = " pointer variable "
    if declare_index != -1 : match_pointer = True    

    if declare_index == -1:
        declare_index = r_text.find(" pointer variables ")
        declare_target = " pointer variables "
        if declare_index != -1 : match_pointer = True

    if declare_index == -1:
        declare_index = r_text.find(" variable ")
        declare_target = " variable "
    elif declare_index == -1:
        declare_index = r_text.find(" variables ")
        declare_target = " variables "

    if declare_index == -1:
        declare_index = r_text.find(" array ")
        declare_target = " array "
        if declare_index != -1 : match_array = True
    elif declare_index == -1:
        declare_index = r_text.find(" arrays ")
        declare_target = " arrays "
        if declare_index != -1 : match_array = True

    declare_word = "zzerrorzz" #変数名が入るが、無ければ"zzerrorzz"

    if declare_index != -1 :
        #print("variable認識に成功")
        declare_start = declare_index + len(declare_target)
        
        # "of type " の位置を探す
        declare_end = r_text.find(" of type ", declare_start)

        # "of type "の前までを抽出
        declare_word = r_text[declare_start:declare_end].strip() if declare_end != -1 else r_text[declare_start:].strip()
        declare_word = declare_word.lower()

        result = []
        capitalize_next = False
        for char in declare_word:
            if capitalize_next and char.isalpha():
                result.append(char.upper())
                capitalize_next = False
            else:
                result.append(char)
            if char == " ":  # 次の文字を大文字にするフラグを立てる
                capitalize_next = True

        declare_word = "".join(result)
        # 抽出結果を整形
    if match_pointer: #ポインタだった場合
        word_before_pointer = r_text[:declare_index].strip().split()
        pointer_modifier = word_before_pointer[-1] if word_before_pointer else ""
        asterisk_count = 1 #デフォルト
        if pointer_modifier.lower() == "a":
            asterisk_count = 1
        else:
            try:
                asterisk_count = w2n.word_to_num(pointer_modifier)
            except ValueError: #数字以外だった場合の処理
                asterisk_count = 1
        declare_word = "*" * asterisk_count + declare_word.replace(" ", "") 
    else : declare_word = declare_word.replace(" ", "")
    #print("変数名 : ",declare_word," 変数型 : ",variable_type) 
    
    ###配列だった場合の処理###
    if declare_index != -1 and match_array:
        print("Array variable detected.")
        word_before_array = r_text[:declare_index].strip().split()
        array_modifier = word_before_array[-1] if word_before_array else ""
        dimention_count = 1 #デフォルト
        dimensions = []
        if array_modifier.lower() == "a" or array_modifier.lower() == "an":
            dimension_count = 1
        else:
            try:
                dimension_count = w2n.word_to_num(array_modifier)
            except ValueError:
                dimension_count = 1
            dimention_count = 1

        # 配列要素数を解析 ("with" 以降の数値を探す)
        element_start = r_text.find(" with ")
        if element_start != -1:
            element_start += len(" with ")
            element_description = r_text[element_start:].split(" element")[0].strip()
            # "by" または "x" を区切り文字として利用
            print("element_discription :",element_description)
            if " by " in element_description:
                element_parts = element_description.split(" by ")
            elif "x" in element_description:
                element_parts = element_description.split("x")
            else: element_parts = [element_description]
            print("element_parts : ",element_parts)
            #各次元サイズを解析
            for part in element_parts:
                try:
                    dimensions.append(str(w2n.word_to_num(part)))
                except ValueError:
                    print("Array error.")
                    dimensions.append("")
        # 次元数と要素数を対応付けて宣言を生成
        while len(dimensions) < dimension_count:
            dimensions.append("")  # 要素数が不足している場合は空の要素数を補完
        #配列の宣言文を生成
        dimension_string = "][".join(dimensions)
        declare_word = f"{declare_word}[{dimension_string}]"
    #-----------------------------#
    ###ここから変数型を取得していく###
    #-----------------------------#
    variable_index = r_text.find(" type ") #何番目かを代入
    variable_target = " type "

    variable_type ="zzerrorzz" #変数型が入るが、無ければNone

    if variable_index != -1: #variable_declareを検索する
        variable_start = variable_index + len(variable_target)

        # type以降をすべて取得
        potential_type = r_text[variable_start:].strip()

        if declare_target == " array " or declare_target == " arrays ": 
            # "with" の位置を探す
            with_index = potential_type.find(" with ")
            if with_index != -1:
                potential_type = potential_type[:with_index].strip()
        else:
            for i, char in enumerate(potential_type):
                if char == "." or char == "\n":
                    potential_type = potential_type[:i]
                    break

        #間以外ののスペースを除去して整形
        variable_type = potential_type.strip()
        variable_type = variable_type.lower()

        #それぞれの単語の後ろにスペースを挿入する処理     
        if "unsigned" in variable_type:
            variable_type = space_after_keyword(variable_type, "unsigned")
        
        elif "signed" in variable_type:
            variable_type = space_after_keyword(variable_type, "signed")

        if "short" in variable_type:
            variable_type = space_after_keyword(variable_type, "short")
        
        if "long" in variable_type:
            variable_type = space_after_keyword(variable_type, "long")
            
        variable_type = variable_type.replace(".", "")    

    #変数型を書き込む
    with open("variable-type.txt", "w",encoding='utf8') as file:
        file.write(variable_type)

    #変数名を書き込む
    with open("declare-word.txt", "w") as file:
        file.write(declare_word)

###変数型を取り出すための空白の処理をする関数###
def space_after_keyword(variable_type: str, keyword: str) -> str:
    keyword_index = variable_type.find(keyword)
    if keyword_index != -1:
        # キーワードの直後の文字をチェック
        if keyword_index + len(keyword) < len(variable_type):
            next_char = variable_type[keyword_index + len(keyword)]
            if next_char != " ":
                # スペースを挿入
                variable_type = (
                    variable_type[: keyword_index + len(keyword)] 
                    + " " 
                    + variable_type[keyword_index + len(keyword):]
                )
    return variable_type

if __name__ == "__main__":
    main()
