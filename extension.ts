//Pythonコードを呼び出すプログラム
//開かれているCエディタに変数型と変数名を書き込む

import * as vscode from 'vscode';
import { exec } from "child_process";
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';


export function activate(context: vscode.ExtensionContext) {
	console.log('Congratulations, your extension "vscode-omikuji" is now active!');

	/*-------------------------------------#
	読み取った変数名と変数型を挿入する関数
	#---------------------------------------*/
	async function insertVariable(VariableType: string, VariableName: string): Promise<void> {
        console.log('Your extension "vscode-omikuji" is now active!');

        fs.writeFileSync('variable-type.txt',VariableType,{encoding:'utf-8'});
        fs.writeFileSync('declare-word.txt',VariableName,{encoding:'utf-8'});	
		let editor = vscode.window.activeTextEditor;
		if (!editor) {
			vscode.window.showInformationMessage('アクティブなエディタが見つかりません。');
			return;
		}

		// カーソルの位置を取得
		let position = editor.selection.active;
	    let filePath = editor.document.uri.fsPath;

		if (editor.document.isDirty) {
			const tempPath = path.join(os.tmpdir(), 'temp_unsaved_file.c');
			fs.writeFileSync(tempPath, editor.document.getText(), { encoding: 'utf-8' });
			//vscode.window.showInformationMessage(`未保存のファイルを一時保存しました: ${tempPath}`);
			//vscode.env.clipboard.writeText(tempPath);
			filePath = tempPath
		    //vscode.window.showInformationMessage('ファイルパスがクリップボードにコピーされました。');
		}

		// カーソル情報を保存するためのファイルパス
		let cursorFilePath = './cursor_position.json';

		// カーソル情報をJSON形式で書き出す
		let cursorData = {
			line: position.line + 1, // 1-based index
			column: position.character + 1, // 1-based index
			file: filePath
		};

		fs.writeFileSync(cursorFilePath, JSON.stringify(cursorData, null, 2));
		//vscode.window.showInformationMessage('カーソル位置を保存しました。Pythonで処理を行います。');

		//コード解析Pythonスクリプトを実行
		//ファイルパスを適切なものに変更
		exec(`python Clang.py`, { encoding: "utf8" }, async (error, stdout, stderr) => {
			if (error) {
				console.error(`Pythonスクリプト実行エラー: ${error}`);
				vscode.window.showInformationMessage('Pythonスクリプトの実行に失敗しました。');
				return;
			}
			//vscode.window.showInformationMessage(`Python実行結果: ${stdout}`);
            try {
                //ファイルを読み込んで、行分割する
                let insertion = fs.readFileSync('insertion.txt', 'utf-8').trim();
                console.log(`Updated insertion.txt content:\n${insertion}`);
                let lines = insertion.split('\n').map(line => line); 
                let setline = parseInt(lines[0].trim());
                let twoline = lines[1] || ""; //改行か宣言が挿入される
                const threeline= lines[2] || ""; //twolineが改行だった場合のみ宣言が入る仕様
                //Cコードに挿入する
                if (!(isNaN(setline)) && twoline.trim()) { //twolineに宣言文があるときに実行される
                    //vscode.window.showInformationMessage(`既存にある変数型に追加`);
					await editor.edit(editBuilder => {
						let targetLine = editor.document.lineAt(setline - 1); // 0-based index
						let range = targetLine.range; // 上書き対象行の範囲を取得
						editBuilder.replace(range, `${twoline}`); // 上書き
					});
                    await editor.document.save();
					vscode.window.showInformationMessage(`${setline}行目に既存変数型${VariableType}型の${VariableName}を宣言。`);
				} else {
                    //vscode.window.showInformationMessage(`新規型の変数を追加`);
                    await editor.edit(editBuilder => {
                        const targetLine = editor.document.lineAt(setline - 1); // 関数の行
                        const insertPosition = targetLine.range.end; // 行の末尾
                        editBuilder.insert(insertPosition, `\n\t${threeline}`);
						vscode.window.showInformationMessage(`${setline +1}行目に新規変数型${VariableType}型の${VariableName}を宣言。`);
                    });
				}

            } catch (err) {
                console.error(`Error reading insertion.txt: ${err}`);
            }
		});
    }

	////////////////////////////
	/*  音声認識システムの開始  */
	////////////////////////////
	let voice = vscode.commands.registerCommand('vscode-omikuji.voiceinput', () => {
		const voicestart = new Date().getTime();
		//vscode.window.showInformationMessage('Hello World from vscode-omikuji!');
		let VariableType = "zzerrorzz";
		let VariableName = "zzerrorzz";
		function runPythonScript(): void {	
			vscode.window.showInformationMessage('音声読み取りを開始。中断したい場合はキャンセルと発言。');
			//ファイルパスを適切なものに変更
			exec("python VoiceInput.py", { encoding: "utf8" }, async(error, stdout, stderr) => {
				if (error) {
			  		console.error(`Error executing Python script: ${error}`);
					vscode.window.showInformationMessage('cant open python file.');
			  		return;
				}
				//vscode.window.showInformationMessage(`voice input実行結果: ${stdout}`);

				try {
					//ファイルパスを適切なものに変更
                    let inputword = fs.readFileSync('Voice-output.txt', 'utf-8').trim();
					vscode.window.showInformationMessage(`Your voice input : ${inputword}`);
					if (inputword == "cancel"){
						vscode.window.showInformationMessage(`cancelと入力されたので終了します。`);
						return;
					} else{
						
						try {
							VariableType = fs.readFileSync('variable-type.txt', 'utf-8').trim();
						} catch (err) {
							console.error(`Error reading variable-type.txt: ${err}`);
						}

						
						try {
							VariableName = fs.readFileSync('declare-word.txt', 'utf-8').trim();
						} catch (err) {
							console.error(`Error reading declare-word.txt: ${err}`);
						}

						if (VariableType === "zzerrorzz" || VariableName === "zzerrorzz") {
							//vscode.window.showInformationMessage('正常な変数名や変数型ではありませんでした。再試行します...');
							vscode.window.showInformationMessage('正常な変数名や変数型ではありませんでした。終了します。');
							//runPythonScript(); // 再実行
							const voiceend = new Date().getTime();
							console.log(`Hand input Execution Time:[${VariableType} ${VariableName}] ${voiceend - voicestart} ms`);	
							return;
						}

						await insertVariable(VariableType, VariableName);
					}
                } catch (err) {
                    console.error(`Error reading Voice-output.txt: ${err}`);
                }
				const voiceend = new Date().getTime();
				console.log(`Hand input Execution Time:[${VariableType} ${VariableName}] ${voiceend - voicestart} ms`);										
			});
		}
		
		
		// runPythonScript関数を呼び出し
		runPythonScript();		
	});
	
	let hand = vscode.commands.registerCommand('vscode-omikuji.handinput', async () => {
		const handstart = new Date().getTime();
		// 変数型を入力させる
		let VariableType = await vscode.window.showInputBox({
			placeHolder: 'int, float, string...',
			prompt: 'Enter the variable type (e.g., int, string):'
		});
		if (!VariableType) {
			vscode.window.showInformationMessage('変数型が入力されませんでした。');
			return;
		}
	
		// 変数名を入力させる
		let VariableName = await vscode.window.showInputBox({
			placeHolder: 'variableName',
			prompt: 'Enter the variable name:'
		});
		if (!VariableName) {
			vscode.window.showInformationMessage('変数名が入力されませんでした。');
			return;
		}
		await insertVariable(VariableType, VariableName);
		const handend = new Date().getTime();
		console.log(`Hand input Execution Time:[${VariableType} ${VariableName}] ${handend - handstart} ms`);
	});
	context.subscriptions.push(voice);
	context.subscriptions.push(hand);
}

// This method is called when your extension is deactivated
export function deactivate() {}
